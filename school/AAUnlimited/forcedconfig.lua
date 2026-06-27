for i,mod in ipairs(mods) do
    if mod[1] == "fakereg" then
        mod.disabled = false
        goto skip
    end
end

table.insert(mods, { "fakereg" })

::skip::
bUsePPeX = true
bUsePP2 = false

-- [Jail-Orchestrator] Force logperiod ON every start (savedconfig had it disabled).
-- logperiod writes _orch_period.flag every 500ms so the orchestrator knows the period
-- (home screen = 9 -> show the JAIL button). forcedconfig is never overwritten by the game.
local found_logp = false
for _, mod in ipairs(mods) do
    if mod[1] == "logperiod" then mod.disabled = false; found_logp = true end
end
if not found_logp then table.insert(mods, { "logperiod" }) end

-- [Jail-Orchestrator] Force orch_savename ON: writes _orch_save.flag with the loaded save
-- name so the orchestrator can couple the matching jail twin to the chosen school playthrough.
local found_sn = false
for _, mod in ipairs(mods) do
    if mod[1] == "orch_savename" then mod.disabled = false; found_sn = true end
end
if not found_sn then table.insert(mods, { "orch_savename" }) end

-- [Jail-Orchestrator] Force master_slave ON: detects the dominance combo (INSULT->FIGHT->FORCE_H)
-- and logs it to _orch_ms_debug.flag (exploratory step 1 of the master/slave transfer system).
local found_ms = false
for _, mod in ipairs(mods) do
    if mod[1] == "master_slave" then mod.disabled = false; found_ms = true end
end
if not found_ms then table.insert(mods, { "master_slave" }) end

-- [Jail-Orchestrator] Force rel_snapshot ON (school only): continuously snapshots the full relationship
-- matrix into the SSOT (char_rels) so relationships are remembered before any transfer (Sims-style
-- "experience"). Lives only in school's mod folder; the orchestrator ingests _orch_rel_snapshot.flag.
local found_rs = false
for _, mod in ipairs(mods) do
    if mod[1] == "rel_snapshot" then mod.disabled = false; found_rs = true end
end
if not found_rs then table.insert(mods, { "rel_snapshot" }) end

-- [Jail-Orchestrator] Force activity_snapshot ON (school only): continuously snapshots each char's
-- cumulative H activity counters into the SSOT (char_activity) so the end-of-day resolve can derive
-- states/modules from them (notes 4.7). Lives only in school's mod folder; the orchestrator ingests
-- _orch_activity_snapshot.flag.
local found_as = false
for _, mod in ipairs(mods) do
    if mod[1] == "activity_snapshot" then mod.disabled = false; found_as = true end
end
if not found_as then table.insert(mods, { "activity_snapshot" }) end

-- [Jail-Orchestrator] Force apply_state ON: the global evolution apply-mod. Reads _orch_char_state.flag
-- (resolver output) and sets each present char's resolved self-values at runtime -- the card is never
-- written (global-pool architecture). Lives in school's mod folder (jail gets its own copy).
local found_ap = false
for _, mod in ipairs(mods) do
    if mod[1] == "apply_state" then mod.disabled = false; found_ap = true end
end
if not found_ap then table.insert(mods, { "apply_state" }) end

-- [Jail-Orchestrator] Force debug_force ON (DEV TOOL): reads _orch_force_activity.flag (written by
-- debug_tool.py) and sets a present char's ENGINE H-counters live, so thresholds can be tested without
-- grinding H scenes -> flows snapshot -> char_activity -> resolver -> apply. Self-gates on the flag
-- (no file -> no-op). DEV ONLY -- remove this block for a real build.
local found_df = false
for _, mod in ipairs(mods) do
    if mod[1] == "debug_force" then mod.disabled = false; found_df = true end
end
if not found_df then table.insert(mods, { "debug_force" }) end