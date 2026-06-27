# AAU Trigger-Modul — ID-Katalog (Events / Actions / Expressions)

> Extrahiert & verifiziert aus AAU-Quelle (`Event.cpp` / `Actions.cpp` / `Expressions.cpp`) und gegen echte
> dekodierte Module gegengeprüft (z.B. Race-Human: STRING id7="Get Card Storage String", id8="+", BOOL id8="Equal",
> INT id9="Triggering Card", id10="This Card" — alle stimmen). Format-Codec: `module_format.py`. Builder: `module_authoring.py`.

## Wie IDs in der Datei gespeichert werden
- **Event-ID** = Enum-Wert / 1-basierte Registrierungsreihenfolge. `Event::FromId(id) → g_Events[id-1]`.
- **Action-ID** = 1-basierte Position in `g_Actions`. `Action::FromId(id) → g_Actions[id-1]`.
- **Expression-ID** = 1-basierter Index **innerhalb der Rückgabe-Typ-Liste**. `Expression::FromId(type,id) → g_Expressions[type][id-1]`.
  - **Jede** Typ-Liste beginnt mit `1=Constant`, `2=Variable`, `3=Enumeration`; echte Funktionen ab id 4.
  - In `ParameterisedExpression`: id 1/2/3 sind Sonderfälle (Constant→Value, Var→wstr, NamedConstant→int);
    alles andere → `vec<ParameterisedExpression>` Parameter.

---

