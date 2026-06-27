# HANDOVER — AAU-Modul-Binärformat reverse-engineeren (Stand 2026-06-26)

> ## ✅ SOLVED (2026-06-26, RE-Session) — Format vollständig geknackt
> Der Serializer wurde gefunden: **`AAUnlimited/Functions/Serialize.h`** (generische `ReadData<T>`/`WriteData<T>`,
> alle Spezialisierungen *inline* im Header, kein Serialize.cpp). Damit ist das gesamte Format exakt bekannt und in
> **`module_format.py`** als vollständiger **Codec (decode + encode)** implementiert.
> **Verifikation:** 466/466 Module × 2 Welten = **932 Dateien**, alle CLEAN PARSE + **byte-exakter Roundtrip**
> (`encode(decode(x)) == x`). Batch-Test: `_batch_test.py`.
>
> **Wichtigste Korrekturen ggü. den Vermutungen unten:**
> - **Pointer ≠ id.** `ReadData_sub(T**)` = `new T(ReadData<T>(...))` → Objekte werden **inline** serialisiert,
>   nicht als id. ABER die Trigger-Structs haben *eigene* Serializer (s.u.), die das anders lösen.
> - **`ParameterisedExpression` ist id-abhängig verzweigt** (das war der Bruch @offset 88): liest `type:u32, id:u32`,
>   dann GENAU EINES: id==1(CONSTANT)→`Value` · id==2(VAR)→`wstr` · id==3(NAMEDCONSTANT)→`int` · sonst→`vec<PExpr>`.
> - **`bool` = 1 Byte** (`sizeof(bool)`), nicht 4.
> - **Variable/GlobalVariable haben KEIN serialisiertes `id`** (struct-Feld, aber nicht in der Datei).
> - **Trigger serialisiert NUR** `name, events, vars, guiActions` — *nicht* `actions/owningCard/broken/bInitialized`
>   (actions werden zur Laufzeit aus guiActions gebaut). → guiActions-Baum ist der gespeicherte, actions ist leer.
> - **`Types`**: INVALID=0, INT=1, BOOL=2, FLOAT=3, STRING=4. **`Value`** = `type:u32` + payload nach type.
> - **GlobalVariable** = `type, name, defaultValue:Value, currentValue:Value, initialized:bool`.
> - **wstr** = `[u32 #chars][chars × UTF-16LE]`, **vec** = `[u32 count][…]`. (wie vermutet, bestätigt.)
>
> Die exakten Feld-Reihenfolgen stehen als Docstring in `module_format.py`.
>
> **✅ ID-KATALOG FERTIG:** `MODULE_ID_CATALOG.md` — alle Events (27), Actions (65), Expressions (pro Typ, voll)
> mit IDs↔Namen↔Param-Typen, aus `Event.cpp`/`Actions.cpp`/`Expressions.cpp` extrahiert und gegen echte Module
> gegengeprüft. Roh-Daten: `_expr_catalog.json`. Speicher-Konvention: Event-id=Enum-Wert · Action-id=1-basierte
> Position · Expression-id=1-basierter Index **pro Rückgabe-Typ** (jede Typ-Liste startet 1=Const/2=Var/3=Enum).
>
> **✅ CONFINEMENT GENERIERT:** `module_authoring.py` (Builder-Lib auf module_format) erzeugt das Confinement-Modul
> exakt nach §6/`CONFINEMENT_MODULE_SPEC.md`: Event 16 (Room Change) → If(ThisCard==TriggeringCard ∧ ThisCard≠PC
> ∧ CurrentRoom(ThisCard)≠39) → MoveNpcToRoom(ThisCard,39). Liegt als `Confinement` (Repo-Root + `school/data/
> override/module/`), 436 B, decodiert sauber + roundtrippt byte-genau.
> **Bausteine (verifiziert):** Event 16 · Action 20 (Make Npc Move to Room) · INT 9/10/55/97 (Triggering/This/PC/
> CurrentRoom) · BOOL 4/8/13 (And/Equal/NotEqual).
>
> **NÄCHSTE PHASE (offen — zurück in Haupt-Session):**
> 1. **In-Game-Test** Confinement: Modul via **AA2QtEdit** an Test-NPC hängen → NPC aus Zelle laufen lassen →
>    kehrt er zurück? Zell-Raum 39 ggf. via `jail/_orch_probe.flag` verifizieren/korrigieren (`build_confinement(cell)`).
> 2. **Confinement Stufe 2** (SSOT): Card-Storage lesen (Get Card Storage Bool/Int = BOOL24 / INT24) statt fester 39.
> 3. **Status-/Evolutions-Module** generieren (Set Virtue=Action32, Set Card Storage = 24–27) — jetzt trivial.
>
> ---
> *(Original-Handover unten — historischer Kontext; §1–3 teils durch obige Fakten überholt.)*

