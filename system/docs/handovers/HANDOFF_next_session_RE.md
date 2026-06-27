# HANDOFF — AA2 Jail-Projekt — für eine NEUE Session (Stand 2026-06-23)

> **Zweck:** Diese Datei sagt einer frischen Claude-Code-Session ALLES, was bisher erarbeitet wurde,
> damit sie ohne Kontextverlust weitermacht. **Aktuelle Aufgabe: die Save-LADE-Funktion des Spiels
> reverse-engineeren** (Details Abschnitt 6).
>
> **ZUERST LESEN:** das kanonische Design-Dokument **`<project-root>\AA2_Jail_Projekt_Notizen.md`**
> (große Datei, vollständige Konzept-/Befund-Historie). DIESE Datei hier ist die Kurz-Übergabe + RE-Briefing.
>
> **Stil:** Nutzer ist Nicht-Coder, aber architektonisch sehr scharf. Antworten: Deutsch, direkt, technisch,
> keine Anfänger-Erklärungen. Token sparsam einsetzen (vorige Session war bei ~50% cap, daher dieser Handoff).

---

## 0. TL;DR — wo wir stehen
- **Ziel des Projekts:** zweiter „Jail"-Modus für Artificial Academy 2 (AAUnlimited). Mehrere Welten (school/jail/…),
  Sofort-Switch zwischen ihnen, persistente Char-Entwicklung über eine DB. Endprodukt = **ein Installer**, der alles einrichtet.
- **FERTIG & BEWIESEN (Runtime + Bedienung):** Ein Startpunkt (`py orchestrator.py`) lädt beide Welten vor, schaltet
  **sofort** zwischen ihnen um (inaktive Welt wird suspendiert = eingefroren, kein Sound/CPU), zeigt ein Welt-Label +
  einen In-Game-Button am Heim-Screen. Deppensicheres Beenden. **Alle harten Machbarkeits-Wände sind geknackt.**
- **AKTUELLE AUFGABE (diese Session-Übergabe):** automatisches Laden des richtigen Speicherstands, damit man beim
  Start/Switch **direkt in der Welt** landet (kein Dev-Logo/Hauptmenü). Das braucht die **Lade-Funktion des Spiels** → **RE**.

---

## 1. Ordner-Realität (wichtig)
```
<AA2-clean-install>     21 GB   ORIGINAL-Install, UNBERÜHRT (Sicherheitsnetz)
<project-root>\school    21 GB   Kopie  (= "school"-Welt, derzeit aktive Basis)
<project-root>\jail      21 GB   Kopie  (= "jail"-Welt)
```
school & jail sind **identische Kopien** (gleiche Mods/ppx). Später: geteilte Basis per Junction (`mklink /J`) → 63 GB → 21 GB.
`AA2Play.exe` (32-bit) ist das Spiel in jeder Welt. Es zeigt beim Start den AAU-Launcher (iup-Dialog), dann das Spiel-Hauptmenü.

---

## 2. WAS GEBAUT WURDE (Dateien + Zweck)

