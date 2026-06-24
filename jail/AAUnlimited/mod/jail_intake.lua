--@INFO [Orchestrator] jail intake - reconstruct the jail roster from the SSOT inmate list

-- The jail roster is NOT baked into the save: it is REBUILT every safe tick from the single source of
-- truth (the orchestrator's inmate list in _orch_jail_inmates.flag). Reconstruction = two-way:
--   * KickCard every roster char that is NOT an inmate (and not the PC), and
--   * AddCard every inmate that is NOT currently present (its base card lives as a .png on disk).
-- => jail always shows exactly {PC + committed inmates}, even if an inmate is committed AFTER jail
-- was already loaded/filtered (the bug a kick-only filter had). Inmate values are injected later.
--
-- Inmate file line: "<name>\t<cardfile>\t<gender>" (gender 0=male/1=female). Read via play_path, so
-- it is world-scoped: absent file => do nothing => can never touch the school roster.
--
-- WHY: "alone in jail" becomes literally true -> basis for the loneliness/isolation modules (notes 2.4c).

local _M = {}
local INMATES_FILE = "_orch_jail_inmates.flag"
local DBG = "_orch_jail_debug.flag"

local function dbg(msg)
    log.warn("[JAIL] %s", msg)
    local ok, f = pcall(io.open, play_path(DBG), "a")
    if ok and f then f:write(msg .. "\n"); f:close() end
end

local function norm(s)   -- collapse whitespace + trim, to agree with the orchestrator's normalize_name
    return (s:gsub("%s+", " "):gsub("^%s+", ""):gsub("%s+$", ""))
end

local function name_of(seat)
    local inst = GetCharInstData(seat)
    if inst then
        local ok, n = pcall(function()
            local cd = inst.m_char.m_charData
            return cd.m_forename .. " " .. cd.m_surname
        end)
        if ok then return norm(n) end
    end
    return "seat" .. tostring(seat)
end

local function is_pc(seat)
    local inst = GetCharInstData(seat)
    if not inst then return false end
    local ok, same = pcall(function() return inst.m_char == GetPlayerCharacter() end)
    return ok and same
end

-- Returns inmates = { [normname] = {card=, gender=} }, count -- or nil if the file is absent.
local function read_inmates()
    local f = io.open(play_path(INMATES_FILE), "r")
    if not f then return nil end
    local inmates, n = {}, 0
    for line in f:lines() do
        if line ~= "" and line:sub(1, 1) ~= "#" then
            local name, card, gender, self = line:match("^([^\t]*)\t([^\t]*)\t([^\t]*)\t?(.*)$")
            if not name then name = line end           -- tolerate a bare-name line
            name = norm(name)
            if name ~= "" then
                inmates[name] = { card = card or "", gender = tonumber(gender or "1") or 1, self = self or "" }
                n = n + 1
            end
        end
    end
    f:close()
    return inmates, n
end

-- Read the current period from logperiod's flag (logperiod reliably writes it; calling GetGameTimeData
-- directly from this mod returned -1). Home screen = 9.
local function cur_period()
    local f = io.open(play_path("_orch_period.flag"), "r")
    if not f then return -1 end
    local v = tonumber((f:read("*a") or ""):match("%-?%d+"))
    f:close()
    return v or -1
end

local function free_seat()
    for seat = 0, 24 do
        if GetCharInstData(seat) == nil then return seat end
    end
    return nil
end

-- Try to AddCard an inmate. The exact filename form AddCard wants is unconfirmed, so try the bare
-- name first (AddCard is expected to pick the folder from the gender bool), then a folder-qualified
-- form. Success = the target seat becomes occupied. Returns the winning form or nil.
local function add_inmate(name, info)
    if info.card == nil or info.card == "" then
        dbg(string.format("cannot AddCard '%s': no card file resolved", name)); return nil
    end
    local seat = free_seat()
    if not seat then dbg("cannot AddCard '" .. name .. "': no free seat"); return nil end
    local female = (info.gender ~= 0)
    local folder = female and "Female\\" or "Male\\"
    for _, fn in ipairs({ info.card, folder .. info.card }) do
        pcall(KickCard, seat)                          -- ensure the seat is clear before each attempt
        local ok = pcall(AddCard, fn, female, seat)
        if ok and GetCharInstData(seat) ~= nil and name_of(seat) == name then
            return fn, seat
        end
    end
    pcall(KickCard, seat)                              -- both forms failed -> leave no wrong card behind
    return nil
