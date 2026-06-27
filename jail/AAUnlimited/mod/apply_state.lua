--@INFO [Orchestrator] apply_state - the global evolution apply-mod: set each char's SSOT-resolved Card-Storage FLAGS

-- The "global pool" runtime half (notes: EVOLUTION_MAP / global-pool architecture). The card is NEVER
-- written, and we NEVER write vanilla stats. The orchestrator's resolver turns the activity/relationship/race
-- DBs into per-char ACTIVE modules + Card-Storage FLAGS, and writes the flags to _orch_char_state.flag. This
-- mod reads that file and, for every present char, sets those flags via setCardStorage -- which GATE the
-- always-loaded dispatcher modules (module_reroute). Behaviour is thus value-/module-driven, on-the-fly, with
-- the SSOT as the single brain and the cards left pristine.
--
-- Line: "<name>\t<active modules csv>\t<field=value;...>". Self-gating: no flag file -> no-op (can't touch
-- anything). Runs on the same events as the other orchestrator mods + a poll timer (so switching INTO a
-- world re-applies even without a fresh event).

local _M = {}
local STATE = "_orch_char_state.flag"
local DBG = "_orch_apply_debug.flag"

local function dbg(msg)
    local ok, f = pcall(io.open, play_path(DBG), "a")
    if ok and f then f:write(msg .. "\n"); f:close() end
end

local function norm(s)
    return (s:gsub("%s+", " "):gsub("^%s+", ""):gsub("%s+$", ""))
end

local function name_of(seat)
    local inst = GetCharInstData(seat)
    if not inst then return nil end
    local ok, n = pcall(function()
        local cd = inst.m_char.m_charData
        return cd.m_forename .. " " .. cd.m_surname
    end)
    return ok and norm(n) or nil
end

-- name -> effects-string, read from the flag. nil if the file is absent (=> this mod does nothing).
local function read_state()
    local f = io.open(play_path(STATE), "r")
    if not f then return nil end
    local out = {}
    for line in f:lines() do
        if line ~= "" and line:sub(1, 1) ~= "#" then
            local name, _mods, eff = line:match("^([^\t]*)\t([^\t]*)\t?(.*)$")
            if name then out[norm(name)] = eff or "" end
        end
    end
    f:close()
    return out
end

-- Apply one char's resolved Card-Storage FLAGS on its live seat. The flags "@b:key" (bool) / "@i:key" (int)
-- -> setCardStorage, which GATES the always-loaded dispatcher modules (e.g. Confinement reads "confined"/
-- "cell"). The card is never written; the SSOT just hands out flags. We DELIBERATELY do NOT write vanilla
-- stats (virtue/int/str/soc): those are read-only input the engine/other modules own -- behaviour is driven
-- by modules/flags, never by hijacking a stat. The seat is only the runtime handle; identity is the NAME.
local function inject(seat, effstr)
    if not effstr or effstr == "" then return "" end
    if not GetCharInstData(seat) then return "" end
    local applied = {}
    for k, v in effstr:gmatch("(@[bi]:[%a_]+)=(%-?%d+)") do   -- only @b:/@i: flags; plain stats are ignored
        local typ, key, val = k:sub(1, 3), k:sub(4), tonumber(v)
        local ok = pcall(function()
            if typ == "@b:" then setCardStorage(seat, key, val ~= 0)
            else                 setCardStorage(seat, key, val) end
        end)
        if ok then applied[#applied + 1] = k .. "=" .. v end
    end
    return table.concat(applied, ";")
end

local applied_sig = nil
local function apply()
    local state = read_state()
    if not state then return end
    -- Which present chars have effects to apply, and what. The signature is over THIS (present roster
    -- AND their resolved effects) -> a NEW resolve re-applies even if the roster did not change. (The old
    -- bug: keyed only on the roster, so a state change with an unchanged roster never re-applied.)
    local todo = {}
    for s = 0, 24 do
        local nm = name_of(s)
        if nm and state[nm] and state[nm] ~= "" then todo[nm] = s end
    end
    local keys = {}
    for nm in pairs(todo) do keys[#keys + 1] = nm .. "=" .. state[nm] end
    table.sort(keys)
    local sig = table.concat(keys, ";")
    if sig == applied_sig then return end
    applied_sig = sig

    local log = {}
    for nm, seat in pairs(todo) do
        local ap = inject(seat, state[nm])
        if ap ~= "" then log[#log + 1] = nm .. "{" .. ap .. "}" end
    end
    if #log > 0 then dbg("applied: " .. table.concat(log, ", ")) end
end

function on.load_class()
    applied_sig = nil      -- fresh class -> re-apply
    apply()
end

function on.period(new, old)
    apply()                -- no return -> don't override the period progression
end

function on.room_change(inst)
    apply()
end

function _M:load()
    local ok, f = pcall(io.open, play_path(DBG), "w")
    if ok and f then f:write("# apply_state (resolved self-values from SSOT char_state)\n"); f:close() end
    -- Poll like jail_intake: events alone miss the case of switching INTO a suspended world (no new event).
    require "iuplua"
    self._timer = iup.timer { time = 700, action_cb = function() pcall(apply) end }
    self._timer.run = "YES"
end

function _M:unload()
    if self._timer then self._timer.run = "NO"; self._timer = nil end
end

return _M
