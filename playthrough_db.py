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
def connect(db_path):
    """Open (creating + initializing if needed) the playthrough DB. Returns a sqlite3.Connection."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.executescript(_SCHEMA)
    cur = con.execute("SELECT value FROM meta WHERE key='schema_version'")
    row = cur.fetchone()
    if row is None:
        con.execute("INSERT INTO meta(key,value) VALUES('schema_version',?)", (str(SCHEMA_VERSION),))
        con.commit()
    return con


# ----------------------------------------------------------------------------
# chars
# ----------------------------------------------------------------------------
def upsert_char(con, char_id, display_name, self_data, last_world, ts):
    con.execute(
        "INSERT INTO chars(char_id,display_name,self_data,last_world,updated) VALUES(?,?,?,?,?) "
        "ON CONFLICT(char_id) DO UPDATE SET display_name=excluded.display_name, "
        "self_data=excluded.self_data, last_world=excluded.last_world, updated=excluded.updated",
        (char_id, display_name, json.dumps(self_data, ensure_ascii=False), last_world, ts))


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
    con.execute(
        "INSERT INTO relationships(from_id,to_id,kind,value,updated) VALUES(?,?,?,?,?) "
        "ON CONFLICT(from_id,to_id,kind) DO UPDATE SET value=excluded.value, updated=excluded.updated",
        (from_id, to_id, kind, value, ts))


def get_relationships(con, from_id):
    return [dict(r) for r in con.execute("SELECT * FROM relationships WHERE from_id=?", (from_id,))]


# ----------------------------------------------------------------------------
# transfers  (the SSOT journal -- model A: commit on save, derive on load, day-keyed)
# ----------------------------------------------------------------------------
def add_transfer(con, char_id, to_world, nday, gender, self_data, ts):
    """Record one committed transfer event. Idempotent on (char_id, nday, to_world)."""
    con.execute(
        "INSERT OR IGNORE INTO transfers(char_id,to_world,nday,gender,self_data,ts) VALUES(?,?,?,?,?,?)",
        (normalize_name(char_id), to_world, int(nday), int(gender), self_data, ts))
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
                "INSERT OR IGNORE INTO transfers(char_id,to_world,nday,gender,self_data,ts) "
                "VALUES(?,?,?,?,?,?)", (name, "jail", nday, gender, self_data, ts))
            n += cur.rowcount
    con.commit()
    return n


def upsert_char_rel(con, from_id, to_id, love, liking, disliking, hate, ts):
    """Store one directed relationship (latest wins). char_id = normalized name; to can be the PC."""
    con.execute(
        "INSERT INTO char_rels(from_id,to_id,love,liking,disliking,hate,ts) VALUES(?,?,?,?,?,?,?) "
        "ON CONFLICT(from_id,to_id) DO UPDATE SET love=excluded.love, liking=excluded.liking, "
        "disliking=excluded.disliking, hate=excluded.hate, ts=excluded.ts",
        (normalize_name(from_id), normalize_name(to_id), int(love), int(liking),
         int(disliking), int(hate), ts))
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
