#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
module_format.py - DEFINITIVE codec for AAU trigger module files (data/override/module/<Name>).
================================================================================================
Format fully reverse-engineered from AAU source `AAUnlimited/Functions/Serialize.h` (the generic
ReadData<T>/WriteData<T> serializer) + Triggers.h/Value.h/Expressions.h. This module can DECODE an
existing module to a nested dict and ENCODE a dict back to byte-exact bytes (roundtrip-proven).

PRIMITIVES (Serialize.h):
  u32   = 4 bytes LE                                  (ReadData<DWORD>/<int>, `*(T*)buffer`)
  int   = 4 bytes LE signed
  float = 4 bytes
  bool  = 1 BYTE                                       (sizeof(bool)==1 ; *(T*)buffer)
  wstr  = [u32 N][N * UTF-16LE code units]             (N = #chars, no BOM, no nul)
  vec<T>= [u32 count][count * T]

ENUMS:
  Types : INVALID=0, INT=1, BOOL=2, FLOAT=3, STRING=4
  EXPR  : INVALID=0, CONSTANT=1, VAR=2, NAMEDCONSTANT=3   (everything else => normal expr with params)

STRUCT LAYOUT (exact field order from each ReadData_sub):
  Module      = name:wstr, description:wstr, triggers:vec<Trigger>, globals:vec<GlobalVariable>,
                dependencies:vec<wstr>
  Trigger     = name:wstr, events:vec<PEvent>, vars:vec<Variable>, guiActions:vec<GUIAction>
                (NOTE: .actions/.owningCard/.broken/.bInitialized exist in the struct but are NOT
                 serialized -- actions are rebuilt at runtime from guiActions.)
  Variable    = type:Types(u32), name:wstr, defaultValue:PExpr
                (struct has a DWORD id but it is NOT serialized.)
  GlobalVar   = type:Types(u32), name:wstr, defaultValue:Value, currentValue:Value, initialized:bool
                (struct has a DWORD id but it is NOT serialized.)
  PExpr       = type:Types(u32), id:int(u32), then BY id:
                  id==1 CONSTANT      -> constant:Value
                  id==2 VAR           -> varName:wstr
                  id==3 NAMEDCONSTANT -> namedConstantId:int(u32)
                  else                -> actualParameters:vec<PExpr>
  PAction     = id:int(u32), actualParameters:vec<PExpr>
  PEvent      = id:int(u32), actualParameters:vec<PExpr>
  GUIAction   = action:PAction, subactions:vec<GUIAction>     (parent ptr NOT serialized)
  Value       = type:Types(u32), then BY type:
                  INT(1)->int  BOOL(2)->bool(1B)  FLOAT(3)->float  STRING(4)->wstr  default->nothing
"""

import struct
import sys
import json

# Types enum
T_INVALID, T_INT, T_BOOL, T_FLOAT, T_STRING = 0, 1, 2, 3, 4
# Expression special ids
EXPR_CONSTANT, EXPR_VAR, EXPR_NAMEDCONSTANT = 1, 2, 3


# --------------------------------------------------------------------------- reader
class Reader:
    def __init__(self, buf):
        self.b = buf
        self.o = 0

    def u32(self):
        (v,) = struct.unpack_from("<I", self.b, self.o); self.o += 4; return v

    def i32(self):
        (v,) = struct.unpack_from("<i", self.b, self.o); self.o += 4; return v

    def f32(self):
        (v,) = struct.unpack_from("<f", self.b, self.o); self.o += 4; return v

    def boolean(self):
        v = self.b[self.o]; self.o += 1; return bool(v)

    def wstr(self):
        n = self.u32()
        s = self.b[self.o:self.o + n * 2].decode("utf-16-le"); self.o += n * 2; return s

    def vec(self, fn):
        return [fn() for _ in range(self.u32())]

    def left(self):
        return len(self.b) - self.o


def r_value(r):
    t = r.u32()
    v = {"type": t}
    if t == T_INT:      v["val"] = r.i32()
    elif t == T_BOOL:   v["val"] = r.boolean()
    elif t == T_FLOAT:  v["val"] = r.f32()
    elif t == T_STRING: v["val"] = r.wstr()
    return v


def r_pexpr(r):
    t = r.u32()
    eid = r.i32()
    pe = {"type": t, "id": eid}
    if eid == EXPR_CONSTANT:
        pe["constant"] = r_value(r)
    elif eid == EXPR_VAR:
        pe["varName"] = r.wstr()
    elif eid == EXPR_NAMEDCONSTANT:
        pe["namedConstantId"] = r.i32()
    else:
        pe["params"] = r.vec(lambda: r_pexpr(r))
    return pe


def r_paction(r):
    return {"id": r.i32(), "params": r.vec(lambda: r_pexpr(r))}


def r_pevent(r):
    return {"id": r.i32(), "params": r.vec(lambda: r_pexpr(r))}


def r_guiaction(r):
    return {"action": r_paction(r), "subactions": r.vec(lambda: r_guiaction(r))}


def r_variable(r):
    return {"type": r.u32(), "name": r.wstr(), "default": r_pexpr(r)}


def r_globalvar(r):
    return {"type": r.u32(), "name": r.wstr(),
            "default": r_value(r), "current": r_value(r), "initialized": r.boolean()}


def r_trigger(r):
    return {"name": r.wstr(),
            "events": r.vec(lambda: r_pevent(r)),
            "vars": r.vec(lambda: r_variable(r)),
            "guiActions": r.vec(lambda: r_guiaction(r))}


def decode(buf):
    r = Reader(buf)
    m = {"name": r.wstr(), "description": r.wstr(),
         "triggers": r.vec(lambda: r_trigger(r)),
         "globals": r.vec(lambda: r_globalvar(r)),
         "dependencies": r.vec(lambda: r.wstr())}
    if r.left() != 0:
        raise ValueError("trailing %d bytes (parse incomplete) at offset %d" % (r.left(), r.o))
    return m


# --------------------------------------------------------------------------- writer
class Writer:
    def __init__(self):
        self.parts = []

    def u32(self, v):    self.parts.append(struct.pack("<I", v & 0xFFFFFFFF))
    def i32(self, v):    self.parts.append(struct.pack("<i", v))
    def f32(self, v):    self.parts.append(struct.pack("<f", v))
    def boolean(self, v): self.parts.append(b"\x01" if v else b"\x00")

    def wstr(self, s):
        enc = s.encode("utf-16-le")
        self.u32(len(enc) // 2)
        self.parts.append(enc)

    def vec(self, items, fn):
        self.u32(len(items))
        for it in items:
            fn(it)

    def out(self):
        return b"".join(self.parts)


def w_value(w, v):
    t = v["type"]
    w.u32(t)
    if t == T_INT:      w.i32(v["val"])
    elif t == T_BOOL:   w.boolean(v["val"])
    elif t == T_FLOAT:  w.f32(v["val"])
    elif t == T_STRING: w.wstr(v["val"])


def w_pexpr(w, pe):
    w.u32(pe["type"])
    w.i32(pe["id"])
    eid = pe["id"]
    if eid == EXPR_CONSTANT:
        w_value(w, pe["constant"])
    elif eid == EXPR_VAR:
        w.wstr(pe["varName"])
    elif eid == EXPR_NAMEDCONSTANT:
        w.i32(pe["namedConstantId"])
    else:
        w.vec(pe["params"], lambda p: w_pexpr(w, p))


def w_paction(w, pa):
    w.i32(pa["id"])
    w.vec(pa["params"], lambda p: w_pexpr(w, p))


def w_pevent(w, pe):
    w.i32(pe["id"])
    w.vec(pe["params"], lambda p: w_pexpr(w, p))


def w_guiaction(w, g):
    w_paction(w, g["action"])
    w.vec(g["subactions"], lambda s: w_guiaction(w, s))


def w_variable(w, v):
    w.u32(v["type"]); w.wstr(v["name"]); w_pexpr(w, v["default"])


def w_globalvar(w, g):
    w.u32(g["type"]); w.wstr(g["name"])
    w_value(w, g["default"]); w_value(w, g["current"]); w.boolean(g["initialized"])


def w_trigger(w, t):
    w.wstr(t["name"])
    w.vec(t["events"], lambda e: w_pevent(w, e))
    w.vec(t["vars"], lambda v: w_variable(w, v))
    w.vec(t["guiActions"], lambda g: w_guiaction(w, g))


def encode(m):
    w = Writer()
    w.wstr(m["name"]); w.wstr(m["description"])
    w.vec(m["triggers"], lambda t: w_trigger(w, t))
    w.vec(m["globals"], lambda g: w_globalvar(w, g))
    w.vec(m["dependencies"], lambda d: w.wstr(d))
    return w.out()


# --------------------------------------------------------------------------- cli / self-test
def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    path = argv[1]
    with open(path, "rb") as f:
        buf = f.read()
    print("# %s (%d bytes)" % (path, len(buf)))
    m = decode(buf)
    print("CLEAN PARSE (consumed all %d bytes)" % len(buf))
    re_enc = encode(m)
    if re_enc == buf:
        print("ROUNDTRIP OK (encode(decode(x)) == x, byte-exact)")
    else:
        print("ROUNDTRIP MISMATCH: re-encoded %d bytes vs original %d" % (len(re_enc), len(buf)))
        n = min(len(re_enc), len(buf))
        for i in range(n):
            if re_enc[i] != buf[i]:
                print("  first diff at byte %d: orig=%02x new=%02x" % (i, buf[i], re_enc[i]))
                break
    print(json.dumps(m, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
