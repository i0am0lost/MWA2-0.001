--@INFO [Orchestrator] module_reroute - reroute card trigger-modules to the SSOT-maintained list

-- ARCHITECTURE (source-verified, aa2g/AA2Unlimited):
--   A card lists trigger modules by NAME; AAUCardData::UpdateModules() (DLL RVA 0x154CF0, __thiscall void)
--   re-resolves each name from data\override\module\<name> and OVERWRITES the embedded copy. It runs ONCE
--   per card at FromPNGBuffer, BEFORE InitOnLoad flattens GetModules() and registers their triggers.
--   => Hooking UpdateModules lets us (a) snapshot the card's module names as the creator's "wish" (-> SSOT),
--   then (b) substitute OUR centrally-maintained module set before activation. Native helpers exist:
--   AddModule(wchar_t const*) @0x14CEC0, RemoveModule(int) @0x14D290 (both __thiscall, bool). m_modules is
--   at offset 0x3C inside AAUCardData (release: std::vector = 12 bytes). No Lua API touches the list, so
--   this is a native binary hook via mod/memory.lua (hook_func/make_callback). See HANDOVER + memory notes.
--
-- BUILD LADDER (this file evolves):
--   v0 = READ-ONLY address verification. (DONE -> MATCH, base live-correct.)
--   v1 = HOOK UpdateModules, log this + m_modules header. (DONE -> 11 fires, no crash, sizeof(Module)=84.)
--   v2 = read card module NAMES + ensure "Confinement" via AddModule. (DONE -> proved read+write.)
--   v3 (CURRENT) = SSOT-DRIVEN: read each card's embedded mwa_id (rename-proof id) -> look up its module
--        list in _orch_reroute.flag (orchestrator-written: '<mwa_id>\t<mods>') -> ensure each is present via
--        AddModule, before InitOnLoad activates triggers. Only chars WITH an SSOT entry are touched (no
--        hardcoded module). ADDITIVE for now; clear+replace ("ignore card modules") is a later flip.
--
-- Module struct layout (sizeof=84, verified): name wstring@0, description wstring@24, triggers vec@48,
-- globals vec@60, dependencies vec@72. MSVC wstring(24): _Bx union@0 (inline wchar[8] OR ptr), _Mysize@16,
-- _Myres@20; inline iff _Myres < 8.

require "memory"
require "strutil"

local _M = {}
local DBG = "_orch_reroute_debug.flag"

-- RVAs in AAUnlimitedDll.dll (ImageBase 0x10000000), extracted from AAUnlimitedDll.pdb S_PUB32 records.
local RVA = {
    UpdateModules = 0x154CF0,   -- void __thiscall AAUCardData::UpdateModules(void)
    AddModule     = 0x14CEC0,   -- bool __thiscall AAUCardData::AddModule(wchar_t const*)
    RemoveModule  = 0x14D290,   -- bool __thiscall AAUCardData::RemoveModule(int)
}
local M_MODULES_OFF = 0x3C      -- std::vector<Module> m_modules within AAUCardData

-- expected first 10 bytes of UpdateModules (static, from pefile): push ebp; mov ebp,esp; push -1; push imm32
local EXPECT = "\x55\x8B\xEC\x6A\xFF\x68"   -- first 6 are address-independent; the imm32 tail varies by base

local function w(msg)
    log.warn("[REROUTE] %s", msg)
    local ok, f = pcall(io.open, play_path(DBG), "a")
    if ok and f then f:write(msg .. "\n"); f:close() end
end

local function hexstr(s)
    local t = {}
    for i = 1, #s do t[i] = string.format("%02X", s:byte(i)) end
    return table.concat(t, " ")
end

local SIZEOF_MODULE = 84

-- Read an MSVC std::wstring (24 bytes) from memory at `addr`; returns its ASCII-folded contents.
local function read_wstr_mem(addr)
    local size = peek_dword(addr + 16)
    if not size or size == 0 then return "" end
    if size > 128 then return "<len?>" end                 -- sanity guard
    local res = peek_dword(addr + 20)
    local ptr = (res and res < 8) and addr or peek_dword(addr)   -- inline buffer vs heap pointer
    local raw = peek(ptr, size * 2)
    local out = {}
    for i = 1, #raw, 2 do out[#out + 1] = string.char(raw:byte(i)) end   -- module names are ASCII
    return table.concat(out)
end

