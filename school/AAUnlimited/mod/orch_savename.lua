--@INFO [Orchestrator] Reports the loaded save name for jail-save coupling

-- Writes the currently loaded class-save name to _orch_save.flag in the game dir.
-- The orchestrator reads it to know WHICH playthrough is active, so it can point jail's
-- save junction at the matching jail twin before loading jail.
--
-- Mechanism = the same one extsave.lua uses: a tiny code patch at 0x470B0 captures the
-- save-info struct pointer into g_var; the save name lives at offset +100 (unicode).
-- (extsave is NOT active in school -> no patch conflict over 0x470B0.)

local _M = {}
require 'memory'

local patch = parse_asm [[
00000000  893578563412      mov [dword 0x12345678],esi
00000006  83EC10            sub esp,byte +0x10
00000009  EB03              jmp short 0xe
0000000B  EBF3              jmp short 0x0
0000000D  90                nop
]]

local g_var
local last_written

local function current_save_name()
	local info = ptr_walk(g_var, 0x18, 0x28, 0)
	if not info or fixptr(info) == 0 then return nil end
	local n = unicode_to_utf8(fixptr(info) + 100)
	if n == nil or n == "" then return nil end
	return n
end

local function write_flag(name)
	local ok, f = pcall(io.open, play_path("_orch_save.flag"), "w")
	if ok and f then f:write(name); f:close() end
end

-- Poll: once a class is loaded AND the patch has populated g_var, capture the name.
-- Only write on change so we don't hammer the disk every tick.
local function poll()
	if not g_var then return end
	local ok, name = pcall(current_save_name)
	if ok and name and name ~= last_written then
		last_written = name
		write_flag(name)
		log.warn("[ORCH] loaded save = %s", name)
	end
end

function on.load_class()
	poll()
end

function _M:load()
	if exe_type ~= "play" then return end
	-- Prefer extsave's shared g_var (it loads first and patches 0x470B0). Using it avoids a
	-- SECOND conflicting patch at the same address. Only patch ourselves if extsave isn't active.
	g_var = rawget(_ENV, "_orch_g_var")
	if not g_var then
		g_var = malloc(4)
		local addr = 0x470B0
		g_poke(addr - #patch + 3, patch)
		g_poke_dword(addr - #patch + 3 + 2, g_var)
	end
	-- periodic poll so the name is captured no matter how the class is entered
	require "iuplua"
	self._timer = iup.timer { time = 500, action_cb = poll }
	self._timer.run = "YES"
end

function _M:unload()
	if self._timer then self._timer.run = "NO"; self._timer = nil end
end

return _M
