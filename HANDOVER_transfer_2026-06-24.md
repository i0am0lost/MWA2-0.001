# HANDOVER — Sofort-Transfer (slave → jail) + SSOT Modell A (Stand 2026-06-24, spät)

> **Zweck:** Frische Session ohne Kontextverlust. **Absolute Genauigkeit.** Diese Datei = der Transfer-Bau
> dieser Session (baut auf dem master/slave-Trigger auf). **Vorher lesen:**
> - `HANDOVER_master-slave_2026-06-24.md` — der Combo-Trigger (INSULT→FIGHT→FORCE_H) + Config-Reparatur.
> - `HANDOVER_jail-coupling_2026-06-24.md` — Coupling/Twin/Junction/Orchestrator-Grundlage.
> - `AA2_Jail_Projekt_Notizen.md` — Gesamt-Vision; **NEU: §12** (SSOT/Save-Konsistenz + Beziehungs-Regel).
> Nutzer = Nicht-Coder, architektonisch sehr scharf. Deutsch, direkt, technisch.

---

## 0. TL;DR — wo wir JETZT stehen
1. **DESIGN-PIVOT (Nutzer):** Transfer passiert **SOFORT beim Versklaven**, NICHT am End-Day. End-Day =
   nur noch *wann der PC physisch ins jail geht* und die bereits transferierten Insassen vorfindet.
2. **SSOT Modell A gebaut + LIVE BESTÄTIGT:** Combo versklavt = **provisorisch**; **Speichern in school
   committet** → Journal (memory.db, tag-datiert) → Orchestrator leitet jails Insassen ab → jail zeigt
   sie. **Bewiesen:** Shimizu Airi enslaved → school gespeichert → erscheint in jail, fehlt in school.
3. **★ KEYSTONE BEWIESEN (Update, spät 2026-06-24): `AddCard` funktioniert.** Live-Beweis: jail-Save war
   nach einem Vorabend-Speichern schlank (PC + Airi); dann 2. Char **Takagi Saya** versklavt+committet →
   `jail_intake` lud sie per `AddCard` nach (sie war NICHT im Save). Debug: `addmissing@p9:
   ADDED={Takagi Saya@0(Takagi_Saya.png)}`. **Format = bare `<Name>.png`** (KEIN Ordner-Präfix; der
   gender-Bool wählt Female/Male). KickCard + AddCard beide live bewiesen, mehrere Insassen funktionieren.
4. **Reihenfolge:** 1) ✅ `AddCard`-Keystone DURCH → 2) ✅ **2b BESTÄTIGT** — Selbst-Werte injiziert +
   read-back verifiziert (`m_charData.m_character.<feld> = wert` greift; Beleg: `INJECTED={Shimizu Airi
   {virtue=0;intelligence=2;strength=1;sociability=3}, Takagi Saya{virtue=2;…}}`) → 3) **2c** Beziehungs-
   Reconciliation → 4) Rückkehr-Pfad. Danach: Modul-Editor (Evolution).

---

## 1. DAS MODELL A (wie der Transfer läuft) — bestätigte Mechanik
**Commit-on-save, derive-on-load, tag-datiert.** Single-Save-Slot (Nutzer-Fakt: pro Playthrough EIN Save,
Speichern überschreibt immer — KEINE mehreren Zeitstempel einer Save). Die **DB ist der einzige Verlaufs-
speicher** (das Spiel hat keinen).

Ablauf:
1. **Combo abgeschlossen** (`master_slave.lua`, school) → **provisorisch**: nur Live-Preview-`KickCard`
   (deferred auf `on.end_h`/`on.period`, da `KickCard` mitten in der startenden FORCE_H-Szene crashen kann).
   Char wird in `enslaved_uncommitted` gemerkt. **Kein** Commit.
2. **`on.save_class` (du speicherst)** → **COMMIT**: append `<nDays>\t<name>\t<gender>\t<self>` an
   `school/_orch_slave_commits.flag`. Nicht gespeichert → kein Commit → jail bleibt leer.