-- Read the module-name list of an AAUCardData* (this) from its m_modules vector at this+0x3C.
local function read_module_names(this)
    local names = {}
    local okv, vec = pcall(peek, this + M_MODULES_OFF, 12)
    if not okv or type(vec) ~= "string" or #vec ~= 12 then return names end
    local first, last = string.unpack("<I4I4", vec)
    local span = (last - first) & 0xffffffff
    local n = span // SIZEOF_MODULE
    if n < 0 or n > 256 then return names end
    for i = 0, n - 1 do
        local ok2, nm = pcall(read_wstr_mem, first + i * SIZEOF_MODULE)
        names[#names + 1] = ok2 and nm or "?"
    end
    return names
end

-- NUL-terminated UTF-16LE buffer for a (utf8) string -> wchar_t* arg.
local function to_wide_z(s)
    return utf8_to_unicode(s) .. "\0\0"
end

-- Call AAUCardData::AddModule(const wchar_t*) at `addr` on `this` with path `pathstr`. Returns true iff
-- the call's bool (AL) is non-zero. AddModule loads ModuleFile(path) from disk; bare name fails, it needs
-- the path UpdateModules uses: <base>data\override\module\<name>.
local function add_module(addr, this, pathstr)
    local wz = to_wide_z(pathstr)
    local p = malloc(#wz)
    poke(p, wz)
    local ok, eax = pcall(proc_invoke, addr, this, p)
    free(p)
    if not ok then return false, "ERR:" .. tostring(eax) end
    return (eax & 0xff) ~= 0, eax
end

function _M:load()
    local ok, f = pcall(io.open, play_path(DBG), "w")
    if ok and f then f:write("# module_reroute v3 (SSOT-driven reroute by mwa_id)\n"); f:close() end

    local base = GetModuleHandleA("AAUnlimitedDll.dll")
    if not base or base == 0 then
        w("FAIL: GetModuleHandleA('AAUnlimitedDll.dll') returned 0 -- cannot resolve DLL base")
        return
    end
    w(string.format("AAU DLL base = 0x%08X", base))

    for name, rva in pairs(RVA) do
        local addr = base + rva
        local okk, bytes = pcall(peek, addr, 10)
        if okk and bytes then
            w(string.format("%-14s RVA=0x%06X  addr=0x%08X  bytes= %s", name, rva, addr, hexstr(bytes)))
        else
            w(string.format("%-14s addr=0x%08X  peek FAILED (%s)", name, addr, tostring(bytes)))
        end
    end

    -- verdict on UpdateModules prologue (the one we hook)
    local addr = base + RVA.UpdateModules
    local bytes = select(2, pcall(peek, addr, 6))
    if not (type(bytes) == "string" and bytes == EXPECT) then
        w("VERDICT: prologue MISMATCH (got " .. (type(bytes)=="string" and hexstr(bytes) or tostring(bytes)) ..
          ") -> NOT hooking; address math is wrong.")
        return
    end
    w("VERDICT: UpdateModules prologue MATCHES -> installing hook (v4: always-inject SSOT-gated dispatchers).")

    -- AddModule needs the full on-disk path; we discover the working <base>data\override\module\ prefix
    -- once and cache it (it loads the module's def from disk = our gated dispatcher).
    local ADDMOD = base + RVA.AddModule
    local MODDIR = "data\\override\\module\\"
    local bases = {}
    local okp, pp = pcall(function() return _BINDING.GetAAPlayPath() end)
    local oke, ep = pcall(function() return _BINDING.GetAAEditPath() end)
    if okp and type(pp) == "string" then bases[#bases + 1] = pp .. MODDIR end
    if oke and type(ep) == "string" and ep ~= pp then bases[#bases + 1] = ep .. MODDIR end
    bases[#bases + 1] = MODDIR
    local winbase = nil
    local function ensure_module(this, modname)
        if winbase then return add_module(ADDMOD, this, winbase .. modname) end
        for _, b in ipairs(bases) do
            local ok2 = add_module(ADDMOD, this, b .. modname)
            if ok2 then winbase = b; return true end
        end
        return false
    end

    -- v4 (dispatcher pattern): ALWAYS inject our always-loaded, SSOT-GATED dispatcher modules into every
    -- card at load (in-memory; card file untouched). They are inert until the SSOT sets their Card-Storage
    -- flags (apply_state) -> behaviour is then value-driven & on-the-fly (no reload, no per-char id needed).
    -- Currently one dispatcher: gated Confinement (acts only on chars whose 'confined' flag is set).
    local DISPATCHERS = { "Confinement" }
    w("dispatchers (always-injected): " .. table.concat(DISPATCHERS, ", "))

    local nfired = 0
    local fixbytes, orig = hook_func(addr, 10, 0, function(o, this)
        nfired = nfired + 1
        local rok = pcall(proc_invoke, o, this)            -- original UpdateModules (re-resolve from disk)
        local present = {}
        for _, nm in ipairs(read_module_names(this)) do present[nm] = true end
        local applied, failed = {}, {}
        for _, modname in ipairs(DISPATCHERS) do
            if not present[modname] then
                if ensure_module(this, modname) then applied[#applied + 1] = modname
                else failed[#failed + 1] = modname end
            end
        end
        w(string.format("#%d dispatchers applied={%s} failed={%s} now(%d)",
            nfired, table.concat(applied, ","), table.concat(failed, ","), #read_module_names(this)))
        return rok
    end)
    self._addr = addr
    self._fixbytes = fixbytes
    w(string.format("hook installed at 0x%08X (trampoline=0x%08X, %d fixbytes).", addr, orig or 0, #fixbytes))
end

function _M:unload()
    if self._addr and self._fixbytes then
        pcall(poke, self._addr, self._fixbytes)   -- restore original prologue; drop the patch
    end
end

return _M
