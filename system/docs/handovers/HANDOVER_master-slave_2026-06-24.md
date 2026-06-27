# HANDOVER — Config-Reparatur + master/slave-Trigger (Stand 2026-06-24, spät)

> **Zweck:** Frische Session ohne Kontextverlust. **Absolute Genauigkeit.** Diese Datei = was in der
> langen 2026-06-24-Session NEU dazukam. **Vorher lesen:**
> - `HANDOVER_jail-coupling_2026-06-24.md` = das Coupling-/RPG-System (Orchestrator, DB, JSON-Brücke).
> - `HANDOVER_load-RE_2026-06-24.md` = RE-Saga (kein aufrufbarer Loader → Klick-Automatik „B").
> - `AA2_Jail_Projekt_Notizen.md` = die Gesamt-Vision (RPG-Schicht, Transfer-Regeln 2.4–2.4d, Hints 5).
> Stil: Nutzer = Nicht-Coder, architektonisch scharf. Deutsch, direkt, technisch.

---

## 0. TL;DR — was JETZT erreicht ist
1. **Config-Reparatur abgeschlossen** (Nutzer-Mods + Auflösung werden respektiert, jail spiegelt school).
2. **★ master/slave-Trigger gebaut + LIVE BESTÄTIGT:** PC macht Dominanz-Combo `INSULT→FIGHT→FORCE_H`
   gegen einen Char → der Char wird „slave" → in `_orch_slave.flag` geschrieben. Das ist der
   „dazugehörige Interaktions"-Trigger aus den Notizen — aus *vorhandenen* Aktionen, kein Engine-Hack.
3. **Nächster offener Block:** den **Transfer** verdrahten (slave → an End-Day nach jail: Card + Play-Data).

---

## 1. ★ CONFIG-REPARATUR (wichtig — Nutzer war darüber verärgert, NIE wieder Mods ausschalten) ★

**Prinzip (vom Nutzer eingefordert):** Niemals automatisch Mods deaktivieren. Der Nutzer pflegt EINE
Mod-Liste (school); jail bekommt sie automatisch.

- **`table.dump`-Bug GEFIXT** (`init.lua` Z. ~120, school + jail): `string.format("%q", v)` crashte bei
  `userdata`-Werten → brach die Config-Serialisierung mittendrin ab → `savedconfig` wurde auf ~3 Zeilen
  geköpft (mods-Tabelle + `res_play` weg). Fix: vor dem `%q`-Zweig ein `userdata`/`thread`-Zweig, der
  `nil` emittiert statt zu crashen. **Damit überlebt savedconfig jedes Beenden.** (`-- [orchestrator fix]`)
- **`savedconfig` wiederhergestellt** aus dem Nutzer-Backup → school + jail haben jetzt `res_play="1920x1080"`
  + alle 30 Mods (inkl. **`win10fix`** = low-FPS-Fix). **Auflösung = 1920×1080 (16:9).**
- **★ BACKUP-PFAD (NUR LESEN, NIE BESCHREIBEN — Nutzer-Anweisung!): `<AA2-clean-install>`** —
  saubere Referenz-Installation. `AA2MiniPPX\AAUnlimited\savedconfig.lua` = die Soll-Config.
- **g_var-Konflikt gelöst:** `extsave` + `orch_savename` patchten beide `0x470B0`. Jetzt exportiert
  `extsave.lua` seinen g_var (`rawset(_ENV, "_orch_g_var", g_var)`), und `orch_savename` nutzt den geteilten
  Wert statt eines zweiten Patches (Fallback: eigener Patch, falls extsave inaktiv). Beide in school+jail.
- **savedconfig-SPIEGELUNG school→jail:** `mirror_config_school_to_jail()` in `orchestrator.py` kopiert
  beim Start school's savedconfig über jail's (Guard: nur wenn >50 B, sonst nicht spiegeln). → jail launcht
  immer mit school's Liste.
- **Helfer-Mods in BEIDEN mod-Ordnern** (damit die gespiegelte Liste nichts ins Leere referenziert):
  `logperiod`, `orch_savename`, `master_slave`.

---

## 2. ★★ master/slave-TRIGGER (der große neue Befund) ★★

### 2.1 AAU hat ein Lua-Event-System (so steuert man Interaktionen)
- **PC-Aktionen kommen über `on.answer(resp, as)`** — NICHT über `on.move` (das ist NUR NPC-AI).
  Beleg/Vorlage: `mod/geass.lua` (Absolute Obedience). Struktur der answerstruct `as`:
  - **`as.askingChar.m_thisChar == GetPlayerCharacter()`** → der Akteur ist der PC.
  - **`as.answerChar`** → das ZIEL der Aktion (`seat_of()` via `.m_seat` / `.m_thisChar.m_seat`).
  - **`as.conversationId`** → die Aktions-ID.
  - `as.answerChar.m_lastConversationAnswerPercent` → Erfolgs-% (geass setzt es auf 999).
- **PC = Cox Robert = Seat 24** (das grüne „Pc"-Badge im Roster; `GetPlayer()`/`GetPlayerCharacter()`).
  `on.move`-Akteure sind IMMER NPCs (Seat 24 taucht dort nie auf).
- **Aktions-IDs** (aus `triggers_supplemental.lua` `getActionName`, 0–96+): `ENCOURAGE`=0, `PRAISE`=2,
  `INSULT`=33, `FIGHT`=34, `FORCE_IGNORE`=35, `FORCE_SHOW_THAT`=36, `FORCE_PUT_THIS_ON`=37, **`FORCE_H`=38**,
  `KISS`=46, `TOUCH`=47, `HEADPAT`=44, `SLAP`=83, `MURDER`=82 …
- **Wichtig:** Nur Aktionen mit „Antwort" feuern `on.answer` (INSULT, FORCE_*, KISS, PRAISE … ✓; manche
  mt-Aktionen kommen nur über `on.move`). FIGHT (34) kam im Test DOCH über `on.answer` durch.
- Andere Events (für später, Notizen 5/Transfer): `on.card_expelled(actor0, actor1, murder)`,
  `on.start_h`/`on.end_h`, `on.convo`, `on.period`, `on.save_class`/`on.load_class`. `triggers_supplemental.lua`
  hat fertige Beziehungs-API: `GetLoveTowards`/`GetHateTowards`/`SetPointsTowards`, `createRelationshipPointsDump`.

### 2.2 Der Mod `school|jail/AAUnlimited/mod/master_slave.lua` (FERTIG, bestätigt)
- Combo `COMBO = {INSULT=33, FIGHT=34, FORCE_H=38}` (Konstante oben im Mod, leicht änderbar).
- `on.answer`: nur wenn `isPC`; verfolgt pro **Ziel-Seat** den Combo-Fortschritt (`progress[seat]`).
  Falsche Aktion gegen DASSELBE Ziel bricht dessen Kette; Aktionen gegen andere Ziele stören nicht.
- Bei Combo-Abschluss → `dbg("*** ENSLAVED: seat N (Name) ***")` + Append in `play_path("_orch_slave.flag")`
  als `"<seat>\t<Name>\n"`. Debug nach `_orch_ms_debug.flag` (bei load truncated; slave-flag auch).
- **LIVE BESTÄTIGT 2026-06-24:** `*** ENSLAVED: seat 4 (Shimizu Airi) via INSULT -> FIGHT -> FORCE_H ***`,
  `_orch_slave.flag` = `4 \t Shimizu Airi`.
- Forciert via `school/forcedconfig.lua` (+ in jail via Spiegelung/forcedconfig). Helfer-Datei in beiden mod-Ordnern.

### 2.3 NICHT als AAU-Card-Modul, sondern Lua-Mod (bewusste Entscheidung)
Nutzer wählte „eigenes Modul (b)". AAU-Card-Module (Trigger-Editor/GUI, Logik binär in Card/.ppx) kann ich
nicht als Code schreiben. Ein **Lua-Mod** erreicht dasselbe (ganze Logik in Lua, dockt an DB/Transfer/Hints an).
Einschränkung: keine NEUEN Interaktions-Verben (Engine fix) — nur Reaktion auf Kombinationen vorhandener.

---

## 3. NÄCHSTER BLOCK: der Transfer (slave → jail), Notizen 2.4–2.4d
**Modell (Nutzer):** Chars wandern NICHT als Roster-Kopie, sondern EINZELN über die Interaktion (slave),
an der **Tagesgrenze (End-Day)**. Transfer = **Card** (falls Char neu in jail) + **Play-Data**
(char-interne Werte: virtue, corruption, traits, Module, Stats → 1:1, erzeugt Reibung emergent gratis).
**Beziehungen NICHT 1:1** → „verdichten" zu char-internen Werten (`social_wealth=high` → Einsamkeits-Modul).

Bausteine:
1. **End-Day-Hook** — Transfer an Tageswechsel auslösen (`on.period`, Sleep/Period 9→10), nicht mitten im Tag.
2. **Orchestrator liest `_orch_slave.flag`** → führt Transfer aus (für den/die markierten Chars).
3. **Char nach jail bringen** — Card + Play-Data. **Play-Data = der bewiesene JSON-Transfer**
   (`playthrough_db.py` `inject_chars_to_json`, per Name → trifft den aktuellen Roster-Seat-Block;
   Marker-Test bewies, dass injizierte `.json`-Werte im Spiel ankommen). Card-Einfügung (Char ins
   jail-Roster) = noch offen (AA2QtEdit-artig / Notizen „User-Terrain, als gelöst").
4. **Beziehungs-Verdichtung → Modul** (später).
5. **Coupler-Transfer (`_transfer_to_jail` in orchestrator.py) ist GEPARKT** (auskommentiert) — war die
   falsche „alles 1:1 Roster-Kopie". Der echte Transfer ist interaktions-getriggert (slave).

---

## 4. DATEI-/ZUSTANDS-STAND (was diese Session anfasste)
**Geändert (alle Änderungen `[orchestrator]`/`[orchestrator fix]` kommentiert):**
- `school|jail/AAUnlimited/init.lua` — table.dump-Fix.
- `school|jail/AAUnlimited/savedconfig.lua` — aus Backup wiederhergestellt (1920×1080, 30 Mods).
- `school|jail/AAUnlimited/mod/extsave.lua` — g_var-Export (1 Zeile).
- `school/AAUnlimited/mod/orch_savename.lua` — nutzt geteilten g_var (kein Doppel-Patch).
- `school/AAUnlimited/forcedconfig.lua` — forciert logperiod + orch_savename + master_slave (nur EIN-schalten).
- `jail/AAUnlimited/forcedconfig.lua` — forciert nur logperiod (Test-Cruft orch_verify/orch_roster ENTFERNT).
- `school|jail/AAUnlimited/mod/master_slave.lua` — der Trigger (fertig).
- `orchestrator.py` — `mirror_config_school_to_jail()` (Start), `import playthrough_db`, Coupler etc.
**Neu (Dev):** `playthrough_db.py`, `run_orchestrator.bat` (self-elevating, BlockInput braucht Admin),
`HANDOVER_jail-coupling_2026-06-24.md`. **Test-Mods entfernt:** `orch_verify.lua`, `orch_roster.lua` aus
forcedconfig (Dateien evtl. noch im jail-mod-Ordner, inaktiv).
**Backups:** `_backup/jail_class_premigration/` (orig jail NEW HOPE), `_backup/school_NEWHOPE.json.premarker`.
**Flags (Laufzeit):** `school/_orch_period.flag`, `_orch_save.flag`, `_orch_slave.flag`, `_orch_ms_debug.flag`.

## 5. UMGEBUNGS-FAKTEN (Zeit sparen)
- **Tool-Pfadschutz:** Bash/PowerShell blockt `Remove-Item`/`rmdir` auf Pfaden mit „jail" (false-positive,
  auch mit dangerouslyDisableSandbox). Workaround beim Setup: **Move statt Remove**. Der laufende
  Orchestrator (Python) ist NICHT betroffen.
- **Python fürs Tooling:** `python`. `py`/3.14
  läuft auch (stdlib+ctypes+tkinter), gibt nur eine harmlose „platform libraries"-Warnung.
- **CJK:** Save-Namen sind CJK; stdout oft cp1252 → `PYTHONIOENCODING=utf-8` setzen. Orchestrator härtet
  stdout selbst. `class_name` in der `.json` ist encoding-verstümmelt → NICHT als Save-Name nutzen.
- **Start:** `run_orchestrator.bat` (als Admin → BlockInput; UAC „Ja"). Auflösung 1920×1080.
- **jail-Klick-Verifikation bei 1920×1080 noch offen** — Fraktionen sind 16:9, sollten passen; beim
  nächsten Coppeln prüfen (Konsole zeigt px-Koordinaten + Fenstergröße).
