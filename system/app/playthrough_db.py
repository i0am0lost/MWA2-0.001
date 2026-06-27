#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
playthrough_db.py - per-playthrough long-term memory (LTM) for the AA2 jail project.
================================================================================
ONE SQLite DB per playthrough, living next to its saves:
    _playthroughs/<save name>/memory.db

It is the cross-world MEMORY (school <-> jail share it within one playthrough), NOT the
game engine. The engine only ever loads the single .sav/.json we hand it; coupling +
memory live entirely in this Python layer (see HANDOVER_jail-coupling + project notes 2.4d).

Three data classes (project notes), mapped to three tables:
  * chars         - per-character SELF values (virtue, corruption, traits, modules, stats).
                    Source = the save's .json (AAU per-char store), which AAU reads back on
                    load (init.lua get/set_class_key) -> editable, no binary save reversing.
  * relationships - char<->char (love/hate ...), presence-dependent. Snapshot/inject mechanism
                    is in-game Lua (triggers_supplemental.lua) - table is here, wiring later.
  * world_state   - per-world scalar state (key/value).

DESIGN DECISIONS (made here, open to change):
  * char_id = normalized character NAME (whitespace-collapsed). Pragmatic stable identity;
    a card-hash refinement can come later if name collisions ever matter.
  * self_data is a JSON blob (the whole per-char block from the .json), so the schema doesn't
    freeze AAU's evolving field set. Querying specific values = json_extract or in Python.
  * The .json is a HISTORICAL accumulator (many "<seat> <name>" entries per name). snapshot
    merges per name, keeping the richest (most-fields) entry as "current". Roster-exact
    attribution ultimately wants the live roster (in-game GetCharInstData) - documented limit.
  * Timestamps are passed IN by the caller (ISO string), never generated here, so callers can
    stay deterministic / the same value works from Python or a Lua-driven sync.

This module is import-safe and has no side effects on import. CLI: `python playthrough_db.py
<db_path> snapshot <world> <json_path>` / `... inject <world> <json_path>` / `... dump`.
"""

import json
import os
import re
import sqlite3
import sys

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS chars (
    char_id      TEXT PRIMARY KEY,   -- normalized character name (stable identity)
    display_name TEXT,
    self_data    TEXT,               -- JSON blob: AAUData + module flags (the transferable self)
    last_world   TEXT,               -- 'school' | 'jail' : where this was last snapshotted
    updated      TEXT                -- ISO timestamp (caller-supplied)
);
CREATE TABLE IF NOT EXISTS relationships (
    from_id  TEXT,
    to_id    TEXT,
    kind     TEXT,                   -- 'love' | 'hate' | numeric axis name
    value    REAL,
    updated  TEXT,
    PRIMARY KEY (from_id, to_id, kind)
);
CREATE TABLE IF NOT EXISTS world_state (
    world  TEXT,                     -- 'school' | 'jail'
    key    TEXT,
    value  TEXT,
    PRIMARY KEY (world, key)
);
CREATE TABLE IF NOT EXISTS transfers (
    char_id   TEXT,                  -- normalized character name
    to_world  TEXT,                  -- destination world this event moves the char INTO ('jail'|'school')
    nday      INTEGER,               -- game day the transfer was COMMITTED (GetGameTimeData().nDays)
    gender    INTEGER,               -- 0 male / 1 female (for AddCard later)
    self_data TEXT,                  -- self-value snapshot at transfer time ("k=v;k=v")
    ts        TEXT,                  -- ISO timestamp (caller-supplied)
    PRIMARY KEY (char_id, nday, to_world)
);
CREATE TABLE IF NOT EXISTS char_rels (
    from_id  TEXT, to_id TEXT,       -- normalized names (directed: from -> to). to_id can be the PC.
    love INTEGER, liking INTEGER, disliking INTEGER, hate INTEGER,   -- relationship points (latest wins)
    ts TEXT,
    PRIMARY KEY (from_id, to_id)
);
CREATE TABLE IF NOT EXISTS char_activity (
    char_id  TEXT,                   -- normalized name (the actor)
    metric   TEXT,                   -- cumulative activity counter, e.g. 'climax','totalH','riskyCum'
    value    INTEGER,                -- engine's running total for this char (summed over partners; latest wins)
    ts       TEXT,
    PRIMARY KEY (char_id, metric)
);
CREATE TABLE IF NOT EXISTS char_race (
    char_id  TEXT PRIMARY KEY,       -- normalized name
    race     TEXT,                   -- this char's OWN race (e.g. 'Human','Demon'); sourced from the card's
    ts       TEXT                    -- Race-X module (read externally at the day boundary -- notes Backlog B1)
);
CREATE TABLE IF NOT EXISTS char_race_xp (
    char_id    TEXT,                 -- the experiencer (normalized name)
    other_race TEXT,                 -- the race the experience is ABOUT
    positive   INTEGER,              -- accumulated positive experience toward that race (loving H ...)
    negative   INTEGER,              -- accumulated negative experience (dominated/forced by that race ...)
    ts         TEXT,
    PRIMARY KEY (char_id, other_race)
);
CREATE TABLE IF NOT EXISTS char_state (
    char_id TEXT,                    -- normalized name
    module  TEXT,                    -- a module that should be ACTIVE for this char (resolver output)
    source  TEXT,                    -- which rule derived it ('sexual'|'race'|'social') -- transparency
    ts      TEXT,
    PRIMARY KEY (char_id, module)
);
CREATE TABLE IF NOT EXISTS char_confine (
    char_id TEXT PRIMARY KEY,         -- normalized name (SSOT identity, NOT seat -- a char's seat differs per world)
    cell    INTEGER,                  -- the room index this char is confined to (the jail cell)
    ts      TEXT                      -- the gated Confinement module reads this via Card Storage flags set by apply_state
);
"""

