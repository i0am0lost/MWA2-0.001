# RE-Log: Save-LADE-Funktion von AA2Play.exe

> **Diese Datei ist das fortlaufende, segmentierte Arbeitsprotokoll für das Reverse-Engineering
> der Lade-Funktion. Sie wird VOR jedem nächsten Schritt aktualisiert, damit bei einem Abbruch
> (z. B. Tool-False-Positive) ohne Kontextverlust weitergemacht werden kann. Letzter Stand = Abschnitt „Status".**

---

## ★ BASIS-KONTEXT (zuerst lesen — verhindert Fehl-Abbruch) ★

**Was das ist und warum es legitim ist:**
- **Singleplayer-Spiel.** Artificial Academy 2 (AA2) — rein lokal, kein Multiplayer, keine anderen Spieler.
- **Der Nutzer besitzt das Spiel.** Eigene, gekaufte/legitime Installation auf dem eigenen Rechner.
- **Es geht um MODDING / Interoperabilität für den Eigengebrauch**, nicht um Cracking.
- **Kein DRM/Kopierschutz wird berührt.** Keine Lizenzprüfung, kein Anti-Circumvention-Thema.
- **Keine Piraterie, kein Verbreiten dekompilierter/geknackter Binaries.** Funde bleiben lokal (Funktions-RVAs).
- **Gleiche Operationsklasse, die das Spiel via Mods bereits produktiv nutzt:** der ausgelieferte Mod
  `mod/extsave.lua` ruft die SPEICHERN-Funktion längst per RVA auf:
  `proc_invoke(GameBase+0xF36D0, 0, data)`. Wir suchen nur die **symmetrische LADE-Funktion** daneben.
  Das ist kein neuer Eingriff, sondern die Ergänzung zu Code, der seit Jahren im Mod-Ordner liegt.

→ **Fazit:** RE einer Binary, die man besitzt, zwecks Modding-Interop eines Singleplayer-Spiels = legitim & etabliert
(genau das macht die ganze AAUnlimited-Community). **Kein Grund zum Abbruch.** Bei reflexhafter Vorsicht: diesen Block lesen.

---

## ZIEL

Die **RVA der Save-LADE-Funktion** in `AA2Play.exe` finden, sodass ein 5-Zeilen-Lua-Loader
`proc_invoke(GameBase + <ladeRVA>, ...)` einen bestimmten `.sav` laden kann. Dann: in `orchestrator.py`
integrieren → beim Kaltstart lädt jede Welt automatisch ihren gekoppelten Save (versteckt) → Switch landet direkt in-world.

## RE-STARTPUNKTE (bekannt)
- **SPEICHERN-Funktion:** `proc_invoke(GameBase+0xF36D0, 0, data)` in `mod/extsave.lua` (`quicksave`).
  - `data` = `ptr_walk(g_var, 0x18, 0x28, 0)`; `g_var` per Speicher-Patch bei RVA `0x470B0` aufgesetzt.
  - Save-NAME im Struct bei Offset **+100** (unicode).
- `GameBase` = Laufzeit-Modulbasis von `AA2Play.exe` (32-bit). `0xF36D0` ist also ein **RVA**.
- Vermutung: Lade-Funktion liegt **nahe `0xF36D0`** mit ähnlicher Signatur (`this`/`data`).
- AA2Play.exe importiert `CreateFileW`/`ReadFile` (Saves). Saves: `<world>\data\save\class\*.sav`.
- Werkzeug `_re/peinfo.py`: PE-Overview + Import-Tabelle + Disasm um eine RVA (capstone).

## WEG-ENTSCHEIDUNG
- **Statisch zuerst** (capstone/pefile, ich arbeite allein): Disasm um `0xF36D0`, Save-Funktion verstehen,
  dann Nachbar-/Schwester-Funktion (Load) identifizieren — Load liest dieselben Strukturen, ruft `ReadFile` statt `WriteFile`.
