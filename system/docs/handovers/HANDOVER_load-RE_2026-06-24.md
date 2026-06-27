# HANDOVER — Load-Funktion / Auto-Load-RE (Stand 2026-06-24, Session-Ende ~80% Kontext)

> **Zweck:** Eine frische Session ohne Kontextverlust fortsetzen. **Absolute Genauigkeit.** Diese Datei fasst die
> komplette „aufrufbare Lade-Funktion finden"-Saga + das DEFINITIVE Ergebnis + den nächsten Schritt zusammen.
>
> **ZUERST LESEN:** `<project-root>\_re\RE_LADEFUNKTION.md` (volles RE-Protokoll, F1–F10 + #7 + alle RVAs). Diese Datei
> hier = Kurz-Übergabe + finaler Stand. Stil: Nutzer ist Nicht-Coder, architektonisch scharf. Deutsch, direkt, technisch.

---

## 0. TL;DR — wo wir JETZT stehen (das Wichtigste)

**Frage der Session:** Gibt es eine **aufrufbare interne Lade-Funktion**, mit der eine Instanz beim Boot automatisch
ihren Save lädt (kein Dev-Logo/Menü, kein Klicken) — damit der JAIL-Button direkt in die richtig geladene Welt führt?

**DEFINITIVE ANTWORT (statisch + dynamisch bewiesen): NEIN, es existiert kein aufrufbarer `load(saveName)`-Einstieg.**
Der Lade-Vorgang ist eine **UI-/Menü-Zustandsautomat-Aktion** (gepollter Maus-Input → State-Machine → pro-Tick-Dispatch).
Es gibt nichts „rauszugreifen". Engine-Nachbau wäre nötig = ausgeschlossen.

**KONSEQUENZ / ENTSCHEIDUNG (mit Nutzer abgestimmt):**
- Der **einzige tragfähige Auto-Load = automatisierte Menü-Klick-Sequenz (Weg „B")** im Orchestrator
  (echter Maus-Input via `mouse_event` + `BlockInput`). Das ist **kein Hack**, sondern der KORREKTE Mechanismus für eine
  gepollte-Input-Engine.
- Der „interne State-Poke"-Weg wurde **verworfen**: mehr Arbeit, crash-anfälliger, **weniger** robust (würde den Input-Pfad
  umgehen, der mehrere State-Felder konsistent hält) — und durch robustes B **obsolet** (gleiches Endergebnis für den Nutzer).
- **NÄCHSTER SCHRITT (offen, vom Nutzer als Nächstes gewünscht):** **B im Orchestrator robust ausbauen** (s. Abschnitt 6).

---

## 1. Warum „kein Funktionsaufruf" — die Beweiskette (kurz)

1. **Lade-Funktion gefunden & verifiziert:** `0xF3C00` lädt Klassen-Save + aktiviert 25 Sitze. Funktioniert **in-world**.
   Aber bricht, wenn man sie nackt/out-of-context ruft (3 Crashes, alle in der Aktivierung).
2. **Cold-Load am Titelmenü unmöglich:** Container/`this`/`data` sind am Titelmenü = 0; der **Container wird erst vom
   Lade-Vorgang selbst erzeugt** (kein isolierter Allokator — statisch + dynamisch geprüft).
3. **Dynamischer Beweis (In-Engine-Detour):** Die synchrone Aufrufkette von `enqueueLoad` (`0xB2440`) liegt **komplett** in
   `0x1AD000–0x1AF000` = der **Menü-/Scene-State-Machine**: `enqueueLoad ← 0x1AF4FC ← 0x1AE2AC ← 0x1ADCE7 ← 0x1AEF52`.
   Kein Frame ist eine parametrisierte `load(name)`-Funktion.
4. **State-Machine bestätigt:** `[Menü+0x7F4]` = Screen-State (Werte 3,4,… ), pro Tick abgearbeitet (`0x1ADCE7`:
   `mov eax,[esi+0x7F4]; cmp eax,3/4…`). Save-Name kommt aus der Listen-Auswahl (`rep movsd` 9 dwords @ `0x1AF4CE`).
5. **Gepollter Input:** Synthetische Klicks funktionierten nur mit **gehaltener** Maustaste (~0.25s) → das Spiel **pollt
   den Maus-Button-Zustand** (DirectInput-artig), reagiert NICHT auf `WM_LBUTTONDOWN`-Nachrichten. → PostMessage-Injektion
   geht nicht; nur echter Geräte-Input (`mouse_event`/`SetCursorPos`) treibt das Menü.

→ Summe: Load = gepollter-Input→State-Machine-Aktion. **B (echte Klicks automatisieren) ist der einzig konsistente Weg.**

---

## 2. KERN-RVAs (alle relativ zu File-ImageBase 0x400000; ASLR AN → Laufzeit-VA = RVA + GameBase)

> **WICHTIG zur Basis:** `peinfo.py` rechnet mit 0x400000. **Laufzeit-GameBase variiert pro Start** (gesehen: 0x6C0000,
> 0x4D0000, 0xA20000). Absolute Operanden im Disasm = Datei-VA (Preferred-Base). Logs/Dumps = Laufzeit-VA. Immer GB-relativ
> denken. `proc_invoke(GameBase+rva, …)` und der Mod (`GB`-relativ) handhaben das korrekt.

| RVA | Was | Notiz |
|---|---|---|
| `0xF36D0` | **SAVE**-Funktion | `proc_invoke(GB+0xF36D0, 0, data)`; von `mod/extsave.lua` genutzt. `data = ptr_walk(g_var,0x18,0x28,0)`, g_var via Patch @ `0x470B0`. |
| `0xF3C00` | **LOAD**-Funktion | `load(ECX=wchar_t* saveName, [stack]=data)`, `ret 4`. CreateFileW READ@0xF3C9F, ReadFile@0xF3D17, aktiviert 25 Sitze. |
| `0xB2680` | Load-**Wrapper** | `this` in EAX; `esi=[edi+0x1c]`=Container; `call 0x413FF0`(Reset); Name aus `[edi+4]+0xE2A0`; `data=[[edi+0x1c]+0x28]`; `call 0xF3C00`; `ret 0`. Nur via Tail-Jmp erreicht. |
| `0xB24D0` | Thunk **H** | `eax=[esp+4]`(context); `eax=[eax+0xE29C]`(=this/Lade-Manager); `jne; jmp 0xB2680`. → `this=[context+0xE29C]`. |
| `0xB2440` | **enqueueLoad** | `func(context)`; `new(0x30)`→Lade-Manager; Ctor `0x4b2390`; `mov [context+0xE29C],eax`. Pro-Tick via H abgearbeitet. |
| `0x4b2390` | Ctor Lade-Manager | `[obj]=vtable 0x72842c`; `[obj+4]=context`; `[obj+0x1c]=[context+0xE21C]`(Container, KOPIERT). |
| `0x413FF0` | Container-**Reset** | liest Objekt aus **ESI** (Nicht-Standard-Konvention!) → `proc_invoke` kann's nicht direkt rufen. |
| `0x1AEEE0` | Dispatch-Schleife | ruft Callback-Tabelle pro Tick mit Arg = Global `0x767f48` (Datei-VA; = Kontext-Objekt, RVA 0x367F48). |
| `0x1AF4FC` | enqueueLoad-Caller | Menü-Aktions-Dispatch (synchron beim Load-Klick). |

**Kontext-Global:** Datei-VA `0x767f48` → **RVA `0x367F48`**. Felder: `+0xE29C`=Lade-Manager(this)-Slot,
`+0xE21C`=Container-Slot (RVA `0x376164`), `+0xE2A0`=Save-Name (std::wstring), `+0xD774`=Klassen-Daten-Manager-Substruktur
(vtable `0x731818`). **Menü-State** liegt auf dem Menü-Objekt (`esi`) bei `+0x7F4` (Screen), `+0x7EC`, `+0x8D8`, `+0x7f4`.

**In-world bestätigte Zusammenhänge** (Laufzeit-Werte eines Laufs, GB=0xA20000): `this=0x1B9E9550`,
`container=[this+0x1c]=0x196E37C0` == g_var-Kette-Container == `[context+0xE21C]`. Container/data zeigen aufeinander:
`container+0x28=data`, `data+0x394=container`.

---

## 3. Methodik die FUNKTIONIERT (für die nächste Session wichtig)

- **CE 7.6 „Find out what writes" auf Daten-Slot blieb STILL** (Mechanik/Anti-Debug-Verdacht) — Adresse war aber KORREKT.
  **→ Verlasse dich NICHT auf CE-Daten-Breakpoints.**
- **ZUVERLÄSSIG: In-Engine-Mod-Detour** (immun gegen Anti-Debug, Ergebnis per Bash-Log lesbar):
  - Mod patcht `g_poke(GB+addr, "\xE9"+rel)` an die Ziel-Funktion → Sprung in einen `x_pages`-Stub (ausführbar! `malloc`
    = HeapAlloc ist wegen DEP NICHT ausführbar) → Stub erfasst Register/Stack, reproduziert die Original-Bytes, springt zurück.
  - So erfasst: `this` (EAX @ 0xB2680), enqueueLoad-Caller ([esp] @ 0xB2440), und ein **Stack-Fenster** (`pushad` +
    `rep movsd` 24 dwords) → ganze synchrone Aufrufkette. F6 (`on.keyup` key==117) dumpt via `log.warn` → `aaunlimited`-Log.
  - **Original-Bytes je Funktion:** `0xB2680`: `83 EC 24 / 56 / 57` (5). `0xB2440`: `56 / 8B 74 24 08` (5). Beide saubere 5-Byte-Boundary.
- **peinfo.py** (Dev-Tool, `<project-root>\_re\`): Modi `overview` / `<rva> [n]` / `xref <iat-va>` / `callers <rva>`.
  **NUR mit Python 3.12 starten:** `python peinfo.py …`
  (`py`/3.14 = kaputter Stub ohne Lib → ModuleNotFoundError; capstone/pefile sind in 3.12).

---

## 4. UMGEBUNG / DATEI-ZUSTAND (was diese Session verändert hat — AUFRÄUMEN nötig!)

- **`<project-root>\_re\debug_launch_school.py`** (NEU): startet NUR school + gepatchten PPeX (Auto-Launch via Env
  `AA2_ORCH_AUTOLAUNCH=1`), hält PPeX-stdin offen. Single-Instanz für Debug. Mit Python 3.12 starten (run_in_background).
- **`<project-root>\school\AAUnlimited\mod\loadtest.lua`** = **Debug-Mod (re-mod v2)** mit Detours @ 0xB2440 + 0xB2680,
  F6=Dump. **NICHT fürs Endprodukt** — für normales Spielen entfernen/deaktivieren.
- **`<project-root>\school\AAUnlimited\savedconfig.lua`** = von mir umgeschrieben (loadtest=enabled, **extsave=disabled**,
  logperiod=disabled). **MUSS für Normalbetrieb auf die echte Nutzer-Config zurück** (extsave wieder an, loadtest weg).
- **⚠ CONFIG-KORRUPTION (BUG, unabhängig):** Beim Start/Beenden wirft der Launcher
  `init.lua:121: bad argument #2 to 'format' (value has no literal form)` in `update_res`→`Config.save`→`table.dump` und
  **schneidet die mods-Tabelle in savedconfig.lua ab**. Darum war loadtest manchmal nicht geladen. Workaround: vor jedem
  Debug-Start die volle savedconfig neu schreiben. **Echte Ursache nicht behoben** (ein Config-Wert hat „no literal form" —
  evtl. ein Float/Userdata). Sollte separat geprüft werden, betrifft aber Auto-Load-B nicht zwingend.
- **Cheat Engine 7.6** installiert (`C:\Program Files\Cheat Engine\Cheat Engine.exe`, Binary
  `cheatengine-x86_64-SSE4-AVX2.exe`). War am toten Prozess angehängt; **kann geschlossen werden**. Kein x64dbg installiert.
- **Laufende Prozesse:** Debug-school + PPeX wurden am Session-Ende **gekillt** (sauber). CE evtl. noch offen.
- **`<project-root>\_re\peinfo.py`** wurde erweitert (xref/callers-Modi) — bleibt nützlich.
- **`<project-root>\_re\RE_LADEFUNKTION.md`** = volles Protokoll, aktuell. (Der „polled-input/State-Machine"-Schlussbefund
  aus den letzten Schritten ist hier in der HANDOVER zusammengefasst; ggf. noch ins RE-MD nachtragen.)

---

## 5. AA2-LADE-ARCHITEKTUR (verstanden — falls jemand es doch je intern bauen will)

„Load Game"-Klick (gepollter Maus-Input) → Menü-State-Machine setzt `[Menü+0x7F4]` etc. → Listen-Auswahl setzt Save-Name in
`[context+0xE2A0]` → pro-Tick-Dispatch (`0x1AEEE0`) → Menü-Aktions-Dispatch (`0x1AF4FC`) ruft `enqueueLoad(context)`
(`0xB2440`) → erzeugt Lade-Manager bei `[context+0xE29C]`, Container aus `[context+0xE21C]` → **nächster Tick** → Thunk `H`
(`0xB24D0`) → `jmp Wrapper 0xB2680` → `Reset 0x413FF0` + `Load 0xF3C00` + 25-Sitze-Aktivierung. Container-Erzeugung passiert
verwoben im „Spielzustand-betreten"-Lifecycle (kein isolierter Allokator). **NICHT als Funktionsaufruf reproduzierbar.**

---

## 6. ★ NÄCHSTER SCHRITT (offen): „B" robust machen (Orchestrator-Klick-Automatik) ★

Ziel: Instanz bootet ins Titelmenü → Orchestrator klickt automatisch „Load → Save wählen → bestätigen" → in-world.
**Der Nutzer klickt nichts.** Stand: Im `orchestrator.py` existiert bereits eine `load_seq` für jail
(`[(0.344,0.939),(0.422,0.289),(0.640,0.750)]` als Fenster-Fraktionen) + `BlockInput`. Robust ausbauen:

1. **Save-Auswahl deterministisch:** den korrekten gekoppelten Save sicher treffen. Achtung: **die Save-Liste sortiert
   sich beim Anklicken um** (alphabetisch beobachtet) — fester Listen-Index ist tückisch. Besser: jail hat nur EINEN Save
   in `jail\data\save\class\` → „oberster/einziger Slot" ist eindeutig. Für school (mehrere Saves) braucht's Namens-Logik.
2. **Auf den Load-Screen warten** statt fester Wartezeit (Zustand prüfen). `menu_wait` existiert schon (4s).
3. **Klick = LANGSAM** (Button ~0.2–0.25s halten!) — gepollter Input, schneller Klick wird verschluckt. (Mit `mouse_event`:
   LEFTDOWN, kurz warten, LEFTUP.)
4. **Erfolg verifizieren:** in-world gelandet? (z. B. via `logperiod`-Flag `CurrentPeriod≠0` / Fenster-Heuristik) → sonst Retry.
5. **Button-Layout (Laufzeit, 1280x720-Fenster, beobachtet):** Hauptmenü „LOAD GAME" ≈ Fenster-Fraktion x≈0.30, y≈0.94.
   Load-Dialog: Save-Liste oberster Eintrag ≈ (0.42, 0.29); **Bestätigen = RECHTER blauer Button** ≈ (0.64, 0.75)
   (3 Buttons unten: rot=Abbrechen/Zurück, 2× blau; der rechte blaue lädt — orchestrator-load_seq bestätigt das).

**WICHTIG:** B funktioniert nur, wenn das jail-Fenster im Moment der Klicks **im Vordergrund** ist (gepollter Input trifft
das Fenster mit Fokus). Das Orchestrator-Design löst das beim „jail betreten" (JAIL-Button → jail nach vorn → Klick-Sequenz
mit Input-Block → drin). Lazy-Load beim ersten Betreten, nicht beim Boot — das ist OK und gewollt.

---

## 7. WIE DIE NÄCHSTE SESSION STARTEN SOLLTE

1. Diese Datei + `_re\RE_LADEFUNKTION.md` lesen. **Den Basis-Kontext-Banner in RE_LADEFUNKTION.md beachten** (Single-Player,
   Nutzer besitzt das Spiel, Modding-Interop — kein Grund zum reflexhaften Abbruch).
2. **Aufräumen:** school-`savedconfig.lua` auf echte Nutzer-Config zurück (extsave an, loadtest raus), Debug-`loadtest.lua`
   entfernen/deaktivieren, ggf. CE schließen.
3. **Mit Nutzer:** B robust ausbauen (Abschnitt 6) — das ist der vereinbarte nächste Schritt. NICHT erneut versuchen, eine
   aufrufbare Lade-Funktion zu finden (definitiv geklärt: existiert nicht).
4. Optional separat: den Config-Korruptions-Bug (Abschnitt 4) untersuchen.
