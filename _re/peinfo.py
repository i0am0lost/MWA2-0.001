import os
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
"""Dev-only RE helper for AA2Play.exe. NOT part of the shipped package.
Prints PE layout + disassembles around a given RVA.
Usage:
  py peinfo.py                 -> PE overview + import table (file/IAT funcs)
  py peinfo.py 0xF36D0 [n]     -> disassemble n bytes (default 200) at RVA
"""
import sys, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = _BASE + r"\school\AA2Play.exe"

def load():
    pe = pefile.PE(EXE, fast_load=True)
    pe.parse_data_directories(directories=[
        pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
    return pe

def overview(pe):
    print(f"ImageBase       0x{pe.OPTIONAL_HEADER.ImageBase:08X}")
    print(f"EntryPoint RVA  0x{pe.OPTIONAL_HEADER.AddressOfEntryPoint:08X}")
    print(f"Machine         0x{pe.FILE_HEADER.Machine:04X} (0x14c=x86)")
    print("Sections:")
    for s in pe.sections:
        name = s.Name.rstrip(b'\x00').decode('latin1')
        print(f"  {name:8s} VA 0x{s.VirtualAddress:08X}  vsize 0x{s.Misc_VirtualSize:06X}"
              f"  raw 0x{s.PointerToRawData:08X} rsize 0x{s.SizeOfRawData:06X}"
              f"  flags 0x{s.Characteristics:08X}")

WANTED = {b"CreateFileW", b"CreateFileA", b"ReadFile", b"WriteFile",
          b"SetFilePointer", b"SetFilePointerEx", b"CloseHandle",
          b"GetFileSize", b"ReadFileEx"}

def imports(pe):
    print("\nImports of interest (name -> IAT VA = where 'call [VA]' points):")
    base = pe.OPTIONAL_HEADER.ImageBase
    found = {}
    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        dll = entry.dll.decode('latin1')
        for imp in entry.imports:
            if imp.name and imp.name in WANTED:
                va = imp.address            # absolute VA of IAT slot
                found[imp.name.decode()] = va
                print(f"  {imp.name.decode():18s} {dll:16s} IAT VA 0x{va:08X}"
                      f"  (RVA 0x{va-base:08X})")
    return found

def xref(pe, iat_va):
    """Find all 'call dword ptr [iat_va]' sites (FF 15 <iat_va LE>) in .text.
    Prints the RVA of each call site (where the call instruction is)."""
    base = pe.OPTIONAL_HEADER.ImageBase
    text = next(s for s in pe.sections
                if s.Name.rstrip(b'\x00') == b'.text')
    data = text.get_data()
    text_rva = text.VirtualAddress
    needle = b'\xff\x15' + iat_va.to_bytes(4, 'little')
    print(f"\nXref 'call [0x{iat_va:08X}]' (pattern {needle.hex(' ')}) in .text:")
    hits = []
    start = 0
    while True:
        i = data.find(needle, start)
        if i < 0:
            break
        rva = text_rva + i           # RVA of the FF 15 byte
        hits.append(rva)
        print(f"  call site @ RVA 0x{rva:08X} (VA 0x{base+rva:08X})")
        start = i + 1
    print(f"  -> {len(hits)} call site(s)")
    return hits

def callers(pe, target_rva):
    """Find relative near-calls (E8 rel32) whose target == target_rva, in .text.
    Also scans for the absolute VA appearing as a dword (vtable/func-ptr ref)."""
    base = pe.OPTIONAL_HEADER.ImageBase
    text = next(s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text')
    data = text.get_data()
    text_rva = text.VirtualAddress
    target_va = base + target_rva
    print(f"\nCallers of RVA 0x{target_rva:08X} (VA 0x{target_va:08X}):")
    # E8 rel32 relative calls
    hits = []
    for i in range(len(data) - 5):
        if data[i] == 0xE8:
            rel = int.from_bytes(data[i+1:i+5], 'little', signed=True)
            site_rva = text_rva + i
            tgt = site_rva + 5 + rel          # next-instr RVA + rel
            if tgt == target_rva:
                hits.append(site_rva)
                print(f"  E8 call @ RVA 0x{site_rva:08X} (VA 0x{base+site_rva:08X})")
    print(f"  -> {len(hits)} relative E8 call site(s)")
    # absolute VA referenced as data (e.g. vtable / push offset)
    needle = target_va.to_bytes(4, 'little')
    refs, start = [], 0
    while True:
        i = data.find(needle, start)
        if i < 0:
            break
        refs.append(text_rva + i)
        start = i + 1
    if refs:
        print("  Absolute-VA dword refs in .text (vtable/ptr):")
        for r in refs:
            print(f"    @ RVA 0x{r:08X}")
    return hits

def disasm(pe, rva, n=200):
    base = pe.OPTIONAL_HEADER.ImageBase
    data = pe.get_data(rva, n)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = False
    print(f"\nDisasm @ RVA 0x{rva:08X} (VA 0x{base+rva:08X}), {n} bytes:")
    for ins in md.disasm(data, base + rva):
        print(f"  0x{ins.address:08X} ({ins.address-base:#08x}): "
              f"{ins.mnemonic:8s} {ins.op_str}")

if __name__ == "__main__":
    pe = load()
    if len(sys.argv) >= 3 and sys.argv[1] == "xref":
        # py peinfo.py xref 0x6E3218   -> find call sites of that IAT slot
        xref(pe, int(sys.argv[2], 0))
    elif len(sys.argv) >= 3 and sys.argv[1] == "callers":
        # py peinfo.py callers 0xF3C00 -> find who calls that function
        callers(pe, int(sys.argv[2], 0))
    elif len(sys.argv) >= 2:
        rva = int(sys.argv[1], 0)
        n = int(sys.argv[2], 0) if len(sys.argv) >= 3 else 200
        disasm(pe, rva, n)
    else:
        overview(pe)
        imports(pe)
