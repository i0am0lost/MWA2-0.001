--@INFO [Orchestrator] rel_snapshot - continuously snapshot the full relationship graph into the SSOT

-- The SSOT keeps EVERY char's relationships (char_id-based, seat-INDEPENDENT) as the cast's persistent
-- "memory" -- like a Sims toon whose relationships survive a vacation away from those Sims. We snapshot
-- the WHOLE relationship matrix in school CONTINUOUSLY, so a relationship is stored LONG before either
-- char is transferred. When two transferred chars are later co-present in jail, jail_intake restores it
-- from this memory (the Luka<->Airi timing problem disappears). Absent/transferred chars are simply not
-- in the snapshot -> their stored relationships stay (sleep) in char_rels until they are present again.
--
-- Triggers (per the design): class load (new roster / new NPCs), end of day (on.period), and after each
-- PC interaction (on.answer) -- the moments relationships can change. School-only (forced in school's
-- forcedconfig, file only in school's mod folder). The orchestrator ingests _orch_rel_snapshot.flag.

local _M = {}
local SNAP = "_orch_rel_snapshot.flag"

local function name_of(seat)
    local inst = GetCharInstData(seat)
    if not inst then return nil end
    local ok, n = pcall(function()
        local cd = inst.m_char.m_charData
        return (cd.m_forename .. " " .. cd.m_surname):gsub("%s+", " ")
    end)
    return ok and n or nil
end

local function snapshot()
    local names = {}
    for s = 0, 24 do names[s] = name_of(s) end           -- present seats -> char names (incl. the PC)
    local lines = {}
    for from = 0, 24 do
        if names[from] then
            for to = 0, 24 do
                if to ~= from and names[to] then
                    local ok, d = pcall(createRelationshipPointsDump, from, to)
                    if ok and type(d) == "table" then
                        local lo, li, di, ha = (d.LOVE or 0), (d.LIKE or 0), (d.DISLIKE or 0), (d.HATE or 0)
                        if lo ~= 0 or li ~= 0 or di ~= 0 or ha ~= 0 then
                            lines[#lines + 1] = string.format("%s\t%s\t%d\t%d\t%d\t%d",
                                names[from], names[to], lo, li, di, ha)
                        end
                    end
                end
            end
        end
    end
    -- overwrite = the current full state; orchestrator upserts it (latest wins). Skip writing an empty
    -- snapshot (e.g. at the menu / no class) so we never wipe a good one with nothing.
    if #lines == 0 then return end
    local ok, f = pcall(io.open, play_path(SNAP), "w")
    if ok and f then
        f:write("# rel snapshot: <from>\t<to>\t<love>\t<like>\t<dislike>\t<hate>\n")
        f:write(table.concat(lines, "\n") .. "\n")
        f:close()
    end
end

function on.load_class()
    snapshot()                                           -- new roster / new NPCs present
end

function on.period(new, old)
    snapshot()                                           -- end of day etc. (no return -> no override)
end

function on.answer(resp, as)
    snapshot()                                           -- after a PC interaction (rels can change)
    return resp
end

function _M:load() end
return _M
