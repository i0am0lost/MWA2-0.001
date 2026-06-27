--@INFO [Orchestrator] apply_state - the global evolution apply-mod: set each char's resolved value-effects from the SSOT

-- The "global pool" runtime half (notes: EVOLUTION_MAP / global-pool architecture). The card is NEVER
-- written. The orchestrator's resolver turns the activity/relationship/race DBs into per-char ACTIVE
-- modules, then writes their self-value EFFECTS to _orch_char_state.flag. This mod reads that file and, for
-- every present char, sets the values on the live character -- exactly the inject_self mechanism, but
-- driven by the resolver instead of a one-off transfer. Behaviour/visual effects are emergent from these
-- values via AA2's own engine (project thesis), or land as later increments.
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

-- Apply one char's resolved effects on its live seat. Two kinds, both in the same "key=value;..." string:
--   * value effects (virtue/int/str/soc) -> written directly on the character (inject_self mechanism).
--   * Card-Storage flags "@b:key" (bool) / "@i:key" (int) -> setCardStorage, which GATES behaviour modules
--     (e.g. Confinement reads "confined"/"cell"). The card is never written; the SSOT just hands out flags.
-- The seat is only the runtime handle for this char -- identity is the NAME (char_id), matched in apply().
local function inject(seat, effstr)
    if not effstr or effstr == "" then return "" end
    local inst = GetCharInstData(seat)
    if not inst then return "" end
    local applied = {}
    for k, v in effstr:gmatch("([%a_@:]+)=(%-?%d+)") do
        local val = tonumber(v)
        local typ = k:sub(1, 3)
        if typ == "@b:" or typ == "@i:" then
            local key = k:sub(4)
            local ok = pcall(function()
                if typ == "@b:" then setCardStorage(seat, key, val ~= 0)
                else                 setCardStorage(seat, key, val) end
            end)
            if ok then applied[#applied + 1] = k .. "=" .. v end
        else
            local got
            pcall(function()
                local c = inst.m_char.m_charData.m_character
                if     k == "virtue"       then c.virtue = val;       got = c.virtue
                elseif k == "intelligence" then c.intelligence = val; got = c.intelligence
                elseif k == "strength"     then c.strength = val;     got = c.strength
                elseif k == "sociability"  then c.sociability = val;  got = c.sociability end
            end)
            if got == val then applied[#applied + 1] = k .. "=" .. v end
        end
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