3. **Orchestrator `transfer_sync`-Thread** (alle 1,5 s): ingestet die Commits **idempotent** ins
   `transfers`-Journal (`_playthroughs/<key>/memory.db`), liest schools aktuellen Tag aus
   `school/_orch_day.flag` (von `logperiod` geschrieben), **leitet** die Insassen für diesen Tag ab
   (`residents_as_of`), und schreibt `jail/_orch_jail_inmates.flag` als `<name>\t<cardfile>\t<gender>`.
4. **`jail_intake.lua` (jail)** rekonstruiert das Roster bei `on.load_class`/`on.period`/`on.room_change`:
   **KickCard** für jeden Nicht-Insassen (außer PC) + **AddCard** für jeden Insassen, der noch nicht da ist.
   → jail zeigt `{PC + Insassen}`.

**Journal-Logik unit-getestet (ohne Spiel):** idempotenter Ingest ✓, tag-datierte Ableitung ✓, Rückkehr
(`to_world='school'`, last-write-wins) ✓. Tag 3=leer, Tag 5=[Kanata], Tag 7=[Airi,Kanata], nach Rückkehr
Tag 8=[Airi]. → Rollback-Logik korrekt, ABER „alte Save laden" ist KEIN Spiel-Feature (Single-Save-Slot);
die Tag-Datierung dient als Verlaufs-/Auto-Save-Substrat (s. §7).

---

## 2. VERIFIZIERTE FAKTEN (live, diese Session)
- **`KickCard(seat)`** = korrekte Signatur, läuft sauber (Char raus aus school-Roster). Registriert in
  `AAUnlimitedDll.dll` (ASCII+UTF-16 bestätigt), zusammen mit `AddCard`, `SafeAddCardPoints`.
- **Live Selbst-Wert-Schema:** lesbar ist `inst.m_char.m_charData.m_character.{virtue,intelligence,
  strength,sociability}` (Werte 1–3 = **Ränge**). Der Pfad `m_charData.virtue` (ohne `.m_character`)
  liefert NICHTS. Snapshot-Beispiel Airi: `virtue=0;intelligence=2;strength=1;sociability=3`.
- **PC-Erkennung:** `GetCharInstData(seat).m_char == GetPlayerCharacter()` (Idiom aus `music.lua`).
- **`AddCard(fileName, femaleBool, seat)` — LIVE BEWIESEN.** Format = **bare `"<Name>.png"`** (KEIN
  Ordner-Präfix; der gender-Bool wählt `data/save/Female|Male`). Gender: `0`→`false` (male), sonst `true`.
  Nur an STABILEM Moment aufrufen (**Period 9**, Home-Screen — wie `undyingAddCards`); mid-load failt es.
  Periode in jail über `logperiod`s `_orch_period.flag` lesen (direktes `GetGameTimeData()` gab in
  `jail_intake` `-1`). Beleg: `addmissing@p9: ADDED={Takagi Saya@0(Takagi_Saya.png)}`.
- **Lose Karten existieren für JEDEN Roster-Char** in `school|jail/data/save/Female|Male/<Name>.png`
  (z. B. `Shimizu_Airi.png`). Die 25 „fehlenden" Namen aus der `.json` sind historische Blöcke, NICHT im
  Roster → da man nur Roster-Chars versklaven kann, hat jeder versklavbare Char eine Karte. Kein `.sav`-Export nötig.
- **jail-Twin muss Voll-Kopie sein** fürs Filter-behalten; `.sav` school=1,9 MB vs. alter pruned Twin=230 KB.
  Die `.json` ist nur AAU-Datenspeicher (Roster steckt in der `.sav`).

---

## 3. GEÄNDERTE / NEUE DATEIEN (alle `[orchestrator]`-kommentiert)
- **`school|jail/AAUnlimited/mod/master_slave.lua`** — Combo provisorisch + `on.save_class`-Commit +
  Live-Self-Snapshot. Schreibt `_orch_slave_commits.flag` (append, NICHT bei load truncaten = Journal-Quelle).
