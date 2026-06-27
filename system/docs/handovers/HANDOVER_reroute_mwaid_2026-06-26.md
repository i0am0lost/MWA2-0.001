# HANDOVER — Module Reroute Hook + stable mwa_id + SSOT re-key (2026-06-26, spät²)

> Frische Session. **Vorher lesen:** `AA2_Jail_Projekt_Notizen.md` (STATUS-Kopf), dann diese Datei.
> Vorgänger (geschlossen): `HANDOVER_confinement_2026-06-26.md`.
> Nutzer = Nicht-Coder, architektonisch sehr scharf, Deutsch/direkt. Denkt vorausschauend (z.B. „Namen sind
> mutierbar → eigene ID"). Korrigiert hart, zu Recht.

## ★★ ARCHITEKTUR-KORREKTUR (Nutzer, Ende der Session) — VOR ALLEM ANDEREN LESEN ★★
**Karten werden NIE verändert.** Sie sind reine, teilbare BASIS-Daten, nur zum Laden für die Engine. Wir stempeln
NICHTS drauf (keine id, keine Module). Grund: Karten werden mit Leuten OHNE unseren Mod geteilt — jede Bit-Änderung
macht die Karte für die kaputt. **Alles Unsere liegt extern in der SSOT.**
- ❌ Damit sind FALSCH (und für die Basis-`.png`s bereits zurückgesetzt): `mwa_id`-Global auf Karten, Confinement-
  Splice in `.sav`/`.png`. Die in §1/§2 beschriebene „mwa_id-auf-Karte"-Persistenz ist VERWORFEN.
- ✅ RICHTIG bleibt: der Reroute-Hook ändert die Modul-Liste nur **in-memory beim Laden** (Karten-Datei unangetastet).
  Die SSOT (memory.db, auf mwa_id umgekeyt) ist extern und ok. Die RE-Fakten in §2 (RVAs, Layout, native Calls) gelten.

**Korrigiertes Identitäts-Modell — „aktives Roster":** Jedes Save startet LEER; das Roster wird per `AddCard` aus
Basis-`.png`s GEBAUT (`jail_intake` macht das schon: liest `_orch_jail_inmates.flag` = `name\tcardfile\tgender`).
Weil WIR das Roster bauen, kennen WIR pro Karte: **Basis-cardfile → (SSOT) mwa_id → Module/Erfahrungen** — ohne id
von der Karte zu lesen, ohne Sitz (Sitz = nur transienter Handle). Dieselbe Basis-Karte ist in verschiedenen
Playthroughs ein anderer evolvierter Char. Verlässt ein Char das Roster → Daten auf Eis in der DB (per id); kommt die
Karte zurück → alte Erfahrungen + neue. `mwa_id` bleibt interner SSOT-Schlüssel, **verlinkt vom cardfile**, nicht gestempelt.

**Nächster Bau (Zielsystem):** (1) chars.cardfile als Link einführen; (2) Orchestrator emittiert pro Inmate
`cardfile→mwa_id→module-liste`; (3) `jail_intake` setzt VOR jedem `AddCard` den Kontext (cardfile/id/module),
der Hook liest diesen Kontext (gleicher Lua-Prozess, KEIN Karten-Stempel) und wendet die Module in-memory an;
(4) Zielbild: leere-Start-Saves (Nutzer testet mit frischem Save + Test-Chars). Details: [[char-id-one-ssot]].

---

## 0. TL;DR — der große Sprung dieser Session (Hook-Mechanik gilt; Persistenz-Teil s. Korrektur oben)
Der Nutzer wollte **kein** Per-Karten-Editieren, sondern einen **Mod, der die Karten-Modul-Liste zur Laufzeit
umleitet**: Karten-Module = nur „Wunsch"/SSOT-Seed, danach fährt in-game **unsere zentral gepflegte Liste**.
Das ist **gebaut und in-game bewiesen** — plus eine rename-stabile eigene Identität (`mwa_id`) und die SSOT
darauf umgekeyt.

## 1. Was BEWIESEN funktioniert (in-game verifiziert)
- **Reroute-Hook** (`jail/AAUnlimited/mod/module_reroute.lua`, jail-forcedconfig): hookt AAUs eigene
  `AAUCardData::UpdateModules` (DLL-RVA 0x154CF0) via `mod/memory.lua`-`hook_func`. Liest/schreibt die Live-
  Modul- und Global-Liste jeder Karte beim Laden, VOR `InitOnLoad` (→ Trigger werden aktiviert).
  - **Confinement via Hook bewiesen:** Stage Luka (Karte nicht splicebar) wurde NUR per Hook-`AddModule`
    confined → lief zur Station (39). = Lesen+Schreiben+Aktivierung end-to-end.
- **Stabile `mwa_id`** (rename-/editor-/transfer-fest): INT-**Global Variable** „mwa_id" auf der Karte.
  - Offline geschrieben (`card_globals.py` für .png, scratchpad `sav_tag_id.py` für .sav-eingebettete Karten).
  - Hook liest sie pro Karte korrekt: **Shimizu=1001, Takagi=1002, Luka=1003** (Round-Trip bewiesen).
- **SSOT umgekeyt** (`memory.db` migriert + `playthrough_db.py` API): mwa_id auf allen char-Tabellen,
  `ensure_mwa_id`/`mwa_id_of`/`name_of`/`rename_char`, `confined_mwa()`→{id:cell}. **Rename-Resilienz bewiesen.**

## 2. HARTE FAKTEN (alle live verifiziert; AAUnlimitedDll.dll = RELEASE x86, ImageBase 0x10000000, reloziert)
- **RVAs** (aus `.pdb` via scratchpad `pdb_rva.py`): UpdateModules=0x154CF0 (`__thiscall void(void)`),
  AddModule(wchar_t*)=0x14CEC0 (`bool`, braucht VOLLEN Pfad: `GetAAPlayPath().."data\\override\\module\\<name>"`,
  Bool in AL → `(eax&0xff)~=0`), RemoveModule(int)=0x14D290.
  DLL-Basis: `GetModuleHandleA("AAUnlimitedDll.dll")`; native Calls via `proc_invoke(addr, this, ...args)`.
- **AAUCardData-Layout** (wstring=24): m_globalVars vec@**0x24**, m_modules vec@**0x3C**, m_cardStorage map@0x48.
  sizeof(Module)=**84** (name@0,desc@24,triggers@48,globals@60,deps@72). sizeof(GlobalVariable)=**0x34**
  (id@0,type@4,name@8,defaultValue@0x20,currentValue@0x28[type@0x28,iVal@0x2C],initialized@0x30).
  wstring lesen: size@+16, res@+20, inline iff res<8 sonst ptr@+0.
- **aaUd on-disk** (Tags byte-reversed): TrGv=`vGrT`, TrMd=`dMrT`, TrAt=`tArT`. Member=[tag][serialized], KEIN
  Längen-Präfix. GlobalVariable=[u32 type][wstr name][Value default][Value current][u8 init]; Value=[u32 type]
  [INT i32/BOOL u8/FLOAT f32/STRING wstr]; `id` NICHT serialisiert. **Insert-Trick:** serialisiertes Element
  direkt nach dem Vektor-Count splicen + Count++ (kein Parsen nötig), dann PNG/sav-Chunk Länge+CRC32 fixen.
  .sav: eingebettete Karten sind echte PNGs mit aaUd-Chunk; KEIN äußeres Längenfeld → selbst-begrenzend bis IEND.
- AAUs eigene `aaUd`-CRCs sind ohnehin ungültig (Engine parst per Länge) — „bad CRC" ist normal.

## 3. STATUS — Phasen 1–3 ALLE FERTIG + in-game bewiesen (2026-06-26)
- **Phase 2b DONE:** `playthrough_db.py` auf mwa_id umgekeyt (`_migrate` self-heal in connect, `ensure_mwa_id`/
  `mwa_id_of`/`name_of`/`rename_char`, alle Writes füllen mwa, `confined_mwa()`). Rename-Resilienz bewiesen.
- **Phase 3 DONE:** `orchestrator.write_reroute()` schreibt `_orch_reroute.flag` (`<mwa_id>\t<mods>`, beide Welten)
  aus der Resolver-Ausgabe; `module_reroute.lua` v3 liest die Karten-`mwa_id` → schlägt nach → `AddModule` (additiv).
  In-game bewiesen: Luka (1003, keine gesplicte Karte) confined REIN flag-getrieben; Log `desired={Confinement}
  applied={Confinement}`. Volle Kette memory.db→resolver→flag→hook→in-game läuft, rename-fest.

### NÄCHSTER SCHRITT — voller Karten-Tag-Bootstrap (Haupt-Lücke)
Aktuell sind nur die 3 Inmates in der jail-`.sav` korrekt getaggt; PC + Schüler haben Platzhalter-IDs 1900-1910
→ matchen das Flag nicht (PC kriegt z.B. kein Sex Addict, obwohl im Flag). **Alle Chars mit ihrer ECHTEN
DB-`mwa_id` taggen** (school-Karten/.sav + jail-.sav Platzhalter ersetzen). `mwa_id` pro Char = `pdb.mwa_id_of`.
Identifikation der .sav-Blöcke: per Modul-Signatur (wie `sav_tag_id.py`) oder Namen aus dem `.json`-Sidecar.
Danach: (a) Orchestrator-Live-Flag verifizieren (`write_reroute` feuert bei school-save), (b) optional
**clear+replace** (`RemoveModule(0)`-Schleife + AddModule = „Karten-Module ignorieren"; ID-Global bleibt erhalten,
orthogonal), (c) resolver-Schwellen kalibrieren, (d) redundante Confinement-Splices zurücksetzen (Hook macht's;
Backups `_backup/*.preid.*`).

## 4. Diese Session geänderte/neue Dateien
- **`jail/AAUnlimited/mod/module_reroute.lua`** (NEU) — der Hook. v2.1 aktiv (additiv Confinement + Globals/mwa_id-
  Read). Versions-Leiter im Datei-Kopf. In `jail/AAUnlimited/forcedconfig.lua` eingehängt.
- **`card_globals.py`** (NEU) — read/insert card Global Variable (TrGv) in .png aaUd.
- **`playthrough_db.py`** — mwa_id re-key (Migration in connect, Resolver, alle Writes füllen mwa).
- **`card_edit.py`** (vorhanden) — add/remove Module in .png (genutzt für Confinement-Splice; jetzt redundant).
- Scratchpad (Werkzeuge, ggf. in Repo ziehen): `pdb_rva.py`, `sav_splice.py` (Modul-Splice .sav),
  `sav_tag_id.py` (mwa_id in .sav), `migrate_mwaid.py` (DB-Migration), `install_confine.py`.
- **Karten/Save getaggt:** `.sav` (alle 11 Blöcke: Inmates 1001-1003, andere Platzhalter 1900-1910) +
  3 Inmate-`.png`s (1001/1002/1003) + Confinement in Shimizu/Takagi `.sav`/`.png` (TrMd).
- Backups in `_backup/`: `memory.preidkey.bak.db`, `NEW HOPE_class.preid.sav` / `.bak.sav`, `*.preid.png` / `*.bak.png`.

## 5. OFFENE PUNKTE / Warnungen
- **Platzhalter-IDs 1900-1910** in den 8 Nicht-Inmate-`.sav`-Blöcken sind throwaway (die Schüler werden in jail
  gekickt; ihre echten Karten in school sind UNGETAGGT). Beim vollen Bootstrap: alle 34 Chars per DB-mwa_id taggen
  (school-Karten/.sav), inkonsistente Platzhalter ersetzen.
- **Redundante Splices:** Confinement-Modul-Splices in Shimizu/Takagi `.sav`+`.png` sind jetzt überflüssig (Hook
  macht's). Optional auf pristine zurücksetzen (Backups da), damit Karten unangetastet sind (Architektur-Ideal).
- **Reroute-Mod nur jail-seitig.** Für school/evolution später auch dort einhängen.
- **resolver/orchestrator** noch name-gekeyt (rückwärtskompatibel) — Phase 3 fügt das mwa-Flag hinzu.
- Confinement-Modul ist Stufe-1 (flaglos, „NPC≠PC, room≠39 → MoveToRoom 39"). Flag-gegate Stufe-2 später.

## 6. FAKTEN / Umgebung
- Python: `C:\Users\Henta\AppData\Local\Programs\Python\Python312\python.exe`. Bei japanischen Pfaden
  `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` setzen (cp1252-Konsole crasht sonst).
- Playthrough: **NEW HOPE** (`_playthroughs\NEW HOPE学園1年1組\memory.db`). PC=Cox Robert (mwa_id 1006).
  Inmates: Shimizu Airi(1001), Takagi Saya(1002), Stage Luka(1003). Zelle=Raum 39.
- Mod-Code wird nur bei **Prozess-Start** gelesen → für neuen Mod-Code jail komplett neu starten (nicht nur Reload).
- Hook-Debug-Log: `jail/_orch_reroute_debug.flag` (wird pro Class-Load neu geschrieben).
- Recherche-Subagent-Befunde (AAU-Quelle) sind in den Memory-Notes verdichtet: [[module-load-chain-and-reroute-hook]].
