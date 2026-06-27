#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
resolver.py - the evolution "brain": turn accumulated SSOT data into ACTIVE modules per character.
==================================================================================================
Reads the per-playthrough DBs (char_activity, char_race_xp, char_rels) and evaluates the EVOLUTION_MAP
threshold rules to decide which modules each character should currently have ACTIVE. Writes the result to
char_state. The global apply-mod reads char_state at runtime and activates those modules on the LIVE
characters -- the card file is NEVER written (global-pool architecture; notes Backlog/EVOLUTION_MAP).

Pure Python, no game needed: the resolve is deterministic and unit-testable. Runs at the end-of-day
resolve (orchestrator) or via CLI. Thresholds are tunable design constants.
"""

import sys

import playthrough_db as pdb

# --- Tunable thresholds (EVOLUTION_MAP). Free design choices; calibrate later. ----------------------
SEX_CORRUPT = 15      # combined sexual-exposure score -> Corruption (Kuroda's ~17 still triggers)
SEX_ADDICT  = 40      # ... -> Sex Addict (the higher tier on the same axis)

# NOTE: we DELIBERATELY do NOT translate modules into vanilla-stat writes (the old MODULE_EFFECTS:
# virtue=0/sociability=3). Vanilla stats are read-only INPUT the engine/other modules own; writing them
# would hijack volatile values and fight the game. Evolution behaviour is produced by MODULES (activate the
# behaviour module, e.g. chaste / Sex Addict) and by our own Card-Storage FLAGS that gate dispatchers
# (cardstorage_string below) -- never by setting a stat. The resolver therefore outputs only the active
# module set + the flags; apply_state writes the flags, the reroute hook injects/gates the modules.


def _race_module(race, label):
    """Map a race-attitude valence label (pdb.race_attitude) to the actual AAU module name
    (MODULE_CATEGORIZATION race axis). Returns None for an unknown label."""
    return {
        "bias":             "Bias-%s" % race,
        "obsession":        "Obsession-%s" % race,
        "prejudice":        "Prejudice-%s" % race,
        "hostile/hunter":   "Hunter-%s" % race,
        "hostile/natenemy": "Natural Enemy-%s" % race,
        "hostile/slayer":   "Slayer-%s" % race,
    }.get(label)


def resolve_char(con, char_id):
    """Derive the modules that should be ACTIVE for one char from its SSOT data. Returns a list of
    (module, source) pairs. Pure read -- writes nothing. The single place evolution decisions are made."""
    out = []

    # --- sexual / corruption axis (from char_activity) ---
    act = pdb.activity_of(con, char_id)
    sexual = (act.get("climax", 0) + act.get("cumSwallowed", 0)
              + act.get("cumInVagina", 0) + act.get("cumInAnal", 0))
    if sexual >= SEX_ADDICT:
        out.append(("Sex Addict", "sexual"))
    elif sexual >= SEX_CORRUPT:
        out.append(("Corruption", "sexual"))

    # --- race axis (from char_race_xp via the attitude ladder) ---
    for race, label in pdb.race_attitude(con, char_id).items():
        mod = _race_module(race, label)
        if mod:
            out.append((mod, "race"))

    # --- confinement axis (char_id-keyed, from char_confine): a behaviour module, not a value effect.
    #     The Card-Storage flags it needs are emitted by cardstorage_string(); here we just record that
    #     the Confinement module should be ACTIVE for this char (transparency in char_state).
    if pdb.confine_of(con, char_id) is not None:
        out.append(("Confinement", "confine"))

    # --- social / loneliness axis: TODO. The trigger is "was socially rich AND now isolated", which
    #     needs runtime co-presence (world-state), not yet in the DB. social_wealth (pdb.social_wealth)
    #     gives the "rich" half; the "isolated" half lands with world-state. Deferred.

    return out


def cardstorage_string(con, char_id):
    """The Card-Storage flags for a char as a stable '@key=value;...' string (the form apply_state sets via
    setCardStorage, gating behaviour modules). char_id-keyed -- the resolver never deals in seats. Derived
    from the ONE memory.db. Currently: confinement (confined=true, cell=<room>). Empty string if none."""
    parts = []
    cell = pdb.confine_of(con, char_id)
    if cell is not None:
        parts.append("@b:confined=1")     # @b: -> Card-Storage Bool ; @i: -> Card-Storage Int (apply_state)
        parts.append("@i:cell=%d" % cell)
    return ";".join(parts)


def resolve_all(con, ts):
    """Resolve every char that has data and write char_state. Returns {char_id: [active module names]}."""
    result = {}
    for cid in pdb.all_char_ids_with_data(con):
        items = resolve_char(con, cid)
        pdb.replace_char_state(con, cid, items, ts)
        result[cid] = [m for m, _ in items]
    return result


def _main(argv):
    if len(argv) < 2:
        print("usage: resolver.py <db_path> [resolve|dump]")
        return 2
    con = pdb.connect(argv[1])
    cmd = argv[2] if len(argv) > 2 else "resolve"
    if cmd == "resolve":
        res = resolve_all(con, ts="cli")
        for cid, mods in res.items():
            if mods:
                print("  %s -> %s" % (cid, mods))
        print("resolved %d chars (%d with active modules)"
              % (len(res), sum(1 for m in res.values() if m)))
    elif cmd == "dump":
        for cid in pdb.all_char_ids_with_data(con):
            st = pdb.char_state_of(con, cid)
            if st:
                print("  %s : %s" % (cid, st))
    else:
        print("unknown command:", cmd)
        return 2
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
