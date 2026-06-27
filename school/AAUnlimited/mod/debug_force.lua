--@INFO [Orchestrator] debug_force - DEV TOOL: force a char's engine H-counters live (fast threshold testing)

-- The test accelerator (notes: debug tool). Setting char_activity in the DB doesn't stick -- the next
-- activity_snapshot overwrites it from the engine. So to test the evolution pipeline without grinding H
-- scenes, we set the ENGINE counter directly; it then flows snapshot -> char_activity -> resolver ->
-- char_state -> apply_state, exactly like real activity. debug_tool.py writes _orch_force_activity.flag;
-- this mod reads it and, for each PRESENT named char, sets the counter, then drops the consumed line.
--
-- Setter API (proven in triggers_supplemental.lua): m_characterStatus:m_<metric>(towards, value) sets
-- (second arg). Counters are per-partner (towards); the snapshot SUMS over partners. We therefore clear
-- the metric on all partner slots and put the whole value on one -> the summed total equals the value
-- (predictable). Destructive to that metric's per-partner history -- fine for a deliberate debug force.
--
-- One-shot: a line is applied as soon as its char is present, then removed from the flag (lines whose
-- char isn't present yet stay, so they fire when the char appears). Self-gating: no flag -> no-op.
-- DEV ONLY -- forced in school's forcedconfig; remove for a real build.

local _M = {}
local FORCE = "_orch_force_activity.flag"
local DBG = "_orch_force_debug.flag"

-- metric name -> m_characterStatus accessor (same map as activity_snapshot; set form = method(self, towards, value)).
local METHOD = {
    climax = "m_climaxCount", simultaneousClimax = "m_simultaneousClimax",
    totalH = "m_totalH", vaginalH = "m_vaginalH", analH = "m_analH",
    totalCum = "m_totalCum", cumInVagina = "m_cumInVagina", cumInAnal = "m_cumInAnal",
    cumSwallowed = "m_cumSwallowed", riskyCum = "m_riskyCum", condomsUsed = "m_condomsUsed",
}

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

-- Set the engine counter for `metric` on a present seat so the summed-over-partners total == value.
local function force(seat, metric, value)
    local method = METHOD[metric]
    if not method then return false end
    local inst = GetCharInstData(seat)
    if not inst then return false end
    local ok = pcall(function()
        local status = inst.m_char.m_characterStatus
        local slot = (seat == 0) and 1 or 0          -- any partner slot != self
        for towards = 0, 24 do
            if towards ~= seat then
                status[method](status, towards, (towards == slot) and value or 0)
            end
        end
    end)
    return ok
end

-- Read the force flag -> list of {name, metric, value}. nil if the file is absent (=> no-op).
local function read_force()
    local f = io.open(play_path(FORCE), "r")
    if not f then return nil end
    local out = {}
    for line in f:lines() do
        if line ~= "" and line:sub(1, 1) ~= "#" then
            local name, metric, value = line:match("^([^\t]*)\t([^\t]*)\t(%-?%d+)")
            if name and metric and value then
                out[#out + 1] = { name = norm(name), metric = metric, value = tonumber(value) }
            end
        end
    end
    f:close()
    return out
end

-- Write back the lines that are still PENDING (their char wasn't present), or delete the flag if none.
local function write_pending(pending)
    local path = play_path(FORCE)
    if #pending == 0 then
        pcall(os.remove, path)
        return
    end
    local ok, f = pcall(io.open, path, "w")
    if ok and f then
        f:write("# force engine activity: <name>\t<metric>\t<value> (consumed when the char is present)\n")
        for _, p in ipairs(pending) do
            f:write(string.format("%s\t%s\t%d\n", p.name, p.metric, p.value))
        end
        f:close()
    end
end

local function apply()
    local items = read_force()
    if not items then return end
    -- present name -> seat
    local seats = {}
    for s = 0, 24 do
        local nm = name_of(s)
        if nm then seats[nm] = s end
    end
    local pending = {}
    for _, it in ipairs(items) do
        local seat = seats[it.name]
        if seat and METHOD[it.metric] then
            if force(seat, it.metric, it.value) then
                dbg(string.format("forced: %s %s=%d", it.name, it.metric, it.value))
            else
                pending[#pending + 1] = it          -- present but set failed -> retry next tick
            end
        else
            pending[#pending + 1] = it              -- char not present (or bad metric) -> keep waiting
        end
    end
    if #pending ~= #items then write_pending(pending) end   -- something consumed -> rewrite/clear
end

function on.load_class() apply() end
function on.period(new, old) apply() end       -- no return -> don't override the period progression
function on.room_change(inst) apply() end

function _M:load()
    local ok, f = pcall(io.open, play_path(DBG), "w")
    if ok and f then f:write("# debug_force (engine H-counters set live for testing)\n"); f:close() end
    require "iuplua"
    self._timer = iup.timer { time = 700, action_cb = function() pcall(apply) end }
    self._timer.run = "YES"
end

function _M:unload()
    if self._timer then self._timer.run = "NO"; self._timer = nil end
end

return _M