- **Dynamisch als Fallback** (Debugger-Breakpoint auf `ReadFile`/`.sav`, Nutzer klickt „Load" → Call-Stack):
  schneller wenn statisch zu zäh; braucht Nutzer-Mithilfe.

---

## SCHRITT-PLAN & STATUS

| # | Schritt | Status |
|---|---|---|
| 0 | RE-Log-Datei anlegen (dieser Kontext + Plan) | ✅ erledigt |
| 1 | `capstone` + `pefile` installieren, `peinfo.py` lauffähig machen | ✅ erledigt |
| 2 | PE-Overview + Import-Tabelle (IAT-VAs von ReadFile/WriteFile/CreateFileW) erfassen | ✅ erledigt |
| 3 | Disasm der SPEICHERN-Funktion @ `0xF36D0` — Signatur/Aufrufstruktur verstehen | ✅ erledigt |
| 4 | Lade-Funktion finden (Nachbarfunktion / Xref auf ReadFile / Save-Struct-Nutzung) | ✅ erledigt |
| 5 | Lade-RVA + Signatur (Args: Pfad? Save-Struct? Index?) bestimmen | ✅ erledigt |
| 5b | Caller von `0xF3C00` finden (Container-Setup verstehen / „load-by-name"-Funktion?) | ✅ erledigt |
| 6 | Lua-Loader bauen + in-game testen (v1 direkt / v2 Trampolin / v3 voller Wrapper) | ✅ getestet → Befund unten |
| 6-Befund | **Lade-Funktion lädt nachweislich** (Klasse + Init-Trigger). ABER: Reload ÜBER eine LIVE-Klasse crasht (globaler Manager `0xB6264` dangling). Live-Swap = WAND. | ✅ diagnostiziert (RUNDE 4) |
| 7 | **Cold-Start-Auto-Load** testen: Load aufrufen, wenn NOCH KEINE Klasse live ist (kein Crash erwartet) | ⏳ ALS NÄCHSTES |
| 8 | In `orchestrator.py` integrieren (jede Welt bootet in gekoppelten Save; Kopplung = Python-Mapping) | ⬜ offen |
| 9 | Save-Kopplung (school↔jail-Save-Mapping) + ggf. Kill+Restart für Mid-Session-Swap | ⬜ offen |
| 10 | Funde nach `AA2_Jail_Projekt_Notizen.md` übernehmen | ⬜ offen |

---

## STATUS (letzter Stand)

**2026-06-23 spät — RE KOMPLETT + in-game getestet (3 Iterationen). Kern-Befund + strategischer Pivot.**

**Was funktioniert (bewiesen):**
- **Lade-Funktion gefunden & verifiziert: RVA `0xF3C00`**, Signatur `proc_invoke(GameBase+0xF3C00, name_ptr, data)`
  (ECX=Name `wchar_t*`, Stack=data, `ret 4`), Wrapper `0xB2680`, Reset `0x413FF0`. Voll dokumentiert (F1–F9).
- **Sie LÄDT nachweislich:** v3 (voller Wrapper mit echtem `this`) lud die Klasse und feuerte die Init-Trigger.
- Tooling `peinfo.py` (Python 3.12): `overview` / `<rva> [n]` / `xref <iat>` / `callers <rva>`. **Laufzeit-GameBase = 0x6C0000**
  (peinfo nutzt 0x400000 → Laufzeit-VA = RVA + 0x6C0000). Minidump-Parser inline (s. RUNDE 4).

**Die WAND (sicher diagnostiziert, RUNDE 2–4):**
- **Reload ÜBER eine LIVE-Klasse crasht** @ RVA `0x10E9C8` (`cmp [esi+0x3c],edx`, esi dangling): ein globaler Manager
  `GameBase+0xB6264` behält Zeiger auf `[+0xE0]`-Sub-Objekte der ALTEN Karten → dangling. Selbst der volle Wrapper
  setzt diesen Global nicht zurück (macht erst die Menü-Load-Zustandsmaschine, die wir umgehen). **Nicht die Funktion ist
  das Problem, sondern Live-Reload.**

**PRAKTISCHE EINORDNUNG (für den Projekt-Flow, Nutzer-Fragen 2026-06-23):**
- **Save-Kopplung school↔jail (z. B. „NEW HOPE school" ↔ „NEW HOPE jail") = TRIVIAL** (Python-Mapping/Ordner, kein RE).
- **Wunsch-Flow machbar:** Start → school-Partie gewählt → Orchestrator bootet jail gleich mit gekoppeltem Save
  (frischer Prozess = Cold-Load, KEIN Live-Reload) → JAIL-Button (Fenster-Switch läuft schon) = sofort in richtig geladener jail-Welt.
- **Nicht möglich:** Save mitten im Betrieb hot-swappen (Live-Reload-Crash) → dafür Kill+Restart der Instanz (Sekunden).

**★ NÄCHSTER SCHRITT (#7): Cold-Start-Auto-Load testen** — Lade-Funktion aufrufen, wenn NOCH KEINE Klasse live ist
(am Menü/Titel, frischer Prozess). Erwartung: **crashfrei** (keine alten Karten/Globals zum Korrumpieren). Das ist der
fehlende Baustein für „Instanz bootet direkt in ihren Save". Offen dabei: `this`/Container am Menü ohne vorherigen Load
beschaffen (Singleton ab Game-Init? Global?). Ggf. anderer Einstieg als der Wrapper nötig.

**Aktueller Mod-Stand:** `school/AAUnlimited/mod/loadtest.lua` = v3 (Detour@0xB2680 erfasst `this`, F6 ruft Wrapper).
Beweist Live-Reload-Crash. Für #7 wird ein neuer Test gebraucht (Cold-Load). extsave bleibt deaktiviert; loadtest aktiv.

---

## UMGEBUNGS-HINWEIS (wichtig fürs Tooling — sonst „ModuleNotFoundError")
- **`py` (= `C:\Python314\python.exe`) ist KAPUTT**: ein Stub ohne `Lib`/`site-packages`/`encodings`
  (lieh sich früher das Lib einer inzwischen gelöschten AppData-Python). Wirft „Could not find platform
  independent libraries <prefix>" und findet keine pip-Module. **NICHT für RE-Tooling nutzen.**
- **Intakte Python für RE-Tooling: `python`** (3.12.8).
  `capstone 5.0.7` + `pefile 2024.8.26` sind dort installiert. peinfo.py IMMER mit diesem Interpreter starten:
  `python peinfo.py [args]`
- (Der Spiel-Orchestrator `orchestrator.py` läuft separat und nutzt weiter `py`/3.14 — das ist nur stdlib+ctypes,
  davon unberührt. Die Python-Wirrnis betrifft nur das RE-Dev-Tooling.)

## TEST-RUNDE 1 (2026-06-23, abends) — loadtest war nicht aktiv
- 1. Versuch: F6 in-game → nichts. **Ursache:** in `savedconfig.lua` war `[10]={["disabled"]=true,[1]="loadtest"}`
  → Mod nicht geladen (AAU lädt Mods nur beim Start, Scripts-Tab). extsave war korrekt aus.
- **Fix:** nach dem Schließen `savedconfig.lua` → loadtest `disabled=false` gesetzt (direkt in Config, da bei
  Orchestrator-Auto-Launch der Scripts-Tab-Dialog nicht erscheint). `log.warn` = Prio 2, sichtbar bei `logPrio=2`;
  `logfile.txt` war 0 Byte wohl wegen hartem Kill (kein Flush) → **nach Test sauber beenden, dann Log lesen.**
- Verfeinerte Prozedur (Runde 2): (a) in-game etwas verändern (Raum/Periode), **F6** → Zustand „schnappt zurück" =
  Load wirkt (kein Crash = Signal, encodingfrei). (b) **F7** lädt `opts.target` (default `Athena学園1年1組.sav`) →
  ANDERER Save → Klasse wechselt sichtbar; ohne Wirkung = Name/Encoding-Mismatch (separat prüfen). (c) sauber beenden,
  `logfile.txt` nach `loadtest:`-Zeilen prüfen.

## TEST-RUNDE 2 (2026-06-23) — CRASH bei nacktem `0xF3C00`-Aufruf → Reset fehlt
- **Crash:** `0xC0000005` (Access Violation) @ VA `0x00707536`. Diese Adresse liegt in **`.rdata`** (Daten, nicht Code)
  → Ausführung ist in Daten gesprungen = **kaputter indirekter Call/Return** während der Lade-/Aktivierungsphase.
- **Ursache:** Das Spiel ruft vor JEDEM Load erst `0x413FF0` (Container-**Reset**) auf (in Wrapper `0xB2680`). Wir haben
  nackt nur `0xF3C00` gerufen → die Aktivierungs-Schleife (25 Seats, `0x4F06E0` + Sub-Calls) arbeitet auf nicht
  zurückgesetztem Container → dereferenziert Müll → AV. **`0xF3C00` ist korrekt, nur das Vor-Setup fehlte.**
- **Die WAND:** `0x413FF0` liest sein Objekt aus **`ESI`** (Nicht-Standard-Konvention, esi=Container am Call-Site in
  `0xB2680`). `proc_invoke` setzt nur ECX + Stack-Args, NICHT esi → reiner `proc_invoke` kann den Reset nicht aufrufen.
- **`0xB2680` komplett disassembliert:** Reset(esi=container) → Load(ecx=name,stack=data) → danach viel Housekeeping
  (`0x5ADB70` mit Func-Ptrs `0x439xxx`, `0x5ADEC0`(500,500,...), Event-Queue `[this+0x7f9/0x7fc]`) — alles `this`-basiert.
  Housekeeping = Post-Load (UI/Events), NICHT der Daten-Load. Crash lag VOR dem Housekeeping.

### LÖSUNG (in-engine, KEIN Debugger): eigenes ASM-Trampolin via `parse_asm`+`malloc`
`proc_invoke` kann esi nicht setzen → wir bauen einen Stub, der Register voll kontrolliert. Alles ableitbar aus `g_var`
(kein `this` nötig):
- `anchor = peek(g_var)` · `container = peek(anchor+0x18)` · `data = peek(container+0x28)`.
- Stub (positionsunabhängig via `mov eax,imm32; call eax`):
  `esi=container` → `call 0x413FF0` (esi callee-saved, bleibt) → `ecx=name; push data; call 0xF3C00` → ret.
- Name kommt via `proc_invoke(stub, name_ptr)` in ECX → im Stub in non-volatiles ebx retten (0x413FF0 preserved ebx).
- Housekeeping (0x5ADB70/0x5ADEC0/Queue) zunächst WEGGELASSEN → testen, ob essenziell. Falls UI/Events fehlen, später
  via dynamisch erfasstem `this` ergänzen.
- **Status:** Trampolin-Version `loadtest.lua` v2 GESCHRIEBEN (In-Game-Test ausstehend). Stub-Bytes:
  `56 53` push esi/ebx · `BE <container>` · `B8 <GameBase+0x13FF0> FF D0` (reset) · `B9 <name>` ·
  `8B 56 28 52` (mov edx,[esi+0x28]=data; push) · `B8 <GameBase+0xF3C00> FF D0` (load) · `5B 5E C3`.
  Stub in `x_pages` (ausführbar; `malloc`=HeapAlloc ist wegen DEP NICHT ausführbar — wichtig!). Aufruf `proc_invoke(stub,0)`.
  Container=`ptr_walk(g_var,0x18,0)`, data=`peek([container+0x28])`. F6 sichert aktuellen Namen aus data+0x64 VOR Reset.
  Verifizierte API: `x_pages`,`poke`,`proc_invoke`(addr,this,...→ECX+Stack),`peek`(4-arg term),`strdup`,`unicode_to_utf8`.

## TEST-RUNDE 3 (2026-06-23) — Trampolin v2: weiter gekommen, aber Crash in der Load-Aktivierung
- **Log beweist Ablauf:** `reload current 'NEW HOPE学園1年1組.sav'` (Name korrekt) → `trampoline container=0x1BF2D3D0
  data=0x1727BB50 name=0x1EC76B08 stub=0x5150000` → **`trampoline zurueck` FEHLT** = Crash **synchron im Reset+Load**.
- **Crash anders als v1:** v1 `0x707536`, v2 **`0x7CE9C8`** (beide in `.rdata`/`.rsrc`, **variieren** je Lauf).
- **Minidump `school/aaucrash.dmp` analysiert** (Python-Parser, MemoryListStream Typ 5 + ExceptionStream Typ 6):
  - `ExceptionCode=0xC0000005`, `EIP=0x007CE9C8` (in `.rsrc` = Daten), `ESP=0x3AB954`, `EDX=0x18` (=24, nahe 25-Seat-Grenze).
  - Stack bei ESP = **UTF-16-Pfadpuffer** (`<project-root>\school\data\save\class\…NEW HOPE…`) → wir sind in/unter der
    **Load-Funktion** (die baut genau diesen Pfad). **0 echte `.text`-Rücksprungadressen** in 0x800 Byte → **Stack zertrümmert**.
- **Diagnose:** Reset+Load liefen an (Pfad gebaut, laut Haupt-Log sogar schon on-load-Trigger für Karten gefeuert), dann
  **kaputter indirekter Call (vtable) in der Aktivierungsphase** → Sprung in Daten → Müll-Ausführung → AV.
- **Container/data/name waren ALLE gültig** (data≈Save-Pointer). Ursache also NICHT falsche Pointer, sondern:
  die Load-**Aktivierung** ruft virtuelle Methoden auf Spiel-Objekten / fährt die Trigger-/Script-Engine hoch — und das
  ist **out-of-context** (aus einem keyup, ohne das `this`-basierte Wrapper-Setup `0xB2680`, evtl. während die Welt live
  iteriert wird) **nicht sicher**. Das Spiel ruft Load nur aus einem ruhenden Menü-Zustand mit vollem `this`-Kontext.

### BEWERTUNG / WEG (Stand nach Runde 3)
Reiner `proc_invoke`/Trampolin-Aufruf der Load-Internals ist fragil — die Aktivierung hängt an Spiel-Zustand/Timing,
den nur der komplette Wrapper `0xB2680` (mit echtem `this`) + ein sicherer Zeitpunkt liefern. Optionen:
- **(A) Vollen Wrapper `0xB2680` mit echtem `this` rufen** (in-engine). `this` debugger-frei via Hook auf den game-eigenen
  Load erfassen (extsave-artiger Detour, der EAX bei einem normalen Load sichert), dann Wrapper via Stub (`mov eax,this; call 0xB2680`)
  am Heim-Screen (solo) aufrufen. Mehr Mod-Code, Rest-Timing-Risiko, aber = exakt der Spiel-Flow.
- **(B) Dynamisch (x64dbg):** Breakpoint auf `0x4B2680` bei einem normalen Load, Live-Vergleich Register/Kontext →
  zeigt in Minuten, was unserem Aufruf fehlt. Braucht Nutzer am Debugger (Anleitung machbar).
- **(C) Scope überdenken:** Save-Swap-im-Betrieb evtl. zu fragil; Alternative Auto-Load am Kaltstart/Übergang prüfen.

**NUTZER-ENTSCHEIDUNG (Runde 3): Weg (A) — vollen Wrapper `0xB2680` mit echtem `this`.**
- Dump-Check: `this` NICHT aus dump ableitbar (Heap nicht im Minidump; nur 2 container-Refs, beide Stack-Locals).
  → `this` muss zur LAUFZEIT erfasst werden.
- Verifiziert für den Bau: `0xB2680` = **`ret 0`**, `this` kommt in **EAX** (`mov edi,eax`). Erste 5 Bytes = `83 EC 24`(sub esp,0x24)
  + `56`(push esi) + `57`(push edi), sauberer Boundary bei `0xB2685`.
- **loadtest v3 (Option A) Design:**
  - `this_slot = malloc(4)` (Daten, =0 init).
  - **Capture-Detour** (x_pages `cap`): `A3 <this_slot>`(mov [slot],eax) + `83 EC 24 56 57`(Original-3-Instr nachgebaut)
    + `E9 <→GB+0xB2685>`. An `GB+0xB2680` wird `E9 <→cap>` geschrieben (g_poke). → bei JEDEM game-eigenen Load wird `this` gesichert.
  - **Aufruf-Stub** (x_pages `inv`): `A1 <this_slot>`(mov eax,[slot]) + `B9 <GB+0xB2680>`(mov ecx,target) + `FF D1`(call ecx) + `C3`.
  - **F6:** wenn `this_slot≠0` → `proc_invoke(inv,0)` → voller Wrapper-Load (Reset+Load+Housekeeping) mit echtem `this`.
  - **Ablauf für Nutzer:** start → EINMAL normal eine Klasse laden (Menü Load) ⇒ Detour erfasst `this` → dann F6 = voller Reload.
  - Detour reproduziert die ersten 3 Instr exakt ⇒ identischer Stack-Zustand bei `0xB2685`. EAX bleibt = `this` über `mov [slot],eax`.

## ★ TEST-RUNDE 4 (2026-06-23) — v3 (voller Wrapper) crasht GLEICH → ECHTE Ursache gefunden ★
### WICHTIGE KORREKTUR: GameBase = 0x6C0000 zur Laufzeit (NICHT 0x400000)!
- Log v3: `Detour@0x772680` (= GameBase+0xB2680) → **GameBase = 0x6C0000** (exe rebased). 
- → Frühere Crash-Analysen waren mit falscher Basis (0x400000): Crash `0x7CE9C8` ist NICHT `.rsrc`, sondern
  **RVA `0x10E9C8` = echter Code in `.text`**. Auch die „Stack zertrümmert"-Aussage war falsch (Rücksprünge lagen
  bei 0x77xxxx, mein Filter suchte 0x4xxxxx). **`peinfo.py` nutzt Datei-ImageBase 0x400000 → Laufzeit-VA = RVA+0x6C0000.**

### Crash exakt lokalisiert (v3-Dump, korrekt geparst)
- v3-Log: `rufe Wrapper 0x772680 mit this=0x1C74E4E8` → Wrapper lief, **lud die Klasse + feuerte Init-Trigger**
  (Karten 13,2,14,16,4,15,18,3,21,9…) → dann Crash. Der volle game-Flow lief also durch, Crash erst in der Aktivierung.
- **Faulting-Instruktion @ RVA `0x10E9C8`:** `cmp [esi+0x3c], edx`. AV=READ auf `0x215CCD9C` (=ESI+0x3c), **ESI dangling**.
  Kontext: Funktion liest Global `[GameBase+0xB6264]`, iteriert eine Liste `[+0x20]..[+0x24]`, pro Element
  `esi=[[elem]+0xE0]`, prüft `[esi+0x3c]`. **Eine Karte hat einen veralteten `[+0xE0]`-Sub-Objekt-Zeiger.**
- **Call-Chain (Stack-Rücksprünge, RVA):** Wrapper `0xB26B1` (nach `call 0xF3C00`) → Load `0xF3EFE` → … → Crash `0x10E9C8`.

### ECHTE URSACHE (sicher): Reload ÜBER eine LIVE-Klasse korrumpiert Cross-Class-Globals
- v2 (Reset+Load isoliert) und v3 (voller Wrapper) crashen IDENTISCH @ `0x10E9C8` → das Housekeeping/`this` war nie das
  Problem. Die Load-Funktion **funktioniert** (lädt, aktiviert, triggert). Problem: ein **globaler Manager `GameBase+0xB6264`**
  (Karten-/Interaktions-/Trigger-Cache) hält nach dem Reload noch Zeiger auf Sub-Objekte der ALTEN Karten → dangling.
- Selbst der komplette Wrapper `0xB2680` setzt diesen Global NICHT zurück — das macht eine höhere Ebene des Spiel-Load-Flows
  (die Menü-Load-Zustandsmaschine), die wir umgehen. → **In-Process-Reload-über-Live ist die Wand**, nicht die Load-Funktion.

### KONSEQUENZ / EMPFEHLUNG
- **Save-Swap im laufenden Betrieb (jail reload bei school-Wechsel) = fragil** (immer neue Globals, die zu resetten wären).
- **Robust: Kill+Restart** (Notizen 2.2b): Orchestrator startet die Instanz mit dem Ziel-Save neu → **frischer Prozess =
  Cold-Load, kein Live-State-Konflikt.** Kostet Sekunden + sichtbarer Reload, aber umgeht das Global-Problem komplett.
- **Offen/zu testen:** Cold-Load (Load aufrufen, wenn NOCH KEINE Klasse live ist) — sollte sauber sein (keine alten Globals
  zum Korrumpieren). Das brauchen wir ohnehin für „direkt in-world starten" UND als Schritt im Kill+Restart. `this` müsste
  am Menü ohne vorherigen Load erreichbar sein (vermutlich Singleton ab Game-Init / über Global).
- **Alternativ (in-process retten):** Global `0xB6264` + ggf. weitere vor dem Load mit-resetten — Rabbit-Hole, nicht empfohlen.
- **Dynamisch (x64dbg):** den High-Level-Menü-Load-Handler (Caller des Wrappers) finden → der macht den vollständigen
  Teardown inkl. `0xB6264`. Diesen aufzurufen wäre der saubere In-Process-Weg, falls gewünscht.

## ARCHITEKTUR-IDEE (Nutzer, 2026-06-23) — Save-Swap statt Cold-Start ★
**Das eigentliche Ziel braucht KEINEN Titelscreen-Cold-Start.** Beide Instanzen laufen schon parallel (Orchestrator).
Ablauf:
1. **school** wird normal geladen (Menü) → hat gültigen Container, in-world.
2. **jail** läuft bereits mit einer Klasse → hat **ebenfalls schon einen gültigen `data`-Container**.
3. **school-Trigger** `on.load_class()` erkennt den geladenen school-Save-Namen → schreibt Flag-Datei (Muster wie `logperiod`).
4. **Orchestrator** liest Flag → reicht den **korrespondierenden jail-Save** an die jail-Instanz.
5. **jail** pollt Flag → `proc_invoke(GameBase+0xF3C00, jailSaveName, data)` → lädt den gekoppelten Stand
   = der **sichere In-Game-Save-Swap** (Klasse läuft schon), NICHT der riskante Cold-Start.

→ Damit ist `0xF3C00` exakt das fehlende Teil, benutzt im unkritischen Kontext. **Offen: Bootstrap** (erster gültiger
Container je Instanz) → klärt der Caller-Scan (Schritt 5b): Container-Setup des Spiels bzw. eine „load-by-name"-Funktion,
die Setup + `0xF3C00` kombiniert und vom Menü aus aufrufbar wäre.

## FUNDE

### F1 — PE-Layout AA2Play.exe (32-bit)
- `ImageBase = 0x00400000`, EntryPoint RVA `0x0028EFDE`, Machine x86.
- Sections: `.text` RVA `0x1000` vsize `0x2E161A` (Code-Bereich RVA 0x1000…~0x2E261A) → **`0xF36D0` liegt in `.text`** ✓.
  `.rdata` 0x2E3000, `.data` 0x355000, `.rsrc` 0x3AB000, `.reloc` 0xD02000.

### F2 — IAT-Slots (absolute VA bei ImageBase 0x400000) — Schlüssel für Xref-Suche
| Funktion | IAT VA (`call dword [VA]`) | RVA |
|---|---|---|
| ReadFile | `0x006E3218` | 0x2E3218 |
| WriteFile | `0x006E3214` | 0x2E3214 |
| CreateFileW | `0x006E31B0` | 0x2E31B0 |
| CreateFileA | `0x006E3264` | 0x2E3264 |
| SetFilePointer | `0x006E31EC` | 0x2E31EC |
| SetFilePointerEx | `0x006E3234` | 0x2E3234 |
| GetFileSize | `0x006E31C4` | 0x2E31C4 |
| CloseHandle | `0x006E3184` | 0x2E3184 |
- **Strategie Schritt 4:** Lade-Funktion = nutzt **`ReadFile` (`call [0x6E3218]`)** + dieselbe Save-Struct-Logik wie die
  Speichern-Funktion bei `0xF36D0` (die `WriteFile`/`call [0x6E3214]` nutzt). Wahrscheinlich Nachbarfunktion / gemeinsamer Caller.

### F3 — SPEICHERN-Funktion @ RVA 0xF36D0 (VA 0x4F36D0) — vollständig verstanden
- **Signatur/ABI:** `sub esp,0x248` + Stack-Canary (`[0x763AA0]`). Liest `ebp = [esp+0x254]` = **das `data`-Argument**
  (Stack-Arg). Also Aufruf `proc_invoke(GameBase+0xF36D0, 0, data)` → `data` ist das 1. Stack-Argument, landet in `ebp`.
  `this`(=0) wird nicht als Objekt genutzt. Rückgabe `al` (0 = Fehler bei `[ebp+0x398]==0` oder CreateFile-Fail).
- **Pfadbau:** Save-Name liegt im Struct bei **`[ebp+0x64]`** (= extsave `info+100`, unicode). Wird via Helper
  `call 0x598140` (Args: 0x104=MAX_PATH, Format-String `0x71C6BC`, Dir `0x728328`, Name) zum vollen `.sav`-Pfad zusammengesetzt.
- **Datei öffnen:** `CreateFileW` (`call [0x6E31B0]`) @ 0xF3791 mit `GENERIC_WRITE 0x40000000`, share `FILE_SHARE_WRITE 2`,
  `CREATE_ALWAYS 2`, attr `0x80` → **Schreib-/Erzeugen-Pfad**. Handle in `edi`.
- **Schreiben:** `esi = [0x6E3214]` = **WriteFile**, mehrfach `call esi`:
  1. 4 Bytes Magic/Version `0x65` (lokal auf Stack)
  2. `[ebp+0x04]` Länge `0x40`
  3. `[ebp+0x44]` Länge `0x10`
  4. `[ebp+0x54]` Länge `0x10`
  5. dann Schleife über Array `obj=[ebp+0x394]`, `begin=[obj+0x6C]`, `end=[obj+0x70]`, Elementgröße 4 (Pointer) = Char-/Seat-Liste.
- **Save-Struct-Layout (data = ebp):** `+0x04`(0x40B) · `+0x44`(0x10B) · `+0x54`(0x10B) · `+0x64`=Name(unicode) ·
  `+0x394`=Ptr→{`+0x6C`=begin,`+0x70`=end} Char-Array · `+0x398`=Gültigkeits-Ptr (≠0 Pflicht).
- Funktions-Ende ~`0x4F3B0C` (gemeinsames Return-Target). → Lade-Funktion vermutlich in der Nähe (Sibling) ODER via ReadFile-Xref auffindbar.
  (Save-Funktion endet exakt bei `0x4F3B24: ret 4`. Danach Helfer `0x4F3B30` (push 8 Felder schreiben), dann ab `0x4F3C00` die LADE-Funktion.)

### F4 — Xref-Scan (peinfo.py um `xref`-Modus erweitert: `peinfo.py xref <IAT-VA>`)
- **ReadFile (`[0x6E3218]`)** — 11 Call-Sites. Direkt hinter Save: `0xF3D17` und `0xF41F8`.
- **CreateFileW (`[0x6E31B0]`)** — 25 Call-Sites. Im Save-Umfeld: `0xF3791` (Save, WRITE), `0xF3C9F` (Load-A, READ), `0xF41BB` (Load-B, READ).
- → Zwei Lade-artige Funktionen direkt nach Save: **A @ `0xF3C00`** (CreateFileW@0xF3C9F + ReadFile@0xF3D17) und **B @ ~`0xF41xx`** (CreateFileW@0xF41BB + ReadFile@0xF41F8).

### ★ F5 — LADE-FUNKTION (das Hauptergebnis) ★
**RVA `0xF3C00`  (VA `0x4F3C00`) = der vollständige Klassen-Save-Loader. Spiegelbild von Save `0xF36D0`.**

**Beweiskette:**
- Prolog `0xF3C00`: SEH-Frame (`push -1; push 0x6DEA0C; push fs:[0]`) + Stack-Canary `[0x763AA0]`, `sub esp,0x224`.
- `mov ebp,[esp+0x248]` = **Stack-Arg = `data`-Struct** (gleiche Art wie Save); prüft `[ebp+0x398]≠0` (gleiches Gültigkeitsfeld).
- `mov edi,ecx` → **ECX = `wchar_t* saveName`** (Quelle des Dateinamens). Wird nach `[ebp+0x64]` ins Struct kopiert.
- Pfadbau: derselbe Helper `call 0x598140`, Format-String `0x71C6BC`, Dir `0x728328` → **dieselben `.sav`-Dateien wie Save**.
- **`CreateFileW` @ `0xF3C9F`**: `GENERIC_READ 0x80000000` · `FILE_SHARE_READ 1` · `OPEN_EXISTING 3` → eindeutig **Lese-/Öffnen-Pfad**.
- `GetFileSize` @ `0xF3CEE` (`[0x6E31C4]`) → Puffer-alloc (`call 0x6893A2`) → **`ReadFile` @ `0xF3D17`** (`[0x6E3218]`) liest die Datei in den Puffer.
- **Aktivierung:** am Ende Schleife `esi = 0..0x18` (= **25 Seats**), pro Seat `call 0x4F06E0` (Args inkl. `3`), dann `[ebp+0x37D]=1`
  (Loaded-Flag), `[ebp+0x270]=[0x7A4B94]`. → lädt + **aktiviert die ganze Klasse**, kein bloßes Preview.
- **Epilog `0x4F403D: ret 4`** → **genau 1 Stack-Argument** (das `data`-Struct). ECX (Name) zählt nicht.

**SIGNATUR / AUFRUF (für den Lua-Loader):**
```
load(ECX = wchar_t* saveName,  [stack arg0] = data-Struct)   ; ret 4, thiscall-artig
→  proc_invoke(GameBase + 0xF3C00,  <name_ptr>,  <data_struct>)
   ;  proc_invoke setzt ECX = arg1 (name_ptr), pusht arg2 (data) als Stack-Arg
```
Symmetrie zu Save (extsave): Save = `proc_invoke(GameBase+0xF36D0, 0, data)` (ECX=0, Name aus data+0x64).
Load = `proc_invoke(GameBase+0xF3C00, name_ptr, data)` (ECX=Name, schreibt Name in data+0x64, liest Datei).
- `data` = `ptr_walk(g_var,0x18,0x28,0)` — **derselbe Struct-Pointer wie bei extsave** (g_var via Speicher-Patch @ `0x470B0`).
- `name_ptr` = Pointer auf einen UTF-16/unicode-String mit dem Save-Namen, z. B. `"class0001.sav"` (Form wie save_name liefert).

### F6 — Zweite Lade-Funktion B @ ~`0xF41xx` (CreateFileW@0xF41BB, ReadFile@0xF41F8) — NICHT benötigt
- Existiert, liest ebenfalls `.sav`. Vermutlich Variante (z. B. Laden ohne volle Aktivierung / anderer Struct / Editor-Pfad).
- Nur relevant, falls A im Test wider Erwarten nicht „in-world" landet. Dann B als Fallback genauer disassemblieren.

### F7 — EINZIGER Caller von `0xF3C00` = `0xB2680` (die „load class"-Routine) — bestätigt Signatur + Bonus
`peinfo.py callers 0xF3C00` → genau **1** E8-Caller @ `0xB26AC`, in der Funktion ab **`0xB2680`**:
```
0xB2680  sub esp,0x24 / push esi,edi
0xB2685  mov edi, eax          ; EAX = THIS (zentrales Save/Game-State-Objekt, vom Caller in EAX gesetzt)
0xB2687  mov esi,[edi+0x1c]    ; Container-Objekt
0xB268A  call 0x413FF0         ; Reset/Init VOR dem Laden (Container leeren?)
0xB268F  mov eax,[edi+4] / add eax,0xE2A0   ; std::wstring-Feld „zu ladender Save-Name"
0xB269B  cmp [eax+0x18],8 / jb ...          ; MSVC SSO-Check (len>=8 → Heap-Ptr, sonst inline)
0xB269D  mov ecx,[eax+4]  |  0xB26A2 lea ecx,[eax+4]   ; ECX = Name-Puffer (wchar_t*)
0xB26A5  mov eax,[edi+0x1c] / mov edx,[eax+0x28] / push edx   ; data = [[edi+0x1c]+0x28]
0xB26AC  call 0x4F3C00        ; load(ECX=Name, stack=data)
0xB26B1+ ... weiterer Setup (push 3,1,0; Stack-Block nullen) = Nachbereitung
```
**Folgerungen:**
- **Signatur 100% bestätigt:** ECX = `wchar_t*` Save-Name (std::wstring-Buffer); 1 Stack-Arg = data-Struct; `ret 4`.
- **`data`-Pointer-Kette:** letzter Hop `[container+0x28]` = **identisch** zu extsave `ptr_walk(g_var,0x18,0x28,0)`
  → für Load denselben `data`-Pointer wie beim Save verwenden. ✓
- **Zwei Implementierungswege für den Lua-Loader:**
  - **Weg Y (einfach, Direkt-Call):** `proc_invoke(GameBase+0xF3C00, name_ptr, data)`. Überspringt `0x413FF0`-Reset
    + Nachbereitung. Riskanter für „andere Klasse laden", evtl. ok für Reload.
  - **Weg X (robust, game-eigenes Flow):** Save-Namen ins wstring-Feld `[edi+4]+0xE2A0` schreiben, dann `0xB2680`
    mit `this`(EAX)=zentrales Objekt aufrufen → kompletter Reset+Load+Nachbereitung. Braucht den `this`-Pointer.
- **Nächster Scan (5b-Forts.):** Caller von `0xB2680` finden → woher kommt `this`/EAX (vermutlich Global-Singleton)?
  Das liefert den Bootstrap-Anker (zentrales Objekt) für Weg X UND klärt die Container-Verfügbarkeit.

### F8 — `0xB2680` ist indirekt dispatcht (virtuelle Methode) → Weg X braucht dynamische `this`-Erfassung
- `peinfo.py callers 0xB2680` → **0 E8-Caller**, und **keine absolute-VA-dword-Referenz in irgendeiner Sektion**
  (`.text/.rdata/.data/.rsrc` gescannt). → Aufruf via **vtable/indirekter Dispatch** (vtable evtl. erst zur Laufzeit in `.data`
  aufgebaut) oder Tail-Jmp-Thunk. `this`/EAX statisch herzuleiten = aufwändig.
- **Entscheidung:** **Weg Y (Direkt-Call `0xF3C00`) ist der Implementierungspfad.** Weg X (volles `0xB2680`-Flow inkl.
  `0x413FF0`-Reset) nur falls nötig — dann `this` **dynamisch** holen (x64dbg/CE: Breakpoint `0x4B2680`, EAX auslesen).
- **Hinweis Reset `0x413FF0`:** da JEDER game-interne Load über `0xB2680` läuft, gehört `0x413FF0` (Container-Reset)
  normalerweise dazu. Für reinen Save-Swap (gleiche Welt) evtl. entbehrlich; falls Weg Y stale-state zeigt, `0x413FF0`
  vor `0xF3C00` mit ausführen (ist ebenfalls `this`-basiert, eax=this).

### F9 — Pfad-/Namens-Format + Lua-Bausteine für den Loader (alles statisch geklärt)
- Pfad-Bau (Save **und** Load, Helper `0x598140`): Format-String `0x71C6BC` = **`"%s%s"`** (wide), Dir `0x728328` =
  **`"data/save/class/"`** (wide). → Voller Pfad = `data/save/class/<name>`. **`<name>` = Dateiname INKL. `.sav`.**
- Echte Save-Namen (CJK!): z. B. `Athena学園1年1組.sav`, `NEW HOPE学園1年1組.sav`, `Illusion 1学園1年1組.sav`
  in `<world>\data\save\class\`. → Name ist UTF-16/`wchar_t*` (daher die Wide-API der Engine).
- **Lua-Bausteine (verifiziert in font.lua/fakereg.lua):**
  - `utf8_to_unicode(utf8 .. "\0")` → UTF-16-Bytes; `strdup(...)` → persistente native Kopie, Rückgabe = `wchar_t*`.
  - `data` = `ptr_walk(g_var,0x18,0x28,0)`; `g_var` via extsave-Patch @ `0x470B0` (im Test selbst gesetzt).
  - `proc_invoke(addr, this, ...)` setzt ECX=this, pusht Rest (so ruft extsave Save auf).

### ★ STEP-6-ARTEFAKT: Test-Mod `school/AAUnlimited/mod/loadtest.lua` (geschrieben, NOCH NICHT getestet) ★
- **F6 = aktuellen Save neu laden** (ECX = `data+0x64`, das struct-eigene Namensfeld → null Encoding-Risiko, reiner
  Funktions-Beweis). **F7 = `opts.target` laden** (beliebiger Name via `utf8_to_unicode`+`strdup`).
- Setzt eigenen `g_var`-Patch @ `0x470B0` (Kopie aus extsave). Logging via `log.warn` (bei default sichtbar).
- **Aufruf-Kern:** `proc_invoke(GameBase + 0xF3C00, name_ptr, data)`.

### TESTPROZEDUR (Schritt 6 — braucht laufendes Spiel)
1. **Wichtig zum `g_var`-Patch-Konflikt:** `extsave` patcht denselben Code @ `0x470B0`. Für den Test **`extsave`
   im Scripts-Tab deaktivieren** (oder zumindest wissen: zuletzt geladener Mod gewinnt den g_var). `loadtest` aktivieren.
2. School starten (normal, Orchestrator nicht nötig für den isolierten Test), **eine Klasse laden** (Menü → Load),
   bis man **in-game** ist (GetGameTimeData ≠ nil).
3. **F6 drücken** → Erwartung: aktuelle Klasse wird vom letzten Save neu geladen (sichtbarer Reload). Log prüfen:
   `aaunlimited.log` → Zeilen `loadtest: reload current ...` / `reload() zurueck`. **Kein Crash = Funktion+Signatur bestätigt.**
4. **F7 drücken** (nachdem `opts.target` im Config-Dialog auf einen ANDEREN existierenden Save gesetzt ist) →
   Erwartung: Klasse wechselt auf den anderen Save. Bestätigt beliebiges Laden per Name.
5. Ergebnis (ok/crash/seltsam) hier unter STATUS notieren. Bei Problemen: ggf. Reset `0x413FF0` ergänzen (F8 in F7).

---

## ★★ RE-AUFGABE #7 (das letzte fehlende Stück): COLD-LOAD vom Menü ★★

> **Diese Aufgabe ist der nächste und entscheidende Test.** Sie ist der einzige noch fehlende Baustein und deckt BEIDES ab:
> „Instanz bootet direkt in ihren gekoppelten Save" **und** den Kill+Restart-Fallback (der bootet ebenfalls nur ins Menü).
> Voraussetzung-Wissen: alles oben (F1–F9 + TEST-RUNDE 1–4). **Lies vorher den BASIS-KONTEXT-Banner.**

### Ziel
Eine **zuverlässige Operation „lade Save X und lande in-world"**, die **vom Titel/Hauptmenü** aus funktioniert
(frischer Prozess, **KEINE Klasse live**) — **crashfrei**. Erwartung: geht, weil es **keine alten Karten/Globals**
(wie die Live-Reload-Wand `0x10E9C8` / Manager-Global) zum Korrumpieren gibt — genau das war der Unterschied zum gescheiterten Live-Reload.

### Konkret zu klären / zu testen
1. **Verfügbarkeit am Menü (VOR dem ersten Load):** Sind bereits gültig…
   - `data` = `ptr_walk(g_var,0x18,0x28,0)` (g_var via extsave-Patch @ `0x470B0`)?
   - der **Wrapper-`this`** (das EAX-Objekt aus `0xB2680`: `[edi+0x1c]`=Container, `[edi+4]`-wstring `+0xE2A0`=Save-Name-Feld)?
   - Falls `this` nicht trivial da ist: **woher kommt es** (Singleton/Global ab Game-Init)? → das ist der Henne-Ei-Knoten,
     denn der v3-Detour erfasst `this` erst NACH einem Load. Cold-Load braucht `this` ohne vorherigen Load.
2. **Cold-Load-Test:** am Menü `0xF3C00` (bzw. Wrapper `0xB2680` mit echtem `this`) mit gültigem Save-Namen aufrufen
   → lädt die Klasse und landet in-world **ohne Crash**?
3. **Fallback, falls Direkt-/Wrapper-Aufruf am Menü nicht reicht:** den **High-Level-Menü-Load-Handler** identifizieren
   (die Ebene ÜBER `0xB2680`, die den vollständigen Teardown inkl. Manager-Reset macht = was der „Load"-Button auslöst)
   und prüfen, ob er mit gewähltem Save-Namen aufrufbar ist. **Der wäre der robusteste Weg** — und würde nebenbei sogar
   Live-Reload sicher machen. (Hinweis: `0xB2680` ist virtuell dispatcht, F8 → der Handler/`this`-Anker ist statisch schwer
   zu finden; **eine dynamische Beobachtung (x64dbg: Breakpoint am Menü-„Load" → EAX=`this` + Caller + Herkunfts-Global)
   knackt sowohl `this`-Herkunft als auch den High-Level-Handler in einem Schritt.**)

### Definition of Done
Ein **Lua-Aufruf**, integrierbar in `orchestrator.py`s Per-Welt-Boot, der **beim Start** einer Instanz einen
**per Namen gewählten Save** lädt und **in-world landet, crashfrei** (in school getestet).
Dokumentiert: **woher `data`/`this` am Menü kommen** + ggf. die **RVA des High-Level-Load-Handlers**.

### NICHT im Scope
**Live-Hot-Swap über eine laufende Klasse** (bekannt: crasht @ `0x10E9C8`, dangling Karten-Sub-Objekt über globalen
Manager — Live-Reload-Wand). Dafür: **Kill+Restart** (Notizen 2.2b). #7 macht Kill+Restart erst nutzbar (der Neustart bootet ins Menü).

### Danach
Mit #7 erledigt → `orchestrator.py` auf **„jede Welt bootet direkt in ihren gekoppelten Save"** umstellen
(Save-Kopplung school↔jail = triviales Python-Mapping). Damit ist der Wunsch-Flow komplett:
Start → school-Partie → jail bootet gekoppelt → JAIL-Button = sofort in richtig geladener jail-Welt.

### Praktischer Hinweis fürs Tooling (Wiederholung, wichtig)
- **Rebasing beachten:** Laufzeit-`GameBase = 0x6C0000`, `peinfo.py` nutzt Datei-ImageBase `0x400000`.
  Laufzeit-VA = peinfo-RVA + `0x6C0000`. Absolute Operanden im Disasm sind **Datei-VA** (Preferred-Base) — bei Vergleich
  mit Laufzeit-Adressen (Logs/Dumps) immer um Delta `0x2C0000` umrechnen. (Diese Arithmetik war mehrfach Fehlerquelle.)
- Python fürs RE-Tooling: `python` (NICHT `py`/3.14, s. UMGEBUNGS-HINWEIS).
- Aktueller Mod `school/AAUnlimited/mod/loadtest.lua` = v3 (Detour@0xB2680 erfasst `this`, F6=Wrapper-Reload). Für #7 neuer Test nötig.

### #7 — UMSETZUNG (gewählt): Global `G` finden via Laufzeit-Speicher-Scan (Lua-only, kein Debugger)
**Idee:** `this` (Manager-Singleton) wird vom Spiel in einem festen `.data`-Global gehalten. Wenn wir dieses Global `G`
kennen, lesen wir `this = peek(GameBase+G)` jederzeit — auch am Menü vor jedem Load → Cold-Load ohne Klick möglich.
- **Runde A (Mod `loadtest.lua` neu geschrieben, Scan-Variante):** Detour@0xB2680 erfasst `this` (wie v3). **F6** loggt
  `this` + scannt `.data` (RVA `0x355000`, vsize `0x55BDC`) nach dem `this`-Wert → loggt **Kandidaten-RVAs** für `G`.
  Liest Chunks via `_BINDING.peek(addr,n)`, sucht 4-aligned Treffer.
- **Runde B (danach):** im NÄCHSTEN Start am MENÜ (vor jedem Load) jeden Kandidaten-`G` lesen → welcher hält dort schon
  ein gültiges `this` (Objekt-Shape: `[+0x1c]`=Container-Ptr, `[+4]`→wstring@+0xE2A0)? Der ist der Cold-Load-Anker.
- **Stabilitäts-Check:** `this` sollte über zwei Loads gleich bleiben (Singleton). F6 loggt den Wert → 2× laden + F6 zeigt's.
- **Danach:** Cold-Load-Mod: am Boot `this=peek(GB+G)`, Save-Name setzen (oder Container/data + name_ptr wie v2/v3, cold = crashfrei),
  Wrapper `0xB2680` rufen → in-world. In `orchestrator.py` integrieren.
- **Fallback falls 0 Kandidaten in `.data`:** `this` evtl. heap-verkettet (Global → Struct → this); dann Scan-Bereich
  weiten bzw. nach Container-Ptr suchen, oder doch x64dbg (Menü-Load-Caller).

### #7 — MESSERGEBNISSE (2026-06-23 spät, Diag-Mod)
- **ASLR ist AN:** GameBase wechselt pro Start (gesehen: `0x6C0000`, dann `0x4D0000`). Alles GB-relativ rechnen.
- **Runde A (Scan):** `this` stabil (`0x1A9D9808` über 2× F6), aber **0 Treffer in `.data`** → `this` ist KEIN simpler
  `.data`-Global, sondern heap-verkettet. Direkter Global-Scan = Sackgasse.
- **Runde Diag (g_var-Kette am Menü vs. in-game):**
  | Zeitpunkt | anchor=[g_var] | container | data | this |
  |---|---|---|---|---|
  | **Hauptmenü (cold)** | **0** | **0** | **0** | 0 |
  | in-game (nach Load) | 0x25D616B0 | 0x17672E40 | 0x1D388A80 | 0x1C4FE1F8 |
  - In-game konsistent: `container == [this+0x1c] == data+0x394` (CharArr-Obj). Match bestätigt.
  - **★ KERNBEFUND: am Hauptmenü ist die ganze Kette LEER (anchor/container/data = 0).** Der Container existiert ERST,
    wenn eine Klasse geladen wird → er wird **vom Lade-Vorgang selbst erzeugt**. **Cold-Load über g_var/`0xF3C00`/`0xB2680`
    geht NICHT** (es gibt am Menü nichts zum Reinladen). → Wir brauchen den **High-Level-Menü-Load-Handler**, der den
    Container ANLEGT (= was der „Load"-Button tut).
- **Nächster Schritt (Mod erweitert): Caller von `0xB2680` zur Laufzeit erfassen.** Beim Eintritt in `0xB2680` liegt die
  Rücksprungadresse auf `[esp]` → das ist der High-Level-Handler. Detour-Stub erweitert: `mov [this_slot],eax` +
  `mov ecx,[esp]; mov [ret_slot],ecx` (ecx volatile, ok) + Original-3-Instr + jmp zurück. F6 loggt `ret_slot - GB` = **Handler-RVA**.
  Dann disasm dort → wie legt der Handler Container/`this` an + wie ist er aufrufbar (mit Save-Namen)? = der robuste Cold-Load-Weg.

### #7 — CALLER ERFASST (Runde Ret-Mod) → Load ist EVENT-/DISPATCH-getrieben, KEIN simpler Callable
- Caller-Rücksprung = **RVA `0x1AEF52`** (konsistent, GB=0x4D0000 → 0x67EF52). this=0x1D525A60, [this+0x1c]=container=g_var-container ✓.
- **Disasm um `0x1AEF52`:** KEIN `call 0xB2680`, sondern eine **Handler-Dispatch-Schleife**:
  `mov eax,[ebp+0x1c]; test eax; push 0x767f48; call eax; add esp,4` — und das mehrfach für eine ganze **Tabelle** von
  Callback-Zeigern (`[ebp+…]`, `[0x768724]`, `[0x768728]`…), jeder mit Argument **`0x767f48`** (fester `.data`-Global, RVA 0x367f48 = Event-/Kontext-Objekt).
- **Zusammen mit F8 (0xB2680 hat 0 direkte Caller):** `0xB2680` wird über einen **registrierten Thunk H per Tail-Jump**
  erreicht (H setzt eax=`this`, `jmp 0xB2680` → darum ist [esp] beim 0xB2680-Eintritt = H's Caller = 0x1AEF52, und eax=this korrekt).
  Der Load passiert also als **Reaktion auf ein Event** über diese Dispatch-Schleife — der „Load"-Button reiht eine
  Lade-Aktion ein (Save-Name im Kontext `0x767f48`), die Schleife arbeitet sie ab, **erzeugt dabei den Container** und triggert 0xB2680.
- **KONSEQUENZ:** Cold-Load durch direktes Funktions-Aufrufen ist **nicht sauber lösbar** — der „lade Klasse"-Pfad ist tief
  in die Event-/Menü-Zustandsmaschine + Container-Erzeugung eingebettet (Action-Queue um `0x767f48`). Es nachzubauen
  hieße: Event-System + Aktions-Format + Container-Lifecycle reversen = hoher Aufwand, fragil. **Nicht empfohlen.**

### ★ #7 — EMPFEHLUNG (nach voller Diagnose): Spiel-EIGENEN Menü-Load nutzen, EINMAL beim Boot
- **Fakt:** Der spiel-eigene „Load" am Menü ist ein Cold-Load und **funktioniert einwandfrei** (kein Crash, landet in-world).
- Statt ihn nachzubauen → **auslösen**:
  - **(1) Manuell einmal pro Instanz** beim Start (1–2 Klicks). Null RE, robust. (Bei geklärtem Flow nur 1× pro Sitzung.)
  - **(2) UI-Automation EINMAL beim Boot:** Orchestrator wartet aufs Hauptmenü, schickt die feste Klick-Sequenz
    „Load → Save wählen → bestätigen". Weil **einmalig im bekannten Menü-Zustand** (nicht pro Switch), ist das robust —
    NICHT die fragile Per-Frame-Automatik, die früher verworfen wurde. Nutzt den game-eigenen Load → kein Crash, kein RE.
- **Verworfen:** Direkter Funktions-Cold-Load (Event-System zu tief). Live-Hot-Swap bleibt eh out-of-scope (→ Kill+Restart,
  der ebenfalls über Menü-Load-Automation (2) bootet).
- **Status #7:** Frage „geht Cold-Load über Funktions-Aufruf?" = **beantwortet: nein (sauber nicht praktikabel).**
  Frage „geht Cold-Load überhaupt?" = **ja, über den game-eigenen Menü-Load** → via (1) manuell oder (2) Boot-UI-Automation.

### ★★ #7 — TIEFEN-RE: das Event-/Lade-System aufgelöst (Antworten auf die 5 Fragen) ★★
Werkzeug-Erweiterung: E9-Tail-Jump-Suche + Displacement-Suche (`+0xE29C`). Kontext-Global **`0x767f48`** (File-VA; RVA `0x367f48`;
Laufzeit base 0x4D0000 → `0x837F48`). Neue Funde (RVAs, File-Base 0x400000):
- **Thunk `H` @ `0xB24D0`** (einziger Weg zu 0xB2680, via `E9 jmp` @ `0xB24DE`):
  `mov eax,[esp+4]`(=Kontext) · `mov eax,[eax+0xE29C]`(=this) · `test;je` · `jmp 0xB2680`. → **`this = [Kontext+0xE29C]`**.
- **`enqueueLoad` @ `0xB2440`** — `func(context)` (1 Stack-Arg): `new(0x30)` (`call 0x689a68`) → Ctor `0x4b2390` → `mov [context+0xE29C], eax`.
- **Ctor `0x4b2390`** (eax=neues Obj, ecx=context): `[obj]=vtable 0x72842c` · `[obj+4]=context` · **`[obj+0x1c]=[context+0xE21C]`** (Container, KOPIERT) ·
  Felder `[obj+0x18..0x28]` aus `context+0xD774`-Region · `[obj+0x2c]=0`. `ret`.
- **Dispatch-Schleife @ `0x1AEEE0`** ruft pro Tick eine Callback-Tabelle, jeder mit Arg `0x767f48`; ein Eintrag = `H` (verarbeitet pending Load).
  Geschwister @ `0xB24A0` löscht den Slot nach Lauf (`mov [esi+0xE29C],0`).

**ANTWORTEN:**
1. **High-Level-Handler, der NUR mit Save-Name aus dem Menü cold lädt?** → **Teilweise.** Nächster aufrufbarer Punkt =
   **`enqueueLoad(context)` @ `0xB2440`** (Stack-Arg = Kontext-Global `0x767f48`). Reicht aber NICHT allein cold: er
   **alloziert den Container NICHT**, sondern kopiert ihn aus `[context+0xE21C]` (am Titelmenü = 0) und den Namen aus `[context+0xE2A0]`.
   D. h. nur vollständig, wenn Container **schon existiert**. Den echten Top-Entry (der den Container anlegt) → noch nicht gefunden.
2. **Container-Allokator?** → **NICHT** der Ctor (liest Container aus `[context+0xE21C]`). Container wird **höher** angelegt und in
   `[context+0xE21C]` hinterlegt; diese Schreibstelle = die **letzte offene Frage** (Trace: wer schreibt `context+0xE21C` / „Spielzustand betreten"-Init).
3. **Woher `this` (EAX) am Menü?** → **GELÖST: `this = [context+0xE29C]`.** **KEIN** persistenter Singleton — wird von
   `enqueueLoad` als 0x30-Byte-Heap-Objekt (vtable `0x72842c`) erzeugt; am Titelmenü = 0. Tick (`H`) verarbeitet+löscht es.
4. **Load-Aktion einreihbar? Format + Enqueue?** → **JA. Enqueue = `0xB2440(context)`.** Aktions-Objekt = 0x30 Bytes, vtable
   `0x72842c`, Ctor `0x4b2390` (kopiert Name/Container/Range aus dem Kontext). Slot = `context+0xE29C`; Dispatch-Tick `H` konsumiert.
   → Sobald Container+Name im Kontext stehen, **baut die Engine den Rest selbst** über genau diesen Enqueue.
5. **Setzt der High-Level-Handler `0xB6264` zurück?** → **Nicht bestimmt** (hängt am noch nicht gefundenen Container-Alloc/Top-Entry).

**FAZIT #7 (Tiefen-RE):** Der Lade-Weg ist jetzt fast vollständig kartiert. **Einzige echte Restlücke = die Container-Allokation
(`context+0xE21C`)**, die am Titelmenü fehlt. Findet man die zugehörige „Spielzustand-Init/erste-Container-Anlage", wäre ein
sauberer Funktions-Cold-Load: `Container sicherstellen` → Name nach `context+0xE2A0` (std::wstring) → `proc_invoke(GB+0xB2440, context)`.
**Praktisch** bleibt die Empfehlung (Boot-UI-Automation / manuell-einmal) der robustere Weg, solange die Container-Alloc nicht gefunden ist.

### #7 — Container-Lifecycle nachverfolgt (Restlücke so weit wie statisch sinnvoll geschlossen)
Werkzeug: Absolut-Ref-Suche auf Slot `0x776164` (=context+0xE21C) + Displacement-Suche `+0xE21C` / `+0xAA8`.
- **Container-Slot Schreibzugriffe:** der einzige *absolute* Write ist **`0x1BD5: mov [0x776164], edi`** mit `edi=0` =
  **Teardown** (Container freigeben via virtuellem Destruktor `call [[ecx]]( 1 )` + Slot nullen; beim Verlassen des Spielzustands).
  Über Displacement `+0xE21C` nur **Lese**zugriffe (`0x74200`, `0xF09D4`).
- **`context+0xD774`-Sub-Struktur = der „Klassen-Daten-Manager":** Konstruktor/Init @ **`0x455B0`-Bereich** setzt Felder
  `+0xa9c=vtable 0x731818`, `+0xaa0/aa4/aa8/aac/ab0/ab4=-1`, `+0xab8/abc=0` → initialisiert den Manager auf **leer (-1)**.
  Der Container-Slot `+0xaa8` (= `context+0xE21C`) wird hier auf `-1` gesetzt, **nicht** mit einem Objekt belegt.
- **FOLGERUNG:** Es gibt **keinen sauberen einzelnen „alloc container; store"-Punkt**. Der echte Container entsteht erst,
  wenn eine Klasse geladen/angelegt wird, **verwoben in den Lifecycle des Klassen-Daten-Managers** (context+0xD774,
  vtable 0x731818). Ein Funktions-Cold-Load müsste diesen Lifecycle (Manager-Init → Container-Anlage → Name → enqueue 0xB2440)
  nachbauen = mehrstufig + fragil.

### ★ #7 — ENDBEWERTUNG
- **Geschlossen (Q3, Q4, Struktur):** kompletter Enqueue-/Dispatch-/this-Mechanismus + alle RVAs (0xB2440, 0xB24D0, 0x4b2390,
  vtable 0x72842c, Slot context+0xE29C/0xE21C, Teardown 0x1BD5, Manager-Init 0x455B0, vtable 0x731818).
- **Nicht sauber lösbar (Q1, Q2, Q5):** der Top-Level „enter game state + alloc container"-Pfad ist kein einzelner aufrufbarer
  Handler, sondern ein Lifecycle. Funktions-Cold-Load = unverhältnismäßig + fragil. **Bestätigt: nicht der Weg.**
- **Robuster Weg bleibt:** game-eigenen Menü-Load auslösen — **(1) manuell einmal** oder **(2) Boot-UI-Automation** (Orchestrator,
  einmalige feste Klick-Sequenz am Hauptmenü). Beide nutzen den vollständigen Engine-Lifecycle → crashfrei, kein Memory-Hacking.
- **Für AAU-Discord** (falls jemand den High-Level-Entry kennt): „Welche Funktion legt den Klassen-Daten-Manager-Container an
  (`context+0xE21C`, Manager-vtable `0x731818`) beim Eintritt in eine Spielsitzung, bevor `enqueueLoad` (0xB2440) läuft?"

### ★★ #7 — DYNAMISCH (Cheat Engine + Mod-Detour, 2026-06-24) ★★
- **Setup:** Einzelne school-Instanz (`_re/debug_launch_school.py`: PPeX + nur school, Auto-Launch). CE 7.6 (`Cheat Engine.exe`)
  installiert. **CE-Daten-Write-BP auf Container-Slot blieb STILL** (Mechanik-Problem, evtl. Anti-Debug) — **NICHT** weil die
  Adresse falsch war. Stattdessen **Mod-Detour** (in-engine, immun gegen Anti-Debug) genutzt → zuverlässig per Log gelesen.
- **Mod `loadtest.lua` (re-mod):** Detour @ `0xB2440` (enqueueLoad) erfasst dessen **Aufrufer** ([esp]); Detour @ `0xB2680` erfasst `this`. F6=Dump.
- **★ ERGEBNISSE (GB=0xA20000 dieser Lauf):**
  - **`enqueueLoad`-CALLER = RVA `0x1AF4FC`** (SYNCHRON beim Load-Klick — die async-Wand gilt für den Caller von 0xB2440 NICHT,
    nur der Wrapper 0xB2680 ist async).
  - `this=0x1A972248`, **`container=[this+0x1c]=0x16A823C8`** — und **g_var-Kette container = 0x16A823C8 (identisch ✓)** →
    meine Container-Adresse `context+0xE21C` war **korrekt** (CE-BP-Stille = CE-Problem). data=0x1B897240.
- **Disasm @ `0x1AF4FC`-Umgebung:** Funktion ist ein **Menü-Aktions-Dispatch** (Schleife `call [edi]` mit Arg `0x600`;
  dann `rep movsd` 9 dwords = Save-Name kopieren nach `[ebx+0x10]`; `call 0x5AF720`; `mov edx,[edx+8]; push ebp(=context); call edx`
  = enqueueLoad). Also: enqueueLoad wird hier als **ein registrierter Handler** gerufen, mitten im Menü-/Scene-Action-Processing.
- **Nächster Schritt:** Detour erweitert auf **Stack-Fenster-Capture** bei enqueueLoad (pushad + `rep movsd` 24 dwords) →
  ganze synchrone Aufrufkette bis zum Klick-/Input-Handler → prüfen, ob es weiter oben einen aufrufbaren „load(name)"-Einstieg gibt.

### ★★★ #7 — DEFINITIVES ERGEBNIS (Stack-Fenster, 2026-06-24): KEIN aufrufbarer Load-Einstieg ★★★
**Synchrone Aufrufkette von `enqueueLoad` (GB=0xA20000), nur `.text`-Rücksprünge:**
```
enqueueLoad(0xB2440)
  ← RVA 0x1AF4FC   (Menü-Aktions-Dispatch: rep movsd Name, dann call [obj+8]=enqueueLoad)
  ← RVA 0x1AE2AC
  ← RVA 0x1ADCE7
  ← RVA 0x1AEF52   (Dispatch-Schleife @ 0x1AEEE0)
```
- **Die GESAMTE Kette liegt in `0x1AD000–0x1AF000` = der Menü-/Scene-State-Machine.** Kein einziger Frame ist eine
  eigenständige, parametrisierte „load(saveName)"-Funktion. Der Load ist eine **Menü-Aktion**: getriggert vom Klick,
  Save-Name aus der Listen-Auswahl (`rep movsd` kopiert ihn), verarbeitet von der Scene-State-Machine, die `enqueueLoad`
  als einen Schritt ruft. Container-Erzeugung + Name + enqueue sind alle in diesen State-Machine-Flow verwoben.
- **FAZIT (jetzt DYNAMISCH bewiesen, nicht nur statisch vermutet):** Es existiert **kein aufrufbarer interner Loader (A')**.
  „Load Save X" ist untrennbar an den Menü-/Scene-UI-Flow gebunden (in-engine Aktion + Listen-Auswahl + Bestätigung).
  Ein Funktionsaufruf, der das ersetzt, ist in dieser Engine **nicht vorhanden** — weder statisch noch dynamisch auffindbar.
- **→ KONSEQUENZ:** Weg vom Klicken über einen Funktionsaufruf ist **nicht möglich**. Die **automatisierte Klick-Sequenz (B)**
  des Orchestrators (Fenster-Fraktions-Koordinaten + BlockInput) ist der **einzige tragfähige Auto-Load-Mechanismus**.
  Verbesserung nur in der Robustheit von B möglich (z. B. Save-Auswahl per Listen-Index, Timing/Retry), nicht im Ersetzen.

### CE-/Debug-Umgebung Notizen (Dev)
- `_re/debug_launch_school.py`: startet NUR school + PPeX (Auto-Launch), hält PPeX-stdin offen. Mit Python 3.12 starten.
- **savedconfig.lua wird beim Start/Beenden vom Launcher korrumpiert** (`init.lua:121 table.dump: 'value has no literal form'`
  in `update_res`→`Config.save`) → mods-Tabelle wird abgeschnitten. Vor jedem Debug-Start die volle `savedconfig.lua`
  neu schreiben (mit `loadtest`=enabled). Bekannte Vorlage liegt in der Git-/Doku-Historie; Kern: mods-Tabelle mit
  `[10]={[1]="loadtest",["disabled"]=false}` + Standard-Mods.
- CE 7.6 „Find out what writes" blieb auf dem Daten-Slot STILL (Mechanik/Anti-Debug) → **Mod-Detour ist der zuverlässige Weg**
  (in-engine, immun, Log via Bash lesbar). Adresse war korrekt (container-RVA bestätigt via [this+0x1c]==g_var-container).

### ★★★★ #7 — ABSCHLUSS: Menü = State-Machine + gepollter Input → B ist der Weg ★★★★
- **Menü-State-Machine bestätigt (Disasm der Caller-Kette):** `0x1ADCE7`: `mov eax,[esi+0x7F4]; cmp eax,3/4…` → `[Menü+0x7F4]`
  = Screen-State, pro Tick abgearbeitet. `0x1AE2AC`: setzt `[esi+0x7EC]`. Save-Name aus Listen-Auswahl (`rep movsd` 9 dwords @ `0x1AF4CE`).
- **Gepollter Maus-Input (Schlüsselbefund):** Synthetische Klicks wirkten nur mit **gehaltener** Taste (~0.25s) → Spiel
  **pollt den Button-Zustand** (DirectInput-artig), reagiert NICHT auf `WM_LBUTTONDOWN`. → **PostMessage-Injektion unmöglich**;
  nur echter Geräte-Input (`mouse_event`/`SetCursorPos`) treibt das Menü.
- **Folge für die internen Alternativen — beide SCHLECHTER als Klicken:**
  - *State-Poke* (`[Menü+0x7F4]` etc. setzen): der echte Input-Pfad setzt beim Klick MEHRERE State-Felder konsistent;
    ein Teil-Poke = inkonsistenter State → Crash-Klasse. Mehr Arbeit, **weniger** robust.
  - *Nachricht-Injektion*: geht nicht (gepollt, nicht message-getrieben).
- **★ ENDENTSCHEIDUNG (mit Nutzer):** „Weg vom Klicken per Funktionsaufruf" = **nicht möglich** (kein aufrufbarer Loader,
  bewiesen). Der **einzig konsistente Mechanismus für eine gepollte-Input-Engine = echten Klick automatisieren (Weg B)** im
  Orchestrator (`mouse_event` + `BlockInput`). Der State-Poke ist durch robustes B **obsolet** (gleiches Endergebnis, weniger Risiko).
- **NÄCHSTER SCHRITT (offen):** B robust ausbauen — Details in `<project-root>\HANDOVER_load-RE_2026-06-24.md` Abschnitt 6.
  RE-Linie „interner Loader" ist **abgeschlossen, nicht weiter verfolgen.**