> **Ziel dieser eigenen Session:** Das AAU-Trigger-**Modul-Dateiformat** vollständig knacken, sodass wir Module
> per Python **dekodieren UND erzeugen** können. Das ist der Schlüssel-Enabler: damit werden Custom-Module
> (Confinement, Prisoner, broken, trainer, Heimkehrer …) und die gesamte Evolutions-/Verhaltens-Manipulation
> **trivial** — wir generieren Module aus Code statt sie im Editor zu bauen (User baut keine Trigger).
>
> **Wenn fertig:** zurück zur Haupt-Arbeit; wir hängen generierte Module an Karten und sehen, was passiert.
> Vorher lesen: `AA2_Jail_Projekt_Notizen.md` (STATUS) + `HANDOVER_evolution_2026-06-25.md` (Pipeline-Kontext).

---

## 0. Warum dieser Weg (der Kontext, kurz)
Confinement (NPCs auf 1 Map-Knoten halten) brauchte einen Weg, `NpcMoveRoom` auszulösen. Ergebnis der
Recherche (alles verifiziert):
- **Kein Lua-Weg:** `m_forceAction` ist aus Lua **nicht erreichbar** (Probe `jail_probe.lua` bestätigt: Userdata,
  kein Member). `GetNpcCurrentRoom`/`IsPC`/`on.roomChange` gehen (Erkennung), nur der **Setter** fehlt.
- **Kein fertiges Modul:** keines der 466 Module hält einen NPC an einem Ort (Jailer = Rollen/roof/temporär;
  Chained Maiden/Toilet Police/Thot Patrol = was anderes). Geprüft.
- **Keine Format-Doku:** weder GitHub-Wiki noch anime-sharing-Wiki (nur Download-Index). Das Format lebt **nur
  im Quellcode** als generische Template-Serialisierung.
- **g_poke** ginge, aber Crash-Risiko + CharInstData-Adresse aus Lua unsicher.
→ **Modul-Generator (Format-RE) ist der einzige saubere, wiederverwendbare Weg.** Das ist diese Session.

## 1. Format-Erkenntnisse (gesichert)
Die Datei (`data/override/module/<Name>`, z.B. `Race-Human` = 328 B) ist **NICHT opak** — generische
Serialisierung verschachtelter Structs:
- **`wstring`** = `[uint32 Länge N][N × UTF-16LE code units]` (kein BOM, kein Nullterminator)
- **`vector<T>`** = `[uint32 count][count × T]`
- **`int`/`DWORD`/`enum`** = `uint32` little-endian
- **`pointer`** (Expression*/Action*/Event*/NamedConstant*) = vermutlich `uint32 id` (→ Lookup in der globalen
  Definitions-Tabelle; **zu verifizieren** inkl. null-Sentinel)
- Verifiziert per Byte-Diff `Race-Human` vs `Race-Demon`: nur die Strings `"Human"`/`"Demon"` unterscheiden sich.

**`Race-Human` Token-Folge (Referenz fürs Kalibrieren):**
```
"Race-Human" "Is a human" 1 "Init" 1 6 0 1 4 "race" 4 1 4 "Human " 1 2 1 2 8 2 …(driftet ab hier)…
```
Lesart bisher: name, desc, triggers.count=1, trigger.name="Init", events.count=1, event{id=6,params=0}, dann
beginnt die innere Struktur (Variablen/Actions) — **ab ~Offset 88 bricht der aktuelle Decoder.**