## EVENTS  (gespeicherte id = Enum-Wert)
| id | Name |
|---:|---|
| 1 | Clothes Changed |
| 2 | Card Initialized |
| 3 | Card Destroyed |
| 4 | Hi Poly Model Initialized |
| 5 | Hi Poly Model Loaded |
| 6 | Card Added to Class *(„Init")* |
| 7 | A Period Ends |
| 8 | Npc Answers in a Conversation |
| 9 | Npc Starts Walking to a Room |
| 10 | Npc Wants to do something with no Target |
| 11 | Npc Wants to Talk With Someone |
| 12 | Npc Wants to Talk With Someone About Someone |
| 13 | PC conversation state updated |
| 14 | Pc Answers in a Conversation |
| 15 | PC conversation line updated |
| **16** | **Card Changes Room** ← Confinement |
| 17 | Key Press |
| 18 | H Position Change |
| 19 | After PC Response |
| 20 | After NPC Response |
| 21 | HI Poly Despawn |
| 22 | H Ends |
| 23 | H Starts |
| 24 | Card Expelled |
| 25 | Conversation End |
| 26 | Relationship Points Changed |
| 27 | Delayed Execution |

Alle Events haben **keine** Parameter (`{}`).

---

## ACTIONS  (gespeicherte id = 1-basierte Position; Params = Argument-Typen)
| id | Name | Params |
|---:|---|---|
| 1 | Set Variable | (INVALID, INVALID) |
| 2 | **If** | (BOOL) |
| 3 | Else If | (BOOL) |
| 4 | Else | () |
| 5 | Conditional Jump | (INT, BOOL) |
| 6 | Loop | () |
| 7 | Break If | (BOOL) |
| 8 | Continue If | (BOOL) |
| 9 | For Loop | (INVALID, INT, INT) |
| 10 | Switch Style | (INT, INT) |
| 11 | End Execution | () |
| 12 | Add Love Points | (INT, INT, INT) |
| 13 | Add Like Points | (INT, INT, INT) |
| 14 | Add Dislike Points | (INT, INT, INT) |
| 15 | Add Hate Points | (INT, INT, INT) |
| 16 | Add Points | (INT, INT, INT, INT) |
| 17 | Conditional End Execution | (BOOL) |
| 18 | Set Npc Normal Response Success | (BOOL) |
| 19 | Set Npc Normal Response Percent | (INT) |
| **20** | **Make Npc Move to Room** | (INT seat, INT room) ← Confinement |
| 21 | Make Npc do Action with no Target | (INT, INT) |
| 22 | Make Npc Talk to Character | (INT, INT, INT) |
| 23 | Make Npc Talk to Character about someone | (INT, INT, INT, INT) |
| 24 | Set Card Storage Integer | (INT, STRING, INT) |
| 25 | Set Card Storage Float | (INT, STRING, FLOAT) |
| 26 | Set Card Storage String | (INT, STRING, STRING) |
| 27 | Set Card Storage Bool | (INT, STRING, BOOL) |
| 28–31 | Remove Card Storage Integer/Float/String/Bool | (INT, STRING) |
| 32 | Set Virtue | (INT, INT) |
| 33 | Set Trait | (INT, INT, BOOL) |
| 34 | Set Personality | (INT, INT) |
| 35 | Set Voice Pitch | (INT, INT) |
| 36–38 | Set Club / Club Value / Club Rank | (INT, INT) |
| 39–41 | Set Intelligence / Value / Rank | (INT, INT) |
| 42–44 | Set Strength / Value / Rank | (INT, INT) |
| 45 | Set Sociability | (INT, INT) |
| 46 | Set First Name | (INT, STRING) |
| 47 | Set Last Name | (INT, STRING) |
| 48 | Set Sex Orientation | (INT, INT) |
| 49 | Set Description | (INT, STRING) |
| 50 | Change Player Character | (INT) |
| 51 | Start H scene | (INT, INT) |
| 52–53 | Set Sex Experience Vaginal/Anal | (INT, BOOL) |
| 54 | Add Mood | (INT, INT, INT) |
| 55 | Replace Mood | (INT, INT, INT, INT) |
| 56–58 | Set Item Lover's/Friend's/Sexual | (INT, STRING) |
| 59 | Set H Compatibility | (INT, INT, INT) |
| 60 | Set NPC status | (INT, INT) |
| 61 | Voyeur Clean Up | () |
| 62 | Set Points | (INT, INT, 5×FLOAT) |
| 63 | Write Log | (STRING) |
| 64–65 | Cum Stat Vaginal/Anal | (INT, INT, INT) |

> Card-Storage-Actions (24–27) + Get-Expressions (s.u.) sind die **SSOT-Brücke** für Confinement Stufe 2 und alle
> Status-Module: Orchestrator/Lua schreibt `setCardStorage`, das Modul liest es per „Get Card Storage …".

---

## EXPRESSIONS  (id = 1-basierter Index **pro Rückgabe-Typ**; jede Liste: 1=Constant 2=Variable 3=Enumeration)

### → INT
4 Random Int(I,I) · 5 +(I,I) · 6 −(I,I) · 7 /(I,I) · 8 *(I,I) · **9 Triggering Card()** · **10 This Card()** ·
11 Npc Answer-Target() · 12 Npc Answer-ConvID() · 13 Npc Room Target() · 14 Npc Action() · 15 Npc Talk Target() ·
16 Npc Talk About() · 17 Period-Starting() · 18 Period-Ending() · 19 Love Points(I,I) · 20 Like Points(I,I) ·
22 Hate Points(I,I) · 23 Float→Int(F) · 24 Get Card Storage Int(I,S,I) · 25 Virtue(I) · 26 Personality(I) ·
27 Voice Pitch(I) · 28 Club(I) · 29 Club Value(I) · 30 Club Rank(I) · 31 Intelligence(I) · 32 Int. Value(I) ·
33 Int. Rank(I) · 34 Strength(I) · 35 Str. Value(I) · 36 Str. Rank(I) · 37 Sociability(I) · 38 Partner Count(I) ·
41 Sex Orientation(I) · 42 String Length(S) · 43 First Index Of(S,S) · 44 String→Int(S) · 46 Gender(I) ·
47 Days Passed() · 48 Current Day() · 49 Current Period() · 51 Current Style(I) · 52 State() · 53 Actor(I) ·
**55 Player Character()** · 56 Find Seat(S) · 64 Find Style(I,S) · 68 Get NPC Status(I) · **97 Current Room(I)** ·
103 Get Target(I) · 106 Get Height(I) · 111 Get Figure(I) · 113 Get Breast Size(I) · 121 Get Class Storage Int(S,I) ·
124 Real Virtue(I) · 145 Club Type(I) … *(voll: `_expr_catalog.json` / Quelle)*

### → BOOL
**4 Logical And(B,B)** · 5 Logical Or(B,B) · 6 Greater Than(I,I) · 7 ≥(I,I) · **8 Equal(I,I)** · 9 ≤(I,I) ·
10 Less Than(I,I) · 11 Not(B) · 12 String-Equal(S,S) · **13 Not Equal(I,I)** · 16 Is Seat Filled(I) · 17 Is Lover(I,I) ·
18–23 Float-Vergleiche(F,F) · 24 Get Card Storage Bool(I,S,B) · 25 Trait(I,I) · 35/36 Sex Exp Vaginal/Anal(I) ·
37 Has Lovers(I) · 46 Get Class Storage Bool(S,B) · 49 Has Date With(I,I)

### → FLOAT
4 Random Float(F,F) · 5 +(F,F) · 6 −(F,F) · 7 /(F,F) · 8 *(F,F) · 9 Int→Float(I) · 10 Get Card Storage Float(I,S,F) ·
11 String→Float(S) · 13 Get Class Storage Float(S,F)

### → STRING
4 Substring(S,I,I) · 5 Last Name(I) · 6 First Name(I) · **7 Get Card Storage String(I,S,S)** · **8 +(S,S)** ·
9 Int→String(I) · 10 Float→String(F) · 11 Bool→String(B) · 12 Description(I) · 20 Full Name(I) ·
22 Get Class Storage String(S,S)

> Vollständige Tabellen (alle Typen, alle ids inkl. Lücken) jederzeit reproduzierbar aus AAU `Expressions.cpp`
> mit dem Parser-Ansatz in `module_authoring.py`-Begleitskript. Hier sind die für Status-/Evolutions-Module
> relevanten fett markiert.