# Per-char JSON keys that are POSITION/popularity-bound, not part of the transferable "self".
# (Popularity* live at the JSON top level, not inside a char block, so they're excluded anyway;
# this set is for any position-y keys that might appear inside a char block.)
_NON_SELF_CHAR_KEYS = set()

# Top-level .json keys that are NOT character blocks.
_NON_CHAR_TOP_KEYS_RE = re.compile(r"^(Popularity\d+|PopularityPlace\d+|PopularitySeat\d+"
                                   r"|class_name|LastCardFileName)$")


def normalize_name(name):
    """Stable char_id from a display name: collapse internal whitespace, strip ends."""
    return re.sub(r"\s+", " ", name).strip()


def char_name_from_key(k):
    """'<seat> <name>' -> '<name>'. Leading token is the seat index (an int)."""
    parts = k.split(" ", 1)
    if len(parts) == 2 and parts[0].isdigit():
        return parts[1]
    return k


def is_char_key(k):
    return not _NON_CHAR_TOP_KEYS_RE.match(k) and bool(char_name_from_key(k))


# ----------------------------------------------------------------------------
# DB lifecycle
# ----------------------------------------------------------------------------
# mwa_id columns added to the name-keyed tables (the stable-identity re-key, dual-key transition: the
# name columns stay as a resolver index; these carry the rename-proof id that the reroute hook reads off
# the card). Self-healing: connect() adds any missing column so old and new DBs converge.
_MWA_COLS = {
    "chars":         ["mwa_id INTEGER"],
    "char_confine":  ["mwa_id INTEGER"],
    "char_activity": ["mwa_id INTEGER"],
    "char_state":    ["mwa_id INTEGER"],
    "transfers":     ["mwa_id INTEGER"],
    "char_race":     ["mwa_id INTEGER"],
    "char_race_xp":  ["mwa_id INTEGER"],
    "char_rels":     ["from_mwa INTEGER", "to_mwa INTEGER"],
    "relationships": ["from_mwa INTEGER", "to_mwa INTEGER"],
}

MWA_ID_BASE = 1000   # assigned ids start above this (1001+); keeps them clear of seats/small sentinels