| Datei / Ordner | Zweck | Status |
|---|---|---|
| `<project-root>\AA2_Jail_Projekt_Notizen.md` | Kanonisches Design-Doc (volle Historie) | gepflegt |
| `<project-root>\orchestrator.py` | **Runtime-Orchestrator** (Python, NUR stdlib+ctypes) | läuft, getestet |
| `<project-root>\{school,jail}\AAUnlimited\mod\logperiod.lua` | Diagnose-Mod + schreibt `CurrentPeriod` alle 500ms in Flag-Datei | aktiv (in school enabled) |
| `<project-root>\_ppex_src\` | Geklontes `aa2g/PPeX`, `PPeXM64/Pipe.cs` auf **multi-client gepatcht** | gebaut |
| `…\_ppex_src\PPeXM64\bin\Release\netcoreapp3.1\PPeXM64.dll` | gepatchter PPeX-Server (multi-client) | fertig, getestet |
| `<project-root>\_mutexfind\` | .NET-Tool: schließt den `__AA2Play_Class__`-Mutex (Modus `close`) | gebaut; **wird fürs Paket nach Python (ctypes) portiert** |
| `…\_mutexfind\bin\Release\net8.0\mutexfind.dll` | das Tool | fertig |
| `<project-root>\{school,jail}\AAUnlimited\mod\launcher\dlg.lua` | **modifiziert**: `loadPPeX()` deaktiviert + Auto-Launch via Env-Var | Backups: `dlg.lua.orig` |
| `<world>\_orch_period.flag` | Flag-Datei: aktuelle Phase (0 = keine Klasse) | wird zur Laufzeit geschrieben |

**WICHTIG zum Zustand der `dlg.lua`:** loadPPeX ist auskommentiert (der Orchestrator startet EINEN gemeinsamen Server).
Für **normales Einzelspiel ohne Orchestrator** müsste man `dlg.lua.orig` zurückkopieren.

---

## 3. WIE MAN DAS SYSTEM STARTET / TESTET
1. Alles Vorherige schließen (Task-Manager: keine `AA2Play.exe`/`dotnet`).
2. `py <project-root>\orchestrator.py` (Python-Launcher `py`, NICHT `python` — letzteres trifft in manchen Shells den Store-Stub).
3. Ablauf automatisch: PPeX-Server (über `school\data`) → school starten (Auto-Launch, kein Klick) → Mutex schließen →
   jail starten (versteckt) → Mutex schließen. Dann Welt-Label oben + Switch-Button am Heim-Screen (Phase 9).
4. **Switch:** In-Game-Button neben „sleep" (nur Phase 9). **Beenden:** Ctrl+C / Terminal zu / Spiel-Quit → räumt alles auf.
- logperiod muss im Scripts-Tab aktiv sein (in school ja; in jail für den Rückweg-Button aktivieren).

---

## 4. KERN-BEFUNDE (verifiziert — eine neue Session muss das nicht neu herausfinden)

### 4.1 PPeX (Asset-Streaming, lokal, KEIN Netzwerk)
- `PPeXM64.exe` = .NET-Core-3.1-Server, entpackt `.ppx`-Mods, liefert sie dem Spiel über **globalen Named-Pipe `\\.\pipe\PPEX`** (hardcodiert).
- Stock = **single-client** (`PPeXM64/Pipe.cs`: 1 NamedPipeServerStream, default maxInstances=1, kein Re-Accept).
- **GEPATCHT auf multi-client:** Accept-Loop mit `MaxAllowedServerInstances`, ein Thread pro Client, EOF-Disconnect,
  `OnDisconnect`/Exit erst beim LETZTEN Client. `Cache.LoadLock` serialisiert `load`-Requests → threadsicher. **Bewiesen: 1 Server bedient 2 Spiele.**
- Server starten: `dotnet PPeXM64.dll "<data-pfad>"`. **stdin offen halten** (sonst crasht der ReadLine-Loop bei EOF).
- Server beendet sich, wenn der letzte Client weg ist.

### 4.2 Single-Instance-Sperre von AA2
- AA2 selbst hat **keine** harte Früh-Mutex (zwei Prozesse koexistierten, solange beide vor PPeX hingen).
- Die Sperre = benannter **Mutex `\Sessions\1\BaseNamedObjects\__AA2Play_Class__`** (gleicher Name wie die Fensterklasse),
  entsteht erst beim VOLLEN Spielstart (nicht im Launcher).
- **Bypass (versionsunabhängig, kein exe-Patch):** den Mutex-Handle der laufenden Instanz schließen via
  `DuplicateHandle(..., DUPLICATE_CLOSE_SOURCE)` → Name frei → nächste Instanz erstellt ihn frisch. → `_mutexfind` Tool, Modus `close`.

### 4.3 Auto-Launch des Launchers
- `dlg.lua` Patch: bei Env-Var `AA2_ORCH_AUTOLAUNCH=1` löst ein iup-Timer (300ms) automatisch `iup.ExitLoop()` aus → Spiel bootet ohne Klick.
- Mods werden NICHT umgangen: jede Welt lädt ihre `savedconfig.lua` normal (Scripts/Mods bleiben aktiv).

### 4.4 Fenster / Suspend
- Spiel-Fensterklasse = `__AA2Play_Class__`. Orchestrator findet HWND via EnumWindows.
- Inaktive Welt: `ShowWindow(SW_HIDE)` + **Prozess suspendieren** (`NtSuspendProcess`) → eingefroren, kein Sound/CPU. Resume = sofort.
- **Borderless-Windowed Pflicht** (exklusiver Fullscreen bricht beim Verstecken). `mod/borderless.lua` aktiv.

### 4.5 AAU-Lua-API (verifiziert via `ScriptLua.cpp` + Mods) — der ganze Brücken-Layer
- **Char-Zugriff:** `GetCharacter(seat)`, `GetCharInstData(seat)` (vacant→nil), `GetPlayerCharacter()`, `SetPlayerCharacter(...)`.
- **Char-Daten (lesen UND schreiben):** `inst.m_char.m_seat`; `inst.m_char.m_charData.m_forename/.m_surname/.m_gender`;
  `…m_charData.virtue` (Quellcode-belegt set/get: `char.virtue = X`), Stats (intelligence/strength/sociability/club…), `fightingStyle`.
- **Beziehungs-/H-Werte:** `…m_charData:m_hCompatibility(towards[,wert])`; `…m_characterStatus:m_totalH/m_climaxCount/m_cherry/…(towards[,wert])`.
- **Dump/Restore (Transfer-Bausteine, `triggers_supplemental.lua`):** `createRelationshipPointsDump(seat,towards)` /
  `restoreRelationshipPointsFromDump(...)`; `createHStatsDump` / `restoreHStatsFromDump`.
- **Roster-Manipulation:** **`AddCard`** (Card in Klasse einfügen), **`KickCard`** (entfernen), `SafeAddCardPoints`. ← Schlüssel für Transfer/Roster-Rotation.
- **Persistenz:** `getCardStorage(card,key)`/`setCardStorage(card,key,val)`, `getClassStorage`/`setClassStorage`;
  `SetClassJSONData`/`GetClassJSONData` bzw. `set_class_key`/`get_class_key` (JSON im Klassen-Save).
- **Events:** `on.period(new,old)` (Rückgabe SETZT die Periode!), `on.load_class`, `on.save_class(data)`, `on.room_change(inst)`,
  `on.move`, `on.card_expelled(a0,a1,murder)`, `on.keyup/keydown`, `on.ui_event(evt)`, `on.plan(ok,e,who)` (häufig), `on.d3d9_preload`.
- **Zeit:** `GetGameTimeData()` → `.currentPeriod`, `.day` (0–6), `.nDays`. Alle setzbar.
- **Roh-Speicher:** `malloc`, `g_poke`, `g_poke_dword`, `peek`/`peek_dword`, `ptr_walk`, **`proc_invoke(GameBase+offset, this, ...)`**, `parse_asm`.
- **Sonstiges:** `iup.timer` funktioniert IN-GAME (Poser-belegt). `play_path()/aau_path()/host_path()`. `log.warn` ist bei default `logPrio=2` sichtbar (`log.info`/`info()` NICHT). Mod-Gerüst: `mod/<name>.lua`, 1. Zeile `--@INFO ...`, `_M:load/unload/config`; neue Mods werden auto-erkannt, müssen im Scripts-Tab aktiviert werden.

### 4.6 Tagesphasen (`CurrentPeriod`)
`1`=day, `2`=nothing, `3`=first lesson, `4`=first break, `5`=sports, `6`=second break, `7`=club, `8`=end, `9`=home again, `10`=sleep.
**Heim-Screen (Quit/Title/Save/Load/sleep) = Phase 9.** Sequenz ist variabel (Engine kann Phasen überspringen, z. B. 4→7).

### 4.7 #10 (Modul-Liste) Status
Modul-IN-USE-Liste ist **NICHT** über Lua schreibbar. Aktueller Workaround: Custom-Modul einmal vorinstallieren + per Card-Storage-Flag gaten.
(RE könnte das Speicher-Layout der Modul-Liste finden → echtes Schreiben via `g_poke` → würde #10 sauber lösen.)

---

## 5. ARCHITEKTUR-ENTSCHEIDUNGEN (bereits getroffen)
- **PPeX bleibt** (ohne ppx startet das gemoddete Spiel nicht) + **Sofort-Switch** gewünscht → multi-client-Patch (erledigt).
- **Beide Welten vorladen** (fixe Kosten, kein Frust später).
- **Datenmanipulation in AAU-Lua**, Python = Orchestrator (Server/Prozesse/Fenster/DB/Brücke).
- **Distributions-Modell:** EIN Installer, alle Laufzeiten gebündelt (PyInstaller für Python; PPeX self-contained). User installiert nichts.
  Welt-Ordner per Junction (geteilte Basis), nur Delta verteilen. Mutex-Closer nach Python (ctypes) portieren.
- **Tägliche Hintergrund-Ticks** (Welten „erinnern sich"): laufen als **Python-Resolver auf der DB** — die inaktive Engine SCHLÄFT,
  wird NICHT geladen/simuliert (so steht's in den Notizen 4.8a). Anwenden beim Betreten = per Lua in die (resumte) Welt injizieren.
  → **Die Lade-Funktion ist für die Ticks NICHT nötig.** Sie ist nötig für den **Kaltstart in-world** (UX) und nützlich für #10/#5.

---

## 6. ★ AKTUELLE AUFGABE: RE der Save-LADE-Funktion ★

### Warum
Damit man beim Start/Switch **direkt im geladenen Spielstand** landet (kein Dev-Logo/Hauptmenü) und damit die Save-Kopplung
(jede school-Partie ↔ eigener jail-Save + DB) automatisch funktioniert. Ohne Auto-Load ist die UX inakzeptabel
(Variante „einmal pro Sitzung manuell laden" verworfen).

### Warum RE (und nicht „nur ein Lua-Element")
Ein Lua-Loader kann einen Save NUR laden, indem er die **Lade-Funktion des Spiels per `proc_invoke` aufruft** — genau wie das
SPEICHERN: `extsave.lua` macht `proc_invoke(GameBase+0xF36D0, 0, data)`. Es gibt **KEINE** Lua-Lade-Funktion (in `ScriptLua.cpp` verifiziert).
Also: **die Lade-Funktions-Adresse zu finden IST die Arbeit**; das Lua drumherum sind 5 Zeilen. RE ist unausweichlich für sauberes Auto-Load.
Einziger RE-freier Weg = fragile Maus-Klick-Automatik auf dem gerenderten Menü → unerwünscht.

### Was wir schon wissen (RE-Startpunkte)
- **SPEICHERN-Funktion:** `proc_invoke(GameBase+0xF36D0, 0, data)` (in `mod/extsave.lua`, Funktion `quicksave`).
  `data` = `ptr_walk(g_var, 0x18, 0x28, 0)`; `g_var` wird in extsave via Speicher-Patch bei `0x470B0` aufgesetzt.
  Der Save-NAME steht im Struct bei Offset **+100** (unicode), siehe `save_name()` in extsave.
- **`GameBase`** = Modul-Basis von `AA2Play.exe` (zur Laufzeit). `0xF36D0` ist also ein **RVA** in `AA2Play.exe`.
- Vermutung: die **Lade-Funktion** liegt nahe `0xF36D0` und hat eine ähnliche Signatur (`this`/`data`).
- AA2Play.exe importiert `CreateWindowExW`, `RegisterClassExW`, `CreateMutexW`, `CreateFileW`/`ReadFile` (für Saves).
- Saves liegen in `<world>\data\save\class\*.sav`.

### RE-Plan (für die neue Session)
1. **Werkzeug einrichten** (Dev-only, NICHT im Endpaket):
   - Statisch: `capstone` via pip (`py -m pip install capstone`) → Python-Skript, das `AA2Play.exe` lädt und um `0xF36D0` disassembliert,
     bzw. die Import-/Call-Struktur analysiert. ODER **Ghidra** (headless) für richtigen Decompiler.
   - Dynamisch (oft schneller): **x64dbg** (32-bit) ODER **Cheat Engine** ODER **Process Monitor**. Breakpoint auf
     `CreateFileW`/`ReadFile` gefiltert auf `.sav`, dann im Spiel auf **„Load" + einen Save** klicken → Call-Stack zeigt die Lade-Routine.
     **Hierfür braucht es evtl. die Mithilfe des Nutzers** (Debugger laufen lassen + im Spiel klicken).
2. **Lade-Funktions-Adresse (RVA) bestimmen.** Signatur klären (welche Args: Pfad? Save-Struct? Index?).
3. **Lua-Loader bauen:** `proc_invoke(GameBase + <ladeRVA>, ...)` analog zu extsave. Testen, dass ein bestimmter `.sav` lädt.
4. **In den Orchestrator integrieren:** beim Kaltstart jede Welt automatisch in ihren gekoppelten Save laden (versteckt) →
   beide vorgeladen IN-WORLD → Switch landet direkt in der Welt.

### Bonus-Ziel des RE (warum es sich mehrfach lohnt)
Eine Karte der Spiel-Funktionen + des Play-Data-Speicherlayouts hilft zusätzlich bei **#10 (Modul-Liste direkt schreiben)** und
**#5 (Aktionen programmatisch auslösen)** — die „aktive Eingriffe"-Klasse, die sonst die harte Wand des Projekts ist.

---

## 7. UMGEBUNG / FAKTEN
- OS: Windows 11. Session-Arbeitsverzeichnis ist `<unrelated-project>` (= ANDERES, Finanz-Projekt — NICHT dieses!). Dieses Projekt lebt in `<project-root>` (+ `<AA2-clean-install>`).
- **Python 3.14.2** — mit `py` aufrufen (`python` trifft in git-bash teils den Windows-Store-Stub). pywin32 NICHT installiert → **ctypes** nutzen.
- **.NET SDK** 8.0.418 + 10.0.201; Runtimes inkl. **netcoreapp 3.1.9** (PPeX läuft).
- `git` vorhanden. `dotnet` vorhanden. Disassembler: **noch keiner installiert** → muss eingerichtet werden.
- Bash-Tool (git-bash) + PowerShell-Tool verfügbar. `grep`/`strings -e l` für UTF-16 mit `LC_ALL=C grep -aP` (sonst Locale-Fehler).
- Das Memory-System (`…\<unrelated-project>\memory\`) gehört zum FINANZ-Projekt — **NICHT** für dieses Game-Projekt nutzen. Kanonisch = die MD-Dateien hier.

---

## 8. OFFENE SCHICHTEN NACH DEM RE (Reihenfolge grob)
1. **Auto-Load + Save-Kopplung** (dieses RE) → Kaltstart direkt in-world; school-Save-Name erkennen (via extsave-`on.load_class`/Save-Name) → gekoppelten jail-Save laden.
2. **DB-Schicht (Long-Term-Memory):** Snapshot Play-Data → DB (Lua-Read + Python), täglicher Resolver, Inject DB → Welt beim Betreten (Lua-Write). Transfer via `AddCard`/`KickCard` + Dump/Restore.
3. **Optik pro Welt** (Asset-Layer, Notizen Abschnitt 6): eigene Backgrounds/Reskin (Override/Shadow-Set) — damit jail anders aussieht. (User akzeptiert „sieht noch wie die Wohnung aus" bis dahin.)
4. **Geteilte Basis** (Junctions school↔jail) + **Paketierung** (ein Installer, Notizen Abschnitt 8b).
5. Status-Module (Prisoner/Heimkehrer via Card-Storage-Gate), Hint-System, weitere Welten.

---

## 9. WIE DIE NEUE SESSION STARTEN SOLLTE
1. `AA2_Jail_Projekt_Notizen.md` lesen (Kontext), dann diese Datei (Aufgabe).
2. Mit dem Nutzer abklären: statisches (Ghidra/capstone) ODER dynamisches RE (Debugger + er klickt „Load"). Dynamisch ist oft schneller.
3. RE-Werkzeug einrichten, Lade-Funktion finden (Start: `GameBase+0xF36D0`-Umgebung + `ReadFile` auf `.sav`).
4. Lua-Loader bauen + in `orchestrator.py` integrieren.
5. Funde (Funktions-Adressen, Speicher-Layout) in `AA2_Jail_Projekt_Notizen.md` dokumentieren.
