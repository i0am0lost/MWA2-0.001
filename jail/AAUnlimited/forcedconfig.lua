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