def _migrate(con):
    """Idempotently add the mwa_id columns + the chars(mwa_id) unique index. No-op once applied."""
    for t, coldefs in _MWA_COLS.items():
        have = {r[1] for r in con.execute("PRAGMA table_info(%s)" % t)}
        for cd in coldefs:
            if cd.split()[0] not in have:
                con.execute("ALTER TABLE %s ADD COLUMN %s" % (t, cd))
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_chars_mwaid ON chars(mwa_id)")
    con.commit()


def connect(db_path):
    """Open (creating + initializing if needed) the playthrough DB. Returns a sqlite3.Connection."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.executescript(_SCHEMA)
    _migrate(con)
    cur = con.execute("SELECT value FROM meta WHERE key='schema_version'")
    row = cur.fetchone()
    if row is None:
        con.execute("INSERT INTO meta(key,value) VALUES('schema_version',?)", (str(SCHEMA_VERSION),))
        con.commit()
    return con


# ----------------------------------------------------------------------------
# stable identity: mwa_id  (the rename-proof key; name is now a mutable attribute)
# ----------------------------------------------------------------------------
def mwa_id_of(con, name):
    """The mwa_id for a (normalized) name, or None if the char is unknown / not yet assigned."""
    row = con.execute("SELECT mwa_id FROM chars WHERE char_id=?", (normalize_name(name),)).fetchone()
    return row["mwa_id"] if row and row["mwa_id"] is not None else None


def name_of(con, mwa_id):
    """The current (normalized) name for an mwa_id, or None. Name is mutable; the id is the identity."""
    row = con.execute("SELECT char_id FROM chars WHERE mwa_id=?", (int(mwa_id),)).fetchone()
    return row["char_id"] if row else None


def ensure_mwa_id(con, name, display=None):
    """Return the mwa_id for `name`, assigning a fresh one (and registering the char) if needed. This is
    the single place new ids are minted (max+1), so callers never invent ids. Rename-safe: the id sticks
    to the char even if the name later changes (update via rename_char)."""
    cid = normalize_name(name)
    mid = mwa_id_of(con, cid)
    if mid is not None:
        return mid
    nxt = con.execute("SELECT COALESCE(MAX(mwa_id), ?) AS m FROM chars", (MWA_ID_BASE,)).fetchone()["m"] + 1
    con.execute(
        "INSERT INTO chars(char_id,display_name,mwa_id) VALUES(?,?,?) "
        "ON CONFLICT(char_id) DO UPDATE SET mwa_id=excluded.mwa_id",
        (cid, display or cid, nxt))
    con.commit()
    return nxt


def rename_char(con, mwa_id, new_name, ts=None):
    """Rename a char (the mutable attribute) while keeping its stable mwa_id. Updates the chars row only;
    the name columns in keyed tables are a transitional index and resolve via mwa_id going forward."""
    con.execute("UPDATE chars SET char_id=?, display_name=?, updated=COALESCE(?,updated) WHERE mwa_id=?",
                (normalize_name(new_name), new_name, ts, int(mwa_id)))
    con.commit()


# ----------------------------------------------------------------------------
# chars
# ----------------------------------------------------------------------------
def upsert_char(con, char_id, display_name, self_data, last_world, ts):
    cid = normalize_name(char_id)
    mid = ensure_mwa_id(con, cid, display_name)   # mint/keep the stable id for this char
    con.execute(
        "INSERT INTO chars(char_id,display_name,self_data,last_world,updated,mwa_id) VALUES(?,?,?,?,?,?) "
        "ON CONFLICT(char_id) DO UPDATE SET display_name=excluded.display_name, "
        "self_data=excluded.self_data, last_world=excluded.last_world, updated=excluded.updated",
        (cid, display_name, json.dumps(self_data, ensure_ascii=False), last_world, ts, mid))


def get_char(con, char_id):
    row = con.execute("SELECT * FROM chars WHERE char_id=?", (char_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["self_data"] = json.loads(d["self_data"]) if d["self_data"] else {}
    return d


def list_chars(con):
    return [r["char_id"] for r in con.execute("SELECT char_id FROM chars ORDER BY char_id")]


# ----------------------------------------------------------------------------
# relationships  (table + API now; the in-game snapshot/inject wiring comes later)
# ----------------------------------------------------------------------------
def upsert_relationship(con, from_id, to_id, kind, value, ts):
    fmwa, tmwa = ensure_mwa_id(con, from_id), ensure_mwa_id(con, to_id)
    con.execute(
        "INSERT INTO relationships(from_id,to_id,kind,value,updated,from_mwa,to_mwa) VALUES(?,?,?,?,?,?,?) "
        "ON CONFLICT(from_id,to_id,kind) DO UPDATE SET value=excluded.value, updated=excluded.updated, "
        "from_mwa=excluded.from_mwa, to_mwa=excluded.to_mwa",
        (from_id, to_id, kind, value, ts, fmwa, tmwa))


def get_relationships(con, from_id):
    return [dict(r) for r in con.execute("SELECT * FROM relationships WHERE from_id=?", (from_id,))]


# ----------------------------------------------------------------------------
# transfers  (the SSOT journal -- model A: commit on save, derive on load, day-keyed)
# ----------------------------------------------------------------------------
def add_transfer(con, char_id, to_world, nday, gender, self_data, ts):
    """Record one committed transfer event. Idempotent on (char_id, nday, to_world)."""
    cid = normalize_name(char_id)
    mid = ensure_mwa_id(con, cid)
    con.execute(
        "INSERT OR IGNORE INTO transfers(char_id,to_world,nday,gender,self_data,ts,mwa_id) "
        "VALUES(?,?,?,?,?,?,?)",
        (cid, to_world, int(nday), int(gender), self_data, ts, mid))
    con.commit()


def ingest_transfer_commits(con, commits_path, ts):
    """Read a world's append-only commit log into the journal. Each non-comment line is
    '<nday>\\t<name>\\t<gender>\\t<self>' (self optional). Always destination 'jail' for now (the
    school dominance combo). Idempotent. Returns the number of NEW rows inserted."""
    if not os.path.exists(commits_path):
        return 0
    n = 0
    with open(commits_path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            try:
                nday, gender = int(parts[0].strip()), int(parts[2].strip())
            except ValueError:
                continue
            name = normalize_name(parts[1])
            self_data = parts[3] if len(parts) > 3 else ""
            cur = con.execute(
                "INSERT OR IGNORE INTO transfers(char_id,to_world,nday,gender,self_data,ts,mwa_id) "
                "VALUES(?,?,?,?,?,?,?)", (name, "jail", nday, gender, self_data, ts, ensure_mwa_id(con, name)))
            n += cur.rowcount
    con.commit()
    return n


def upsert_char_rel(con, from_id, to_id, love, liking, disliking, hate, ts):
    """Store one directed relationship (latest wins). char_id = normalized name; to can be the PC."""
    f, t = normalize_name(from_id), normalize_name(to_id)
    fmwa, tmwa = ensure_mwa_id(con, f), ensure_mwa_id(con, t)
    con.execute(
        "INSERT INTO char_rels(from_id,to_id,love,liking,disliking,hate,ts,from_mwa,to_mwa) "
        "VALUES(?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(from_id,to_id) DO UPDATE SET love=excluded.love, liking=excluded.liking, "
        "disliking=excluded.disliking, hate=excluded.hate, ts=excluded.ts, "
        "from_mwa=excluded.from_mwa, to_mwa=excluded.to_mwa",
        (f, t, int(love), int(liking), int(disliking), int(hate), ts, fmwa, tmwa))
    con.commit()


def ingest_rel_commits(con, path, ts):
    """Read a school-written relationship commit log into char_rels. Each non-comment line is
    '<nday>\\t<from>\\t<to>\\t<love>\\t<like>\\t<dislike>\\t<hate>'. Idempotent-ish (latest wins).
    Returns rows ingested."""
    if not os.path.exists(path):
        return 0
    n = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            p = line.split("\t")
            if len(p) < 7:
                continue
            try:
                upsert_char_rel(con, p[1], p[2], int(p[3]), int(p[4]), int(p[5]), int(p[6]), ts)
                n += 1
            except ValueError:
                continue
    return n


def char_rels_from(con, from_id):
    """All directed relationships originating at from_id. Each: {to_id, love, liking, disliking, hate}."""
    rows = con.execute("SELECT to_id,love,liking,disliking,hate FROM char_rels WHERE from_id=?",
                       (normalize_name(from_id),)).fetchall()
    return [dict(r) for r in rows]


def ingest_rel_snapshot(con, path, ts):
    """Ingest a FULL relationship-graph snapshot (continuous, school-side). Each non-comment line is
    '<from>\\t<to>\\t<love>\\t<like>\\t<dislike>\\t<hate>' (no day - it is the current state). Upserts
    into char_rels (latest wins). The snapshot only lists CURRENTLY present chars, so transferred chars'
    relationships are left untouched (they sleep). Returns rows ingested."""
    if not os.path.exists(path):
        return 0
    n = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            p = line.split("\t")
            if len(p) < 6:
                continue
            try:
                upsert_char_rel(con, p[0], p[1], int(p[2]), int(p[3]), int(p[4]), int(p[5]), ts)
                n += 1
            except ValueError:
                continue
    return n


def social_wealth(con, char_id, threshold=3):
    """Derive a char's social wealth from the SSOT graph: how many positive bonds (love+like > 0) it has.
    'high' if >= threshold else 'low'. Feeds the loneliness/loner module (notes 2.4c). Returns (label, n)."""
    bonds = sum(1 for r in char_rels_from(con, char_id) if (r["love"] + r["liking"]) > 0)
    return ("high" if bonds >= threshold else "low"), bonds


# ----------------------------------------------------------------------------
# char_activity  (the activity DB -- notes 4.7: cumulative per-char activity counters that the
# end-of-day resolve turns into states/modules, e.g. lots of H -> chaste->Sex Addict. The engine
# keeps these counters itself (m_characterStatus); activity_snapshot.lua snapshots them per char.)
# ----------------------------------------------------------------------------
def upsert_activity(con, char_id, metric, value, ts):
    """Store one cumulative activity counter for a char (latest wins). char_id = normalized name."""
    cid = normalize_name(char_id)
    mid = ensure_mwa_id(con, cid)
    con.execute(
        "INSERT INTO char_activity(char_id,metric,value,ts,mwa_id) VALUES(?,?,?,?,?) "
        "ON CONFLICT(char_id,metric) DO UPDATE SET value=excluded.value, ts=excluded.ts, mwa_id=excluded.mwa_id",
        (cid, metric, int(value), ts, mid))
    con.commit()


def ingest_activity_snapshot(con, path, ts):
    """Ingest a per-char activity snapshot (continuous, school-side). Each non-comment line is
    '<name>\\t<metric>\\t<value>' (the char's current cumulative engine counter). Upserts into
    char_activity (latest wins). Only CURRENTLY present chars are listed, so absent chars' counters
    sleep untouched (same contract as ingest_rel_snapshot). Returns rows ingested."""
    if not os.path.exists(path):
        return 0
    n = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            p = line.split("\t")
            if len(p) < 3:
                continue
            try:
                upsert_activity(con, p[0], p[1], int(p[2]), ts)
                n += 1
            except ValueError:
                continue
    return n


def activity_of(con, char_id):
    """All cumulative activity counters for a char as {metric: value}. Empty dict if none.
    The end-of-day resolve reads this to decide state/module transitions (notes 4.7)."""
    rows = con.execute("SELECT metric,value FROM char_activity WHERE char_id=?",
                       (normalize_name(char_id),)).fetchall()
    return {r["metric"]: r["value"] for r in rows}


# ----------------------------------------------------------------------------
# Race axis (notes Backlog B1): each char has an OWN race; experiences accumulate per OTHER race into
# char_race_xp; the end-of-day resolve derives a racial ATTITUDE (the Bias/Prejudice/Hostile ladder from
# EVOLUTION_MAP). char.race is sourced externally from the card's Race-X module (modules aren't Lua-readable
# at runtime) -- here we only store/derive. Domination (master_slave) -> negative XP toward the master's race.
# ----------------------------------------------------------------------------
def set_char_race(con, char_id, race, ts):
    """Record a char's own race (from its card's Race-X module). Latest wins."""
    cid = normalize_name(char_id)
    con.execute(
        "INSERT INTO char_race(char_id,race,ts,mwa_id) VALUES(?,?,?,?) "
        "ON CONFLICT(char_id) DO UPDATE SET race=excluded.race, ts=excluded.ts, mwa_id=excluded.mwa_id",
        (cid, race, ts, ensure_mwa_id(con, cid)))
    con.commit()


def get_char_race(con, char_id):
    """A char's own race, or None if unknown (not yet sourced from the card)."""
    row = con.execute("SELECT race FROM char_race WHERE char_id=?",
                      (normalize_name(char_id),)).fetchone()
    return row["race"] if row else None


