--@INFO [Orchestrator] jail_probe - DEV R&D: dump char Lua members + which room-change hook fires (read-only)

-- Recon for NPC-confinement. v1 guessed wrong (inst.m_forceAction MISSING, no roomChange events). This
-- version EXPLORES instead of guessing: it enumerates the actual Lua members of the char instance (so we
-- see if/where m_forceAction lives) and registers EVERY plausible movement hook to see which one fires.
-- Read-only. Writes _orch_probe.flag. DEV-only -- remove once confinement is built.

local _M = {}
local DBG = "_orch_probe.flag"

local ROOMS = {
    [0]="School gates",[1]="Back street",[2]="Outside gym",[3]="School route",[4]="Mens changing",
    [11]="Outside classroom",[12]="Rooftop access",[18]="Library",[19]="Classroom",[22]="Rooftop",
    [25]="Courtyard",[31]="Dojo",[32]="Gymnasium",[38]="Cafeteria",[39]="Outside Station",[40]="Karaoke",
    [43]="Boys' room",[44]="Girls' room",[51]="Love Hotel",
}

local function w(msg)
    local ok, f = pcall(io.open, play_path(DBG), "a")
    if ok and f then f:write(msg .. "\n"); f:close() end
end

local function name_of(inst)
    local ok, n = pcall(function()
        local cd = inst.m_char.m_charData
        return cd.m_forename .. " " .. cd.m_surname
    end)
    return ok and n or "?"
end

-- Try to enumerate an object's Lua members (works if it's a table or pairs-iterable; userdata may be empty).
local function dump(label, get_obj)
    local ok, obj = pcall(get_obj)
    if not ok or obj == nil then w("  " .. label .. " = <nil/err>"); return end
    local cnt = 0
    local ok2 = pcall(function()
        for k, v in pairs(obj) do
            w(string.format("    %s.%-22s : %s", label, tostring(k), type(v)))
            cnt = cnt + 1; if cnt > 80 then break end
        end
    end)
    if cnt == 0 then w("  " .. label .. " : pairs empty (userdata) ok2=" .. tostring(ok2)) end
end

local dumped = false
local function dump_once()
    if dumped then return end
    for s = 0, 24 do
        local inst = GetCharInstData(s)
        if inst then
            dumped = true
            w("=== member dump for seat " .. s .. " (" .. name_of(inst) .. ") ===")
            dump("inst", function() return inst end)
            dump("inst.m_char", function() return inst.m_char end)
            -- probe likely m_forceAction locations
            for _, p in ipairs({ "inst.m_forceAction", "inst.m_char.m_forceAction" }) do
                local got = "nil"
                pcall(function()
                    local v = (p == "inst.m_forceAction") and inst.m_forceAction or inst.m_char.m_forceAction
                    if v ~= nil then got = type(v) end
                end)
                w("  path " .. p .. " = " .. got)
            end
            w("")
            return
        end
    end
end

local function snap(hook)
    w("[hook fired] " .. hook)
    for s = 0, 24 do
        local inst = GetCharInstData(s)
        if inst then
            local pc = "?"; pcall(function() pc = tostring(inst:IsPC()) end)
            local room = "?"
            pcall(function() room = tostring(inst:GetCurrentRoom()) end)
            w(string.format("    seat %2d  %-18s pc=%-5s room=%s %s",
                s, name_of(inst), pc, room, ROOMS[tonumber(room) or -1] or ""))
        end
    end
    w("")
end

function on.load_class() dump_once(); snap("load_class") end
function on.room_change(inst) snap("on.room_change(inst)") end       -- §3.4 verified hook
function on.roomChange(seat, room, action) snap("on.roomChange(seat,room,action)") end  -- cram_school style
function on.move(inst) snap("on.move(inst)") end
function on.period(new, old) snap("period " .. tostring(old) .. "->" .. tostring(new)) end

function _M:load()
    local ok, f = pcall(io.open, play_path(DBG), "w")
    if ok and f then f:write("# jail_probe v2: member dump + which room hook fires (read-only)\n"); f:close() end
end

function _M:unload() end

return _M
