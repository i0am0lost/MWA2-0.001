# HANDOVER — Evolution-Pipeline + Globaler-Pool (Stand 2026-06-25)

> Frische Session ohne Kontextverlust. **Vorher lesen:** `AA2_Jail_Projekt_Notizen.md` (STATUS-Kopf + §4.6/4.7
> + Backlog), dann diese Datei. Verwandt: `EVOLUTION_MAP.md`, `MODULE_CATEGORIZATION.md`, `MOD_CARTOGRAPHY.md`.
> Nutzer = Nicht-Coder, architektonisch sehr scharf, Deutsch/direkt/technisch.

---

## 0. TL;DR — der große Pivot dieser Session
1. **Modul-Applikation hat die Architektur gewechselt:** weg von „Module auf die Karte SCHREIBEN" (SACKGASSE,
   korrumpiert Karten — §3) hin zum **GLOBALEN POOL**: DB ist die Wahrheit, Evolution wird **zentral berechnet**
   (resolver), zur **Laufzeit auf Live-Chars angewandt**, die **Karte wird NIE geschrieben**.
2. **Pipeline gebaut + in-game bewiesen.** Echte H-Aktivität (Kuroda) → DB → Resolver entschied korrekt
   `Kuroda → Corruption` → in `char_state` geschrieben. Der letzte Hop (`apply_state`) hing an einem Gate-Bug,
   der **gefixt** ist. Verifikation nach Neustart steht noch aus (Formalität).

