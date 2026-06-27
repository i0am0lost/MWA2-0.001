# HANDOVER — Confinement + SSOT-Modul-Steuerung (Stand 2026-06-26, spät)

> Frische Session. **Vorher lesen:** `AA2_Jail_Projekt_Notizen.md` (STATUS-Kopf + §4.6!), dann diese Datei.
> Verwandt (geschlossen): `HANDOVER_module_format_RE_2026-06-26.md` (Modul-Format geknackt + ID-Katalog).
> Nutzer = Nicht-Coder, architektonisch sehr scharf, Deutsch/direkt. Korrigiert hart wenn was falsch ist — zu Recht.

---

## 0. TL;DR — wo wir feststecken
Die **komplette Python/Lua-Pipeline funktioniert** (SSOT → char_state → apply_state ruft `setCardStorage`,
per Flag bewiesen). **ABER das Confinement-Modul greift in-game NICHT** — NPCs laufen frei, keiner geht in
die Zelle (Raum 39). Zwei Ursachen isoliert; der **entscheidende offene Test**: das Modul **auf eine Karte
installieren** (AA2QtEdit „In Use") → klärt, ob Module geladen werden müssen oder global laden.

## 1. Das KERN-PROBLEM (hier ansetzen)
**Confinement-Modul (`jail/data/override/module/Confinement`, von uns generiert) wirkt in-game nicht.**
Zwei getrennte Ursachen gefunden:

**(A) Card-Storage-Inkompatibilität** — betrifft die *flag-gegated* Version (Stufe 2):
- Engine-Action „Set/Get Card Storage" (Actions.cpp) nutzt `inst->m_cardData.GetCardStorage()[key]`.
- Unsere Lua `setCardStorage` (`triggers_supplemental.lua:309`) schreibt in **Class Storage** unter
  `"<seat> <forename> <surname>"` — **andere Stelle**. Das Modul liest die Engine-Card-Storage → sieht
  unsere Flags nie → `confined` bleibt false.
- Lua-cruft Wiki: **keine** dokumentierte Lua-API für die Engine-Card-Storage. Wege: raw memory (`poke`),
  ODER **Class Storage als gemeinsamer Kanal** (Lua `set_class_key` + Modul-Expression „Get Class Storage
  Bool/Int" BOOL46/INT121, char-Name als Key), ODER undokumentierte init.lua-API.

**(B) Modul lädt nicht** — betrifft AUCH die *flaglose* Stufe-1-Version:
- Stufe-1-Modul (kein Card Storage: „NPC≠PC, room≠39 → MoveNpcToRoom(39)") greift **ebenfalls nicht**.
- → Schließt (A) als alleinige Ursache aus. Stärkster Verdacht: **ein Modul in `data/override/module/`
  feuert nur, wenn es auf mind. einer Karte „In Use" ist.** „Alle Module laden immer" gilt für die schon
  auf den Karten installierten, NICHT für unser neues.
- Init-Trigger (Event 6 = Card Added) hinzugefügt — **alle** echten Module haben einen — greift trotzdem nicht.

**★ NÄCHSTER SCHRITT (offen, vom Nutzer auszuführen):** Confinement via **AA2QtEdit** auf **eine** jail-NPC-
Karte (z.B. Shimizu Airi) „In Use" schieben → speichern → jail neu laden. Geht sie dann zu Raum 39?
- ✅ → Module müssen installiert werden. Echter Weg = **§4.6: einmal auf alle Karten vorinstallieren**,
  dann SSOT-Flags steuern (+ Ursache A für die Flag-Version lösen).
- ❌ → Modul ist strukturell nicht ladbar (trotz Codec-Roundtrip) → dort weitergraben (Init/Globals/Format).

## 2. Was BEWIESEN funktioniert (nicht nochmal anfassen)
- **apply_state v1:** `virtue=0` auf Live-Char, read-back-verifiziert.
- **Modul-Format-Codec** (`module_format.py`): 932 Dateien byte-exakt decode+encode.
- **SSOT→Card-Storage-Brücke (Python/Lua-seitig, voll):** `confine` → `memory.db` → resolver →
  `char_state.flag` mit `@b:confined=1;@i:cell=39` → apply_state ruft `setCardStorage` (apply_debug zeigt
  `applied: Shimizu Airi{@b:confined=1;@i:cell=39}`). Die Brücke ist NICHT das Problem — nur ihr Ziel (A).
- **Auto-Confine:** Orchestrator confined alle jail-residents (Shimizu Airi, Stage Luka, Takagi Saya) zu 39.

## 3. ★ ARCHITEKTUR-REGELN (vom Nutzer hart korrigiert — einhalten!) ★
- **char_id-basiert, NIE Seat.** Identität = normalisierter Name. NPC hat in school/jail verschiedene Seats.
  Seat ist nur Laufzeit-Handle. (Notizen §2.4d.)
- **EINE `memory.db` pro Playthrough**, von allen Welten geteilt. KEINE welt-spezifischen redundanten DBs/Flags.
  (Mein Fehler war eine separate `_orch_confine.flag` — entfernt, jetzt `char_confine`-Tabelle in der einen DB.)
- **Module: vorinstalliert auf Karten + storage-gegated (§4.6).** SSOT verteilt NUR die Flags. Die Karten-
  Modul-Liste ist Träger; die SSOT ist die Wahrheit. „Egal was auf der Karte ist" = die Flags steuern, nicht
  die Karten-Auswahl. (Genau deshalb scheitert unser nicht-installiertes Modul.)
- **jail = ALLE Inmates confined** (Definition von jail). Nicht selektiv. Der jail-Roster = nur Inmates + PC.
- **PPeX ist irrelevant** fürs Confinement (streamt nur Assets, fasst Card Storage/Logik nie an).

## 4. Diese Session gebaut/geändert (Dateien)
- **`module_authoring.py`** — Builder auf `module_format`. `build_confinement(cell)` = Stufe-1 (kein Flag,
  +Init-Trigger), `build_confinement_gated()` = Stufe-2 (liest Card Storage `confined`/`cell`). IDs verifiziert:
  Event16 RoomChange/Event6 CardAdded · Action20 NpcMoveRoom/2 If/24-27 SetCardStorage · Expr INT9/10/55/97,
  BOOL4/8/13/24, INT24 GetCardStorageInt.
- **`playthrough_db.py`** — `char_confine(char_id,cell,ts)` Tabelle + `set_confine`/`clear_confine`/
  `all_confined`/`confine_of`. char_id-keyed, in der EINEN memory.db.
- **`resolver.py`** — `resolve_char` fügt `("Confinement","confine")` wenn confined; `cardstorage_string(con,
  char_id)` → `@b:confined=1;@i:cell=N` (`@b:`=Bool, `@i:`=Int Card-Storage-Konvention).
- **`orchestrator.py`** — `JAIL_CELL=39`; `transfer_sync` auto-confined alle jail-residents (vor write_char_state)
  + released Nicht-Residents; `write_char_state` kombiniert `effects_string`+`cardstorage_string`.
- **`*/AAUnlimited/mod/apply_state.lua`** (beide Welten, identisch) — `inject` setzt jetzt auch `@b:`/`@i:`
  Felder via `setCardStorage` (neben virtue/stats). Separate confine-flag-Logik wieder ENTFERNT.
- **`debug_tool.py`** (+`run_debug.bat`) — CLI: `dump/show/set/race/racexp/resolve/force/confine/unconfine`.
  `confine`/`unconfine` schreiben in `char_confine` (memory.db). `resolve` schreibt char_state inkl. @-Flags.
- **`jail/.../mod/jail_phase.lua`** — Zeitphasen: lenkt Club(7)→End(8). ⚠️ greift in-game auch noch nicht
  (debug-flag leer) — SEPARATES offenes Thema (Tag startet nicht zur passenden Zeit).
- **`jail/.../mod/jail_probe.lua`** — read-only Recon (Räume + m_forceAction-Erreichbarkeit). DEV, kann raus.
- **`debug_force.lua`** (school) — Engine-H-Stats per Flag setzen (Test-Beschleuniger).
- **`jail/data/override/module/Confinement`** — generiertes Modul (Stufe-1 + Init, 516 B). NUR jail.
- **Frühere Fixes:** `run_orchestrator.bat`→Python312 + `run_ui`→`run_headless`-Fallback (Bat-Crash war Tcl);
  apply_state nach jail gespiegelt + forciert.

## 5. WEITERE OFFENE PUNKTE
- **jail_phase** (Club→End) greift in-game nicht — Tag startet nicht zur passenden „in game time". Debug-flag
  leer (kein Redirect gesehen). Nach dem Confinement angehen.
- **Card-Storage-Brücke (Ursache A)** für die flag-gegate Stufe-2 / alle künftigen selektiven Status-Module
  (Prisoner/broken/trainer) — sobald „Module müssen installiert werden" geklärt ist.
- **Schwellen/Effekte kalibrieren** (resolver MODULE_EFFECTS = Platzhalter).

## 6. FAKTEN / Umgebung
- Python-Tooling: `C:\Users\Henta\AppData\Local\Programs\Python\Python312\python.exe` (3.12.8). Orchestrator
  via `run_orchestrator.bat` (zeigt jetzt auf Python312).
- Aktiver Playthrough: **NEW HOPE** (`_playthroughs\NEW HOPE学園1年1組\memory.db`). PC = **Cox Robert**.
  jail-Inmates: Shimizu Airi, Stage Luka, Takagi Saya. Zell-Raum = **39** (Outside Station).
- `D:\Games\AA2MiniPPX` = read-only Pre-Mod-Backup. AAU-Quelle via WebFetch (raw.githubusercontent.com),
  `gh` fehlt im Bash-PATH. `AA2QtEdit.exe` = standalone Karten-Editor (pflegt AUSS sicher; kein PPeX nötig).
- Flags (gitignored, Laufzeit): `_orch_char_state/apply_debug/activity_snapshot/probe/phase_debug.flag` etc.
- school/jail-Mods + Module via `git add -f` (gitignored). Nutzer pusht später.