## 2. Struct-Layouts (aus AAU-Quelle, Feld-Reihenfolge = Serialisierungs-Reihenfolge)
```
Module   = name:wstr · description:wstr · triggers:vec<Trigger> · globals:vec<GlobalVariable> · dependencies:vec<wstr>
Trigger  = name:wstr · events:vec<ParameterisedEvent> · vars:vec<Variable> · guiActions:vec<GUIAction*> ·
           actions:vec<ParameterisedAction> · globalVars:vec<GlobalVariable>* (POINTER—evtl. nicht serialisiert) ·
           owningCard:int · broken:bool · bInitialized:bool
Variable = id:DWORD · type:Types(enum) · name:wstr · defaultValue:ParameterisedExpression
ParameterisedExpression = expression:Expression*(→id) · actualParameters:vec<ParameterisedExpression> ·
           constant:Value · varName:wstr · namedConstant:NamedConstant*(→id) · varId:int
ParameterisedAction = action:Action*(→id) · actualParameters:vec<ParameterisedExpression>
ParameterisedEvent  = (NICHT gefunden; Vermutung analog: event:Event*(→id) · actualParameters:vec<PExpr>)
GUIAction = action:ParameterisedAction · subactions:vec<GUIAction*> · parent:GUIAction*(skip)   # If/then-Baum!
Value    = type:Types · union{ wstring* · int · float · bool }     # Payload nach type
Expression/Action (GLOBALE Defs, NICHT pro Modul serialisiert; nur per id referenziert):
           id:DWORD · category:int · name:wstr · interactiveName:wstr · description:wstr · parameters:vec<Types> · returnType/func
```

## 3. OFFENE UNBEKANNTE (das ist die eigentliche Arbeit)
1. **★ Die generische `ReadData<T>`/`WriteData<T>` finden ★** — der Schlüssel. `Files/ModuleFile.cpp` nutzt
   `ReadData<decltype(mod)>(bufCpy,sizeCpy)` + `WriteData(&buffer,&size,at,mod,true)`, aber die **Definition**
   ist NICHT in Buffer.h/InfoData/den Triggers-Dateien (alle geprüft). **Erster Schritt: `ModuleFile.cpp` die
   `#include`-Zeilen holen** → zeigt den Header. (Alte Doku nannte `Serialize.h` — also existiert es; finden.)
   Dort stehen die Spezialisierungen für `wstring`/`vector`/`bool`/`pointer`/structs = das ganze Format.
2. **`Types`-Enum-Werte** (für `Value`-Payload-Dispatch + `Variable.type`). In Value.h/Triggers.h/einem enum.
3. **Event/Action/Expression-ID-Werte** — aus `Actions.cpp`/`Expressions.cpp`/`Event.cpp` (die `g_*`-Listen mit
   id-Zuweisungen). Brauchst du fürs ENCODER (z.B. die id von `NpcMoveRoom`, `GetNpcCurrentRoom`, `GetPC`).
4. **bool-Breite** (1 Byte vs uint32). 5. **Pointer null-Sentinel** (0? -1?). 6. **guiActions-Baum vs actions-flat**
   — welcher wird serialisiert? Vermutung: **guiActions-Baum** (Editor zeigt If/then-Verschachtelung; `actions`
   wird per `Trigger::AddActionsFromGuiActions()` zur Laufzeit generiert → evtl. leer in der Datei).

## 4. Schon gebaute Tools (im Repo-Root)
- **`module_decode.py`** — greedy Token-Dumper (zeigt strings + uint32s grob).
- **`module_schema.py`** — **schema-getriebener Decoder** mit „bis-EOF-konsumieren"-Sweep über die Unbekannten
  (bool-Breite, Value-string-types, gui-vs-actions). **Stand: 28% von Race-Human** (bricht @offset 88).
  **Methode:** ein Schema ist korrekt, wenn es ein bekanntes Modul EXAKT bis EOF konsumiert (left==0). Erweitere
  die Schema-Klasse, bis Race-Human (328 B, einfachstes) clean parst, dann `Begone Thot`, dann ein Modul mit
  echten Conditions.

