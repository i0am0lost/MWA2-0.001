--@INFO [Orchestrator] Verifies the JSON transfer reached the loaded game

-- On class load, reads each character's AAUData.intelligenceValue out of AAU's per-class JSON
-- store (the .json the orchestrator injects into) via get_class_key, and logs it. A value of
-- 9999 (the marker set in school's save) proves the transfer school->DB->jail reached the game.
-- Writes the outcome to _orch_verify.flag so it can be read after the run.

local _M = {}

local MARKER = 9999   -- school marker; normal intelligenceValue is ~300-900

local function check()
    local lines = {}
    local found = false
    for seat = 0, 24 do
        local ok, inst = pcall(GetCharInstData, seat)
        if not ok or not inst then goto cont end
        local okn, fore, sur = pcall(function()
            local cd = inst.m_char.m_charData
            return cd.m_forename, cd.m_surname
        end)
        if not okn then goto cont end
        -- the JSON key is "<seat> <name>"; try both name orders to be safe
        for _, nm in ipairs({ tostring(sur) .. " " .. tostring(fore),
                              tostring(fore) .. " " .. tostring(sur) }) do
            local okk, data = pcall(get_class_key, seat .. " " .. nm)
            if okk and type(data) == "table" and type(data.AAUData) == "table"
               and data.AAUData.intelligenceValue then
                local iv = data.AAUData.intelligenceValue
                local hit = (iv and iv >= 9000)
                if hit then found = true end
                local line = string.format("seat %d '%s' int=%s%s",
                    seat, nm, tostring(iv), hit and "  <<< MARKER FOUND" or "")
                lines[#lines + 1] = line
                log.warn("[ORCHVERIFY] %s", line)
            end
        end
        ::cont::
    end
    local head = found and "RESULT: MARKER FOUND - transfer reached the game\n"
                        or "RESULT: marker NOT found - json did not carry through\n"
    log.warn("[ORCHVERIFY] %s", head)
    local okf, f = pcall(io.open, play_path("_orch_verify.flag"), "w")
    if okf and f then f:write(head .. table.concat(lines, "\n")); f:close() end
end

function on.load_class()
    pcall(check)
end

function _M:load()
    log.warn("[ORCHVERIFY] loaded - will check the transfer marker on class load.")
end

return _M
