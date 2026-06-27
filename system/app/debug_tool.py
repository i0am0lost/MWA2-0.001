#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
debug_tool.py - inspect & tune the evolution SSOT without grinding the game.
============================================================================
The "global pool" pipeline is: engine counters -> activity_snapshot -> char_activity (DB)
-> resolver -> char_state (DB) -> _orch_char_state.flag -> apply_state.lua sets values on the
LIVE char. This tool sits on the DB layer (the SSOT) so you can:

  * SEE what the SSOT holds and what the resolver WOULD decide (offline, no game).
  * FORCE values (activity counters, race, race-xp) to drive a char over a threshold for testing.
  * RESOLVE on demand and write _orch_char_state.flag into BOTH worlds, so a running game picks
    up the change live (apply_state polls the flag every 700ms) -- the fast tuning loop.

It auto-locates the ACTIVE playthrough DB the same way the orchestrator does: the school world
writes its loaded save name to school/_orch_save.flag; the DB is _playthroughs/<key>/memory.db.

  IMPORTANT about `set` (activity): activity_snapshot OVERWRITES a char's counters every tick
  WHILE that char is present in a loaded class (latest-wins). So forcing char_activity is reliable
  only for (a) chars who are ABSENT, or (b) the RACE axis (char_race/char_race_xp have NO live
  capture yet -> forcing them is the ONLY way to test the race ladder today). For a present char,
  the real lever is the engine counter (the planned Lua keypress setter), not the DB.

Usage (run via run_debug.bat, or with the Python312 interpreter directly):
  debug_tool.py                         # overview: every char's activity + resolved state
  debug_tool.py show <name>             # full detail for one char + WHY the resolver decides it
  debug_tool.py set <name> <metric> <v> # force one DB activity counter (see caveat above)
  debug_tool.py force <name> <metric> <v> # set the live ENGINE counter (debug_force.lua, game running)
  debug_tool.py race <name> <race>      # set a char's OWN race (e.g. Demon) -- enables race axis
  debug_tool.py racexp <name> <other_race> <pos> <neg>   # force racial experience toward a race
  debug_tool.py resolve                 # re-resolve + write _orch_char_state.flag to both worlds
  debug_tool.py --db <path> <cmd...>    # operate on a specific DB instead of the active one
"""

import os
import sys

import playthrough_db as pdb
import resolver

# The active save (hence the DB path) can contain CJK characters; the Windows console is cp1252.
# Force UTF-8 on our streams so printing the path / char names never dies on an encode error.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from _root import ROOT as _BASE   # project root (holds school/ + jail/); app code lives under system/app/
PLAYTHROUGHS = os.path.join(_BASE, "_playthroughs")
SCHOOL_DIR = os.path.join(_BASE, "school")
WORLD_DIRS = [SCHOOL_DIR, os.path.join(_BASE, "jail")]
TS = "debug_tool"   # marker timestamp so forced rows are recognisable in the DB

# Engine H-counter metrics debug_force.lua can set live (must match its METHOD map / activity_snapshot).
FORCE_METRICS = ("climax", "simultaneousClimax", "totalH", "vaginalH", "analH", "totalCum",
                 "cumInVagina", "cumInAnal", "cumSwallowed", "riskyCum", "condomsUsed")


# ----------------------------------------------------------------------------
# Locating the active playthrough DB (mirrors the orchestrator's read_save_name)
# ----------------------------------------------------------------------------
def active_key():
    """The active playthrough key = the school save name (no .sav) from school/_orch_save.flag.
    None if no save is loaded / the flag is absent."""
    path = os.path.join(_BASE, "school", "_orch_save.flag")
    try:
        with open(path, encoding="utf-8") as f:
            v = f.read().strip()
    except OSError:
        return None
    if not v:
        return None
    return v[:-4] if v.lower().endswith(".sav") else v


def active_db_path():
    """Path to the active playthrough's memory.db, or None if it can't be determined / doesn't exist."""
    key = active_key()
    if not key:
        return None
    p = os.path.join(PLAYTHROUGHS, key, "memory.db")
    return p if os.path.exists(p) else None


# ----------------------------------------------------------------------------
# Read-side rendering
# ----------------------------------------------------------------------------
def _sexual_score(act):
    """The combined sexual-exposure score the resolver thresholds on (same formula as resolve_char)."""
    return (act.get("climax", 0) + act.get("cumSwallowed", 0)
            + act.get("cumInVagina", 0) + act.get("cumInAnal", 0))


