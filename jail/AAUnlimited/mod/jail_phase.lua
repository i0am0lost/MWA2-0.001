--@INFO [Orchestrator] jail_phase - keep jail out of off-limits phases (skip club -> end of day)

-- jail confinement WITHOUT a teleport API (there is no Lua room-setter). Instead of ejecting the PC/NPCs
-- out of a forbidden room (impossible from Lua), we steer the PHASE machine so nobody is ever teleported
-- there in the first place. The day's phases each teleport everyone to a node; the off-limits ones (club)
-- get redirected to "end of day" via the on.period return value (the proven mechanism, same as timewarp.lua).
--
-- Period table (notes 3.1):
--   1 day · 2 nothing · 3 first lesson · 4 first break · 5 sports · 6 second break · 7 club · 8 end · 9 home · 10 sleep
-- Normal phases (1-4) stay -> the PC plays them in normal rooms and always returns to the fixed node.
-- The day just wraps up early instead of going to the club. jail-only (school keeps normal clubs).
--
-- NOTE: the on.period RETURN sets the engine's target period. To block more phases, add them to REDIRECT
-- below (e.g. [5] = 8 to also skip sports). The target (8) must itself NOT be in REDIRECT, or it loops.

local _M = {}
local DBG = "_orch_phase_debug.flag"

-- off-limits period -> where to send the engine instead. Tune freely (this is the one line to edit).
local REDIRECT = {
    [7] = 8,   -- club -> end of day (the clubrooms the player wants to keep everyone out of)
}

local function dbg(msg)
    local ok, f = pcall(io.open, play_path(DBG), "a")
    if ok and f then f:write(msg .. "\n"); f:close() end
end

function on.period(new, old)
    if new == old then return end          -- no real transition -> nothing to do
    local to = REDIRECT[new]
    if to then
        dbg(string.format("redirect period %d -> %d (off-limits)", new, to))
        return to                          -- override: engine goes to `to` instead of `new`
    end
    -- not blocked -> return nothing so the normal progression stands (don't fight other period mods)
end

function _M:load()
    local ok, f = pcall(io.open, play_path(DBG), "w")
    if ok and f then f:write("# jail_phase (off-limits period redirects; jail-only)\n"); f:close() end
end

function _M:unload() end

return _M