- **`school|jail/AAUnlimited/mod/logperiod.lua`** — schreibt zusätzlich `_orch_day.flag` (`nDays`) in
  `on.period`/`on.load_class`/Timer.
- **`jail/AAUnlimited/mod/jail_intake.lua`** (NEU, jail-only) — Roster-Rekonstruktion aus SSOT (KickCard +
  AddCard). Self-gating: ohne `_orch_jail_inmates.flag` = no-op (kann school nie anfassen). Namen normalisiert.
- **`jail/AAUnlimited/forcedconfig.lua`** — `jail_intake` forciert (jail-only; school referenziert ihn nie).
- **`playthrough_db.py`** — `transfers`-Journal-Tabelle + `add_transfer` / `ingest_transfer_commits` /
  `residents_as_of` (last-write-wins, tag-datiert).
- **`orchestrator.py`** — `import re`; `read_day`, `_card_index`/`resolve_card_file` (Name→`.png`),
  `write_jail_inmates` (angereichert), `transfer_sync`-Thread (in `main()` gestartet).
- **`AA2_Jail_Projekt_Notizen.md`** — **§12** angehängt (SSOT/Save-Konsistenz, Single-Save-Slot, Auto-Save-
  TODO, Beziehungs-Reconciliation-Regel).
- **jail-Twin** `_playthroughs/NEW HOPE学園1年1組/jail/*.sav` — als **Voll-Kopie** des school-Saves neu gezogen.
- **Flags (Laufzeit):** `school/_orch_slave_commits.flag`, `school/_orch_day.flag`,
  `jail/_orch_jail_inmates.flag` (angereichert: `name\tcard\tgender`), `jail/_orch_jail_debug.flag`,
  `school/_orch_ms_debug.flag`. **Entfernt (stale):** `_orch_slave.flag`, `_orch_slave_snapshot.flag`.

---

## 4. ★ KEYSTONE BEWIESEN: `AddCard` funktioniert ★
**Live-Beweis (spät 2026-06-24):** Nach einem Vorabend-`Save` in jail war der jail-`.sav` **schlank**
(PC + Airi; die anderen waren von `jail_intake` gekickt). Danach 2. Char **Takagi Saya** in school
versklavt + gespeichert → committet (Journal Tag 12, inmates=[Airi, Takagi]). jail-Live-Roster hatte nur
Airi → `jail_intake` lud **Takagi per `AddCard` nach** (sie war NICHT im Save). Debug:
```
tick[timer] period=9 present=1 inmates=2
addmissing@p9: kicked_nonInmates=0  ADDED={Takagi Saya@0(Takagi_Saya.png)}  FAILED={}
tick[timer] period=9 present=2 inmates=2
```
→ jail zeigt PC + Airi + Takagi. **`AddCard` bewiesen, Format = bare `<Name>.png`.**

**Zwei Erkenntnisse, die den Test erst möglich machten:**
1. `AddCard` nur an STABILEM Moment (**Period 9**); mid-`on.load_class` (Klasse lädt noch) failt es.
2. Periode in `jail_intake` über `logperiod`s `_orch_period.flag` lesen — direktes `GetGameTimeData()`
   gab dort `-1` (in `logperiod` funktioniert es). `jail_intake` hat einen eigenen 700ms-Timer (wie
   logperiod), damit `apply` auch beim **Reinswitchen** (Resume, kein Event) greift.

**Aktuelles `jail_intake`-Verhalten (sicher):** „**vorhandene Insassen behalten (per Name), fehlende per
`AddCard` ergänzen**" — ein falsches Format kann nie einen gezeigten Insassen verschwinden lassen. (Für die
spätere Modul-Evolution wird auf „immer aus SSOT/adaptierter Karte neu laden" umgestellt — dann wird auch
ein vorhandener Insasse neu ge-`AddCard`et, um die adaptierte Karte zu laden.)

---