def cmd_dump(con):
    """Overview: every char with any data -> sexual score, resolved modules, race attitude."""
    ids = pdb.all_char_ids_with_data(con)
    if not ids:
        print("(no chars with data yet -- the DB is empty)")
        return
    print("%-22s %6s  %-26s %s" % ("char", "sexual", "resolved modules", "race attitude"))
    print("-" * 78)
    for cid in ids:
        act = pdb.activity_of(con, cid)
        score = _sexual_score(act)
        mods = [m for m, _ in resolver.resolve_char(con, cid)]
        att = pdb.race_attitude(con, cid)
        att_s = ", ".join("%s:%s" % (r, l) for r, l in att.items()) or "-"
        print("%-22s %6d  %-26s %s" % (cid[:22], score, ", ".join(mods) or "-", att_s))
    print("\nthresholds: Corruption >= %d, Sex Addict >= %d (resolver.py)"
          % (resolver.SEX_CORRUPT, resolver.SEX_ADDICT))


def cmd_show(con, name):
    """Full detail for one char: raw counters, the score, the resolver decision + reasoning, race xp."""
    cid = pdb.normalize_name(name)
    act = pdb.activity_of(con, cid)
    if not act and not pdb.race_xp_of(con, cid) and not pdb.char_state_of(con, cid):
        print("no data for '%s'. Known chars: %s"
              % (cid, ", ".join(pdb.all_char_ids_with_data(con)) or "(none)"))
        return
    print("=== %s ===" % cid)
    print("own race: %s" % (pdb.get_char_race(con, cid) or "(unknown -- race axis off)"))
    print("\nactivity counters:")
    for m, v in sorted(act.items()):
        print("  %-20s %d" % (m, v))
    score = _sexual_score(act)
    print("\nsexual score = climax+cumSwallowed+cumInVagina+cumInAnal = %d" % score)
    if score >= resolver.SEX_ADDICT:
        print("  -> Sex Addict (>= %d)" % resolver.SEX_ADDICT)
    elif score >= resolver.SEX_CORRUPT:
        print("  -> Corruption (>= %d), Sex Addict at %d" % (resolver.SEX_CORRUPT, resolver.SEX_ADDICT))
    else:
        print("  -> neutral (Corruption at %d)" % resolver.SEX_CORRUPT)
    rxp = pdb.race_xp_of(con, cid)
    if rxp:
        print("\nrace xp:")
        for r, xp in rxp.items():
            print("  toward %-10s +%d / -%d" % (r, xp["positive"], xp["negative"]))
    mods = resolver.resolve_char(con, cid)
    print("\nRESOLVED -> %s" % (", ".join("%s(%s)" % (m, s) for m, s in mods) or "(nothing)"))
    print("flags     -> %s" % (resolver.cardstorage_string(con, cid) or "(none)"))


# ----------------------------------------------------------------------------
# Write-side (force values for testing)
# ----------------------------------------------------------------------------
def cmd_set(con, name, metric, value):
    """Force one activity counter. NOTE: overwritten by the live snapshot if this char is present."""
    cid = pdb.normalize_name(name)
    pdb.upsert_activity(con, cid, metric, int(value), TS)
    print("set %s %s = %s" % (cid, metric, value))
    print("(reminder: a PRESENT char's counters are overwritten by the next snapshot -- "
          "use this for absent chars or run `resolve` immediately to apply)")


def cmd_race(con, name, race):
    """Set a char's own race -> enables the race axis for it (no live capture exists yet)."""
    cid = pdb.normalize_name(name)
    pdb.set_char_race(con, cid, race, TS)
    print("set own race of %s = %s" % (cid, race))


def cmd_racexp(con, name, other_race, pos, neg):
    """Force racial experience toward a race. Absolute set (clears prior, then adds the deltas)."""
    cid = pdb.normalize_name(name)
    con.execute("DELETE FROM char_race_xp WHERE char_id=? AND other_race=?", (cid, other_race))
    con.commit()
    pdb.add_race_xp(con, cid, other_race, int(pos), int(neg), TS)
    print("set race xp of %s toward %s = +%s / -%s" % (cid, other_race, pos, neg))
    att = pdb.race_attitude(con, cid).get(other_race, "neutral")
    print("  -> attitude now: %s" % att)


