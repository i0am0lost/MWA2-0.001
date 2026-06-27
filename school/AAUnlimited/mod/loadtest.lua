--@INFO RE #7: Detour 0xB2440 faengt STACK-FENSTER (synchrone Aufrufkette bis Klick-Handler). + 0xB2680 -> this/Container. F6=dump.
local _M = {}
require 'memory'

local WRAP, WRAP_AFTER = 0xB2680, 0xB2685
local ENQ,  ENQ_AFTER  = 0xB2440, 0xB2445
local NDW = 24                          -- 24 dwords Stack-Fenster
local this_slot, stkbuf

local patch = parse_asm [[
00000000  893578563412      mov [dword 0x12345678],esi
00000006  83EC10            sub esp,byte +0x10
00000009  EB03              jmp short 0xe
0000000B  EBF3              jmp short 0x0
0000000D  90                nop
]]
local g_var

local function p32(x)
	x = math.floor(x); if x < 0 then x = x + 0x100000000 end
	return string.pack("<I4", x & 0xFFFFFFFF)
end
local function rdw(addr)
	addr = fixptr(addr) & 0xFFFFFFFF
	if addr == 0 then return nil end
	local ok, v = pcall(peek_dword, addr); if ok then return v & 0xFFFFFFFF end; return nil
end

local function dump()
	local GB = fixptr(GameBase)
	local LO, HI = GB + 0x1000, GB + 0x2E261A
	log.warn("===== DUMP  GB=0x%X =====", GB)
	log.warn("Stack-Fenster bei enqueueLoad (nur .text-Rueckspruenge = Aufrufkette):")
	for i = 0, NDW-1 do
		local v = rdw(fixptr(stkbuf) + i*4)
		if v and v >= LO and v < HI then
			log.warn("  [esp+0x%02X] = 0x%X  -> RVA 0x%X", i*4, v, v - GB)
		end
	end
	local t = rdw(this_slot) or 0
	if t ~= 0 then
		log.warn("this=0x%X  container=[this+0x1c]=0x%X (RVA 0x%X)", t, rdw(t+0x1c) or 0, (rdw(t+0x1c) or GB)-GB)
	end
end

function on.keyup(key)
	if key == 117 then dump() end
end

function _M:load()
	if exe_type ~= "play" then return end
	local GB = fixptr(GameBase)

	g_var = malloc(4); poke_dword(g_var, 0)
	g_poke(0x470B0 - #patch + 3, patch)
	g_poke_dword(0x470B0 - #patch + 3 + 2, g_var)

	this_slot = malloc(4); poke_dword(this_slot, 0)
	stkbuf    = malloc(NDW*4)

	-- Detour A @ 0xB2680: this erfassen
	local capA = x_pages(4096)
	poke(capA, "\xA3"..p32(this_slot).."\x83\xEC\x24".."\x56".."\x57".."\xE9"..p32((GB+WRAP_AFTER)-(capA+15)))
	g_poke(WRAP, "\xE9"..p32(capA - (GB+WRAP+5)))

	-- Detour B @ 0xB2440: pushad ; esi=orig esp ; rep movsd 24 -> stkbuf ; popad ; Original(56 / 8B 74 24 08) ; jmp
	local capB = x_pages(4096)
	poke(capB,
		"\x60" ..                          -- pushad
		"\x8D\x74\x24\x20" ..              -- lea esi,[esp+0x20]  (= original esp)
		"\xBF"..p32(stkbuf) ..            -- mov edi, stkbuf
		"\xB9"..p32(NDW) ..              -- mov ecx, 24
		"\xF3\xA5" ..                     -- rep movsd
		"\x61" ..                          -- popad
		"\x56" ..                          -- push esi   (orig 1)
		"\x8B\x74\x24\x08" ..             -- mov esi,[esp+8] (orig 2)
		"\xE9"..p32((GB+ENQ_AFTER)-(capB+28)))
	g_poke(ENQ, "\xE9"..p32(capB - (GB+ENQ+5)))

	log.warn("re-mod v2 geladen (Stack-Fenster). Erst laden, dann F6.")
end

function _M:unload() end
function _M:config() end
return _M