## 1. Die Architektur (globaler Pool) — bewiesen tragfähig
```
Engine-Events → DBs (char_activity · char_rels · char_race_xp)
   → resolver.py (EVOLUTION_MAP-Regeln) → char_state ("aktive Module pro Char")
   → orchestrator write_char_state → _orch_char_state.flag (in BEIDE Welten)
   → apply_state.lua → setzt virtue/Stats auf den LIVE-Char   (Karte unangetastet)
```
**Warum es geht:** AAU-Trigger-System ist **global** (`TriggerEventDistributor`: `loc_triggers`, laufen pro Event
unabhängig vom „Besitzer"). Projekt-These: Verhalten **emergiert aus WERTEN** via AA2-Engine → Werte aus der SSOT
anwenden (bewiesenes `inject_self`-Muster) deckt die Mehrheit. Rassen-Hass = Beziehungs-Injektion auf anwesende
Chars der Rasse (späterer Increment).

## 2. Diese Session gebaut (Dateien)
- **`playthrough_db.py`** — neue Tabellen + Funktionen, **alle unit-getestet**:
  `char_activity` (kum. H-Zähler), `char_race`+`char_race_xp` (Rassen-Achse, Eskalations-Leiter via `race_attitude`),
  `char_state` (Resolver-Output: aktive Module pro Char) + `replace_char_state`/`char_state_of`/`all_char_ids_with_data`.
- **`resolver.py`** (NEU) — das Gehirn. `resolve_char`/`resolve_all` werten EVOLUTION_MAP-Regeln aus (sexuelle Achse
  Corruption→Sex Addict; Rassen-Achse via `race_attitude`). `MODULE_EFFECTS`/`effects_string` = Modul→Wert-Effekt.
  **Unit-getestet.** Schwelle `SEX_CORRUPT=15` (war kurz 1 zum Test, zurückgestellt).
- **`school/AAUnlimited/mod/activity_snapshot.lua`** (NEU, school) — snapshottet kum. H-Zähler pro Char (climax,
  totalH, cumIn*, riskyCum…, über Partner summiert) → `_orch_activity_snapshot.flag`. Erzwungen in forcedconfig.
- **`school/AAUnlimited/mod/apply_state.lua`** (NEU, school) — **der globale Apply-Mod.** Liest `_orch_char_state.flag`,
  setzt pro anwesendem Char die Werte (Muster `jail_intake`/`inject_self`). **Gate-Bug gefixt** (hing am Roster,
  jetzt am tatsächlich-anzuwendenden Inhalt → re-applied auch bei Zustands-Änderung ohne Roster-Wechsel). Erzwungen.
- **`orchestrator.py`** — `import resolver`; `write_char_state(con,ts)` (resolve_all → `_orch_char_state.flag` in
  beide Welten, self-gated); `ingest_activity_snapshot` + `write_char_state` in `transfer_sync` eingehängt.
- **`run_edit.py` + `run_edit.bat`** (NEU) — startet **AA2Edit** (Char-Creator) mit PPeX-Umgebung. AA2Edit braucht
  laufenden PPeX-Server (Assets); standalone crasht es. `run_edit` startet PPeX + Editor, stoppt sauber. **Läuft.**
- **`card_edit.py`** (NEU) — Karten-Modul-**LESER** (funktioniert). Schreiben ist tot, s. §3.
- **Docs:** `MOD_CARTOGRAPHY.md`, `MODULE_CATEGORIZATION.md` (466 Module + `developable` + Race-Subsystem 24×5 +
  HOSTILE-Leiter), `EVOLUTION_MAP.md`, Notizen-Backlog.

## 3. ★ SACKGASSE: Module auf Karten schreiben (dokumentiert, NICHT wiederholen) ★
- `card_edit.py` **liest** Module sauber (PNG-`aaUd`-Chunk → `dMrT`-Member = `[count][selbst-begrenzende Module]`;
  ein Karten-Element ist **byte-identisch zur Definitionsdatei** `data/override/module/<name>`). Leser = solide.
- **Schreiben per Byte-Splice (Definitionsdatei anhängen + count erhöhen + CRC fixen) KORRUMPIERT die Karte.** Grund:
  AAU koppelt Modul-Zustand mit dem **`AUSS`-Member** (AAU-Char-Daten). Corruption-Hinzufügen änderte dort **5 Bytes**
  (Byte 161 = Style-Count=4; + 4 Style-Slots im Schritt-92-Array), die „Update Modules" im Editor pflegt, ein Splice
  aber nicht. **Auch ein style-freies Modul (Blackmailer) zerschoss die Karte.** Symptom: AAU verwirft den ganzen
  `aaUd` → kein Tan/Module, schwarzer Render-Fallback. **Bewiesen** per Diff „game-erzeugte vs. gesplicte 3-Modul-Karte"
  (nur 5 `AUSS`-Bytes Unterschied). Quelle bestätigt das Format (`AAUCardData.cpp`/`Serialize.h`), aber `AUSS` ist der Killer.
- **→ Chirurgisches Modul-Schreiben ist tot.** Der globale Pool (Runtime-Apply) umgeht es komplett. `card_edit.py` bleibt
  als **Leser** nützlich (Inspektion, Katalog).

## 4. Aktueller Test-Stand + Verifikation
- **In-game-Beweis erfasst** (Diagnose-Flags): `_orch_activity_snapshot.flag` hatte Kuroda (climax 11, cumIn* …);
  `_orch_char_state.flag` hatte `Kuroda Katsuki → Corruption (virtue=0)` (+ weitere, da Schwelle kurz=1). Resolver ✓.
- `_orch_apply_debug.flag` war LEER → apply_state hatte (wg. Gate-Bug) nicht angewandt. **Gate gefixt.**
- **Verifikation (offen):** Neustart → `_orch_apply_debug.flag` sollte `applied: Kuroda Katsuki{virtue=0}` zeigen,
  Kurodas virtue=0, Karte unberührt. (Kuroda-Summe ~17 ≥ Schwelle 15 → triggert weiterhin.)
- **Neustart-Hinweis:** `run_orchestrator.bat` **CRASHT** (s. §5 offen) — Neustart über **orchestrator.py direkt**
  (lädt PPeX + Welten + Mods). Lua/Python-Änderungen brauchen Neustart.

## 5. OFFEN / nächste Schritte
1. **Apply nach Neustart verifizieren** (Gate-Fix) — `_orch_apply_debug.flag` `applied:`-Zeile.
2. ✅ **jail-Mirror (apply_state) ERLEDIGT.** `apply_state.lua` nach `jail/AAUnlimited/mod/` kopiert (byte-identisch zu
   school) + in `jail/AAUnlimited/forcedconfig.lua` erzwungen. jail wendet jetzt die Evolution an (korrumpierte Chars
   landen dort). Flag wird schon in beide Welten geschrieben. ⚠️ `apply_state.lua` ist gitignored → beim späteren Push
   `git add -f`. **Offen/Entscheidung:** `activity_snapshot` jail-seitig? (zählt jail-H-Aktivität in dieselbe SSOT —
   aktuell „school only"; nötig, wenn jail-H zur Evolution beitragen soll.)
3. **Debug-Tool** (Nutzer-Wunsch): SSOT-Werte inspizieren/setzen + Engine-H-Stats setzen (zum Tunen + schnell Testen).
   - ✅ **Python-CLI gebaut + getestet:** `debug_tool.py` (+ `run_debug.bat`). Findet die aktive DB automatisch
     (`school/_orch_save.flag` → `_playthroughs/<key>/memory.db`). Befehle: `dump` (Übersicht aller Chars: sexueller
     Score + aufgelöste Module + Rassen-Attitude), `show <name>` (Detail + Resolver-Begründung), `set <name> <metric>
     <value>` (Aktivitäts-Zähler forcieren), `race <name> <race>` + `racexp <name> <other_race> <pos> <neg>` (Rassen-Achse
     — die hat KEINE Live-Erfassung, das ist der einzige Weg sie zu testen), `resolve` (neu auflösen + `_orch_char_state.flag`
     in beide Welten schreiben). UTF-8-Streams (CJK-Save-Pfade).
   - ✅ **Lua-Engine-Setter gebaut (flag-getrieben).** `debug_tool.py force <name> <metric> <value>` schreibt
     `school/_orch_force_activity.flag`; `school/AAUnlimited/mod/debug_force.lua` (in school-forcedconfig erzwungen, DEV-only)
     pollt es (iup-Timer 700ms, Muster `apply_state`), setzt für den **anwesenden** Char den Engine-Zähler via
     `m_characterStatus:m_<metric>(towards,value)` (Setter-Form bewiesen in `triggers_supplemental.lua` Z.443-450), und
     **konsumiert** die Zeile (one-shot; wartet, bis der Char präsent ist). Semantik: Zähler sind pro Partner, Snapshot
     summiert → der Mod nullt die anderen Partner-Slots und legt den vollen Wert auf einen → **Summe = Wert** (vorhersehbar,
     zerstört diese Metrik-pro-Partner-Historie = ok fürs Debug). Fließt Engine → snapshot → char_activity → resolver →
     apply. CLI-Seite getestet (Flag-Format, Metrik-Validierung); Lua **in-game ungetestet** (kein Lua-Compiler lokal).
4. **Race-Capture verdrahten:** `char_race` befüllen (Rasse aus Karten-Modulen, extern an der Tagesgrenze — Module nicht
   Lua-lesbar) + race-xp-Capture (Dominanz→negativ via master_slave, liebevolle H→positiv). DB-Layer steht, Capture nicht.
5. **Wert-Effekt-Modell kalibrieren:** `MODULE_EFFECTS` sind Platzhalter (virtue=0).
6. ✅ **`run_orchestrator.bat`-Crash GEFIXT.** Ursache: der Bat löste `python`/`py` → **Python314**, dessen tkinter
   `init.tcl` nicht findet (Tcl liegt unter `Python314\tcl\…`, gesucht wird `Python314\lib\…`) → `tk.Tk()` (run_ui)
   wirft `TclError` → das `finally: cleanup()` riss alle Welten ab. Direkt-Start lief, weil er Python312 nutzte (tkinter
   intakt). **Zwei Fixes:** (a) `run_orchestrator.bat` zeigt jetzt explizit auf Python312 (wie `run_debug.bat`); (b)
   `run_ui` fällt bei `TclError` auf `run_headless` zurück (Welten bleiben oben, Wechsel per Konsolen-Enter) statt
   abzureißen — `jail_ready_for_current`/`switch_world` dafür auf Modulebene gezogen. Auf 3.12 verifiziert (compile/import/
   `tk.Tk()`).
7. **Loneliness-Regel** (resolver) — braucht Welt-State/Präsenz (Co-Präsenz-Isolation).

## 6. FAKTEN / Umgebung
- **Python fürs Tooling/Tests:** `C:\Users\Henta\AppData\Local\Programs\Python\Python312\python.exe` (3.12.8).
  `py`/`python` im Bash-PATH = Windows-Store-Stub (kaputt). Orchestrator läuft auf `py`/3.14 (stdlib+ctypes).
- **`D:\Games\AA2MiniPPX` = unveränderte Pre-Mod-Backup-Installation → NUR LESEN, nie schreiben** (Memory gespeichert).
- **AAU-Quelle:** github.com/aa2g/AA2Unlimited (`AAUnlimited/Functions/AAUCardData.cpp`, `…/Serialize.h`,
  `…/Shared/TriggerEventDistributor.cpp`, `…/Shared/Triggers/*`). `gh` fehlt im Bash-PATH → WebFetch auf raw-URLs.
- **Editoren:** `AA2QtEdit.exe` = dedizierter Karten-/Daten-Editor (standalone, liest `aaUd` direkt, kein PPeX nötig).
  `AA2Edit.exe` = Char-Creator mit 3D (braucht PPeX + AAU-Laufzeit → über `run_edit`).
- Aktiver Playthrough: **NEW HOPE**. PC = **Cox Robert**.
- Flags (Laufzeit, gitignored): `_orch_activity_snapshot.flag`, `_orch_char_state.flag`, `_orch_apply_debug.flag`.
- Git: getrackte Custom-Mods via `git add -f` (school/ ist gitignored). Push-Ziel `clean`/MWA2-0.001 (Nutzer pusht später).