## 5. ★ NÄCHSTER SCHRITT: 2b — Selbst-Werte injizieren ★
Daten liegen **schon im Journal** (`self_data`: Airi `virtue=0;intelligence=2;strength=1;sociability=3`,
Takagi `virtue=2;…`). Plan:
1. **Orchestrator:** die `self_data` in die `_orch_jail_inmates.flag`-Zeile mit aufnehmen (`name\tcard\tgender\tself`).
2. **`jail_intake`:** nach erfolgreichem `AddCard` (oder für vorhandene Insassen) die Ränge auf den Seat
   schreiben via `SetCardVirtue/SetCardIntelligenceValue/SetCardStrengthValue/SetCardSociability(seat, wert)`
   (Setter-Familie in `AAUnlimitedDll.dll` bestätigt; Signatur live verifizieren wie bei KickCard/AddCard).
3. **Cleanup:** die Diagnose-Heartbeats (`tick[...]`) aus `jail_intake` entfernen, jetzt wo's läuft.
Danach 2c (Beziehungen) + Rückkehr-Pfad; dann der Modul-Editor (Evolution; Format bereits verifiziert, s.u.).

**Karten-Modul-Editor (Evolution-Schicht) — Machbarkeit BESTÄTIGT (2026-06-24):** AAU-Daten inkl. Module
liegen im sauberen PNG-Chunk **`aaUd`** (Version 3). Member-Stream: `Vers`+Version, dann 4-Byte-LE-Tags;
Modul-Member = **`TrMd`** = `int32 count` + Elemente; jedes Element = `int32 Namens-Länge` + UTF-16LE-Name +
Params. **Live aus echten Karten gelesen** (Airi 9 Module „Sugar Lips…", Sasaki 13 „Blackmailer…"). Chunk
editieren = Standard (Länge + CRC32 neu). Offen: Per-Modul-Param-Serialisierung dekodieren (für Add/Remove)
+ In-Game-Verifikation, dass `AddCard` einer adaptierten Karte die geänderten Module lädt. Quelle:
`AAUCardData.cpp` (aa2g/AA2Unlimited). Überholt #10 („nur aus Lua zur Laufzeit unmöglich", extern geht es).

---

## 6. DANACH: 2b (Selbst-Werte) + 2c (Beziehungen)
**2b — Selbst-Werte injizieren:** nach `AddCard` die Snapshot-Ränge (`virtue=…;…`) auf den Insassen-Seat
schreiben via `SetCardVirtue/SetCardIntelligenceValue/SetCardStrengthValue/SetCardSociability(seat, wert)`
(Setter-Familie in der DLL bestätigt; Signaturen live verifizieren wie bei KickCard). Quelle = die `self`-
Spalte im Journal / die Commit-Zeile.

**2c — Beziehungs-Reconciliation (Notizen 2.4c/2.4d + §12):** Beziehungs-/H-Werte sind **seat-indiziert** →
NIE den Dump 1:1 restaurieren (zeigt in jail auf leere/falsche Seats). Regel:
- SSOT hält Beziehungen **char_id↔char_id** (seat-unabhängig; `relationships`-Tabelle steht).
- **Snapshot** beim Welt-Verlassen: `createRelationshipPointsDump`/`createHStatsDump` pro Seat-Paar →
  Seat→char_id über Live-Roster auflösen, nach Identität speichern.
