# HANDOVER — AA2 „Jail"-Projekt — Stand 2026-06-23 (für die nächste Session)

> **Das ist die „Start-hier"-Datei.** Lies in dieser Reihenfolge:
> 1. **DIESE Datei** (Gesamt-Stand, deine Wünsche, was erfüllt/machbar/nicht, wo wir stehen).
> 2. `<project-root>\AA2_Jail_Projekt_Notizen.md` — kanonisches Design-Doc (volle Konzept-/Befund-Historie).
> 3. `<project-root>\_re\RE_LADEFUNKTION.md` — vollständiges Reverse-Engineering-Protokoll (Lade-Funktion).
>
> **Nutzer:** Nicht-Coder, architektonisch sehr scharf. **Stil:** Deutsch, direkt, technisch, keine Anfänger-Erklärungen.
> **Projektort:** `<project-root>` (NICHT das Session-cwd `<unrelated-project>` — das ist ein fremdes Finanzprojekt).

---

## 1. WAS DAS PROJEKT IST
Ein zweiter „Jail"-Modus (und generisch: mehrere Welten) für **Artificial Academy 2** (AAUnlimited-Mod-Framework).
Mehrere vorgeladene Spiel-Welten, **Sofort-Switch** dazwischen, persistente Char-Entwicklung über eine DB.
**Endprodukt:** EIN Installer, der beim Nutzer alles einrichtet (alle Laufzeiten gebündelt, Nutzer installiert nichts).

Ordner: `AA2MiniPPX` (21 GB Original, unberührt), `MWA2\school` + `MWA2\jail` (je 21 GB Kopien = die zwei Welten).
Spiel = `AA2Play.exe` (32-bit) je Welt. Mods/PPeX bereits installiert.

---

## 2. DEINE WÜNSCHE (wie geäußert) — STATUS: erfüllt / machbar / nicht

