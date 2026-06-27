--@INFO [DEV] Period-Logger + Live-Char-Dump (Jail-Projekt)

-- Diagnose-Mod fuer das Jail-Projekt (siehe AA2_Jail_Projekt_Notizen.md).
-- Laeuft IM SPIEL (nur dort gibt es eine geladene Klasse / Live-State).
--
-- Tasten (im Spiel):
--   F9  = Roster-Dump (alle belegten Seats + Namen)
--   F10 = Detail-Dump Seat 0 (+ Beziehung 0->1) ueber die in 3.4 verifizierten Felder
--
-- Ausgabe: log.warn -> erscheint im Log-Ausgabe-Fenster (das schwarze Konsolenfenster
-- des Spiels). log.info/info() (prio 1) waeren bei logPrio=2 unsichtbar.
--
-- Zweck:
--   #1  Welche currentPeriod hat der naechtliche Heim-Screen? (on.period loggt jeden Wechsel)
--   3.4 GetGameTimeData / GetCharInstData / m_characterStatus live bestaetigen.

local _M = {}

local VK_F9  = 0x78
local VK_F10 = 0x79

local function fmt_time()
	local ok, d = pcall(GetGameTimeData)
	if not ok or not d then return "GameTimeData=nil (keine Klasse geladen?)" end
	return string.format("day=%s nDays=%s currentPeriod=%s",
		tostring(d.day), tostring(d.nDays), tostring(d.currentPeriod))
end

-- Write the current period to a flag file so the orchestrator knows when this
-- world is on the home screen (period 9) and can show the in-game "jail" button.
local function write_period(p)
	local okp, f = pcall(io.open, play_path("_orch_period.flag"), "w")
	if okp and f then f:write(tostring(p)); f:close() end
end

-- Write the current game day (GetGameTimeData().nDays) to a flag so the orchestrator can derive the
-- jail roster for the day school is currently on (SSOT model A: derive-on-load is day-keyed). Only
-- written when a class is loaded (nDays valid); at the menu the last value persists.
local function write_day()
	local ok, d = pcall(GetGameTimeData)
	if ok and d and d.nDays then
		local okd, f = pcall(io.open, play_path("_orch_day.flag"), "w")
		if okd and f then f:write(tostring(d.nDays)); f:close() end
	end
end

-- Returning nothing -> the period is not changed (init.lua __DISPATCH_EVENT).
function on.period(new, old)
	log.warn("[LOGP] period %s -> %s  | %s", tostring(old), tostring(new), fmt_time())
	write_period(new)
	write_day()
end

function on.load_class()
	log.warn("[LOGP] class loaded | %s", fmt_time())
	local ok, d = pcall(GetGameTimeData)
	if ok and d then write_period(d.currentPeriod) end
	write_day()
end

local function safe(fn)
	local ok, v = pcall(fn)
	if ok then return tostring(v) end
	return "<err: " .. tostring(v) .. ">"
end

local function dump_roster()
	log.warn("[LOGP] ---- roster dump ----")
	local found = 0
	for seat = 0, 24 do
		local ok, inst = pcall(GetCharInstData, seat)
		if ok and inst then
			found = found + 1
			local name = safe(function()
				local cd = inst.m_char.m_charData
				return cd.m_forename .. " " .. cd.m_surname
			end)
			log.warn("[LOGP] seat %d: %s", seat, name)
		end
	end
	log.warn("[LOGP] ---- %d chars im Roster ----", found)
end

-- Findet die ersten n belegten Seats (Roster ist NICHT lueckenlos - Seats 0/1 oft leer).
local function first_seats(n)
	local seats = {}
	for s = 0, 24 do
		local ok, inst = pcall(GetCharInstData, s)
		if ok and inst then
			seats[#seats + 1] = s
			if #seats >= n then break end
		end
	end
	return seats
end

-- Detail-Dump: nur die im Mod-Code BELEGTEN Felder (3.4). Virtue/Stats/Module
-- tauchen hier NICHT auf -> die brauchen die AAU-Wiki-Bindings (offener Punkt #10).
local function dump_detail()
	local s = first_seats(2)
	if #s == 0 then
		log.warn("[LOGP] kein belegter Seat - ist eine Klasse geladen?")
		return
	end
	local a = GetCharInstData(s[1])
	log.warn("[LOGP] === Seat %d Detail ===", s[1])
	log.warn("[LOGP] seat     = %s", safe(function() return a.m_char.m_seat end))
	log.warn("[LOGP] forename = %s", safe(function() return a.m_char.m_charData.m_forename end))
	log.warn("[LOGP] surname  = %s", safe(function() return a.m_char.m_charData.m_surname end))
	log.warn("[LOGP] gender   = %s", safe(function() return a.m_char.m_charData.m_gender end))
	if s[2] then
		local t = s[2]
		log.warn("[LOGP] hCompat %d->%d = %s", s[1], t, safe(function() return a.m_char.m_charData:m_hCompatibility(t) end))
		log.warn("[LOGP] totalH  %d->%d = %s", s[1], t, safe(function() return a.m_char.m_characterStatus:m_totalH(t) end))
		log.warn("[LOGP] cherry  %d->%d = %s", s[1], t, safe(function() return a.m_char.m_characterStatus:m_cherry(t) end))
		log.warn("[LOGP] relDump %d->%d = %s", s[1], t, safe(function() return p(createRelationshipPointsDump(s[1], t)) end))
	end
	log.warn("[LOGP] === Ende Detail ===")
end

function on.keyup(key)
	if key == VK_F9 then
		dump_roster()
	elseif key == VK_F10 then
		dump_detail()
	end
end

function _M:load()
	log.warn("[LOGP] geladen. F9 = Roster, F10 = Detail Seat 0. | %s", fmt_time())
	-- Poll the current period every 500ms and write it to the flag file, so the
	-- orchestrator's in-game button works no matter HOW the home screen is reached
	-- (e.g. loading a save directly into period 9, where on.period never fires).
	-- Writes 0 when no class is loaded -> button only shows on the real home screen.
	require "iuplua"
	self._timer = iup.timer { time = 500, action_cb = function()
		local ok, d = pcall(GetGameTimeData)
		if ok and d and d.currentPeriod then
			write_period(d.currentPeriod)
			write_day()
		else
			write_period(0)
		end
	end }
	self._timer.run = "YES"
end

function _M:unload()
	if self._timer then self._timer.run = "NO"; self._timer = nil end
end

return _M