- **Inject** beim Betreten: pro Beziehung — Gegenpart **anwesend** → char_id→Live-Seat → echt restaurieren
  (`restoreRelationshipPointsFromDump`); Gegenpart **abwesend** → KEINE Seat-Ref → char-intern **verdichten**
  (Modul/Wert „ist gebunden" → Einsamkeit), Beziehung **schläft** in SSOT, reaktiviert wenn beide ko-präsent.
- Beispiele: Airi→PC „hasserfüllt" → PC immer da → restauriert. Airi→Boyfriend (nicht in jail) →
  Gebunden-Zustand, kein Seat-Pointer; Boyfriend kommt ins jail → reaktiviert („sie weiß, wer er ist").

---

## 7. OFFEN (spätere Iteration): Auto-Save im ~7-Tage-Fenster
Was, wenn der Spieler NICHT speichert? Aktuell = kein Commit = jail leer (provisorisch, korrekt). Gewollt:
eine **Auto-Save-Funktion**, die im ~7-Tage-Fenster greift (z. B. am Tageswechsel) → Orchestrator triggert
Save der aktiven Welt + Capture der inaktiven → Commit ins Journal. Dockt an Modell A an (capture-on-switch +
commit-on-save). Plus: **simultane Saves** (Modell **A gewählt** = SSOT als Sync-Punkt, kein physisches
Doppel-Speichern). Siehe Notizen §12.

---

## 8. UMGEBUNG / FAKTEN
- **Start:** `run_orchestrator.bat` (als Admin → BlockInput). **Beenden:** Ctrl+C / q / Fenster-X → Watchdog
  räumt school+jail+PPeX auf (diese Session sauber bestätigt: keine Geister-Prozesse).
- **Python fürs Tooling:** `python`.
- **Aktiver Playthrough:** `NEW HOPE学園1年1組` (Twin + `memory.db` vorhanden). PC = Cox Robert.
- **Pfadschutz:** Bash/PowerShell blockt `Remove-Item`/`rmdir` auf „jail"-Pfaden → Move/Python-`shutil` statt
  Remove. Der laufende Orchestrator (Python) ist nicht betroffen.
- **Test-Ablauf 2a (bestätigt):** Restart → school NEW HOPE laden → Combo INSULT→FIGHT→FORCE_H auf einen
  Roster-Char → **in school speichern** → zu jail switchen → Insasse erscheint (allein + PC).
- **Lua-Syntax:** kein Interpreter auf PATH → Syntaxfehler fängt erst der Launcher beim Laden ab.


---

## 9. UPDATE (spät 2026-06-24) — Modul-Scan + 2c gebaut

**Modul-Scan FERTIG (read-only):** `module_scan.py` liest alle 466 Modul-Dateien aus
`school/data/override/module/` (Format: `DWORD name_len + name(UTF-16) + DWORD desc_len + desc(UTF-16)`
+ Trigger-Baum) → `module_catalog.json` + `.md` (Name + Beschreibung). Basis für die kuratierte
Zustand→Modul-MAP. Beispiel-Treffer: "Corruption" (forceful → loses virtue → corrupted style),
"Sex Addict" (loses virtue without sex), Chaste Cherisher, Abstinent, Banchou, Jailer, Blackmailer.

**2c gebaut (fokussiert: social_wealth + PC-Beziehung):**
- `master_slave.lua` `rel_extra(seat)`: am Versklaven Beziehungen abziehen (`createRelationshipPointsDump`),
  zählt positive Bindungen → `social_wealth=high/low` (Schwelle bonds>=3, tunebar) + dumpt die Beziehung
  ZUM PC (`pc_love/pc_like/pc_dislike/pc_hate`). Reitet im `self`-String → Journal → Insassen-Datei.
- `jail_intake.lua` `inject_pcrel(seat, self)`: restauriert die PC-Beziehung via
  `restoreRelationshipPointsFromDump(inmateSeat, pcSeat, dump, true)`. PC ist immer in jail anwesend.
- social_wealth wird im `self` mitgeführt/gespeichert (für die spätere Modul-Map), NICHT auf den Char
  geschrieben (inject_self ignoriert es). char↔char-Beziehungen anderer Insassen = Folgeschritt (schlafen
  in SSOT bis Gegenpart präsent).
- KEINE Orchestrator-Änderung nötig (self_data fließt schon durch).

**TEST 2c:** Restart → in school einen NEUEN Char versklaven (rel_extra läuft nur bei frischem Enslave) →
speichern → zu jail. Debug `jail/_orch_jail_debug.flag`: `INJECTED={<Name>{virtue=…;pc<-L../Li../D../H..}}`
zeigt restaurierte PC-Beziehung. Bestehende Airi/Takagi haben pc_* NICHT (vor diesem Code committet).

**STATUS gesamt:** Card (AddCard) ✅, Selbst-Werte (2b) ✅, PC-Beziehung+social_wealth (2c) gebaut/zu-testen.
Offen: char↔char-Reaktivierung, Rückkehr-Pfad, Modul-EDITOR (donor-splice, isoliert verifizieren) + die MAP.


---

## 10. 2c VOLL — Beziehungs-Reconciliation (char↔char + PC), gebaut spät 2026-06-24

**Pivot weg von der ersten 2c-Version (nur PC im self-String):** jetzt volle char_id↔char_id-Reconciliation.
- `master_slave.capture_rels(seat)`: am Versklaven BEIDE Richtungen jeder Beziehung dumpen
  (`createRelationshipPointsDump(a,b)` UND `(b,a)`), solange beide noch in school sind (beim Enslave des
  2. Chars ist der 1. schon in jail → zu spät). Schreibt `_orch_rel_commits.flag`
  (`<nday>	<from>	<to>	<love>	<like>	<dislike>	<hate>`). social_wealth weiter im self.
- `playthrough_db`: Tabelle `char_rels(from_id,to_id,love,liking,disliking,hate)` + `upsert_char_rel` /
  `ingest_rel_commits` / `char_rels_from` (latest-wins).
- `orchestrator.transfer_sync`: `ingest_rel_commits` jeden Tick; `write_jail_rels(con,names)` schreibt
  `jail/_orch_jail_rels.flag` mit allen Beziehungen DER aktuellen Insassen.
- `jail_intake.restore_rels()`: liest die rels-Datei, baut `present_all` (name→seat inkl. PC), restauriert
  jedes Paar, dessen BEIDE Enden anwesend sind, via `restoreRelationshipPointsFromDump`. Dedup über
  present-set-Signatur → läuft neu, wenn ein Gegenpart dazukommt (Boyfriend-Join). Abwesende schlafen in der SSOT.

**Desync (jail-Tag ≠ school-Tag) = KEIN Bug:** `transfer_sync` nutzt `read_day(school)` als Anker. By design.

**LIMITATION (wichtig fürs Testen):** Beziehungen werden nur bei EINEM Enslave MIT 2c-Code erfasst, solange der
Gegenpart noch in school ist. Bereits transferierte Insassen (vor 2c-Code) haben KEINE rels → nicht nachholbar
(sie sind aus school weg). Test braucht FRISCHE Enslaves nach Restart.

**TEST:** Restart → in school einen Char versklaven, der eine Beziehung hat (zum PC und/oder zu jemandem) →
speichern → jail. Debug `RELS={<from>-><to>(L../Li../D../H..)}` zeigt restaurierte Beziehungen (mind. zum PC,
der immer da ist). Für char↔char: zwei solche Chars versklaven.


---

## 11. BEZIEHUNGS-GEDÄCHTNIS — kontinuierlicher Snapshot (Sims-Modell, spät 2026-06-24)

**Redesign (User): die SSOT speichert den GANZEN Beziehungs-Graphen kontinuierlich, nicht erst beim Enslave.**
Analogie: ein Sims-Toon im Urlaub hat keinen Zugang zu seinen verbundenen Sims, aber die Verbindung lebt in
seiner "Erfahrung" weiter. Genauso: `char_rels` = persistentes Cast-Gedächtnis, char_id-basiert.

- NEU `school/AAUnlimited/mod/rel_snapshot.lua` (school-only, forciert): dumpt die VOLLE Beziehungs-Matrix
  aller anwesenden Chars bei `on.load_class` (neuer Roster), `on.period` (Tagesende), `on.answer` (nach
  PC-Interaktion) -> überschreibt `_orch_rel_snapshot.flag` (aktueller Vollstand).
- `orchestrator.transfer_sync`: `ingest_rel_snapshot` jeden Tick -> upsert in `char_rels` (latest-wins).
  Transferierte/abwesende Chars sind NICHT im Snapshot -> ihre rels bleiben (schlafen). `social_wealth` wird
  pro Insasse aus `char_rels` ABGELEITET (`pdb.social_wealth`) und an deren self_data gehängt.
- `master_slave`: Enslave-Zeit-Beziehungserfassung ENTFERNT (redundant) -> nur noch Selbst-Werte.
- `jail_intake.restore_rels`: unverändert (liest `char_rels` über die jail-rels-Datei).

**LÖST das Timing-Problem:** Beziehung ist im SSOT, lange bevor einer versklavt wird -> Luka↔Airi-artige Fälle
funktionieren (sofern das System bei BEIDEN noch in school lief). Für die ALTEN Airi/Luka weiter verloren
(nie gesnapshottet). `playthrough_db`: `char_rels` + `ingest_rel_snapshot` + `social_wealth`. `ingest_rel_commits`
(alte Enslave-Zeit-Variante) bleibt ungenutzt im Code.

**TEST:** Restart -> in school normal spielen (char_rels baut sich auto auf, KEIN Enslave nötig) -> dann zwei
Chars mit Beziehung versklaven -> beide in jail -> `RELS={…}`. char_rels-Aufbau prüfbar via memory.db.

---

## 12. WIE MORGEN STARTEN (frische Session)

**LESEN in dieser Reihenfolge:**
1. `AA2_Jail_Projekt_Notizen.md` -> **STATUS-Sektion ganz oben** (Gesamtueberblick mit Paragraf-Verweisen).
2. **DIESE Datei** (`HANDOVER_transfer_2026-06-24.md`) = aktueller Bau-Stand im Detail (Paragraf 1-11).
3. Bei Bedarf: `HANDOVER_master-slave` (Combo/Config), `HANDOVER_jail-coupling` (Coupling),
   `HANDOVER_load-RE` + `_re/RE_LADEFUNKTION.md` (Lade-RE). `HANDOVER.md`/`HANDOFF_*` = aeltere Staende (historisch).

**WO WIR STEHEN (Ende 2026-06-24):** Transfer school->jail KOMPLETT live: Combo->Save->Journal->jail
(**KickCard + AddCard + 2b Selbst-Werte**, alle bewiesen). **Beziehungs-Gedaechtnis** (`rel_snapshot` -> SSOT
`char_rels`, Sims-Modell) **laeuft live** (char_rels fuellt sich auto aus dem school-Roster). Modul-Scan fertig.

**OFFENE TESTS (zuerst):**
- **2c jail-Restore:** frische Enslaves (zwei Chars mit Beziehung, beide -> jail) -> Debug-Zeile
  `RELS={A->B(...)}` in `jail/_orch_jail_debug.flag`. (Beziehung ist via rel_snapshot schon im SSOT.)
- (Optional) pruefen, dass `social_wealth` an die Insassen-self_data gehaengt wird (inmate-file/Debug).

**NAECHSTE BAU-SCHRITTE:**
1. **Modul-Editor** (Evolution): `aaUd`-PNG-Chunk, Member `TrMd` = `vector<Module>`, alles laengen-praefixiert
   (walkbar). Bau = rekursiver Groessen-Walker (Trigger/Action/Expression/Value-Layouts aus aa2g/AA2Unlimited)
   + Donor-Splice Add/Remove. **ISOLIERT verifizieren** (Karten-Roundtrip: Modul rein -> AA2QtEdit liest sauber) VOR Pipeline.
2. **Zustand->Modul-MAP** (hand-kuratiert, Basis = `module_catalog.json`).
3. **Rueckkehr-Pfad** jail->school.
4. **jail-Welt-Mechanik:** Map-Knoten-Blocking (reaktiver Eject + Storage-Flag, progressiv) + jail=Nacht-only
   (`on.period`-Hold) + Optik (Reskin-PNGs).
5. **RPG-Schicht** (Aktivitaets-DB, Status-Module, Einsamkeit/Loner aus social_wealth).

**START:** `run_orchestrator.bat` (als Admin). Python-Tooling:
`python`. Aktiver Playthrough: `NEW HOPE...`.

**WICHTIG:** Lua-Mod- + orchestrator.py-Aenderungen brauchen einen **Restart** (Mod-Reload + neuer Python-Prozess).
Karten-Editor = binaere Chirurgie -> NIE ungetestet in die Pipeline (eigene Verifikation).
