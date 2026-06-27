--@INFO [Orchestrator] master/slave - dominance combo enslaves a target; transfer commits on SAVE

-- PC interactions arrive via on.answer(resp, as): as.askingChar.m_thisChar == GetPlayerCharacter()
-- means the PC is acting; as.answerChar = the target; as.conversationId = the action id.
-- Dominance combo (PC vs the SAME target): INSULT(33) -> FIGHT(34) -> FORCE_H(38).
--
-- SSOT MODEL A (commit-on-save): enslaving a char is PROVISIONAL. We only show a live preview
-- (KickCard removes the target from the school roster - which itself reverts on reload if you don't
-- save). The transfer becomes TRUTH only when you SAVE the class: on.save_class writes a commit line
-- <nDays>\t<name>\t<gender>\t<self> to _orch_slave_commits.flag. The orchestrator ingests that into
-- the per-playthrough journal (memory.db) keyed by the game day, then DERIVES jail's roster for the
-- day school is on. So: no save -> nobody in jail; load an older save -> jail rolls back with it.
--
-- SAFETY: the combo ends on FORCE_H (starts an H-scene). KickCard mid-on.answer is risky, so the
-- preview kick is DEFERRED to a safe boundary: on.end_h (scene over), with on.period as a net.

local _M = {}
local COMMITS = "_orch_slave_commits.flag"   -- append-only commit log the orchestrator ingests
local DBG = "_orch_ms_debug.flag"

local INSULT, FIGHT, FORCE_H = 33, 34, 38
local COMBO = { INSULT, FIGHT, FORCE_H }
local COMBO_NAME = "INSULT -> FIGHT -> FORCE_H"

-- Read-only self-value probes (live schema confirmed 2026-06-24: m_charData.m_character.*).
local SELF_PROBES = {
    { "virtue",       function(i) return i.m_char.m_charData.m_character.virtue end },
    { "intelligence", function(i) return i.m_char.m_charData.m_character.intelligence end },
    { "strength",     function(i) return i.m_char.m_charData.m_character.strength end },
    { "sociability",  function(i) return i.m_char.m_charData.m_character.sociability end },
}

local progress = {}              -- target seat -> combo steps done
local pending_kick = {}           -- seat -> name : enslaved, KickCard preview deferred to a safe tick
local enslaved_uncommitted = {}   -- name -> {gender=, self=} : awaiting a SAVE to commit to the journal

local function dbg(msg)
    log.warn("[MS] %s", msg)
    local ok, f = pcall(io.open, play_path(DBG), "a")
    if ok and f then f:write(msg .. "\n"); f:close() end
end

local function name_of(seat)
    local inst = GetCharInstData(seat)
    if inst then
        local ok, n = pcall(function()
            local cd = inst.m_char.m_charData
            return cd.m_forename .. " " .. cd.m_surname
        end)
        if ok then return n end
    end
    return "seat" .. tostring(seat)
end

local function gender_of(seat)
    local ok, g = pcall(function() return GetCharInstData(seat).m_char.m_charData.m_gender end)
    if ok and type(g) == "number" then return g end
    return -1
end

local function self_str(seat)
    local parts = {}
    for _, p in ipairs(SELF_PROBES) do
        local inst = GetCharInstData(seat)
        if inst then
            local ok, v = pcall(p[2], inst)
            if ok and type(v) == "number" then parts[#parts + 1] = p[1] .. "=" .. tostring(v) end
        end
    end
    return table.concat(parts, ";")
end

-- (Relationship capture moved to rel_snapshot.lua, which maintains the full char_rels graph
-- continuously in school -> a relationship is in the SSOT long before either char is enslaved.)

local function seat_of(cc)
    for _, fn in ipairs({ function() return cc.m_seat end,
                          function() return cc.m_thisChar.m_seat end }) do
        local ok, s = pcall(fn)
        if ok and s ~= nil then return s end
    end
    return nil
end

local function nday()
    local ok, d = pcall(GetGameTimeData)
    if ok and d and d.nDays then return d.nDays end
    return -1
end

-- Deferred KickCard preview (the target visibly leaves school; reverts on reload unless you save).
local function flush_pending(reason)
    for seat, nm in pairs(pending_kick) do
        local ok, err = pcall(KickCard, seat)
        if ok then dbg(string.format("preview KICK seat %d (%s) from school [%s]", seat, nm, reason))
        else dbg(string.format("KickCard FAILED seat %d (%s) [%s]: %s", seat, nm, reason, tostring(err))) end
        pending_kick[seat] = nil
    end
end

function on.answer(resp, as)
    local ispc = false
    pcall(function() ispc = (as.askingChar.m_thisChar == GetPlayerCharacter()) end)
    if not ispc then return resp end

    local target, action = nil, nil
    pcall(function() target = seat_of(as.answerChar) end)
    pcall(function() action = as.conversationId end)
    if target == nil or action == nil then return resp end

    local p = progress[target]
    if action == COMBO[1] then
        progress[target] = 1
        dbg(string.format("combo 1/%d (INSULT) on seat %d", #COMBO, target))
    elseif p and action == COMBO[p + 1] then
        progress[target] = p + 1
        dbg(string.format("combo %d/%d on seat %d", progress[target], #COMBO, target))
        if progress[target] == #COMBO then
            progress[target] = nil
            local nm, g, sf = name_of(target), gender_of(target), self_str(target)
            enslaved_uncommitted[nm] = { gender = g, self = sf }   -- commit on next save
            -- NOTE: relationships are NOT captured here anymore -> rel_snapshot.lua maintains the full
            -- char_rels graph continuously, so a relationship is already in the SSOT long before enslave.
            pending_kick[target] = nm                              -- preview kick at a safe boundary
            dbg(string.format("*** ENSLAVED (provisional): %s via %s -- {%s}; commits on SAVE ***",
                nm, COMBO_NAME, sf))
        end
    else
        progress[target] = nil
    end
    return resp
end

function on.end_h()
    flush_pending("end_h")
end

function on.period(new, old)
    flush_pending("period")
    -- no return: don't override the period progression
end

-- THE COMMIT POINT. Saving the class makes every provisional enslavement TRUTH, stamped with the
-- current game day. Idempotent on the orchestrator side; cleared here so a re-save doesn't re-commit.
function on.save_class(data)
    local day = nday()
    local committed = 0
    for nm, info in pairs(enslaved_uncommitted) do
        local ok, f = pcall(io.open, play_path(COMMITS), "a")
        if ok and f then
            f:write(string.format("%d\t%s\t%d\t%s\n", day, nm, info.gender, info.self)); f:close()
            committed = committed + 1
        end
        enslaved_uncommitted[nm] = nil
    end
    if committed > 0 then
        dbg(string.format("=== SAVE: committed %d transfer(s) at day %d ===", committed, day))
    end
end

function _M:load()
    progress = {}
    pending_kick = {}
    enslaved_uncommitted = {}
    local ok, f = pcall(io.open, play_path(DBG), "w")
    if ok and f then f:write("# master_slave (combo " .. COMBO_NAME .. "; transfer commits on SAVE)\n"); f:close() end
    -- NOTE: _orch_slave_commits.flag is the durable journal source -> NOT truncated here.
end

return _M