def add_race_xp(con, char_id, other_race, d_positive, d_negative, ts):
    """Accumulate racial experience for a char toward `other_race` (deltas add to the running totals)."""
    cid = normalize_name(char_id)
    con.execute(
        "INSERT INTO char_race_xp(char_id,other_race,positive,negative,ts,mwa_id) VALUES(?,?,?,?,?,?) "
        "ON CONFLICT(char_id,other_race) DO UPDATE SET positive=positive+excluded.positive, "
        "negative=negative+excluded.negative, ts=excluded.ts, mwa_id=excluded.mwa_id",
        (cid, other_race, int(d_positive), int(d_negative), ts, ensure_mwa_id(con, cid)))
    con.commit()


def race_xp_of(con, char_id):
    """All racial experience for a char as {other_race: {'positive':p,'negative':n}}."""
    rows = con.execute("SELECT other_race,positive,negative FROM char_race_xp WHERE char_id=?",
                       (normalize_name(char_id),)).fetchall()
    return {r["other_race"]: {"positive": r["positive"], "negative": r["negative"]} for r in rows}


def accrue_domination(con, slave_id, master_id, ts, negative=1):
    """One domination event: the slave gains NEGATIVE racial XP toward the master's race -- but only if
    their races differ (you don't develop prejudice toward your own race) and both races are known.
    Reuses the existing enslavement signal; returns the master's race if XP was added, else None."""
    m_race = get_char_race(con, master_id)
    s_race = get_char_race(con, slave_id)
    if not m_race or not s_race or m_race == s_race:
        return None
    add_race_xp(con, slave_id, m_race, 0, negative, ts)
    return m_race


