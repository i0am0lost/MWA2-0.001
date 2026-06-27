#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""card_globals.py - read/insert an AAU card Global Variable (the m_globalVars / 'TrGv' member) in a
card .png's aaUd chunk. Used to embed a stable per-character id ("mwa_id") that survives renames, editor
re-saves and world transfers, and is cheaply readable from the runtime hook (a vector walk).

FORMAT (source: AAU Serialize.h / Triggers.h; tags are stored byte-reversed on disk, e.g. 'TrGv'->'vGrT'):
  aaUd member = [4-byte tag][serialized member]  (NO per-member length prefix; parse by type)
  m_globalVars = vector<GlobalVariable> = [u32 count][count x GlobalVariable]
  GlobalVariable = [u32 type][wstring name][Value defaultValue][Value currentValue][u8 initialized]
                   (the DWORD `id` field is NOT serialized)
  wstring = [u32 char_count][char_count x UTF-16LE]   (no NUL)
  Value   = [u32 type][payload]   type: 1=INT(i32) 2=BOOL(u8) 3=FLOAT(f32) 4=STRING(wstring)

INSERT trick (no need to parse existing elements): splice our serialized GlobalVariable right after the
count field and bump the count by 1. FromBuffer reads count+1 elements; ours first, originals intact.
"""
import os
import struct
import zlib

import card_edit as ce   # reuse _aaud / _png_chunks / _replace_aaud / _read_wstr

TYPE_INT, TYPE_BOOL, TYPE_FLOAT, TYPE_STRING = 1, 2, 3, 4
TRGV_REV = b"vGrT"   # on-disk (byte-reversed) tag for 'TrGv' (m_globalVars)


def _wstr(s):
    return struct.pack("<I", len(s)) + s.encode("utf-16-le")


def _ser_int_global(name, value):
    """Serialize one GlobalVariable holding an INT (default==current==value, initialized=true)."""
    val = struct.pack("<I", TYPE_INT) + struct.pack("<i", value)   # Value{INT, value}
    return (struct.pack("<I", TYPE_INT)   # GlobalVariable.type = INT
            + _wstr(name)                  # name
            + val                          # defaultValue
            + val                          # currentValue
            + b"\x01")                     # initialized = true


def _read_value(b, off):
    (t,) = struct.unpack_from("<I", b, off); off += 4
    if t == TYPE_INT:    (v,) = struct.unpack_from("<i", b, off); return ("int", v), off + 4
    if t == TYPE_BOOL:   (v,) = struct.unpack_from("<B", b, off); return ("bool", v), off + 1
    if t == TYPE_FLOAT:  (v,) = struct.unpack_from("<f", b, off); return ("float", v), off + 4
    if t == TYPE_STRING: s, off = ce._read_wstr(b, off);          return ("str", s), off
    return ("invalid", t), off


def _read_global(b, off):
    (gtype,) = struct.unpack_from("<I", b, off); off += 4
    name, off = ce._read_wstr(b, off)
    dval, off = _read_value(b, off)
    cval, off = _read_value(b, off)
    (init,) = struct.unpack_from("<B", b, off); off += 1
    return {"type": gtype, "name": name, "default": dval, "current": cval, "init": init}, off


def read_globals_from_aaud(aaud):
    """Parse the TrGv member of an aaUd buffer. Returns (list_of_globals, dmrt_off, liststart, list_end)
    or (None, ...) if no TrGv member. list_end is the byte just past the last element."""
    i = aaud.find(TRGV_REV)
    if i < 0:
        return None, -1, -1, -1
    (count,) = struct.unpack_from("<I", aaud, i + 4)
    pos = liststart = i + 8
    out = []
    for _ in range(count):
        g, pos = _read_global(aaud, pos)
        out.append(g)
    return out, i, liststart, pos


def insert_int_global_in_aaud(aaud, name, value):
    """Return a NEW aaud bytearray with an INT global (name,value) inserted into the TrGv member (or a
    fresh TrGv appended at the end if none exists), count bumped."""
    aaud = bytearray(aaud)
    elem = _ser_int_global(name, value)
    i = aaud.find(TRGV_REV)
    if i < 0:
        # no TrGv member: append a fresh one at the end of the member region
        aaud += TRGV_REV + struct.pack("<I", 1) + elem
        return aaud
    (count,) = struct.unpack_from("<I", aaud, i + 4)
    aaud[i + 8:i + 8] = elem                      # splice element right after the count field
    struct.pack_into("<I", aaud, i + 4, count + 1)  # bump count
    return aaud


def add_int_global(card_path, name, value, out_path):
    """Insert an INT global into a card .png; rebuild the aaUd chunk (length + CRC). Returns new count."""
    buf = open(card_path, "rb").read()
    aaud, aoff, alen = ce._aaud(buf)
    new_aaud = insert_int_global_in_aaud(aaud, name, value)
    with open(out_path, "wb") as f:
        f.write(ce._replace_aaud(buf, aoff, alen, new_aaud))
    gl, *_ = read_globals_from_aaud(new_aaud)
    return len(gl) if gl else 0
