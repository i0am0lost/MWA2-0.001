#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
card_edit.py - read/add AAU modules on a character card (.png), the day-boundary "module editor".
================================================================================================
AAU stores a card's data in a custom PNG chunk `aaUd` (version 3). Inside it, the module list is the
member tagged `dMrT` (4-byte tags are stored reversed -> "TrMd"): a `uint32 count` followed by `count`
module elements laid out back-to-back. KEY FACT (verified): a card module element is **byte-identical to
that module's standalone definition file** in `data/override/module/<name>` (the same file module_scan.py
reads). So we never need to decode the trigger serialization: to ADD a module we splice in its definition
file's bytes, bump the count, and fix the PNG chunk length + CRC32. To WALK the list we advance by each
element's definition-file size.

This is the EXTERNAL, day-boundary path (modules are NOT writable from Lua at runtime - project notes 4.6).
Verify in isolation (round-trip) before any pipeline use.
"""

import os
import struct
import zlib

from _root import ROOT
DEF_MODDIR = os.path.join(ROOT, "school", "data", "override", "module")


def _png_chunks(buf):
    """List PNG chunks as [type, data, file_off, data_len]. PNG chunk length is big-endian."""
    out, off = [], 8
    while off + 8 <= len(buf):
        (ln,) = struct.unpack_from(">I", buf, off)
        out.append([buf[off + 4:off + 8], buf[off + 8:off + 8 + ln], off, ln])
        off += 12 + ln
    return out


def _aaud(buf):
    """Return (aaUd_data, file_offset, data_len) for the card's aaUd chunk."""
    for typ, data, off, ln in _png_chunks(buf):
        if typ == b"aaUd":
            return data, off, ln
    raise ValueError("no aaUd chunk (not an AAU card?)")


def _read_wstr(b, off):
    """(string, next_off) for a serialized std::wstring: uint32 char-count + count*2 bytes UTF-16LE."""
    (n,) = struct.unpack_from("<I", b, off)
    return b[off + 4:off + 4 + n * 2].decode("utf-16-le"), off + 4 + n * 2


def _replace_aaud(buf, aoff, alen, new_aaud):
    """Rebuild the PNG with the aaUd chunk replaced (new length + fresh CRC32 over type+data). The original
    aaUd chunk occupies [aoff .. aoff+12+alen]; everything before and after (incl. IEND + any trailer) is
    preserved verbatim."""
    nb = bytes(new_aaud)
    chunk = struct.pack(">I", len(nb)) + b"aaUd" + nb + struct.pack(">I", zlib.crc32(b"aaUd" + nb) & 0xffffffff)
    return buf[:aoff] + chunk + buf[aoff + 12 + alen:]


def read_modules(card_path, moddir=DEF_MODDIR):
    """Read a card's module list. Returns dict with count, names, and list-region offsets (within aaUd).
    Walks by definition-file size (element == its def file). Raises if an element's def file is missing
    (then the size is unknown -> we cannot safely walk/splice that card)."""
    aaud, _, _ = _aaud(open(card_path, "rb").read())
    i = aaud.find(b"dMrT")
    if i < 0:
        raise ValueError("no dMrT (module list) member in aaUd")
    (count,) = struct.unpack_from("<I", aaud, i + 4)
    pos = liststart = i + 8
    names = []
    for _ in range(count):
        name, _after = _read_wstr(aaud, pos)
        names.append(name)
        deff = os.path.join(moddir, name)
        if not os.path.isfile(deff):
            raise ValueError("element %r has no definition file -> cannot size it" % name)
        db = open(deff, "rb").read()
        # SAFETY: an element is byte-identical to its def file. If it is NOT, the card carries a
        # customized/older version of this module -> its true size is unknown -> walking by def-file
        # size would desync and a splice would corrupt the card. Refuse rather than risk it.
        if aaud[pos:pos + len(db)] != db:
            raise ValueError("element %r at %d does not match its definition file (customized card?) "
                             "-> cannot safely edit this card" % (name, pos))
        pos += len(db)
    return {"count": count, "names": names, "dmrt_off": i, "liststart": liststart,
            "list_end": pos, "aaud_len": len(aaud)}


def add_module(card_path, module_name, out_path, moddir=DEF_MODDIR):
    """Add `module_name` to a card by splicing its definition file at the end of the module list, bumping
    the dMrT count, and rebuilding the aaUd chunk (new length + CRC32). Writes to out_path. Returns the
    new module count. Idempotent guard: raises if the module is already present."""
    info = read_modules(card_path, moddir)
    if module_name in info["names"]:
        raise ValueError("%r already on the card" % module_name)
    deff_path = os.path.join(moddir, module_name)
    if not os.path.isfile(deff_path):
        raise ValueError("no definition file for %r" % module_name)
    element = open(deff_path, "rb").read()

    buf = open(card_path, "rb").read()
    aaud, aoff, alen = _aaud(buf)
    aaud = bytearray(aaud)
    i = info["dmrt_off"]
    # splice the element at the end of the module list + bump the count
    aaud[info["list_end"]:info["list_end"]] = element
    struct.pack_into("<I", aaud, i + 4, info["count"] + 1)
    with open(out_path, "wb") as f:
        f.write(_replace_aaud(buf, aoff, alen, aaud))
    return info["count"] + 1


def remove_module(card_path, module_name, out_path, moddir=DEF_MODDIR):
    """Remove `module_name` from a card: cut its element bytes (= its def-file size), decrement the dMrT
    count, rebuild the aaUd chunk. Removes the FIRST occurrence if a module appears more than once. Writes
    to out_path. Returns the new module count. Raises if the module is not present."""
    info = read_modules(card_path, moddir)               # safety: refuses customized cards
    if module_name not in info["names"]:
        raise ValueError("%r not on the card" % module_name)
    buf = open(card_path, "rb").read()
    aaud, aoff, alen = _aaud(buf)
    aaud = bytearray(aaud)
    i = info["dmrt_off"]
    pos = info["liststart"]
    for name in info["names"]:                           # walk to the target element by def-file size
        size = os.path.getsize(os.path.join(moddir, name))
        if name == module_name:
            del aaud[pos:pos + size]                     # cut this element
            struct.pack_into("<I", aaud, i + 4, info["count"] - 1)
            break
        pos += size
    with open(out_path, "wb") as f:
        f.write(_replace_aaud(buf, aoff, alen, aaud))
    return info["count"] - 1


def verify_png(path):
    """Structural check: every PNG chunk's stored CRC matches the data. Returns (ok, n_chunks)."""
    buf = open(path, "rb").read()
    if buf[:8] != b"\x89PNG\r\n\x1a\n":
        return False, 0
    off, n = 8, 0
    while off + 12 <= len(buf):
        (ln,) = struct.unpack_from(">I", buf, off)
        typ = buf[off + 4:off + 8]
        (stored,) = struct.unpack_from(">I", buf, off + 8 + ln)
        if zlib.crc32(buf[off + 4:off + 8 + ln]) & 0xffffffff != stored:
            return False, n
        n += 1
        if typ == b"IEND":
            break
        off += 12 + ln
    return True, n