def cmd_confine(con, name, room):
    """Confine a char to <room> in the ONE memory.db (char_id-keyed). The resolver then emits @b:confined/
    @i:cell into char_state, apply_state sets the Card Storage on the present char, and the gated Confinement
    module keeps them there. No seats, no per-world files -- one SSOT, identity = name."""
    cid = pdb.normalize_name(name)
    pdb.set_confine(con, cid, int(room), TS)
    print("confined %s -> cell room %s  (memory.db, char_id-keyed)" % (cid, room))
    print("(resolver -> char_state @b:confined/@i:cell -> apply_state sets Card Storage -> module confines)")


def cmd_unconfine(con, name):
    cid = pdb.normalize_name(name)
    pdb.clear_confine(con, cid)
    print("unconfined %s  (memory.db). In-game Card Storage clears on next resolve/apply." % cid)


def cmd_force(name, metric, value):
    """Queue an ENGINE H-counter set for a PRESENT char (debug_force.lua applies it live in-game).
    Unlike `set` (which the next snapshot overwrites), this drives the real engine counter -> it flows
    snapshot -> DB -> resolver -> apply, the proper way to test thresholds without grinding H. The flag
    is consumed once the char is present. Needs the game running with debug_force forced (school)."""
    if metric not in FORCE_METRICS:
        print("unknown metric '%s'. Known: %s" % (metric, ", ".join(FORCE_METRICS)))
        return
    path = os.path.join(SCHOOL_DIR, "_orch_force_activity.flag")
    body = ("# force engine activity: <name>\t<metric>\t<value> (consumed when the char is present)\n"
            + "%s\t%s\t%d\n" % (pdb.normalize_name(name), metric, int(value)))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(body)
    os.replace(tmp, path)
    print("queued force: %s %s=%s -> %s" % (pdb.normalize_name(name), metric, value, path))
    print("(debug_force.lua sets the engine counter when the char is present, then consumes the flag;")
    print(" the next activity_snapshot carries it into the DB -> resolver -> apply)")


def cmd_resolve(con):
    """Re-resolve every char and write _orch_char_state.flag into both worlds (game picks it up live)."""
    resolved = resolver.resolve_all(con, TS)
    lines = []
    for nm in sorted(resolved):
        eff = resolver.cardstorage_string(con, nm)   # Card-Storage flags only (no vanilla-stat writing)
        if eff:
            lines.append("%s\t%s\t%s" % (nm, ",".join(resolved[nm]), eff))
    body = ("# char_state (resolved): <name>\\t<active modules>\\t<card-storage flags>\n"
            + "\n".join(lines) + "\n")
    for wd in WORLD_DIRS:
        if not os.path.isdir(wd):
            continue
        path = os.path.join(wd, "_orch_char_state.flag")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(body)
        os.replace(tmp, path)
        print("wrote %s" % path)
    n = sum(1 for m in resolved.values() if m)
    print("resolved %d chars (%d with active modules)" % (len(resolved), n))
    for nm in sorted(resolved):
        if resolved[nm]:
            print("  %s -> %s" % (nm, resolved[nm]))


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def _main(argv):
    args = argv[1:]
    db_override = None
    if args and args[0] == "--db":
        if len(args) < 2:
            print("--db needs a path")
            return 2
        db_override, args = args[1], args[2:]

    db_path = db_override or active_db_path()
    if not db_path:
        print("could not find the active playthrough DB.")
        print("  is a save loaded? (school/_orch_save.flag = active key)")
        print("  or pass one explicitly:  debug_tool.py --db <path> <cmd>")
        return 2
    con = pdb.connect(db_path)
    print("# DB: %s\n" % db_path)

    cmd = args[0] if args else "dump"
    rest = args[1:]
    try:
        if cmd == "dump":
            cmd_dump(con)
        elif cmd == "show" and len(rest) == 1:
            cmd_show(con, rest[0])
        elif cmd == "set" and len(rest) == 3:
            cmd_set(con, rest[0], rest[1], rest[2])
        elif cmd == "force" and len(rest) == 3:
            cmd_force(rest[0], rest[1], rest[2])
        elif cmd == "confine" and len(rest) == 2:
            cmd_confine(con, rest[0], rest[1])
        elif cmd == "unconfine" and len(rest) == 1:
            cmd_unconfine(con, rest[0])
        elif cmd == "race" and len(rest) == 2:
            cmd_race(con, rest[0], rest[1])
        elif cmd == "racexp" and len(rest) == 4:
            cmd_racexp(con, rest[0], rest[1], rest[2], rest[3])
        elif cmd == "resolve":
            cmd_resolve(con)
        else:
            print(__doc__.split("Usage")[1] if "Usage" in __doc__ else "bad command")
            return 2
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
