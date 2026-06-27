--@INFO [Orchestrator] activity_snapshot - continuously snapshot each char's cumulative H activity into the SSOT

-- The activity DB (notes 4.7) is the second SSOT layer: per-char CUMULATIVE activity counters that the
-- end-of-day resolve turns into states/modules (e.g. lots of H -> chaste becomes "Sex Addict"). The engine
-- already keeps these counters itself (m_characterStatus, per partner) -- we only READ and snapshot them,
-- exactly like rel_snapshot does for relationships. Per char we SUM the counter over all partner seats to
-- get that char's lifetime total. Absent chars are simply not in the snapshot -> their counters sleep.
--
-- Triggers: end of H (on.end_h, the moment these counters change), end of day (on.period) and class load.
-- School-only (forced in school's forcedconfig). The orchestrator ingests _orch_activity_snapshot.flag.

local _M = {}
local SNAP = "_orch_activity_snapshot.flag"

-- metric name (DB) -> m_characterStatus accessor method. Read form = method(self, towards).
local METRICS = {
    { "climax",             "m_climaxCount" },
    { "simultaneousClimax", "m_simultaneousClimax" },
    { "totalH",             "m_totalH" },
    { "vaginalH",           "m_vaginalH" },
    { "analH",              "m_analH" },
    { "totalCum",           "m_totalCum" },
    { "cumInVagina",        "m_cumInVagina" },
    { "cumInAnal",          "m_cumInAnal" },
    { "cumSwallowed",       "m_cumSwallowed" },
    { "riskyCum",           "m_riskyCum" },
    { "condomsUsed",        "m_condomsUsed" },
}

local function name_of(seat)
    local inst = GetCharInstData(seat)
    if not inst then return nil end
    local ok, n = pcall(function()
        local cd = inst.m_char.m_charData
        return (cd.m_forename .. " " .. cd.m_surname):gsub("%s+", " ")
    end)
    return ok and n or nil
end

-- Sum one char's counter over all partner seats (the engine keys it per partner). Returns 0 on any error.
local function metric_total(seat, method)
    local inst = GetCharInstData(seat)
    if not inst then return 0 end
    local total = 0
    pcall(function()
        local status = inst.m_char.m_characterStatus
        for towards = 0, 24 do
            if towards ~= seat then
                local v = status[method](status, towards)
                if type(v) == "number" then total = total + v end
            end
        end
    end)
    return total
end

local function snapshot()
    local names = {}
    for s = 0, 24 do names[s] = name_of(s) end             -- present seats -> char names (incl. the PC)
    local lines = {}
    for seat = 0, 24 do
        if names[seat] then
            for _, m in ipairs(METRICS) do
                local v = metric_total(seat, m[2])
                if v ~= 0 then
                    lines[#lines + 1] = string.format("%s\t%s\t%d", names[seat], m[1], v)
                end
            end
        end
    end
    -- overwrite = the current totals; orchestrator upserts (latest wins). Skip an empty snapshot (menu /
    -- no class / nobody has any activity) so we never wipe good counters with nothing.
    if #lines == 0 then return end
    local ok, f = pcall(io.open, play_path(SNAP), "w")
    if ok and f then
        f:write("# activity snapshot: <name>\t<metric>\t<value> (cumulative, summed over partners)\n")
        f:write(table.concat(lines, "\n") .. "\n")
        f:close()
    end
end

function on.end_h()
    snapshot()                                             -- H just ended -> counters changed
end

function on.period(new, old)
    snapshot()                                             -- end of day etc. (no return -> no override)
end

function on.load_class()
    snapshot()                                             -- new roster present
end

function _M:load() end
return _M
