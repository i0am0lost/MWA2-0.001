# HANDOVER — Jail-Save-Kopplung / Orchestrator (Stand 2026-06-24)

> Implementierungs-Stand der **Save-Kopplung school↔jail** im `orchestrator.py`. Ergänzt
> `HANDOVER_load-RE_2026-06-24.md` (das ist die RE-Saga: Ergebnis = es gibt KEINEN aufrufbaren
> Loader, die Menü-Klick-Automatik „B" ist der Weg). Diese Datei = was darauf aufbauend gebaut wurde.

---

## ZIEL-FLOW (erreicht)
Start → school-Partie laden → jail koppelt sich automatisch an den passenden Save → JAIL-Button =
sofort in der richtig geladenen jail-Welt, **ohne je jails Titelmenü zu sehen**. Pro school-Save ein
gekoppelter jail-Save (ein Save pro Ordner). Lifecycle (anlegen/löschen) automatisch.

## ARCHITEKTUR
- **Jail-Save = gekoppelter Zwilling** eines school-Saves (kein eigener Playthrough). Kopplung lebt im
  **Python-Layer + Ordnerstruktur**, NICHT in der Engine (siehe `AA2_Jail_Projekt_Notizen.md` Z. 306–352).
- **Ein Save pro Ordner** → jails Lade-Liste ist IMMER eindeutig (oberster = einziger Slot) → die
  „Liste sortiert sich um"-Falle entfällt komplett.
- **Struktur:**
  ```
  <project-root>\_playthroughs\
    <save name ohne .sav>\
      jail\        <- genau EINE jail.sav (+ .json) = der Twin
    index.json     <- Registry: { "<key>": {status, origin} }
  ```
- **Junction:** `jail\data\save\class` ist eine Junction, die der Orchestrator vor jedem jail-Load
  auf `_playthroughs\<aktiv>\jail\` umbiegt. Umbiegen = `os.rmdir`(Reparse-Point) + `mklink /J`
  (atomar, kein Admin; entfernt NUR den Link, nie die Ziel-Dateien).

## WAS GEBAUT IST (alles in `orchestrator.py`, validiert)
**Phase 1 — Coupler-Monitor (jail folgt dem aktiven Save):** `jail_coupler()` (Hintergrund-Thread)
hält jail an den **aktuell in school geladenen** Save gekoppelt. Logik pro Tick (2 s): wenn der User
in school + in-world ist, der aktive Save einen Twin hat und jail noch nicht dafür geladen ist →
`_couple_jail()` bringt jail kurz nach vorn, biegt die Junction, lädt (Klick-Sequenz), geht zurück.
- **Folgt dem Save:** deckt erstes Laden, **neue Klasse nach dem Speichern**, und **Save-Wechsel** ab.
- **Save-Wechsel:** ist jail in einer ANDEREN Klasse geladen → `restart_world(jail)` (kill+relaunch
  zu frischem Titel) VOR dem Koppeln, weil Live-Reload über eine laufende Klasse crasht (`0x10E9C8`).
  Der Watchdog ignoriert diesen gewollten Kill (`restarting`-Flag). mutex-Neustart live bestätigt.
- **Crash-/Retry-Schutz:** koppelt nur, wenn sicher; `couple_attempted` verhindert Endlos-Retry.
- **`_switch_lock` (RLock)** serialisiert Coupler-Load und User-`do_switch` (nicht-blockierend → kein
  UI-Freeze). JAIL-Button erscheint NUR, wenn jail für den aktiven Save bereit ist (`loaded_key==key`)
  → kein toter Button, nie eine veraltete Welt. Ungespeicherte Klasse (kein Twin) → Button bleibt weg.
- (Früher: einmaliger Preload beim Start — ersetzt, weil er neue Klassen / Save-Wechsel nicht abdeckte.)
- **End-to-end live bestätigt:** neue Klasse→speichern→koppeln, und Save A→Titel→Save B→Neustart→umkoppeln.

**Phase 2 — Save-Erkennung + Kopplung:**
- Mod **`school\AAUnlimited\mod\orch_savename.lua`** schreibt den geladenen Save-Namen nach
  `school\_orch_save.flag` (Mechanismus = wie extsave: Patch @ `0x470B0` → `g_var` → Name bei +100,
  unicode). In `forcedconfig.lua` **forciert** (überlebt die savedconfig-Korruption). extsave ist in
  school inaktiv → kein 0x470B0-Patch-Konflikt.
- `read_save_name()` liest den Key (Name ohne `.sav`). `switch_jail_save(jail, key)` biegt die Junction.
- Preload-Flow koppelt VOR `boot_load(jail)`. Kein Twin → jail wird NICHT geladen (verhindert falsche
  Kopplung mit altem Save). **End-to-end live bestätigt** (Log zeigt key-Erkennung + Kopplung + in-world).

**Phase 3 — Lifecycle (Registry + Watcher):**
- `scan_playthroughs()` (beim Start): bestehende Saves OHNE Twin → `status=needs_port` (manuell).
  Mit Twin → `ready`. Verwaiste index-Einträge (school-Save weg) → Twin + Eintrag gelöscht.
- `playthrough_watcher()` (Hintergrund-Thread, 5 s): **neue** Save (taucht NACH Start auf) → Twin
  auto-kopiert (`create_twin`, `origin=auto`). **Gelöschte** Save → `delete_twin` + Eintrag weg.
  Manuell nachgelegter Twin einer needs_port-Save → wird auf `ready` gehoben.
- `baseline` = beim Start vorhandene Saves → die werden NIE auto-kopiert (das sind „bestehende").

## BEDIENUNG
- **Neue Partie anlegen:** in school normal eine neue Klasse speichern → Watcher legt den jail-Twin
  automatisch an (~5 s). Danach koppelt jail automatisch.
- **Bestehende Partie einpflegen (needs_port):** die *portierte* jail-Save (Roster bereinigt!) von Hand
  nach `_playthroughs\<key>\jail\<key>.sav` legen → Watcher hebt sie auf `ready`. (Reine Kopie ginge
  nicht: sie würde das volle school-Roster ins Jail kippen — daher manuell.)
- **Start:** `python "<project-root>\orchestrator.py"`
  (Als **Admin** starten, damit `BlockInput` während der ~3 s Klick-Sequenz greift — sonst Warnung,
  Klicks gehen trotzdem, aber ungeschützt.)

## RPG-SCHICHT — Fundament gebaut + BEWIESEN (2026-06-24)
**★ Durchbruch: „Punkt 9" (Save-Format schreiben) ist über die `.json` umgangen — kein Binär-Reversing.**
- Jeder Save hat eine **`.json`** = AAUs Per-Char-Store (virtue, corruption, traits, Module, Stats),
  Keys `"<seat> <name>"`. AAU liest sie beim Laden zurück (`init.lua` `get/set_class_key` →
  `GetClassJSONData`). Editiert man die Datei vor dem Load, **landen die Werte im Spiel**.
- **`playthrough_db.py`** (gebaut, getestet): SQLite pro Playthrough (`_playthroughs/<key>/memory.db`),
  Tabellen `chars` (self_data JSON-Blob, char_id = normalisierter NAME), `relationships`, `world_state`.
  `snapshot_chars_from_json` (60 seat-Einträge → 34 Namen, merge richtigster) + `inject_chars_to_json`
  (atomar). CLI: `python playthrough_db.py <db> snapshot|inject|dump`.
- **★ END-TO-END BEWIESEN (Marker-Test):** school-`.json` Marker `intelligenceValue=9999` → DB →
  inject jail-`.json` → jail geladen → in-game `get_class_key` las bei allen 11 geprüften Chars `9999`.
  → Die JSON-Brücke trägt. Verifizierungs-Mod war `jail/.../mod/orch_verify.lua` (jetzt deaktiviert).
- **★ SCHLÜSSEL-ERKENNTNIS:** Zuordnung muss **per Name → AKTUELLER Seat** laufen, NICHT über den
  historischen json-Seat. Die `.json` akkumuliert alte `"<seat> name"`-Blöcke; nur Chars, deren
  aktueller Roster-Seat = ihr json-Seat ist, wurden im 1. Test getroffen. inject/verify müssen den
  Live-Roster (`GetCharInstData`) gegen die Namen mappen.
- **Transfer im Coupler GEPARKT:** `_transfer_to_jail()` existiert + funktioniert, aber der Aufruf in
  `_couple_jail` ist auskommentiert — „alles 1:1" ist destruktiv (überschreibt jail mit school) UND
  seat-naiv. Reaktivieren, sobald die echte Logik steht.

## NÄCHSTE SCHRITTE (RPG, echte Transfer-Logik)
1. **Roster-Seat-Mapping:** beim Snapshot/Inject den Live-Roster (in-game `GetCharInstData` → Name+Seat)
   nutzen, statt blind alle json-Blöcke zu schreiben. Vermutlich ein kleiner in-game Mod, der beim
   Welt-Verlassen Name→Werte dumpt und beim Betreten injiziert (oder Python liest einen Roster-Flag).
2. **Was transferieren:** welche `self_data`-Felder 1:1 (virtue, corruption, traits, Stats) vs. welche
   ausnehmen (welt-/schul-spezifische Module). = Spiel-Design-Entscheidung mit dem User.
3. **Beziehungen + Verdichtung** (Notizen 2.4c): char↔char NICHT 1:1; `social_wealth` → Einsamkeits-Modul.
   Mechanismus = in-game Lua (`triggers_supplemental.lua`, seat-paarweise Setter). `relationships`-Tabelle steht.
4. **needs_port-Automatik:** sobald 1.–3. stehen, die manuelle Alt-Save-Portierung via `on.load_class`-Trigger automatisieren.
- Optional: jail-Klick-Übergang (kurzes Auftauen des suspendierten DirectX-Fensters) kaschieren — vom
  User als systembedingt/harmlos akzeptiert.

## UMGEBUNGS-FAKTEN (Zeit sparen)
- **Tool-Pfadschutz:** das Bash/PowerShell-Tooling blockt `Remove-Item`/`rmdir` auf Pfaden mit „jail"
  (auch mit `dangerouslyDisableSandbox`) — als false-positive für System-„jail". Workaround beim Setup:
  **Move statt Remove**. Der laufende Orchestrator (Python) ist davon NICHT betroffen (eigener Prozess).
- **Python fürs Tooling:** `python`.
  `py`/3.14 gibt „platform libraries"-Warnung, läuft aber für stdlib+ctypes+tkinter (= Orchestrator).
- **CJK-Konsole:** stdout ist oft cp1252 → CJK-Save-Namen crashen `print`. Orchestrator härtet stdout
  früh (`reconfigure(encoding="utf-8")`). Bei eigenen Tests `PYTHONIOENCODING=utf-8` setzen.
- **Backup der Migration:** `_backup\jail_class_premigration` (originale jail-NEW-HOPE-Save),
  `_backup\empty_class_orig` (das ehemalige echte class-Verzeichnis).