# Default thresholds for the attitude ladder (EVOLUTION_MAP 4.2). Tunable design constants.
RACE_THRESH = {"prejudice": 3, "hunter": 6, "natenemy": 10, "slayer": 15, "bias": 3, "obsession": 8}


def race_attitude(con, char_id, thresh=None):
    """Derive a char's racial attitude per other_race from accumulated XP -> the Bias/Prejudice/Hostile
    ladder (EVOLUTION_MAP). Negative wins over positive. Neutral races are omitted. Returns {race: label}
    where label in {bias, obsession, prejudice, hostile/hunter, hostile/natenemy, hostile/slayer}.
    This is what the end-of-day resolve reads to assign the racial modules."""
    t = thresh or RACE_THRESH
    out = {}
    for race, xp in race_xp_of(con, char_id).items():
        neg, pos = xp["negative"], xp["positive"]
        if   neg >= t["slayer"]:    out[race] = "hostile/slayer"
        elif neg >= t["natenemy"]:  out[race] = "hostile/natenemy"
        elif neg >= t["hunter"]:    out[race] = "hostile/hunter"
        elif neg >= t["prejudice"]: out[race] = "prejudice"
        elif pos >= t["obsession"]: out[race] = "obsession"
        elif pos >= t["bias"]:      out[race] = "bias"
        # else: neutral -> omitted
    return out


