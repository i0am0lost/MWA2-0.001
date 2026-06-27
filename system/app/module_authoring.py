#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
module_authoring.py - build AAU trigger modules from code, on top of module_format.py.
========================================================================================
ID catalog + builder helpers, all ids extracted & verified from AAU source
(Event.cpp / Actions.cpp / Expressions.cpp) and cross-checked against decoded real modules.

How ids are stored in the file (verified):
  * EVENT id  = the Events-enum value (1-based registration order). FromId(id)->g_Events[id-1].
  * ACTION id = 1-based position in g_Actions.               FromId(id)->g_Actions[id-1].
  * EXPRESSION id = 1-based index WITHIN its return-type list. FromId(type,id)->g_Expressions[type][id-1].
       Every type's list begins with CONSTANT(1), VAR(2), NAMEDCONSTANT(3); real exprs from id 4 up.

Run:  python module_authoring.py            # generates Confinement, writes it, verifies roundtrip
"""

import os
import sys
import module_format as mf
from module_format import T_INT, T_BOOL, T_FLOAT, T_STRING

# --------------------------------------------------------------------------- ID CATALOG (verified)
# Events (stored id == enum value)
EV_CLOTHES_CHANGED = 1
EV_CARD_ADDED = 6              # "Card Added to Class" (used as "Init")
EV_ROOM_CHANGE = 16            # "Card Changes Room"
EV_KEY_PRESS = 17
EV_DELAYED_EXECUTION = 27

# Actions (stored id == 1-based position in g_Actions)
AC_SETVAR = 1
AC_IF = 2
AC_ELSEIF = 3
AC_ELSE = 4
AC_NPC_MOVE_ROOM = 20          # "Make Npc Move to Room"  (seat:int, room:int)
AC_SET_CARDSTORAGE_INT = 24    # (seat:int, key:str, val:int)
AC_SET_CARDSTORAGE_STR = 26    # (seat:int, key:str, val:str)
AC_SET_CARDSTORAGE_BOOL = 27   # (seat:int, key:str, val:bool)
AC_SET_VIRTUE = 32             # (seat:int, val:int)

# Expressions (stored id == 1-based index within the return-type's list)
#   INT-returning
EX_INT_TRIGGERING_CARD = 9     # ()            GetTriggeringCard
EX_INT_THIS_CARD = 10          # ()            GetThisCard
EX_INT_GET_CARDSTORAGE_INT = 24  # (seat:int, key:str, default:int)  Get Card Storage Int
EX_INT_PC = 55                 # ()            GetPC  (Player Character, -1 if none)
EX_INT_CURRENT_ROOM = 97       # (seat:int)    GetNpcCurrentRoom
#   BOOL-returning
EX_BOOL_AND = 4                # (bool,bool)   Logical And
EX_BOOL_OR = 5                 # (bool,bool)   Logical Or
EX_BOOL_GT = 6                 # (int,int)     Greater Than
EX_BOOL_EQ = 8                 # (int,int)     Equal
EX_BOOL_NOT = 11               # (bool)        Not
EX_BOOL_STR_EQ = 12            # (str,str)     String Equal
EX_BOOL_NEQ = 13               # (int,int)     Not Equal
EX_BOOL_GET_CARDSTORAGE_BOOL = 24  # (seat:int, key:str, default:bool)


# --------------------------------------------------------------------------- expression/action builders
def const(t, v):
    """A literal constant of type t (CONSTANT = per-type id 1)."""
    return {"type": t, "id": mf.EXPR_CONSTANT, "constant": {"type": t, "val": v}}


def var(t, name):
    """A variable reference of type t (VAR = per-type id 2)."""
    return {"type": t, "id": mf.EXPR_VAR, "varName": name}


def expr(t, eid, *params):
    """A function expression: return type t, per-type id eid, with parameter expressions."""
    return {"type": t, "id": eid, "params": list(params)}


# convenience expression shorthands
def this_card():       return expr(T_INT, EX_INT_THIS_CARD)
def triggering_card(): return expr(T_INT, EX_INT_TRIGGERING_CARD)
def pc():              return expr(T_INT, EX_INT_PC)
def current_room(seat): return expr(T_INT, EX_INT_CURRENT_ROOM, seat)
def eq(a, b):          return expr(T_BOOL, EX_BOOL_EQ, a, b)
def neq(a, b):         return expr(T_BOOL, EX_BOOL_NEQ, a, b)
def land(a, b):        return expr(T_BOOL, EX_BOOL_AND, a, b)


def action(aid, *params):
    return {"id": aid, "params": list(params)}


def gui(act, subs=None):
    return {"action": act, "subactions": subs or []}


def event(eid, *params):
    return {"id": eid, "params": list(params)}


def trigger(name, events, guiActions, varz=None):
    return {"name": name, "events": list(events), "vars": varz or [], "guiActions": list(guiActions)}


def module(name, description, triggers, globals_=None, deps=None):
    return {"name": name, "description": description, "triggers": list(triggers),
            "globals": globals_ or [], "dependencies": deps or []}


# --------------------------------------------------------------------------- Confinement (STAGE 1 / MVP)
def build_confinement(cell=39):
    """CONFINEMENT_MODULE_SPEC.md Stage 1:
       EVENT Room Change; IF ThisCard==TriggeringCard AND ThisCard!=PC AND CurrentRoom(ThisCard)!=cell
       THEN MoveNpcToRoom(ThisCard, cell)."""
    cond = land(
        land(
            eq(this_card(), triggering_card()),    # only react when I moved
            neq(this_card(), pc()),                # never the player
        ),
        neq(current_room(this_card()), const(T_INT, cell)),   # I'm outside the cell
    )
    move_back = gui(action(AC_NPC_MOVE_ROOM, this_card(), const(T_INT, cell)))
    if_block = gui(action(AC_IF, cond), subs=[move_back])
    confine = trigger("Confine", [event(EV_ROOM_CHANGE)], [if_block])
    # Every real module has an Init trigger (Event 6 = Card Added to Class) -- the per-card setup that runs
    # on load. Ours had none, which likely kept the module from activating. Minimal Init: fire on add, guard
    # to this card (matches the real-module shape), no side effect needed for the flagless confinement.
    init = trigger("Init", [event(EV_CARD_ADDED)],
                   [gui(action(AC_IF, eq(this_card(), triggering_card())), subs=[])])
    return module("Confinement",
                  "Keeps this NPC confined to room %d (jail cell): sends them back if they leave." % cell,
                  [init, confine])


# --------------------------------------------------------------------------- Confinement (STAGE 2: flag-gated, SSOT-driven)
def cardstorage_bool(seat, key, default=False):
    """Get Card Storage Bool(seat, key, default) -> the per-char flag our SSOT sets via setCardStorage."""
    return expr(T_BOOL, EX_BOOL_GET_CARDSTORAGE_BOOL, seat, const(T_STRING, key), const(T_BOOL, default))


def cardstorage_int(seat, key, default=-1):
    """Get Card Storage Int(seat, key, default) -> the per-char cell room our SSOT sets."""
    return expr(T_INT, EX_INT_GET_CARDSTORAGE_INT, seat, const(T_STRING, key), const(T_INT, default))


def build_confinement_gated(key_on="confined", key_cell="cell"):
    """Stage 2 (the real one): NO hard-coded room, NO 'all NPCs'. The module is always loaded but does
    NOTHING until our SSOT sets the per-char Card-Storage flags (key_on=bool, key_cell=int). Then:
       EVENT Room Change; IF ThisCard==TriggeringCard AND CardStorage[on]==true
            AND CurrentRoom(ThisCard) != CardStorage[cell]
       THEN MoveNpcToRoom(ThisCard, CardStorage[cell]).
    apply_state writes the flags from the resolver -> behaviour is SSOT-driven exactly like virtue."""
    this = this_card()
    cell = cardstorage_int(this_card(), key_cell)            # the cell room comes from the flag, not a constant
    cond = land(
        land(
            eq(this, triggering_card()),                     # only react when I moved
            cardstorage_bool(this_card(), key_on),           # only if our SSOT marked me confined
        ),
        neq(current_room(this_card()), cell),                # I'm outside my cell
    )
    move_back = gui(action(AC_NPC_MOVE_ROOM, this_card(), cardstorage_int(this_card(), key_cell)))
    if_block = gui(action(AC_IF, cond), subs=[move_back])
    trig = trigger("Confine", [event(EV_ROOM_CHANGE)], [if_block])
    return module("Confinement",
                  "SSOT-gated jail confinement: inert until Card Storage '%s'=true; sends the NPC back to "
                  "Card Storage '%s'. No effect on unflagged chars." % (key_on, key_cell),
                  [trig])


def main(argv):
    m = build_confinement_gated()
    data = mf.encode(m)

    # verify our own output round-trips through the decoder cleanly
    back = mf.decode(data)
    assert mf.encode(back) == data, "self-roundtrip failed"
    assert back == m, "decode(encode(m)) != m"
    print("Confinement (flag-gated) built: %d bytes  (self-roundtrip OK)" % len(data))

    # write into BOTH worlds' module dirs. Additive, non-destructive.
    from _root import ROOT as base   # project root (holds school/ + jail/)
    targets = [
        os.path.join(base, "school", "data", "override", "module", "Confinement"),
        os.path.join(base, "jail", "data", "override", "module", "Confinement"),
    ]
    for t in targets:
        os.makedirs(os.path.dirname(t), exist_ok=True)
        with open(t, "wb") as f:
            f.write(data)
        print("  wrote %s" % t)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
