--@INFO [Orchestrator] Dumps the live roster (seat -> name + json-block match) on class load

-- For each occupied seat it records: seat index, the live character name, and whether AAU's
-- per-class JSON has a block for "<seat> <name>" (i.e. whether the historical json-seat matches
-- the CURRENT roster seat). This tells the orchestrator how to target the inject by name.
-- Output: _orch_roster.flag (tab-separated: seat <TAB> name <TAB> json=yes|NO).

local _M = {}

local function dump()
    local lines = {}
    local occupied, withjson = 0, 0
    for seat = 0, 24 do
        local ok, inst = pcall(GetCharInstData, seat)
        if ok and inst then
            occupied = occupied + 1
            local okn, sur, fore = pcall(function()
                local cd = inst.m_char.m_charData
                return tostring(cd.m_surname), tostring(cd.m_forename)
            end)
            local nm = okn and (sur .. " " .. fore) or "<name-err>"
            local okk, data = pcall(get_class_key, seat .. " " .. nm)
            local hasjson = (okk and type(data) == "table" and type(data.AAUData) == "table")
            if hasjson then withjson = withjson + 1 end
            lines[#lines + 1] = string.format("%d\t%s\tjson=%s", seat, nm, hasjson and "yes" or "NO")
        end
    end
    local header = string.format("# occupied=%d  with_json_block=%d\n", occupied, withjson)
    local okf, f = pcall(io.open, play_path("_orch_roster.flag"), "w")
    if okf and f then f:write(header .. table.concat(lines, "\n")); f:close() end
    log.warn("[ORCHROSTER] %d occupied seats, %d with matching json block", occupied, withjson)
end

function on.load_class()
    pcall(dump)
end

function _M:load()
    log.warn("[ORCHROSTER] loaded - will dump roster on class load.")
end

return _M