# ----------------------------------------------------------------------------
# char_state  (the RESOLVER output: which modules should be ACTIVE for each char, derived from the DBs
# per EVOLUTION_MAP. The global apply-mod reads this at runtime and activates them -- the card is never
# written. Authored by resolver.py; stored here. Replace-per-char so it always reflects the latest resolve.)
# ----------------------------------------------------------------------------
def replace_char_state(con, char_id, items, ts):
    """Set a char's full active-module state. items = iterable of (module, source). Replaces any prior
    state for this char (so removed/downgraded modules disappear). Idempotent for the same input."""
    cid = normalize_name(char_id)
    mid = ensure_mwa_id(con, cid)
    con.execute("DELETE FROM char_state WHERE char_id=?", (cid,))
    con.executemany("INSERT OR REPLACE INTO char_state(char_id,module,source,ts,mwa_id) VALUES(?,?,?,?,?)",
                    [(cid, mod, src, ts, mid) for mod, src in items])
    con.commit()


def char_state_of(con, char_id):
    """The active modules for a char as a sorted list of names (what the apply-mod activates)."""
    rows = con.execute("SELECT module FROM char_state WHERE char_id=? ORDER BY module",
                       (normalize_name(char_id),)).fetchall()
    return [r["module"] for r in rows]


def set_confine(con, char_id, cell, ts):
    """Confine a char to room `cell` (identity-keyed, NOT seat). Carries the stable mwa_id so the reroute
    hook can match the char by the id embedded on its card. Lives in the ONE per-playthrough memory.db."""
    cid = normalize_name(char_id)
    mid = ensure_mwa_id(con, cid)
    con.execute(
        "INSERT INTO char_confine(char_id,cell,ts,mwa_id) VALUES(?,?,?,?) "
        "ON CONFLICT(char_id) DO UPDATE SET cell=excluded.cell, ts=excluded.ts, mwa_id=excluded.mwa_id",
        (cid, int(cell), ts, mid))
    con.commit()