## 5. Validierungs-Strategie
1. **consume-to-EOF** an `Race-Human` (trivial) → `Race-Demon` (Diff-Check) → `Begone Thot` (hat Events+Actions,
   matcht User-Screenshot „slap detect") → ein Modul mit verschachtelten If/then.
2. **Editor als Ground Truth:** generiertes Modul in `data/override/module/` ablegen → im AAU-Trigger-Editor
   öffnen → rendert es die beabsichtigte Logik? (User kann Screenshots liefern.) Roundtrip-Test:
   decode(encode(decode(x))) == x byte-genau.

## 6. Zielmodul (sobald Encoder steht): „Confinement"
```
EVENT:  Room Change
WENN:   This Card == Triggering Card  UND  This Card != PC  UND  GetNpcCurrentRoom(This Card) != 39
TUE:    NpcMoveRoom(This Card, 39)            # „Make Npc Move to Room"; 39 = Outside Station (verifiziert)
```
Verifizierte Bausteine: `NpcMoveRoom` (Actions.cpp — setzt `m_forceAction.movementType=2; roomTarget=roomId`),
`GetNpcCurrentRoom(seat)`, `GetPC()`, `GetThisCard()`. Vollständige Spec: `CONFINEMENT_MODULE_SPEC.md`.
**Stufe 2:** Zell-Raum + „ist Insasse"-Flag aus **Card Storage** lesen (`getCardStorage`) → SSOT-getrieben, pro
NPC, generisch. Orchestrator setzt das Flag (wie `_orch_char_state.flag` → apply_state).

## 7. Integration zurück ins Projekt
1. Generator erzeugt `school/data/override/module/<Name>` (+ jail-Spiegel).
2. User hängt das fertige Modul via **AA2QtEdit** an NPC-Karten (Editor pflegt die `AUSS`-Bytes → **umgeht** die
   Karten-Korruptions-Sackgasse §3, die beim rohen Byte-Splice auftrat).
3. Damit ist die **ganze Status-/Evolutions-Modul-Ebene entsperrt** (Prisoner/broken/trainer/Heimkehrer + Confinement).

## 8. Schlüssel-Quelldateien (AAU GitHub, raw-URLs via WebFetch; `gh` fehlt im Bash-PATH)
```
github.com/aa2g/AA2Unlimited  →  AAUnlimited/Functions/Shared/Triggers/
   Module.h/.cpp · Triggers.h/.cpp · Actions.h/.cpp · Expressions.h/.cpp · Event.h/.cpp ·
   Value.h/.cpp · NamedConstant.h/.cpp · InfoData.h/.cpp · Thread.h/.cpp
AAUnlimited/Files/ModuleFile.cpp   ← nutzt ReadData/WriteData (deren Header = ★ Schritt 1)
AAUnlimited/Files/PersistentStorage.* ← könnte denselben Serializer nutzen (Card Storage) → Quersuche
```
raw-Form: `https://raw.githubusercontent.com/aa2g/AA2Unlimited/master/<pfad>`
Verzeichnis-Listing: `https://api.github.com/repos/aa2g/AA2Unlimited/contents/<pfad>`

## 9. Test-Module (lokal, klein → groß)
- `school|jail/data/override/module/Race-Human` (328 B, NUR Init+Variable — **hier kalibrieren**)
- `…/Race-Demon` (Diff-Partner zum Parameter-Check)
- `…/Begone Thot` (3992 B — Events + Actions; matcht User-Screenshot „slap detect")
- `…/Blackmailer` (komplex, verschachtelte If/then — User-Screenshot „Blackmailer::PC")

## 10. Erster konkreter Schritt der RE-Session
1. `ModuleFile.cpp` holen → die `#include`-Zeilen lesen → den `ReadData/WriteData`-Header finden + holen.
2. Dessen Spezialisierungen (wstring/vector/bool/pointer/struct) in `module_schema.py` exakt nachbauen.
3. `python module_schema.py Race-Human` bis **CLEAN PARSE (left=0)**. Dann Begone Thot.
4. Encoder = Umkehrung der Reader-Schemas. Roundtrip-Test byte-genau.
5. Confinement-Modul generieren (§6) → testen.

> Python fürs Tooling: `C:\Users\Henta\AppData\Local\Programs\Python\Python312\python.exe` (3.12.8).
> Aktiver Playthrough: NEW HOPE, PC = Cox Robert. Zell-Raum = 39 (Outside Station).