end

-- 2b: write the SSOT-stored self values onto an inmate's live seat (Card + Play-Data model). Same
-- field path master_slave READ from (m_char.m_charData.m_character.<field>), so write is symmetric.
-- self string = "virtue=0;intelligence=2;strength=1;sociability=3". Returns what was applied.
local function inject_self(seat, selfstr)
    if not selfstr or selfstr == "" then return "" end
    local inst = GetCharInstData(seat)
    if not inst then return "" end
    local applied = {}
    for k, v in selfstr:gmatch("([%a_]+)=(%-?%d+)") do
        local val = tonumber(v)
        local got = nil
        pcall(function()
            local c = inst.m_char.m_charData.m_character
            if     k == "virtue"       then c.virtue = val;       got = c.virtue
            elseif k == "intelligence" then c.intelligence = val; got = c.intelligence
            elseif k == "strength"     then c.strength = val;     got = c.strength
            elseif k == "sociability"  then c.sociability = val;  got = c.sociability end
        end)
        if got == val then applied[#applied + 1] = k .. "=" .. v             -- write took (read-back ok)
        elseif got ~= nil then applied[#applied + 1] = k .. "!=" .. tostring(got) end  -- did NOT stick
    end
    return table.concat(applied, ";")
end

-- 2c: restore relationships among CO-PRESENT chars in jail (another inmate, or the PC who is always
-- here). The orchestrator writes _orch_jail_rels.flag (from\tto\tlove\tlike\tdislike\thate) for the
-- current inmates; we restore each pair whose BOTH endpoints are present right now. Absent counterparts
-- stay asleep in the SSOT until they too are transferred (Boyfriend-Join / return).
local function read_rels()
    local f = io.open(play_path("_orch_jail_rels.flag"), "r")
    if not f then return nil end
    local out = {}
    for line in f:lines() do
        if line ~= "" and line:sub(1, 1) ~= "#" then
            local fr, to, lo, li, di, ha =
                line:match("^([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)")
            if fr and to then
                out[#out + 1] = { from = norm(fr), to = norm(to), love = tonumber(lo) or 0,
                    like = tonumber(li) or 0, dislike = tonumber(di) or 0, hate = tonumber(ha) or 0 }
            end
        end
    end
    f:close()
    return out
end

local function present_all()                            -- name -> seat for EVERY present char (incl. PC)
    local p = {}
    for s = 0, 24 do if GetCharInstData(s) then p[name_of(s)] = s end end
    return p
end

local rels_sig = nil
local function restore_rels()
    local rels = read_rels()
    if not rels then return nil end
    local pa = present_all()
    local names = {}
    for nm in pairs(pa) do names[#names + 1] = nm end
    table.sort(names)
    local sig = table.concat(names, ",")
    if sig == rels_sig then return nil end              -- already restored for this presence set
    rels_sig = sig
    local done = {}
    for _, r in ipairs(rels) do
        local fs, t2 = pa[r.from], pa[r.to]
        if fs and t2 then
            local dump = { LOVE = r.love, LIKE = r.like, DISLIKE = r.dislike, HATE = r.hate }
            if pcall(restoreRelationshipPointsFromDump, fs, t2, dump, true) then
                done[#done + 1] = string.format("%s->%s(L%d/Li%d/D%d/H%d)", r.from, r.to,
                    r.love, r.like, r.dislike, r.hate)
            end
        end
    end
    return (#done > 0) and table.concat(done, ", ") or nil
end

-- Snapshot the present non-PC roster as name->seat.
local function present_nonpc()
    local present = {}
    for seat = 0, 24 do
        if GetCharInstData(seat) and not is_pc(seat) then present[name_of(seat)] = seat end
    end
    return present
end

-- Do the present non-PC names already EXACTLY match the inmate set? Then nothing to do.
local function matches(present, inmates)
    for nm in pairs(inmates) do if not present[nm] then return false end end
    for nm in pairs(present) do if not inmates[nm] then return false end end
    return true
end

local last_log = nil
local function logonce(msg)                             -- de-spam: timer re-applies every 700ms
    if msg ~= last_log then dbg(msg); last_log = msg end
end

local injected = {}                                     -- name -> true: self-values written this session

local function apply(reason)
    local inmates, n = read_inmates()
    if inmates == nil then return end                  -- no inmate file -> not jail / nothing to do

    local present = present_nonpc()
    local period = cur_period()

    -- Stable AND everything injected? -> nothing to do (the 700ms timer re-enters here constantly).
    local done = matches(present, inmates)
    if done then for nm in pairs(inmates) do if not injected[nm] then done = false break end end end
    if done then return end

    -- Non-inmates can be removed immediately at any moment (KickCard is safe at any tick).
    local kicked = 0
    for nm, seat in pairs(present) do
        if not inmates[nm] then if pcall(KickCard, seat) then kicked = kicked + 1; present[nm] = nil end end
    end

    -- AddCard + value-injection only at a STABLE moment: the home screen (period 9), like undyingAddCards.
    if period ~= 9 then
        logonce(string.format("period %s: kicked %d non-inmates; deferring AddCard to home screen (9)",
            tostring(period), kicked))
        return
    end

    -- AddCard every inmate NOT already present (present ones kept by identity -> never vanish on a bad card).
    local added, failed = {}, {}
    for nm, info in pairs(inmates) do
        if not present[nm] then
            local fn, seat = add_inmate(nm, info)
            if fn then present[nm] = seat; added[#added + 1] = string.format("%s@%d(%s)", nm, seat, fn)
            else failed[#failed + 1] = nm .. "[" .. (info.card or "?") .. "]" end
        end
    end

    -- 2b: inject SSOT self-values onto each present inmate, once per session.
    local injlog = {}
    for nm, info in pairs(inmates) do
        local seat = present[nm]
        if seat and not injected[nm] then
            local ap = inject_self(seat, info.self)
            injected[nm] = true
            if ap ~= "" then injlog[#injlog + 1] = nm .. "{" .. ap .. "}" end
        end
    end

    -- 2c: restore relationships among co-present chars (re-runs when the present set changes).
    local relsdone = restore_rels()

    if #added > 0 or #failed > 0 or #injlog > 0 or relsdone then
        logonce(string.format("p9: kicked=%d ADDED={%s} FAILED={%s} INJECTED={%s} RELS={%s}", kicked,
            table.concat(added, ", "), table.concat(failed, ", "), table.concat(injlog, ", "),
            relsdone or ""))
    end
end

function on.load_class()
    injected = {}                                      -- fresh class -> re-inject after re-adding
    rels_sig = nil                                     -- ...and re-restore relationships
    apply("load_class")
end

function on.room_change(inst)
    apply("room_change")
end

function on.period(new, old)
    apply("period")
    -- no return: don't override the period progression
end

function _M:load()
    local ok, f = pcall(io.open, play_path(DBG), "w")
    if ok and f then f:write("# jail_intake (roster reconstructed from SSOT inmates + PC)\n"); f:close() end
    -- Poll-driven reconcile (like logperiod): events alone miss the case where you SWITCH into jail
    -- while it was suspended at the home screen (no new event fires). The timer resumes with the
    -- process and re-applies. Guarded by matches() -> a no-op once the roster equals the SSOT.
    require "iuplua"
    self._timer = iup.timer { time = 700, action_cb = function() pcall(apply, "timer") end }
    self._timer.run = "YES"
end

function _M:unload()
    if self._timer then self._timer.run = "NO"; self._timer = nil end
end

return _M