def clear_confine(con, char_id):
    con.execute("DELETE FROM char_confine WHERE char_id=?", (normalize_name(char_id),))
    con.commit()


def all_confined(con):
    """{char_id: cell} for every confined char. The resolver emits Card-Storage flags for these."""
    return {r["char_id"]: r["cell"] for r in con.execute("SELECT char_id,cell FROM char_confine")}


def confined_mwa(con):
    """{mwa_id: cell} for every confined char (id-keyed). This is what the reroute flag is built from --
    the hook reads each card's mwa_id and looks up its confinement here. Skips rows without an id."""
    return {r["mwa_id"]: r["cell"] for r in
            con.execute("SELECT mwa_id,cell FROM char_confine WHERE mwa_id IS NOT NULL")}


def confine_of(con, char_id):
    """The cell room a char is confined to, or None."""
    row = con.execute("SELECT cell FROM char_confine WHERE char_id=?",
                      (normalize_name(char_id),)).fetchone()
    return row["cell"] if row else None


def all_char_ids_with_data(con):
    """Every char that has ANY tracked data (activity / race-xp / relationships / self). The resolver
    iterates these. Returns a sorted list of normalized names."""
    ids = set()
    for tbl, col in (("char_activity", "char_id"), ("char_race_xp", "char_id"),
                     ("char_rels", "from_id"), ("chars", "char_id")):
        for r in con.execute("SELECT DISTINCT %s AS c FROM %s" % (col, tbl)):
            if r["c"]:
                ids.add(r["c"])
    return sorted(ids)


def residents_as_of(con, nday, world="jail"):
    """Who is in `world` as of game-day `nday`: for each char, the latest transfer event with
    nday<=given decides their world (last-write-wins). Returns a list of dicts. This is the 'derive
    on load' read -- loading an OLD school save (smaller nday) rolls the roster back automatically."""
    rows = con.execute(
        "SELECT t.char_id, t.gender, t.self_data, t.to_world, t.nday FROM transfers t "
        "JOIN (SELECT char_id, MAX(nday) AS m FROM transfers WHERE nday<=? GROUP BY char_id) x "
        "ON t.char_id=x.char_id AND t.nday=x.m", (int(nday),)).fetchall()
    return [{"char_id": r["char_id"], "gender": r["gender"], "self_data": r["self_data"],
             "nday": r["nday"]} for r in rows if r["to_world"] == world]


