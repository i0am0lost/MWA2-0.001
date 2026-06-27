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

-- [Jail-Orchestrator] Force jail_intake ON (jail only): rebuilds the jail roster from the SSOT inmate
-- list (_orch_jail_inmates.flag) every load -> jail shows only the inmates (+ PC). Self-gates on the
-- inmate file, so it is inert if that file is absent. Lives only in jail's mod folder.
local found_ji = false
for _, mod in ipairs(mods) do
    if mod[1] == "jail_intake" then mod.disabled = false; found_ji = true end
end
if not found_ji then table.insert(mods, { "jail_intake" }) end

-- [Jail-Orchestrator] Force apply_state ON (jail side): the global evolution apply-mod. Reads
-- _orch_char_state.flag (resolver output -- the orchestrator writes it into BOTH worlds) and sets each
-- present char's resolved self-values at runtime -- the card is never written (global-pool architecture).
-- Evolution applies wherever a char is present, and corrupted chars land HERE -> jail needs its own copy.
-- Self-gates on the flag (no file -> no-op). Mirror of school's apply_state.lua.
local found_ap = false
for _, mod in ipairs(mods) do
    if mod[1] == "apply_state" then mod.disabled = false; found_ap = true end
end
if not found_ap then table.insert(mods, { "apply_state" }) end

-- [Jail-Orchestrator] Force jail_phase ON (jail only): steers the phase machine so nobody is teleported
-- into off-limits rooms. Redirects club (period 7) -> end (8) via the on.period return -> the clubrooms
-- are never entered, the day wraps up. No room-setter needed (Lua has none). Mirror lives jail-side only.
local found_jp = false
for _, mod in ipairs(mods) do
    if mod[1] == "jail_phase" then mod.disabled = false; found_jp = true end
end
if not found_jp then table.insert(mods, { "jail_phase" }) end

-- [Jail-Orchestrator] Force jail_probe ON (DEV R&D, read-only): logs each char's room index + whether
-- m_forceAction is reachable from Lua, to settle the NPC-confinement design. Remove once confinement is built.
local found_jpr = false
for _, mod in ipairs(mods) do
    if mod[1] == "jail_probe" then mod.disabled = false; found_jpr = true end
end
if not found_jpr then table.insert(mods, { "jail_probe" }) end

-- [Jail-Orchestrator] Force module_reroute ON (jail only): the SSOT module-reroute hook on AAU's own
-- AAUCardData::UpdateModules. v0 = READ-ONLY address verification (no patching). Confirms the DLL base +
-- RVA math is live-correct before we install the real hook. Writes _orch_reroute_debug.flag.
local found_mr = false
for _, mod in ipairs(mods) do
    if mod[1] == "module_reroute" then mod.disabled = false; found_mr = true end
end
if not found_mr then table.insert(mods, { "module_reroute" }) end