| # | Dein Wunsch | Status | Anmerkung |
|---|---|---|---|
| 1 | PPeX behalten (sonst Mod-Verlust) **und** Sofort-Switch | ✅ **erfüllt** | PPeX `single-client` → von uns auf **multi-client gepatcht** (gebaut+getestet). |
| 2 | Ein Startpunkt → beide Welten vorgeladen, jail automatisch mit, versteckt | ✅ **erfüllt** | `orchestrator.py`: startet Server + beide Welten, jail versteckt+eingefroren. |
| 3 | Hintergrundwelt soll **pausieren** (kein Doppel-Sound) | ✅ **erfüllt** | inaktive Welt wird **suspendiert** (`NtSuspendProcess`) → kein Sound/CPU, Resume sofort. |
| 4 | Launcher-Mods/Scripts NICHT umgehen | ✅ **erfüllt** | Mods laden normal aus `savedconfig.lua`, unabhängig vom Auto-Launch. |
| 5 | Deppensicheres Beenden | ✅ **erfüllt** | q / Ctrl+C / Terminal-zu / Fenster-X / Crash → Watchdog räumt alles auf, keine Geister-Prozesse. |
| 6 | Alles auf Englisch (international) | ✅ **erfüllt** | Orchestrator-Ausgaben + internes Tool-Signal Englisch. |
| 7 | JAIL-Button am Heim-Screen (neben „sleep"), nur dort | ✅ **erfüllt** | Overlay-Button (nur Phase 9). Bug „zeigt am Menü" → **gefixt** (nur frisches Period-Flag zählt). |
| 8 | Welt-Orientierung (welche Welt bin ich?) | ✅ **erfüllt** | dauerhaftes farbiges Label oben (school blau / jail rot). |
| 9 | Beim Switch **direkt in der jail-Welt** landen (kein Dev-Logo/Menü) | 🔶 **gebaut, Tuning offen** | Siehe Abschnitt 4 (Boot-Auto-Load). **Wichtige Einschränkung:** „NIE ein Menü" geht nicht 100% — siehe #not-feasible. |
| 10 | Save-Kopplung: school-Save erkannt → passendes jail laden | 🔶 **halb** | Lade-Mechanismus gebaut (Menü-Automation). Erkennung school→Flag→Mapping noch NICHT gebaut (Mapping = triviales Python). |
| 11 | Geteilte Basis (ein ppx, nicht 3× dupliziert) | ⬜ **geplant** | Per Junction (`mklink /J`). Noch nicht gebaut (aktuell 3×21 GB). |
| 12 | Ein Installer, alles gebündelt (Python etc.), läuft durch | ⬜ **geplant** | Design steht (PyInstaller + self-contained PPeX). Noch nicht gebaut. |
| 13 | Optik pro Welt (jail sieht anders aus) | ⬜ **geplant** | Asset-Layer (Override/Shadow-Set). Du akzeptierst „sieht noch wie Wohnung aus" bis dahin. |
| 14 | Tägliche Hintergrund-Entwicklung der Welten (Erinnerung) | ⬜ **geplant** | DB-Resolver (Python). Engine schläft; Lua liest/schreibt Play-Data. Tools dafür existieren (s. Notizen). |

### NICHT machbar / harte Grenzen (wichtig zu wissen)
- **Save mitten im Betrieb hot-swappen** (laufende jail-Klasse auf anderen Save umladen) → **CRASHT** (RE-bewiesen, globaler Manager dangling). **Lösung: Kill+Restart** der Instanz (Sekunden).
- **Cold-Load per direktem Funktionsaufruf** (Save laden ohne Menü-Klick) → **nicht praktikabel** (RE-bewiesen: am Menü ist der Container leer, Load ist tief in die Event-/Menü-Zustandsmaschine eingebettet). **Lösung: den spiel-eigenen Menü-Load EINMAL beim Boot per UI-Automation auslösen.**
- **„Komplett ohne Menü/Logo"** → **nicht 100%**: das gerenderte Menü muss zum Klicken sichtbar+vorn sein → man sieht beim Boot **einmal kurz** das automatische Laden je Welt. Danach sind alle Switches sauber in-world.
- **Roster-Cap 25 / keine neue Map-Geometrie / keine neuen Aktions-Verben** → harte Engine-Grenzen (Workarounds im Konzept: DB-Rotation, Reskin, Umwidmung).

---

## 3. WAS GEBAUT IST (Dateien)
| Datei | Zweck | Status |
|---|---|---|
| `orchestrator.py` | **Runtime-Orchestrator** (Python 3, nur stdlib+ctypes) — Server, Welten, Switch, Label, Button, Auto-Load, Shutdown | läuft; Auto-Load Tuning offen |
| `_ppex_src\` (geklont aa2g/PPeX) | `PPeXM64/Pipe.cs` **multi-client gepatcht**; Build: `…\PPeXM64\bin\Release\netcoreapp3.1\PPeXM64.dll` | fertig, getestet |
| `_mutexfind\` (.NET 8) | schließt den `__AA2Play_Class__`-Mutex (Modus `close`) → 2. Instanz startbar | fertig (fürs Paket nach Python/ctypes portieren) |
| `{school,jail}\AAUnlimited\mod\logperiod.lua` | schreibt `CurrentPeriod` alle 500 ms in `<world>\_orch_period.flag` (0 = keine Klasse) | aktiv (in school; **in jail aktivieren!**) |
| `{school,jail}\AAUnlimited\mod\launcher\dlg.lua` | **modifiziert**: `loadPPeX()` aus (ein gemeinsamer Server) + Auto-Launch via Env `AA2_ORCH_AUTOLAUNCH=1` | Backups: `dlg.lua.orig` |
| `_re\RE_LADEFUNKTION.md` + `_re\peinfo.py` | RE-Protokoll + Disasm-Tool | RE abgeschlossen |
| `AA2_Jail_Projekt_Notizen.md` | kanonisches Design-Doc | gepflegt |
| `HANDOFF_next_session_RE.md` | älterer RE-Handoff (durch diese Datei überholt) | Referenz |

**Start:** alles schließen → `py <project-root>\orchestrator.py`. Beenden: Ctrl+C / Terminal zu / Spiel-Quit.

---

## 4. WO WIR GENAU STEHEN (zuletzt gebaut, NICHT fertig getestet)
**Gerade gebaut: Boot-Auto-Load** (Wunsch #9/#10) im Orchestrator:
- Jede Welt bootet → wartet aufs Menü → klickt **einmal** automatisch die feste Sequenz **LOAD GAME → obersten Save → Done** → landet in-world. Danach Switch = direkt in-world.
- Klick-Koordinaten (fenster-relativ, aus deinen 1920×1089-Screenshots): `LOAD GAME (0.344,0.939)`, `oberster Save (0.422,0.289)`, `Done (0.640,0.750)`. In `WORLDS[*].load_seq`.
- `menu_wait` = 6 s (Wartezeit bis Menü da ist) — evtl. zu kurz.
- **Status: „geht nicht ganz"** (deine letzte Rückmeldung). Noch nicht eingegrenzt, woran. Wahrscheinlichste Ursachen:
  1. **Timing:** Menü braucht länger als 6 s (Dev-Logo + Asset-Load) → Klicks gehen ins Leere. → `menu_wait` hoch.
  2. **Koordinaten:** Fenster evtl. 1920×**1080** (Screenshot 1089) → Y leicht daneben. → Bruchteile nachjustieren.
  3. **logperiod in jail nicht aktiv** → „in-world erreicht"-Warten (Period-Flag) schlägt fehl.
- **Genau das ist der NÄCHSTE SCHRITT morgen:** Boot-Auto-Load tunen, bis beide Welten zuverlässig in-world booten. (Iterativ: Orchestrator starten, beobachten wo der Klick hinläuft, `menu_wait`/Koordinaten anpassen.)

**Auch gefixt, zu verifizieren:** JAIL-Button-Bug (zeigte am Menü) → Fix „nur frisches Period-Flag (mtime < 2 s) zählt". Beim nächsten Lauf prüfen, ob der Button jetzt wirklich nur am Heim-Screen erscheint.

---

## 5. KERN-TECHNIK (Kurzform — Details in den anderen Docs)
- **PPeX multi-client:** `Pipe.cs` Accept-Loop + Thread/Client; ein Server (`dotnet PPeXM64.dll "<data>"`, stdin offen halten!) bedient alle Welten. Pipe-Name `\\.\pipe\PPEX` hardcodiert.
- **Single-Instance:** Mutex `__AA2Play_Class__` (erst beim vollen Spielstart). Bypass: `DuplicateHandle(...,DUPLICATE_CLOSE_SOURCE)` (mutexfind `close`). Versionsunabhängig.
- **Auto-Launch:** Env `AA2_ORCH_AUTOLAUNCH=1` + iup-Timer-Patch in `dlg.lua` → Launcher startet ohne Klick durch.
- **Suspend:** inaktive Welt `SW_HIDE` + `NtSuspendProcess`. **Borderless Pflicht** (kein exkl. Fullscreen).
- **Lade-Funktion (RE):** RVA `0xF3C00` (`proc_invoke(GB+0xF3C00, name_ptr, data)`), Wrapper `0xB2680`. **Funktioniert in-world**, aber Live-Reload über laufende Klasse crasht; Cold-Load-via-Call unpraktikabel (s. NICHT-machbar). → Menü-Automation + Kill+Restart.
- **AAU-Lua-API (verifiziert):** `GetCharInstData/GetCharacter/GetPlayerCharacter`, Char-Werte les+schreibbar (`virtue`, Stats, `fightingStyle`), Beziehungs-/H-Dump/Restore, **`AddCard`/`KickCard`** (Roster/Transfer!), `get/setCardStorage`, `get/set_class_key` (JSON im Save), Events `on.period`(return setzt Periode)/`on.load_class`/`on.save_class`/`on.room_change`/`on.card_expelled`, `GetGameTimeData()`(.currentPeriod/.day/.nDays), Roh-Speicher `proc_invoke/g_poke/peek/malloc/ptr_walk`. `log.warn` sichtbar bei logPrio=2.
- **Tagesphasen:** 1..10; **Heim-Screen = 9**, sleep = 10, end = 8.

---

## 6. ROADMAP NACH DEM BOOT-AUTO-LOAD (Reihenfolge)
1. **Boot-Auto-Load fertig tunen** (← genau hier weitermachen).
2. **Save-Kopplung** vervollständigen: school-`on.load_class` erkennt geladenen Save-Namen → Flag → Orchestrator-Mapping → jail bootet gekoppelten Save (Mapping = triviales Python; Mid-Session-Wechsel = Kill+Restart).
3. **DB-Schicht** (Long-Term-Memory): Snapshot Play-Data→DB (Lua-Read), täglicher Resolver (Python), Inject DB→Welt beim Betreten (Lua-Write); Transfer via `AddCard`/`KickCard`.
4. **Geteilte Basis** (Junctions, 63→21 GB).
5. **Optik pro Welt** (Backgrounds/Override).
6. **Paketierung** (ein Installer; PyInstaller + self-contained PPeX; Mutex-Closer nach Python; Welt-Setup automatisieren).

---

## 7. UMGEBUNG / TOOLING
- **Spiel-Orchestrator:** `py` (Python 3.14, nur stdlib+ctypes). `python` trifft in git-bash teils den Store-Stub → `py` nutzen.
- **RE-Dev-Tooling:** `py`/3.14 ist KAPUTT für pip-Module → **`python`** (3.12, hat capstone+pefile) für `peinfo.py`.
- **GameBase rebased zur Laufzeit** (ASLR an, wechselt pro Start; peinfo nutzt Datei-Base 0x400000). Immer GB-relativ rechnen.
- .NET SDK 8+10, Runtime netcore 3.1.9 vorhanden. `git`, `dotnet` vorhanden.
- Memory-System (`…\<unrelated-project>\memory\`) = Finanzprojekt, **NICHT** für dieses Game-Projekt. Kanonisch = die MD-Dateien hier.

---

## 8. SO STARTEST DU MORGEN
Sag der neuen Session:
> „Lies `<project-root>\HANDOVER.md` (+ die dort referenzierten Docs). Wir machen beim **Boot-Auto-Load-Tuning** (Abschnitt 4) weiter: Orchestrator starten, schauen wo die Auto-Load-Klicks landen, `menu_wait`/Koordinaten in `orchestrator.py` justieren bis beide Welten zuverlässig in-world booten. Danach Save-Kopplung."

Dann: `py <project-root>\orchestrator.py` laufen lassen, Konsolen-Ausgabe + Beobachtung berichten, iterativ tunen.