# ----------------------------------------------------------------------------
# world_state
# ----------------------------------------------------------------------------
def set_world_state(con, world, key, value):
    con.execute(
        "INSERT INTO world_state(world,key,value) VALUES(?,?,?) "
        "ON CONFLICT(world,key) DO UPDATE SET value=excluded.value", (world, key, str(value)))


def get_world_state(con, world, key, default=None):
    row = con.execute("SELECT value FROM world_state WHERE world=? AND key=?", (world, key)).fetchone()
    return row["value"] if row else default


# ----------------------------------------------------------------------------
# .json  <->  DB  (chars / self values)
# ----------------------------------------------------------------------------
def _merge_char_entries(entries):
    """Several '<seat> <name>' blocks can exist for one name (history). Keep the richest one
    (most fields) as the 'current' self. (Roster-exact attribution wants the live roster - TODO.)"""
    return max(entries, key=lambda e: len(e))


def snapshot_chars_from_json(con, world, json_path, ts):
    """Read a save's .json, extract per-character self values, upsert into chars. Returns count."""
    with open(json_path, encoding="utf-8") as f:
        d = json.load(f)
    by_name = {}
    for k, v in d.items():
        if not isinstance(v, dict) or not is_char_key(k):
            continue
        name = normalize_name(char_name_from_key(k))
        by_name.setdefault(name, []).append(v)
    n = 0
    for name, entries in by_name.items():
        self_data = {kk: vv for kk, vv in _merge_char_entries(entries).items()
                     if kk not in _NON_SELF_CHAR_KEYS}
        upsert_char(con, name, name, self_data, world, ts)
        n += 1
    con.commit()
    return n


def inject_chars_to_json(con, json_path, ts, only_names=None):
    """Write stored self values back into a save's .json for chars that are present in it. Updates
    every '<seat> <name>' block whose name is in the DB (or in only_names). Returns count of blocks
    touched. NOTE: writes to ALL of a name's entries - roster-exact targeting is a later refinement.
    Always writes atomically (tmp + os.replace) so a crash can't corrupt the save."""
    with open(json_path, encoding="utf-8") as f:
        d = json.load(f)
    touched = 0
    for k, v in list(d.items()):
        if not isinstance(v, dict) or not is_char_key(k):
            continue
        name = normalize_name(char_name_from_key(k))
        if only_names is not None and name not in only_names:
            continue
        stored = get_char(con, name)
        if not stored:
            continue
        # merge stored self values into the existing block (don't drop keys the game added)
        v.update(stored["self_data"])
        touched += 1
    tmp = json_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    os.replace(tmp, json_path)
    return touched


# ----------------------------------------------------------------------------
# CLI (dev / inspection)
# ----------------------------------------------------------------------------
def _main(argv):
    if len(argv) < 3:
        print("usage: playthrough_db.py <db_path> <snapshot|inject|dump> [world] [json_path]")
        return 2
    db_path, cmd = argv[1], argv[2]
    con = connect(db_path)
    if cmd == "snapshot":
        world, jp = argv[3], argv[4]
        n = snapshot_chars_from_json(con, world, jp, ts="cli")
        print(f"snapshot: {n} chars from {jp}")
    elif cmd == "inject":
        jp = argv[4] if len(argv) > 4 else argv[3]
        n = inject_chars_to_json(con, jp, ts="cli")
        print(f"inject: {n} char blocks written to {jp}")
    elif cmd == "dump":
        for cid in list_chars(con):
            c = get_char(con, cid)
            print(f"  {cid}: {len(c['self_data'])} fields  (last_world={c['last_world']})")
    else:
        print(f"unknown command: {cmd}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
