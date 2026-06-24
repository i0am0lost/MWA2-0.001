#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
module_scan.py - read-only catalog of all AAU modules (name + description).
================================================================================
AAU modules live as one file each under data/override/module/ (no extension, the
filename IS the module name). Each file is a serialized Shared::Triggers::Module:
    DWORD name_len   (char count)   + name        (UTF-16LE, name_len*2 bytes)
    DWORD desc_len   (char count)   + description (UTF-16LE, desc_len*2 bytes)
    ... (vector<Trigger> etc. -- NOT needed for the catalog)
(Format from AAUnlimited Module.h + Serialize.h: wstring = DWORD len + len*2 bytes.)

This is the read-only basis for the condition->module MAP (the hand-curated "brain"):
the machine lists WHAT modules exist + their descriptions; the mapping (state -> module)
stays curated. Mechanical effect (trigger logic) is NOT machine-readable (project notes 5.3).

Output: module_catalog.json (machine-readable for the map) + module_catalog.md (to read).
Usage: python module_scan.py [module_dir]
"""

import json
import os
import struct
import sys

DEFAULT_DIR = r"school\data\override\module"


def read_wstring(buf, off):
    """(string, next_off) for a serialized std::wstring at buf[off]: DWORD len + len*2 bytes UTF-16LE."""
    (n,) = struct.unpack_from("<I", buf, off)
    off += 4
    if n > 100000 or off + n * 2 > len(buf):      # sanity guard against a misread length
        raise ValueError("implausible wstring length %d at %d" % (n, off - 4))
    s = buf[off:off + n * 2].decode("utf-16-le", errors="replace")
    return s, off + n * 2


def scan_module_file(path):
    """Return {name, description, file, size, trigger_bytes} for one module file."""
    buf = open(path, "rb").read()
    name, off = read_wstring(buf, 0)
    desc, off = read_wstring(buf, off)
    return {"name": name, "description": desc.replace("\r\n", " ").replace("\n", " ").strip(),
            "file": os.path.basename(path), "size": len(buf), "trigger_bytes": len(buf) - off}


def scan_dir(d):
    out, errors = [], []
    for fn in sorted(os.listdir(d)):
        p = os.path.join(d, fn)
        if not os.path.isfile(p):
            continue
        try:
            out.append(scan_module_file(p))
        except Exception as e:
            errors.append((fn, str(e)))
    return out, errors


def main(argv):
    d = argv[1] if len(argv) > 1 else DEFAULT_DIR
    mods, errors = scan_dir(d)
    mods.sort(key=lambda m: m["name"].lower())

    with open("module_catalog.json", "w", encoding="utf-8") as f:
        json.dump(mods, f, ensure_ascii=False, indent=1)

    with open("module_catalog.md", "w", encoding="utf-8") as f:
        f.write("# AAU Module Catalog (auto-scanned, read-only)\n\n")
        f.write("%d modules from `%s`. Name + description are read from the file; the *mechanical "
                "effect* is NOT machine-readable -> the condition->module MAP stays hand-curated.\n\n"
                % (len(mods), d))
        f.write("| Module | Description |\n|---|---|\n")
        for m in mods:
            desc = m["description"].replace("|", "\\|")
            f.write("| **%s** | %s |\n" % (m["name"].replace("|", "\\|"), desc))

    print("scanned %d modules (%d errors) -> module_catalog.json + module_catalog.md"
          % (len(mods), len(errors)))
    if errors:
        for fn, e in errors[:10]:
            print("  ERR %s: %s" % (fn, e))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
