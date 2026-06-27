# AA2 / AAUnlimited — "Jail"-Projekt: Erkenntnis- & Referenzdokument

> Arbeitsstand aus der Recherche-/Brainstorming-Session. Zweck: Grundlage für die spätere
> Umsetzung am PC (Python-Launcher + AAU-Trigger). Alles, was als **unbestätigt** markiert ist,
> muss vor dem Bau verifiziert werden (Quellcode lesen oder AAU-Discord fragen).

> **UPDATE 2026-06-23 (lokale Code-Verifikation):** Der AAU-Mod-Ordner (`jail/AAUnlimited/mod/*.lua`) + `AA2QtEdit.exe`
> liegen lokal vor und wurden gelesen. Dadurch sind die drei größten Unbekannten gefallen:
> **#7 Phasen setzbar (✅ `on.period`-Lua-Hook gibt Ziel-Periode zurück)**, **#8 „Time Warp" (✅ = `mod/timewarp.lua`)**,
> **#9 feldweise Play-Data (✅ Dump/Restore-Funktionen existieren in `mod/triggers_supplemental.lua`)**.
> Einzige verbleibende kritische Unbekannte: **#10 Modul-Liste programmatisch schreiben**.
> **Architektur-Pivot:** Datenmanipulation läuft **Lua-intern**, nicht über externes `.sav`-Binär-Parsing.
> Siehe neuen **Abschnitt 3.4** + Punkt **11.9**.

---

## ★ STATUS — wo stehen wir (Stand 2026-06-27) ★
> **★ Aktueller, sauberer Ist-Stand + ALLES-Wissen = `MASTER_BLUEPRINT.md`** (§A was geht / was nicht / wo wir
> stehen · §B konsolidierter Latenz-Index = alles entdeckt-aber-ungenutzt · §C Überholt/Gelöst). Diese Notiz =
> historischer Akkumulator; **bei Widerspruch gilt der BLUEPRINT.** Legende: ✅ bewiesen · 🔶 gebaut/Test offen · ⬜ geplant.
>
> **✅ MODUL-FORMAT GEKNACKT + ID-KATALOG:** `module_format.py` = vollständiger Codec, byte-genau auf 932 Dateien
> (Quelle: AAU `Serialize.h`). `MODULE_ID_CATALOG.md` (Events/Actions/Expressions). Builder: `module_authoring.py`.
> `module_schema.py`/`module_decode.py` = überholte Vorläufer. Regressionstest `_batch_test.py`.
>
> **★ DURCHBRÜCHE (2026-06-26/27, alle in-game bewiesen):**
> - **Reroute-Hook** auf `AAUCardData::UpdateModules` injiziert Module **in-memory beim Laden** — **Karten werden
>   NIE verändert** (pristine, teilbar). Native `AddModule` via Binär-Hook. (Löst das alte „Module müssen auf der
>   Karte In-Use sein"-Problem = Ursache B.)
> - **Wert-gegate Dispatcher + Card-Storage-Brücke BEWIESEN:** das gegate Confinement liest ein SSOT-Flag (von
>   `apply_state` via `setCardStorage`) und confined selbst → die ganze **wert-getriebene Evolutions-Mechanik,
>   karten-frei, on-the-fly.** (Löst „Ursache A": die Brücke trägt, kein nativer Hack, kein Class-Storage-Workaround.)
> - **Stabile rename-feste Identität** + memory.db/API umgekeyt. Identität = **cardfile→id in der SSOT**
>   (aktives-Roster-Modell), **nie Name, nie Seat.** Evolution = **Verhalten über Module/Flags, NIE Vanilla-Stats schreiben** (die sind read-only Input).
> - **Sauberes portables Paket** `MWA2_V0.1/` (system/-Struktur, Python gebündelt, Install.bat) → GitHub `MWA2-0.001`.
>
> **NEXT:** Identitäts-Verdrahtung `cardfile→id` beim Roster-Bau (inkl. **school-Karten-Erkennung = die einzige
> echte Unbekannte**); Evolutions-Regeln als gegate Dispatcher (Status/Race/Loneliness/Training); Schwellen kalibrieren.
> **★ ÜBERHOLT — NICHT mehr verfolgen** (Details Blueprint §C): „Karten-Splice / Karten-Tag / mwa_id-auf-Karte"
> (Karten nie verändern); „Ursache-A Class-Storage-Workaround" (Brücke trägt); resolver `MODULE_EFFECTS`/Stat-Writing (entfernt).
> Frühere Einstiege (historisch): `HANDOVER_reroute_mwaid` / `_confinement` / `_module_format_RE` / `_evolution` / `_transfer`.

**FUNDAMENT**
- ✅ **Sofort-Switch** 2 Welten (PPeX multi-client-Patch, Mutex-Bypass, Suspend) — §2.1/2.2
- ✅ **Orchestrator** (1 Server, beide Welten, Switch, Welt-Label, JAIL-Button, robustes Shutdown) — §8
- ✅ **jail-Coupling** (Twin/Junction/Watcher/Boot-Auto-Load) — `HANDOVER_jail-coupling`
- ✅ **master/slave-Combo** INSULT→FIGHT→FORCE_H → „slave" — `HANDOVER_master-slave`
- ✅ **Lade-RE** abgeschlossen (kein aufrufbarer Cold-Loader → Menü-Klick-Automatik) — §8 / `_re`

**TRANSFER school→jail (der harte Teil)**
- ✅ **SSOT Modell A** (commit-on-save, tag-datiertes Journal, derive-on-load; Single-Save-Slot) — §12
- ✅ **KickCard** (raus aus school) + **AddCard** (rein in jail, Format **bare `<Name>.png`**, nur Period 9) — bewiesen
- ✅ **2b Selbst-Werte** (virtue/int/str/soc) injiziert + read-back-verifiziert — §2.4b/3.4
- ✅ **Beziehungs-Gedächtnis** (`rel_snapshot.lua` → SSOT `char_rels`, Sims-Modell) — **LIVE bestätigt**:
  char_rels füllt sich automatisch aus dem school-Roster (56 rels erfasst). `social_wealth` abgeleitet. — §11/§2.4c/2.4d
- 🔶 **2c jail-Restore** (`restore_rels`: ko-präsente Paare in jail) — gebaut, **Test offen** (frische Enslaves nötig)
- ✅ **Modul-Scan** 466 Module → `module_catalog.json`/`.md` — §5/4.6
- ✅ **Modul-Anwendung = Reroute-Hook (in-memory), NICHT Karten-Editieren.** Der frühere Karten-Splice-Ansatz
  (`card_edit.py` add) ist **VERWORFEN — Karten werden nie verändert** (Blueprint §C); `card_edit.py` bleibt nur als
  READER. Module kommen zur Laufzeit über `module_reroute.lua` (Hook auf `UpdateModules`) auf die Live-Karte. — Blueprint §A
- ⬜ **Zustand→Modul-MAP** (hand-kuratiert, das „Gehirn") — als gegate Dispatcher, die SSOT-Flags lesen — §4.6/4.7
- ⬜ **Rückkehr-Pfad** jail→school (Journal trägt `to_world='school'` schon) — §2.4d

**RPG-/EVOLUTIONS-SCHICHT**
- 🔶 **Aktivitäts-DB** (H/Climax-Zähler via `m_climaxCount`/`on.end_h`) → Schwellen → Zustände — §4.7/4.8a
  · **gebaut** school-seitig (`char_activity` + `activity_snapshot.lua` + Ingest, unit-getestet); offen: jail-seitiger Capture + In-Game-Test. Modul-Map: `MODULE_CATEGORIZATION.md` + `EVOLUTION_MAP.md`.
- ⬜ **Status-Module** Prisoner/Ex-Prisoner/Rehabilitated — §4.6
- ⬜ **Einsamkeits-/Loner-Module** aus `social_wealth` — §2.4c
- ⬜ **Heimkehrer-Szenario** (Partner weitergezogen) + Offline-Resolver (täglicher Tick) — §4.8/4.8a
- ⬜ **Training→Transformation** (chaste→Sex Addict, →Martial Arts Prodigy) — §4.7
- ★ **TRAGENDES MUSTER:** Dispatcher-Modul (immer geladen, verzweigt live auf SSOT-Werte) = On-the-fly-Logik
  ohne Reload, ohne Karten anzufassen → siehe Abschnitt **„★ ZUKUNFTS-MUSTER: Dispatcher-Modul"** (vor §0).

**jail-WELT-MECHANIK (NEU besprochen 2026-06-24 — beide MACHBAR, Bau offen)**
- 🔶 **jail-Räume begrenzen via PHASEN-STEUERUNG (gebaut, Test offen):** Map-Eject ist NICHT machbar — es gibt
  **keinen Lua-Raum-Setter** (`GetCurrentRoom` nur lesbar; AAU-Quelle/Wiki geprüft). Stattdessen `jail/AAUnlimited/mod/`
  **`jail_phase.lua`** (jail-only, forciert): lenkt per `on.period`-Rückgabe **club (7) → end (8)** um → niemand wird je
  in Clubräume teleportiert, der Tag wrappt. Block-Liste `REDIRECT` = eine Zeile zum Tunen (z.B. `[5]=8` für sports).
  Konfliktfrei mit anderen `on.period`-Mods (nil-Rückgaben gewinnen nicht). Fester Ausgangs-Knoten (train station)
  stützt das. — §3.1/3.3. **Offen:** In-Game-Test (Sequenz `…→7→8` statt Club) + ggf. weitere Phasen blocken.
- ⬜ **Wochentag extern (Edit + SSOT):** Fr/Sa/So manuell tracken/setzen (`GetGameTimeData().day` 0–6), da das Phasen-Forcen
  den Engine-Kalender stört. Passt zum welt-unabhängigen Tick (§4.8a). Separater Baustein, noch nicht gebaut.
- 🔶 **NPC-Confinement auf 1 Knoten (= jail-Zelle):** Idee = NPCs auf EINEM Map-Knoten halten (kriegt später eigenes PNG;
  andere Knoten/PNGs = WIP); PC bleibt frei. **Verifiziert in-game (Probe `jail_probe.lua`, 2026-06-26):** `on.roomChange(seat,
  room,action)` + `on.move(inst)` feuern (NICHT `on.room_change(inst)`); `inst:GetCurrentRoom()` + `inst:IsPC()` funktionieren;
  aber **`m_forceAction` ist NICHT Lua-erreichbar** (Userdata, kein Member-Zugriff, keine Move-Methode gebunden). Die Mechanik
  selbst ist simpel: AAU-Action `NpcMoveRoom` (Actions.cpp) schreibt nur `m_forceAction.movementType=2; .roomTarget=<raum>`
  (kein Funktionsaufruf, KI läuft hin; nur NPC, nicht PC). **→ reiner Lua-Eject versperrt.** Wege: (a) **Trigger-Editor-Modul**
  (Jailer-Stil, `NpcMoveRoom`-Action — empfohlen, kein Crash-Risiko) oder (b) `g_poke` auf den `m_forceAction`-Offset (RE,
  riskant). Erkennung (roomChange + GetCurrentRoom) ist Lua-seitig fertig nutzbar; nur der Setter fehlt.
  **ENTSCHIEDEN: Trigger-Weg** (Stabilität, bewiesene Flee/Loop-Behandlung; g_poke unsicher da CharInstData-Adresse aus
  Lua nicht zugänglich). Jailer-Modul liegt lokal (`*/data/override/module/Jailer`, 34KB binär — nur im Trigger-Editor
  lesbar), zu komplex zum Abwandeln → **neues Minimal-Modul spezifiziert: `CONFINEMENT_MODULE_SPEC.md`**. Verifizierte
  Bausteine: Event `Room Change`; Expr `GetNpcCurrentRoom(seat)`, `GetPC()`, `GetThisCard()`; Action `NpcMoveRoom` =
  „Make Npc Move to Room". Stufe 1 = fester Zell-Raum (MVP), Stufe 2 = Zell-Raum/aktiv-Flag aus Card Storage (SSOT-Brücke,
  globaler Pool). Offen: Nutzer wählt Zell-Index + baut Stufe-1-Modul im Editor + Test.
- ⬜ **Optik pro Welt** (Override/Shadow-Set-Layer) — §6

**PC-HILFEN**
- ⬜ **Hint-System** (Dictionary versteckter Multi-Step-Combos, Launcher-Overlay, rein passiv) — §5
- ✅ Modul-Scanner (Teil davon — Katalog steht) — §5.3

**TAGESLOGIK / SICHERHEIT**
- ✅ Tagesphasen belegt (Home=9, End-Day=8/sleep=10) — §3.1
- ⬜ **Auto-Save im ~7-Tage-Fenster** (Netz, falls Spieler nicht speichert) — §12

**AUSLIEFERUNG (zum Schluss)**
- ⬜ Geteilte Basis (Junctions 63→21 GB) — §8 ; ⬜ Ein Installer (PyInstaller + self-contained PPeX) — §8b ;
  ⬜ Multi-Welten-Generik (Welten als Config) — §9b

**HARTE ENGINE-GRENZEN:** Roster 25 · keine neue Map-Geometrie / keine neuen Aktions-Verben · kein Cold-Loader
(Menü-Automatik) · Live-Reload crasht (Kill+Restart) · Modul-Liste nicht aus Lua zur Laufzeit (→ extern). — §1/§11

---

## ★ ZUKUNFTS-MUSTER: Dispatcher-Modul für On-the-fly-Logik (Kern der Evolutions-Schicht)

> Idee festgehalten 2026-06-26. Das tragende Muster, damit Verhalten **live umschaltbar** ist, **ohne Karten zu
> verändern** und **ohne Reload** — die SSOT ist das Gehirn, ein immer-geladenes „Dispatcher"-Modul der live-
> verzweigende Arm. Setzt voraus: Reroute-Hook (injiziert Module in-memory beim Laden) + „Karten nie verändern".

**Das Problem, das es löst.** Module **laden/entladen** = Trigger werden erst am Lade-Moment scharf
(`InitOnLoad`/`InitTransferedCharacter` → `RegisterTrigger`). Ein Modul zu einem schon geladenen Char dazulegen
**aktiviert seine Trigger NICHT** (Quellen-verifiziert). Also: Modul-SET-Änderungen brauchen einen (Re-)Load.

**Der Trick (warum es trotzdem on-the-fly geht).** Ein Trigger = *Event → Bedingung → Aktion*, und die
**Bedingung wird zur Feuer-Zeit (Laufzeit) ausgewertet, NICHT beim Laden.** Also: **ein immer geladenes Modul A**,
dessen Trigger bei den relevanten Events **live Werte prüfen** und je nach Wert **andere Aktions-Pfade** nehmen,
ändert sein Verhalten in der Sekunde, in der sich der Wert ändert — **kein Reload.** „Modul A immer da, NPCs
interagieren auf bestimmte Art → aufgrund der Werte andere Pfade." Das Verhalten wird über **Werte** gesteuert,
nicht über die Modul-Liste.

**Architektur (passt zu „Karten pristine, SSOT = Gehirn").**
1. Karten unverändert. Modul A wird NICHT auf die Karte gestempelt.
2. Der **Reroute-Hook injiziert Modul A bei jedem Char beim Laden in-memory** (= „always loaded").
3. Modul As Trigger lesen **von der SSOT gesetzte Werte** → verzweigen. Pfad ändern = nur den **Wert** ändern,
   nicht die Modul-Liste → Modul A nimmt beim nächsten Feuern den neuen Pfad.

**Zwei sauber getrennte Ebenen:**
- **Verhalten / Pfade** = on-the-fly (Modul A liest Werte live, kein Reload).
- **Struktur / welche Module überhaupt geladen** = beim (Re-)Load (Hook). On-demand-Re-Apply eines Chars =
  `KickCard` + `AddCard` (kurzes Flackern) → lädt mit neuer Modul-Liste; **nicht** an den end-of-day-Tick gebunden.

**Der Wert-Kanal (die einzige echte Abhängigkeit — wie es erreicht wird):** Die SSOT muss die Werte ins Spiel
schreiben, wo eine Trigger-Bedingung sie liest.
- **Char-Werte (virtue/corruption/stats):** ✅ bewiesen — `apply_state` setzt sie zuverlässig, Trigger-Bedingungen
  prüfen sie direkt. **Sofort nutzbar** für die ersten Dispatcher-Pfade.
- **Card Storage (freie Flags) — ✅ BEWIESEN in-game 2026-06-27:** Die **Brücke trägt.** `apply_state`
  `setCardStorage(seat,key,val)` schreibt genau dorthin, wo die Modul-Expression „Get Card Storage Bool/Int" liest.
  Gegate Confinement (build_confinement_gated, Hook v4 injiziert es immer) hat die 3 Inmates rein flag-getrieben
  confined, Karten unangetastet. **Die alte „Ursache A" ist geschlossen — kein nativer storeCard-Hack nötig.**
  → Wir haben einen eigenen, funktionierenden Flag-Kanal (Card Storage), unabhängig von den volatilen Vanilla-Stats.
  Beliebige SSOT-Flags sind damit als Dispatcher-Bedingungen nutzbar.

**Konkret zu bauen (wenn dran):** (a) ein Dispatcher-Modul mit `module_authoring.py` bauen (Trigger, deren
Bedingungen Stats/Flags prüfen und in Pfade verzweigen); (b) der Roster-Builder/Hook injiziert es immer; (c) die
SSOT setzt die Steuer-Werte (Stats sofort; freie Flags nach Brücken-Schluss); (d) Pfade kalibrieren. So wird die
ganze Evolutions-Schicht (Status, Race-Attitude, Loneliness, Training→Transformation) **wert-getrieben statt
modul-tausch-getrieben** — live, karten-frei, SSOT-zentral.

---

## 0. Kurzfassung des Konzepts

Ein zweiter, separater "Jail"-Modus für Artificial Academy 2:
- Gefangene NPCs werden aus der Schul-Klasse in eine **separate Jail-Welt** überführt.
- Einstieg über einen **Button auf dem nächtlichen Heim-Menü-Screen** (2D-PNG-Screen, nicht Map).
- Technisch: **zwei vorgeladene Spiel-Instanzen**, Umschalten per Fenster-Sichtbarkeit.
- Transfer Schule→Jail per **Python-Script** (Card-Copy).
- End-Day-Berechnung gebunden an den Tagesphasen-Indikator der Engine.
- Jail-Welt: gesperrte/progressiv freischaltbare Map-Knoten, eigene NPCs, eigene Optik.

**Leitprinzip aus der ganzen Analyse:**
AA2 ist **asset- und daten-moddbar bis zum Anschlag, aber engine-starr.**
Passive Operationen (lesen, anzeigen, Assets tauschen, Save-Dateien manipulieren) = problemlos.
Aktive Eingriffe (neue Map-Geometrie, neue Aktions-Verben, Aktionen programmatisch ausführen) = die harte Wand.

---

## 1. Harte Engine-Limits (unveränderlich, kein Mod umgeht sie)

| Limit | Detail |
|---|---|
| **Roster-Cap: 25** | Max. 25 Charaktere pro Klasse. **Nicht erweiterbar.** |
| **Keine neue Map-Geometrie** | Map-Knoten können nicht hinzugefügt / neu gebaut werden. |
| **Keine neuen Aktions-Verben** | Interaktions-Vokabular (talk/club/etc.) ist fix. Nur Konsequenzen vorhandener Aktionen umschreibbar. |

### Warum 25 so tief sitzt
Die 25 ist die **Adressierungsbasis des gesamten Systems**, kein Config-Wert:
- Trigger-Expressions (ThisCard, TriggerCard, AnswerTarget, `[index]::Actor`) geben alle einen **Seat-Index 0–24** zurück.
- Beziehungs-Matrix (jeder-zu-jedem), Save-Format, Card Storage hängen alle an diesem Index.
- Eine 26. Card hinzuzufügen = jedes Array umschreiben, Save-Format brechen, Matrix neu dimensionieren.
- Zusätzlich Performance-/Pathfinding-Deckel: schon Vanilla wird zäh, wenn alle 25 zusammen sind.
- AAU bohrt nur **Maker-Slot-Limits** auf (Gesichter, Haare, Tans, Kleidung) — das ist Asset-Auswahl, nicht die Roster-Datenstruktur.

**Unbestätigt:** Ob irgendwo im /aa2g/-Umfeld ein experimenteller EXE-Hack die Seat-Tabelle aufbohrt. Nicht dokumentiert, sehr unwahrscheinlich. Bei Bedarf nur über Discord klärbar.

---

## 2. Architektur des Jail-Modus

### 2.1 Zwei-Instanzen-Modell (der Kern)

**Erkenntnis:** Save-Swap macht aus dem "interaktiver Raum außerhalb des Rosters"-Problem ein
"zweite normale Klasse"-Problem. Die Jail-Klasse ist ein **vollwertiges normales Klassen-Save**
→ kompletter Spiel-Loop funktioniert (Bewegung, Interaktion, KI, Beziehungslogik), weil es eben
eine echte Klasse ist.

**Konsequenz:**
- Gesamtspeicher > 25 möglich (25 Schule + 25 Jail = 50 existierende Chars).
- Aber jede **geladene Sitzung bleibt 25-Cap**. Nie 50 gleichzeitig geladen — zwei Welten à max. 25.

**Sauberster Bau: zwei getrennte AA2MiniPPX-Installationen**
- Eine Schul-Installation, eine Jail-Installation.
- Jede mit ihren **eigenen Overrides/Backgrounds** fest eingerichtet (löst das "Optik pro Welt"-Problem,
  da Overrides global zur Installation sind, nicht im Save stecken).
- Vorteil: Kein Override-Kollisionsrisiko, **Logik-Kontext gratis** (jede Installation IST per Definition
  ihr Modus → keine Sentinel-Card-Erkennung nötig).
- Python-Script = Brücke (kopiert transferierte Cards zwischen den Save-Verzeichnissen, startet die passende).

### 2.2 Switch-Mechanik (Fenster-Sichtbarkeit)

**User-Idee (tragfähig):** Beide Instanzen bei Launch vorladen, nur eine sichtbar.
Button-Klick → Fenster-Toggle (verstecktes Fenster nach vorn, sichtbares verstecken) → **Sofort-Switch ohne sichtbares Laden.**

**Technik:**
- Windows: Win32-API via `pywin32` oder `ctypes` — `ShowWindow(SW_HIDE / SW_SHOW)`, `SetForegroundWindow`.
- Fenster identifizieren über PID oder Fenstertitel.
- **VORAUSSETZUNG: Borderless-Windowed-Modus** (AAU kann das: borderless fullscreen).
  Exklusiver DX9-Fullscreen reagiert allergisch auf Verstecken → Device-Loss, schwarzes Bild. NICHT nutzen.

**Sync-Problem ist gelöst durch Design:**
- **Immer nur EINE Welt aktiv** — die, in der der Player steht. Die andere darf pausieren (sogar erwünscht).
- Switch nur möglich wenn Player im Heim-Screen (= Übergabepunkt).
- Kein Live-Datenaustausch zwischen Prozessen nötig (zwei isolierte Speicherräume — Prozess-Isolation,
  unabhängig von Hardware/Engine-Alter). Brücke bleibt das Python-Script über die Save-Dateien.

**✅ GETESTET (2026-06-23) — der Blocker ist NICHT der AA2-Mutex, sondern PPeX:**
- AA2 selbst erlaubt 2 Instanzen (getrennte Ordner). ABER der **PPeX-Asset-Server** (`PPeXM64.exe`) nutzt einen
  **global hardcodierten Named-Pipe `\\.\pipe\PPEX`** (kein Pipe-Name-Argument; Start mit `PPeXM64.exe "<data>" [-nowindow]`).
  → Zwei PPeX-Installs gleichzeitig = die zweite hängt in `Failed to connect \\.\pipe\PPEX` / `Waiting for server ready: False` (live bestätigt im jail-logfile).
- Zusatz: PPeX wird vom **Launcher** gestartet (`loadPPeX()` in `mod/launcher/dlg.lua`), NICHT von `aa2play.exe`. Direktstart der exe umgeht das. **Immer über den Launcher starten.**
- **PPeX-Server ist SINGLE-CLIENT (quellcode-belegt, `aa2g/PPeX` → `PPeXM64/Pipe.cs`):**
  `new NamedPipeServerStream(name, PipeDirection.InOut)` ohne maxInstances → Default = **1**; nach `WaitForConnection()`
  folgt eine Endlos-Lese-Schleife für genau diesen einen Client, **kein erneutes Accept**. → **EIN Server bedient genau EIN Spiel.**
  Pipe-Name „PPEX" ist zudem hardcodiert (kein zweiter Server mit anderem Namen ohne Binär-Patch). .NET Core 3.1.9 ist lokal vorhanden.
- **Harte Wahl — Sofort-Switch ODER PPeX, nicht beides:**
  - **(A) Eine Instanz zur Zeit + PPeX behalten (Kill+Restart, 2.2b).** Switch = Save + Background wechseln, neu laden.
    PPeX-Vorteile (Kompression/Cache) bleiben, kein Konflikt. Kostet paar Sek. pro Switch. Einfachste & sicherste Variante.
  - **(B) Sofort-Switch (zwei Instanzen parallel) → PPeX ganz AUS, gemeinsame LOSE Dateibasis** (`bUsePPeX=false` in beiden,
    Assets als lose/`.pp` in EINEM Ordner, via Junction `mklink /J` geteilt). Kein Pipe → kein Konflikt. Erfüllt „geteilte Basis ohne Duplikat".
    Kosten: mehr Disk (unkomprimiert), evtl. langsameres Laden, 2× RAM/GPU. **Letzter offener Test:** hat `aa2play.exe` selbst eine
    Instanz-Sperre? (war bisher von PPeX verdeckt; mit PPeX aus sauber testbar).
  - **(C) PPeX patchen** (Open-Source-.NET) auf multi-instance/multi-client (maxInstances + Accept-Loop pro Thread/Task)
    → Sofort-Switch MIT PPeX. Dev-Arbeit + Pflege bei AAU/PPeX-Updates.

- **ENTSCHEIDUNG (2026-06-23): Weg (C) ist gesetzt.** Ohne ppx startet das stark gemoddete Spiel nicht (kein bUsePPeX-aus-Test möglich),
  und Sofort-Switch ist gewünscht → PPeX bleibt + multi-client-Patch.
- **AA2-Eigen-Mutex faktisch beantwortet (kein Test mehr nötig):** beim Doppelstart via `AA2Play.exe` lief der jail-Prozess bis in die
  Asset-Init und loopte auf „Waiting for server ready" (PPeX). Ein harter Single-Instance-Mutex hätte den 2. Prozess SOFORT beim Start
  beendet, weit vor der PPeX-Stufe. Zwei AA2-Prozesse koexistierten also bereits → **einziger Blocker = PPeX single-client.** Sobald
  PPeX multi-client ist, laden beide Instanzen voll → Sofort-Switch tragfähig. (.NET SDK 8/10 lokal vorhanden → Build möglich.)
- **Distributions-Modell (gewählt):** NICHT Komplett-Install verteilen, sondern **Python als Installer + Orchestrator**. User behält seinen
  eigenen AAU-Install (= Basis/Schul-Welt); Python legt die jail-Welt als Geschwister-Ordner an, der die schweren Daten (ppx/mods) per
  **Junction** (`mklink /J`) auf den User-Install teilt (keine Duplikate) und nur den **Delta** enthält: jail-Config, Background-Layer
  (Override/Shadow-Set), Save-Vorlage, Custom-Module, gepatchter `PPeXM64` (mit Backup des Originals). Skaliert auf N Welten.
- **Laufzeit-Modell:** EIN gemeinsamer (gepatchter) PPeX-Server über die geteilte Datenbasis bedient beide Instanzen; Python startet den
  Server einmal + beide Spiele, regelt Fenster-Switch + Save/DB-Brücke. Per-Launch-`loadPPeX()` muss dafür unterdrückt/idempotent werden.
- **✅ PPeX-MULTI-CLIENT-PATCH GEBAUT & GETESTET (2026-06-23):**
  - Quelle `aa2g/PPeX` geklont, `PPeXM64/Pipe.cs` gepatcht: Accept-Loop mit `MaxAllowedServerInstances`, ein Worker-Thread pro Client,
    EOF-sauberes Disconnect, `OnDisconnect`/Exit erst beim **letzten** Client. `Cache.LoadLock` serialisiert `load`-Requests (threadsicher).
  - Build OK mit .NET SDK 10 (Target netcoreapp3.1, nur EOL-Warnung). Artefakt: `_ppex_src/PPeXM64/bin/Release/netcoreapp3.1/PPeXM64.dll`.
  - **Protokoll-Test bestanden:** Server gegen leeres Datenverz. gestartet, zwei NamedPipe-Clients **gleichzeitig** verbunden (B während A offen),
    beide `ready → True`, A nach B weiter bedient. → Multi-Client funktioniert (Stock-Server hätte B blockiert).
  - **✅ Real-Test gemacht (2026-06-23):** gemeinsamer gepatchter Server über `school\data`; `loadPPeX()` in beiden Installs deaktiviert (Backup `dlg.lua.orig`).
    **school (1. Instanz) läuft voll + verbunden.** **jail (2. Instanz) kommt durch die PPeX-Stufe (der alte „Waiting for server ready"-Hänger ist WEG)
    → PPeX-Patch wirkt.** ABER jail beendet sich danach sofort (0-Byte-Log, kein Prozess).
- **✅ GELÖST: AA2-EIGENER SINGLE-INSTANCE-MUTEX (umgangen, Sofort-Switch Ende-zu-Ende bewiesen 2026-06-23).**
  - Beleg: `AA2Play.exe` nutzt `CreateMutexW`/`ReleaseMutex`; school (1.) läuft, jail (2., identische Kopie, gleiche Edit) stirbt sofort → klassische Zweit-Instanz-Sperre.
  - Greift erst NACH der PPeX-Stufe (beim vollen Hochfahren) → erklärt, warum früher zwei Instanzen koexistierten (beide hingen damals VOR dem Mutex im PPeX-Wait).
  - **PPeX ist damit NICHT mehr der Blocker — AA2 selbst ist es.** Das war der als „letzter Test" markierte Punkt; Antwort: Mutex existiert.
  - **Mechanismus identifiziert:** benannter Mutex `\Sessions\1\BaseNamedObjects\__AA2Play_Class__` (gleicher Name wie die Fensterklasse).
    Entsteht erst beim VOLLEN Spielstart (nicht im Launcher) — deshalb stirbt die 2. Instanz erst nach „Launch", mit 0-Byte-Log.
  - **✅ LÖSUNG (gewählt, versionsunabhängig, automatisierbar): Mutex-Handle der laufenden Instanz schließen** via
    `DuplicateHandle(..., DUPLICATE_CLOSE_SOURCE)` → der Name wird frei → die nächste Instanz erstellt ihn frisch, kein „läuft schon".
    KEIN exe-Patch nötig (funktioniert auf jeder AA2Play.exe, jeder Version), `__AA2Play_Class__` bleibt für AAU/Fensterklasse intakt.
  - Tool gebaut: `_mutexfind/` (.NET 8, NtQuerySystemInformation-Handle-Enum + Close). Modi: listen / `close`.
  - **✅ BEWIESEN 2026-06-23:** gemeinsamer gepatchter PPeX-Server + school in-game → Mutex geschlossen → jail gestartet →
    **zwei AA2Play.exe gleichzeitig (beide ~245 MB), beide am EINEN Server.** PPeX-Multi-Client + Mutex-Bypass zusammen = Sofort-Switch tragfähig.
  - **Orchestrator-Rezept (Laufzeit):** (1) gepatchten PPeX-Server 1× über geteilte Daten starten; (2) Welt 1 starten → warten bis in-game →
    deren `__AA2Play_Class__`-Mutex schließen; (3) Welt 2 starten → deren Mutex schließen; … (4) Sofort-Switch per Fenster-Toggle (`ShowWindow`).
  - **Temporär für den Test:** `loadPPeX()` in school+jail `dlg.lua` deaktiviert (Backups `dlg.lua.orig`); im Endprodukt managt der Orchestrator den einen Server.

### 2.2b Ressourcen & Save-Koordination

**Ressourcen-Realität (wichtig: Annahme "minimal RAM" korrigiert):**
- **CPU laufend:** ~null für pausierte (versteckte) Instanz. Bei Fokusverlust pausiert sie. Kein Thema.
- **CPU-Spitze:** kurzer Peak beim Background-Reload der Jail-Instanz am End-Day. Sekundenkurz, unkritisch.
- **RAM — ACHTUNG:** Verstecktes Fenster (`SW_HIDE`) gibt RAM NICHT frei. Beide vorgeladenen Instanzen liegen
  mit **vollem Footprint ab Launch** im Speicher (nicht "erst beim Klick"). Pausiert ≠ entladen.
  Footprint klein: grob ~1–1,5 GB/Instanz (abhängig von Mods, Texturen, PP2-Cache — Wiki: Cache-Summe >1,5 GB = instabil).
  Total ~1–3 GB → auf 16/32 GB-System irrelevant, aber **konstant**.
- **Disk:** zwei Installationen ≈ 6–8 GB. Einmalig.

**Trade-off-Entscheidung beim Bau:**
- **Vorladen** (beide ab Start im RAM) → Sofort-Switch, kostet konstant RAM.
- **On-demand starten** (zweite Instanz erst beim Klick) → schlanker RAM, kostet Ladezeit beim Wechsel.
- Default-Empfehlung: Vorladen (RAM ist billig, Sofort-Switch ist das bessere UX).

**Save-Koordination (fire-and-forget, aber mit einer Bedingung):**
- Der **Background-Reload** der versteckten Instanz darf fire-and-forget sein → User wartet nie.
- **ABER:** nicht der Write selbst! Race Condition vermeiden: Save darf nicht gelesen werden während er geschrieben wird
  (sonst halbfertige Datei → Crash/Korruption).
- **Richtige Grenze:** Transfer-**Write synchron abschließen** → DANN Reload fire-and-forget feuern.
  Du wartest nur auf den (schnellen) Write, nicht auf den Reload.
- **Atomic Write:** in Temp-Datei schreiben, dann `os.replace` (atomar auf gleichem Volume) → Instanz sieht immer
  alten ODER neuen Save komplett, nie einen halben.
- **File-Lock** als zusätzliche Absicherung (`.lock`-Flag).

**Robuste Reload-Variante: Kill + Restart statt Live-Reload.**
- Statt "laufende Instanz liest Save neu" (unbestätigt ob AA2 das zur Laufzeit sauber kann): versteckte Instanz
  **beenden und frisch mit neuem Save starten**, komplett im Hintergrund, fire-and-forget.
- Frischer Prozess liest Save beim Start garantiert. Etwas mehr CPU-Peak (egal bei der Größe), aber robuster
  und umgeht die offene Frage "liest laufender Prozess seinen Save spontan neu" (Antwort normalerweise: nein).

### 2.3 Einstiegspunkt: Heim-Menü-Screen (der Durchbruch)

**User-Erkenntnis:** Jail-Button gehört auf den nächtlichen Heim-Screen (PNG-Menü mit Save/Load/Roster/Sleep),
der nur aufgeht wenn man **zuhause, allein, ohne andere NPC** ist.

**Warum das alles vereinfacht:**
- Das ist ein **2D-Menü-Screen, KEIN 3D-Mapknoten** → beide Engine-Wände (Map-Geometrie, Aktions-Verben)
  werden **für den Einstieg irrelevant**. Du fügst einem Menü einen Menüpunkt hinzu, keinen Raum zur Map.
- Solo/NPC-frei = **sauberer Übergabepunkt**, kein lebender Klassen-Kontext abzugleichen.

**Zwei Wege für den Button:**
- **Weg A — in Spiel-UI injizieren:** via AAU-Lua (Poser ist Lua-geskriptetes Custom-UI → AAU *kann* eigene UI bauen).
  Ob auf *diesem* Screen platzierbar = **unbestätigt**. Discord/Quellcode-Frage.
- **Weg B — externer Overlay über Python-Launcher (EMPFOHLEN):** Layered/Topmost-Window über das Spielfenster legen.
  Klick → Launcher toggelt zur Jail-Instanz. **Umgeht UI-Modding komplett.** Fügt sich in bestehende Architektur.

**Wann Overlay-Button zeigen:** gesteuert über `CurrentPeriod` (siehe 3.1) — nur bei Heim-Phase einblenden.

### 2.4 Transfer Schule → Jail

**User-Terrain (als gelöst markiert):** Python-Script kopiert die Card bei Interaktions-Trigger in den Jail-Save.
- Gebunden an **End-Day** (Tagesgrenze), damit kein Mid-Session-Knirschen.
- Card-Transfer zwischen Klassen-Saves = das, was AA2QtEdit ohnehin macht (Cards in Klassen-Saves ersetzen ohne History-Verlust).

### 2.4b Zustandstransfer: Card vs. Play-Data (KRITISCH — sonst geht Entwicklung verloren)

**Das Problem (User erkannt):** Chars haben Basis-Werte (z. B. high virtue, Vorlieben), die durch Module
adaptiv verändert werden. Wenn ein Char Schule→Jail wandert, sich dort entwickelt (z. B. lower virtue),
muss beim Rücktransfer der **aktuelle Entwicklungsstand** zurück, NICHT die unveränderte Basis-Card.

**Zwei Datenebenen — nicht verwechseln:**
- **Ebene 1 — Card (PNG):** Aussehen, Persönlichkeit, angewendete Module, **Basis-/Start-Werte**. Die "Vorlage".
- **Ebene 2 — Play-Data (im Klassen-Save, an Seat gebunden):** Der **gelebte Zustand** in DIESER Klasse —
  aktuelle (entwickelte) Virtue, Beziehungspunkte zu allen Seats, Stimmung, Lover-Status, Modul-Veränderungen.
  Liegt NICHT in der Card.

**Schlüssel-Erkenntnis:** "lower virtue" ändert die **Play-Data**, nicht die Basis-Card. Die zwei sind ohnehin getrennt.
→ Basis-Card ist nie in Gefahr, solange man NICHT in die Master-PNG zurückschreibt.

**Belegt:** AA2QtEdit ersetzt Cards in Klassen-Saves "ohne Character-History zu verlieren"
→ Tooling unterscheidet gelebten Zustand vom Card-Inhalt und kann ihn erhalten. Starkes Indiz, dass Zustandstransfer geht.

**Transfer-Regel:**
- NICHT die Basis-Card kopieren (sonst Reset auf Original-Werte).
- Die **Play-Data des Seats** mitnehmen (aktueller Wertestand).
- Rücktransfer: im Jail veränderte Play-Data zurückspielen.

**OFFENER PUNKT — Beziehungs-Matrix-Komplikation:**
- Play-Data enthält auch Beziehungen zu ALLEN anderen Seats der jeweiligen Klasse.
- Schul-Beziehungen ergeben im Jail keinen Sinn (andere Mitbewohner) und umgekehrt.
- → Beim Transfer wahrscheinlich DIFFERENZIEREN:
  - **Char-interne Werte** (Virtue, Vorlieben, Stimmung, Stats, Modul-Effekte) → TRANSFERIEREN ("Entwicklungsstand").
  - **Beziehungs-Werte zu anderen Seats** → klassen-spezifisch, wahrscheinlich NICHT mitnehmen (oder gezielt behandeln).
- Ob das Save-Format diese feldweise Trennung erlaubt (Selbst-Werte nehmen, Beziehungs-Matrix lassen) = **ZU VERIFIZIEREN**
  via AA2QtEdit-Quellcode. "Ohne History-Verlust" legt einzeln adressierbare Felder nahe, aber Cross-Class-Transfer unbestätigt.

**Basis-Card-Schutz (der einfache Teil):** Master-Card NIE als Schreibziel verwenden. Transfer schiebt nur Play-Data
zwischen Saves. Master-PNG bleibt unverändertes Original im Card-Ordner. = natürliche Funktionsweise, nur Disziplin nötig.

**Datenmodell-Konsequenz:** Ein Char = "Basis-Card + welt-spezifische Play-Data". In mehreren Welten = pro Welt eigener Zustand.
- **Variante A (gewollt):** Selbst-Werte folgen dem Char überallhin, Beziehungen pro Welt lokal. Aufwändiger, realistisch.
- **Variante B:** getrennte Leben pro Welt, kein Sync. Einfacher, aber Char "vergisst" Entwicklung beim Wechsel — NICHT gewollt.
- → Variante A für Selbst-Werte. Machbar WENN Save-Format feldweise Trennung erlaubt (s. o.).

### 2.4c Emergenter Konflikt durch divergierende Zustände (großteils GRATIS)

**User-Ziel:** Chars entwickeln sich getrennt; beim Wiedersehen entsteht Reibung/Konflikt automatisch, weil Werte
nicht mehr zusammenpassen. KEINE Hintergrund-Simulation der ganzen Klasse — nur die divergierten Einzel-Zustände.

**Schlüssel-Erkenntnis: AA2-Engine IST eine Kompatibilitäts-Maschine.**
- Interaktionen werden ständig aus dem **Werte-Vergleich zweier Chars** berechnet (Virtue vs. Virtue, Vorlieben, Beziehung, Module).
- Passen Werte nicht zusammen → Engine erzeugt Reibung SELBST: niedrigere Erfolgs-%, Ablehnung, Module feuern auf Diskrepanz
  (z. B. Chaste Cherisher mag high virtue, Hoe Hopper mag low, diverse Bias/Hunter-Module).

**Beispiel Resort (funktioniert EMERGENT, kein eigener Code):**
- A kommt mit high virtue zurück, B hat inzwischen low virtue → beim nächsten Interaktions-Check sieht Engine die Differenz
  → Reibung automatisch. **Du musst nur die divergierten Werte korrekt transferieren, Konsequenz ist Engine-Sache.**

**Beispiel Jail-Beziehung (NICHT komplett automatisch — Design nötig):**
- A geht verliebt/in Beziehung ins Jail → verliebt sich dort neu → kommt zurück, Schul-Partner ahnungslos, A agiert anders.
- Problem: "neue Jail-Beziehung" ist Beziehung zu einem **Jail-Char, der in der Schule nicht existiert** → Lover-Status zeigt ins Leere.
- Engine kann keine Beziehung zu abwesendem Char abbilden → "A agiert anders" fällt NICHT automatisch raus.
- → **Übersetzungsarbeit nötig:** Jail-Ereignis in schul-sinnvolle Werte übersetzen (abgekühlte alte Beziehung, veränderte
  Stimmung, evtl. temporäres Distanz-Modul). Das erzeugt dann die gewünschte Reibung.

**FAUSTREGEL (vereinfacht das Datenmodell erheblich):**
- **Char-interne Werte** (Virtue, Stimmung, Vorlieben, Stats, Modul-Effekte) → 1:1 transferieren → Reibung EMERGENT, gratis.
- **Cross-Welt-Beziehungen** (Beziehung zu Char der anderen Welt) → in char-internen Effekt ÜBERSETZEN (Regel "Ereignis X → Wert-Änderung Y").
- → Viel weniger als "ganze Klasse simulieren": nur die wenigen Beziehungs-Ereignisse übersetzen, die Welt-Grenzen überschreiten.

**ANWENDUNGSFALL: sozialer Reichtum → Verwundbarkeit (User-Idee, korrigierte Richtung):**
- User-Wunsch: belieber Char mit vielen Freundschaften wird transferiert → soll "einsam"/manipulierbar werden; Loner → anderes Modul.
- **Falle:** Beziehungen NICHT 1:1 ins Jail übernehmen — die Freunde (Gegenparts) sind im Jail-Roster nicht da, Beziehungs-Werte zeigen ins Leere.
- **Richtige Lösung — verdichten statt transportieren:**
  - Beziehungs-Reichtum zu char-internem Wert verdichten: `eve.social_wealth = high` (weil viele Schul-Bindungen).
  - Dieser Wert speist ein **"Einsamkeit"-Modul**: hoher Reichtum + jetzt isoliert → starker Manipulations-/Exploitable-Effekt
    (Kontrast "vorher umgeben, jetzt allein" ist der Hebel, nicht die Beziehungen selbst).
  - Loner-Fall: `social_wealth = low` → Einsamkeits-Modul greift kaum → stattdessen anderes Modul für die andere Ausgangslage.
- **Schul-Beziehungen verschwinden NICHT:** sie SCHLAFEN in der DB (char_id-basiert, präsenz-abhängig, s. 2.4d).
  Rückkehr → reaktiviert, sofern Freunde noch im Roster.
- **Optional — Verfalls-Regel:** schlafende Beziehungen während Abwesenheit abkühlen lassen ("X Tage weg → Freundschaft um Y runter").
  Macht den "beliebt → weg → zurück, aber nicht mehr wie früher"-Bogen rund. Freies Design.

**WICHTIG — keine autonome ECHTZEIT-Simulation, ABER täglicher Tick:** Inaktive Welt-Instanz simuliert nicht
autonom/kontinuierlich. ABER: am Tageswechsel (Sleep-Klick / `CurrentPeriod` end-sleep) läuft ein **Hintergrund-Resolver**
über die DB, der inaktive Welten **pro Tag einen Schritt fortschreibt**. Also NICHT "eingefroren tot", sondern
"pausiert zwischen Tagen, fortgeschrieben an jedem Tageswechsel". Detailgrad = so fein wie der Resolver gebaut wird
(Abstraktion, NICHT die volle AA2-Engine-Simulation). Siehe 4.8a.

### 2.4d Roster-Rotation + DB als Long-Term-Memory (die Antwort auf das 25-Limit)

**User-Modell (das eigentliche Kern-System):** Welt läuft NUR wenn Player da ist (keine Hintergrund-Sim).
DB = reine **Erinnerung**, nicht Motor. Mechanismus ist **Roster-Rotation gegen das 25-Limit**:
1. Schul-Roster voll (25). Player will bekannten Char reinholen (z. B. jemand aus dem Jail).
2. Bestehender Char raus → Zustand wandert als **long-term memory in die DB**.
3. Neuer Char rein → weil Player + Char bereits Historie haben (love/hate/Beziehung aus Jail), wird diese aus DB
   **mitgebracht und angewendet** — statt Start mit Basis-Werten.

**Das ist die elegante Antwort auf das harte 25-Limit:**
- Roster NICHT erweitern (geht nicht) → die 25 Slots werden ein **rotierendes Fenster auf einen großen DB-Pool**.
- 25 = wer gerade physisch anwesend ist. DB hält beliebig viele Chars + komplette Beziehungshistorie.
- Rein/raus = Slot-Tausch + DB-Sync. "Mehr als 25" → nicht gleichzeitig geladen, aber **persistent erinnert**.

**Teil 1 — DB-Seite: trivial (User-Terrain).**
"Char raus → Zustand in DB", "Char rein → Historie holen". Standard-Persistenz. Tabellen für Werte + Beziehungen.

**DB-SCHLÜSSELUNG (korrigiert): DB ist PRO PLAYTHROUGH, nicht global, nicht pro einzelnem Welt-Save.**

Dreistufige Identitäts-Hierarchie:
1. **Basis-Card (Eve.png):** unveränderliche Vorlage. Global, read-only. Aus ihr wird jede Instanz erzeugt.
2. **Playthrough (= "Save 01" vs. "Save 02"):** abgeschlossener Durchlauf, eigenes Universum.
3. **Char-Instanz-Zustand:** Eves gelebter Zustand INNERHALB eines Playthroughs.
   Save 01 → deranged-Eve. Save 02 → nonnenhaft-Eve. Zwei Instanzen derselben Card, völlig unabhängig.

**Jail-Save = gekoppelter Zwilling des Hauptsaves, KEIN eigener Playthrough.**
Jeder Hauptsave bekommt einen fest zugeordneten Jail-Save (System-Notwendigkeit). Die Kopplung lebt im **Python-Layer +
Ordnerstruktur**, NICHT in der Engine (AA2 lädt nur die Datei, die man ihm vorlegt — weiß nichts von der Zuordnung).

```
Playthrough 01/                 Playthrough 02/
 ├─ school.sav  (Schul-Instanz)  ├─ school.sav
 ├─ jail.sav    (Jail-Instanz)   ├─ jail.sav
 └─ memory.db   (LTM, playthr.-  └─ memory.db
                 übergreifend)
 → Eve = deranged               → Eve = nonnenhaft
```

- **Pro Playthrough EINE DB** → Schlüssel intern: `char_id` (Ordner beschränkt schon auf den Playthrough).
- Char-Zustand **welt-übergreifend innerhalb des Playthroughs** (Schule + Jail teilen `memory.db`) → Transfer Schule↔Jail trägt Entwicklung.
- Zwischen Playthroughs **komplett getrennt** → deranged-Eve und Nonnen-Eve berühren sich nie.
- Zwei Achsen sauber getrennt:
  - **Achse 1 — Playthrough:** Save 01 vs. 02, getrennte Durchläufe, getrennte DB.
  - **Achse 2 — Welt im Playthrough:** Schule ↔ Jail, dieselbe Eve wandert, Entwicklung via DB mitgetragen.

**PLAYTHROUGH-LIFECYCLE (Launcher-Aufgabe):**
- Neuer Spielstand → automatisch Ordner anlegen, leeren gekoppelten Jail-Save (aus Vorlage) + leere DB erzeugen, Mapping registrieren.
- Spielstand löschen → Jail-Save + DB mitlöschen (sonst Waisen-Dateien).
- Mapping (Hauptsave → Jail-Save → DB) im Launcher als Config halten.

**Teil 2 — Brücke in AA2: die bekannte harte Stelle (Punkt 9).**
- "und wird aktualisiert" = DB-Historie muss in die **Play-Data des neuen Seats geschrieben** werden (Save-Write),
  sonst sitzt der Char mit Basis-Werten da und die Engine kennt die gemeinsame Geschichte nicht.
- **Inject-Timing:** nach Seat-Belegung, VOR Player-Interaktion. Sauberes Fenster = **End-Day/Heim-Übergang** (nichts läuft, Save manipulierbar).

**DESIGN-REGEL — Char↔Char-Beziehungen über die Rotation (bewusst setzen):**
- Beziehungen in DB **char_id-basiert und seat-unabhängig** halten (char_id ↔ char_id, NICHT seat ↔ seat).
- Beim Einfügen NUR die Beziehungen in den Save schreiben, deren **Gegenpart gerade auch im Roster sitzt**.
- Beziehungen zu aktuell abwesenden Chars → bleiben **schlafend in der DB**, werden reaktiviert wenn beide präsent.
- (Player↔Char ist einfacher: eine Beziehung, immer relevant solange Char anwesend.)

**Kohärenz-Check:** Das bindet alle vorigen Teile zusammen — Multi-Welten, Transfer, emergenter Konflikt laufen alle
über diese DB-Schicht. Einzige technische Abhängigkeit bleibt durchgehend **Punkt 9 (Save-Format lesen/schreiben)**.
Alles DB-seitige = Standard. Einzige NEUE Design-Entscheidung = char_id-basierte, präsenz-abhängige Beziehungs-Reaktivierung.

---

## 3. Tagesphasen & End-Day-Hook (QUELLCODE-BELEGT)

### 3.1 `CurrentPeriod` Expression
Gefunden in `AAUnlimited/Functions/Shared/Triggers/Expressions.cpp`.
Gibt aktuellen Tagesabschnitt als Integer zurück:

```
10 = sleep
1  = day
2  = nothing to talk
3  = first lesson
4  = first break
5  = sports
6  = second break
7  = club
8  = end
9  = home again
```

**Nutzung für das Projekt — DOPPELTE FUNKTION:**
1. **End-Day-Resolver-Hook:** Übergang auf `8 = end` oder `10 = sleep` → Transfer + Reload auslösen.
2. **"Button-zeigen"-Signal:** `9 = home again` (bzw. 10) → Overlay-Jail-Button einblenden.

**Vorteil Expression statt Event:** in jedem regelmäßig feuernden Trigger abfragbar (z. B. Room-change),
robuster als ein einmaliges Event.

**✅ GELÖST (Test 2026-06-23, `logperiod`-Mod):**
- Live geloggte Tagessequenz: `1→2→3→4→7→8→9→10→1`. Daraus:
  - **Heim-Screen = Period 9** ("home again"). Sleep-Klick → Übergang `9→10`, dann neuer Tag (`10→1`).
  - **End-Day-Hook**: Übergang auf `8` (end) bzw. `9→10` (sleep) — beide live gesehen.
  - **Overlay-Jail-Button** also auf `CurrentPeriod == 9` einblenden.
- `GetGameTimeData()` liefert `.day` (Woc<user>g 0–6, lief 5→6) und `.nDays` (absoluter Zähler, 6→7) — beide brauchbar als Kalender für den täglichen Resolver (4.8a).
- **NEBENFUND:** Phasen **5 (sports) und 6 (2nd break) wurden an dem Tag übersprungen** (`4→7` direkt). Der Logger verändert nichts (timewarp disabled) → das ist die **Vanilla-Engine**. Bestätigt: die Phasen-Sequenz ist **datengetrieben/variabel**, nicht starr 1..10 → starkes Indiz, dass „nur eine Phase"-Jail bzw. eigene Welt-Rhythmen über das Phasen-System realisierbar sind (stützt 3.3/#7).

### 3.2 Resolver-Ablauf (Plan)
1. Trigger pollt `CurrentPeriod`.
2. Übergang erkannt (8/10) → Trigger schreibt Flag in File (Card Storage / Global Var) **oder** Save-Timestamp ändert sich.
3. Python-Watcher liest Flag/Timestamp → führt Transfer + Background-Reload der versteckten Instanz aus.
4. **Genau-einmal-pro-Tag-Abfang** nötig (sonst doppeltes Feuern) — Flag setzen/zurücksetzen.

**Fallback wenn kein Engine-Hook nutzbar:** Python-File-Watcher auf den Save (Modification-Timestamp kippt beim Schlafen).
Gröber, aber engine-unabhängig.

---

### 3.3 Phasen-Maschine & Teleport-Steuerung (✅ GELÖST 2026-06-23 — Code-belegt)

> **AUFLÖSUNG (2026-06-23):** Phasen-Progression IST setzbar. Der AAU-Lua-Event `on.period(new, old)`
> **gibt die Ziel-Periode zurück** — der Rückgabewert überschreibt, wohin die Engine als Nächstes springt.
> Beleg: `mod/timewarp.lua` (genau dieser Mechanismus), bestätigt in `mod/extsave.lua` (springt per Rückgabe
> auf eine gespeicherte Periode) und `mod/music.lua`. `GetGameTimeData()` liefert zusätzlich `.currentPeriod`,
> `.day` (0–6) und `.nDays` — alle setzbar. → Der „klobige reaktive Fallback" wird nicht gebraucht; es gibt
> einen sauberen Set-Hook. Details: neuer **Abschnitt 3.4**. Offen bleibt nur, ob das **Teleport-ZIEL** einer Phase
> unabhängig umleitbar ist (vs. nur die Perioden-Nummer) — die Nummer steuert den Teleport indirekt, daher unkritisch.

**Worum es geht:** Der Vanilla-Tagesablauf ist eine feste Sequenz von Phasen, die jeweils einen
**Teleport des PC** auslösen:
- Tagesstart → fester Raum (z. B. Street vor Apartment)
- Time-Skip → Klassenraum
- Sport-Phase (5) → Sportplatz-Knoten
- Club-Phase (7) → Clubraum
- → Diese Phasen SIND die Teleport-Trigger. Player läuft nicht hin, die Phase versetzt ihn.

**Jail-Vereinfachung (User-Ansatz, clever):** Jail hat nur EINE Phase, kein Phasen-Teleport.
PC bleibt im Jail-Raum. "Verlassen" = nächster Tag → zurück in die Klasse. Umgeht die Sequenz, statt sie neu zu bauen.

**Was belegt ist:**
- `CurrentPeriod` ist eine **Expression** → Phase ist **auslesbar**.
- **Jailer-Modul** hält einen NPC trotz laufender Phasen in der Zelle und holt ihn bei Verlassen zurück.
  → Beweist: der normale Phasen-Teleport eines Chars **kann überschrieben werden** ("reaktiv statt gatend").
  → "Player can play as Jailer too" → PC-Confinement existiert ebenfalls.

**~~Was UNBESTÄTIGT ist (der Kern-Unbekannte):~~ → AUFGELÖST (siehe Banner oben):**
- ~~Ob die Phasen-Progression **setzbar/steuerbar** ist~~ → **JA**: die `on.period`-Rückgabe setzt die Ziel-Periode.
  Es liest nicht nur eine Expression — der **Lua-Hook schreibt**. Eine setzende „Action" war im Trigger-System
  deshalb nicht belegt, weil der Set-Weg auf der **Lua-Ebene** liegt, nicht im Trigger-Editor.

**Indizien PRO Steuerbarkeit (User-Beobachtungen, zu verifizieren):**
- **Sonntag** hat (angeblich) andere Phasenanzahl/-struktur als Schultag → Phasen-Sequenz ist VARIABEL, nicht starr.
  → Das Konzept "unterschiedliche Phasen-Schemata" existiert intern bereits.
- **Dates** verbrauchen mehr Zeit / modifizieren den Ablauf zur Laufzeit (nicht nach Woc<user>g, sondern nach Aktion)
  → riecht nach steuerbarem Mechanismus, nicht reiner Hardcodierung.
- **Vanilla Ver.6-Patch**: fügte Steuerung für PC/NPC-Bewegungsgeschwindigkeit, Feld-Geschwindigkeit und "Endzeit festlegen" hinzu.

**Untersuchungspfad (statt blindem Fleck):**
- Frage wird von "kann man Phasen skippen?" zu "WIE macht es die Date-/Sonntag-Logik?" → konkrete Code-Suche.
- Verifikation 1: `CurrentPeriod` an einem Sonntag mitloggen → fährt Sonntag anderes Schema?
- Verifikation 2: Quellcode nach Phasen-Progression / Teleport-Ziel-Logik durchsuchen → setzbar?

**Fallback (falls keine setzbare Skip-Action existiert):**
- Phasen weiterlaufen lassen, JEDEN ungewollten Teleport **reaktiv abfangen** (Room-change → "PC im Jail? → zurück").
  Exakt das Jailer-Prinzip, angewandt auf den PC. Engine denkt "Sport-Phase", PC wird sofort zurückgeholt.
  Aus Spielersicht: durchgehende Jail-Phase, obwohl Phasen intern weiterlaufen.

**✅ AUFGELÖST: "Time Warp" = `mod/timewarp.lua` (lokal vorhanden, gelesen 2026-06-23).**
Kein Tempo-Regler, kein Debug-Skip, sondern exakt der `on.period(new, old)`-Set-Hook (Variante (a) = Volltreffer).
14 Zeilen Lua: `new = 1 + (old-1+10+back) % 10` für Perioden, `GetGameTimeData()` (`.day`, `.nDays`) für Tage.
**Bestätigt als der wichtigste Fund.** Der Verifikations-Plan (README/Trigger-Code/Discord) ist erledigt — die Quelle lag die ganze Zeit im Mod-Ordner.

**~~KANDIDAT~~ (historische Notiz): "Time Warp" Modul/Script (vom User gesichtet, ZU VERIFIZIEREN):**
- Existiert offenbar für Mini/Unlimited. In offiziellen Quellen (Wiki, Modulliste, erreichbarer Quellcode) NICHT auffindbar
  → nicht extern verifizierbar, Name allein beweist nichts.
- Name könnte bedeuten: (a) Phasen überspringen/vorspulen = VOLLTREFFER für dieses Projekt;
  (b) Spiel-/Feldgeschwindigkeit ändern (wie Ver.6-Patch) = NICHT dasselbe; (c) Tage/Wochen-Debug-Skip = anderer Use-Case.
  Diese drei sind völlig unterschiedlich relevant — Name unterscheidet sie nicht.
- **Verifikation (User am PC, bessere Quelle als Websuche):**
  1. Modul-Beschreibung/README lesen (Modulliste-Eintrag / Script-Settings / readme).
  2. **Trigger-Code entpacken & im Editor öffnen** → zeigt die exakte Action. Falls eine setzende Phasen-Action existiert,
     steht sie da → das ist der Action-Name, den das eigene Welten-System braucht (auch wenn man Time Warp nicht direkt nutzt).
  3. Discord (`MqP8rwwSP4`) fragen.
- **Wenn Time Warp Phasen setzt:** Abschnitt-3.3-Bewertung kippt von "stärkste Unbekannte + klobiger reaktiver Fallback"
  zu "fertige Action vorhanden" → sauberer Weg fürs Multi-Welten-System. **Potenziell wichtigster Fund des Projekts.**


ist DAS der Hebel, der jeder Welt einen eigenen Tagesrhythmus gibt (Beach: alle Phasen → Strand-Knoten; etc.).
Das hebt "Welt = Reskin" zu "Welt = eigener Ablauf". → ~~Stärkste unbestätigte Komponente des Projekts~~ **jetzt bestätigt & nutzbar (`on.period`).**



### 3.4 ✅ BESTÄTIGTE AAU-LUA-API (Architektur-Pivot, Code-belegt 2026-06-23)

**Quelle:** direkte Lektüre des lokalen Mod-Ordners `jail/AAUnlimited/mod/*.lua`. Alle folgenden Funktionen sind
in ausgelieferten Mods produktiv im Einsatz → keine Vermutung, sondern belegte API.

**Folge fürs Projekt (PIVOT):** Der in Abschnitt 2 angenommene Weg „Python parst die `.sav`-Binärdatei feldweise"
(die harte, unsichere Stelle #9/#10) ist **größtenteils überflüssig**. Der gesamte Brücken-Layer existiert auf
Lua-Ebene und läuft IN der Engine mit Live-Zugriff. **Python schrumpft zum Orchestrator** (Fenster-Switch,
Prozess-Management, DB, Datei-Brücke, Overlay). Datenmanipulation = AAU-Lua.

**Zeit / Phasen (löst #7/#8):**
- `on.period(new, old)` — Event bei Periodenwechsel. **Rückgabewert setzt die Ziel-Periode** (Perioden 1–10).
- `GetGameTimeData()` → `.currentPeriod`, `.day` (0–6 Woc<user>g), `.nDays` (Tageszähler). Felder setzbar.
  → „Jail = nur eine Phase" + „Tage/Wochen vergehen während Abwesenheit" beide direkt baubar.

**Charakter-Daten / Play-Data (löst #9 weitgehend):**
- `GetCharInstData(seat)` → Live-Instanz. Felder u. a.:
  - `inst.m_char.m_seat`
  - `inst.m_char.m_charData.m_forename` / `.m_surname`
  - `inst.m_char.m_charData:m_hCompatibility(towards[, value])` — Getter UND Setter.
- **Selbst-Werte vs. Beziehungs-Matrix sind getrennt adressierbar** — exakt die feldweise Trennung aus 2.4b:
  - `createRelationshipPointsDump(seat, towards)` / `restoreRelationshipPointsFromDump(seat, towards, dump, doNuke)`
  - `createHStatsDump(seat, towards)` / `restoreHStatsFromDump(seat, towards, dump, doNuke)`
  → Beziehungspunkte + H-Stats lassen sich seat-paar-weise dumpen und woanders wieder einspielen = der Transfer-Mechanismus
    (Schule↔Jail, Roster-Rotation) ist als Funktion **schon vorhanden**. Beleg: `mod/triggers_supplemental.lua`.

**Persistenz (Card Storage aus 4.3/4.x — in Lua verfügbar):**
- `getCardStorage(card, key)` / `setCardStorage(card, key, value)` — per-Card, persistent.
- `getClassStorage(key)` / `setClassStorage(key, value)`, `getCardStorageKey(card)` (Schlüssel = `<seat LastName FirstName>`).

**Events (Hooks für Transfer-Timing, Confinement, Brücke):**
- `on.save_class(data)` / `on.load_class()` — Save/Load der Klasse → idealer Transfer- & DB-Sync-Zeitpunkt.
- `on.period(new, old)` — End-Day-Hook (siehe 3.1) + Phasen-Set.
- `on.room_change(inst)` / `on.move(inst)` — für Eject-/Confinement-Logik (4.2–4.4).
- `on.card_expelled(actor0, actor1, murder_action)` — Char verlässt Roster → Hook für Roster-Rotation (2.4d).
- `on.keyup(key)` / `on.keydown(k)`, `on.convo()`, `on.start_h(hi)` / `on.end_h()`, `on.ui_event(evt)`, `on.launch()`.
- `on.dispatch_trigger(name, args)` + `dispatch_{string,int,bool,float}_trigger(...)` — eigene Trigger/Module in **Lua** statt nur im Editor.

**Roh-Speicherzugriff (Notausgang für alles, was die High-Level-API nicht abdeckt):**
- `malloc`, `g_poke`, `g_poke_dword`, `peek_dword`, `ptr_walk`, `proc_invoke(GameBase+offset, ...)`, `parse_asm`.
  → `mod/extsave.lua` patcht damit live den Save-Code. Heißt: prinzipiell ist JEDER Speicherwert erreichbar (mit Offset-Arbeit).

**Mod-Gerüst (für eigene Mods):**
- Datei `mod/<name>.lua`, erste Zeile `--@INFO <Beschreibung>`, am Ende `local _M = {...}; return _M`.
- `_M:load()` / `_M:unload()` / `_M:config()`; Config via `mod_load_config(self, opts)` / `mod_edit_config(...)`.
- Logging: `info(...)`, `log.info(...)`. Tasten: `is_key_pressed(code)`.

**✅ #10 GEKLÄRT (2026-06-23, Wiki „Lua character data fields"/„Lua cruft" + Quellcode):**
- **Char-Zugriff:** `GetCharacter(seat)` / `GetCharInstData(seat)` (vacant → nil), `GetPlayerCharacter()` für den PC.
- **Schreibbar aus Lua:** Scalar-Char-Daten `virtue`, `intelligence`/`strength`/`sociability`/`clubValue`, `fightingStyle` u. v. m.
  Lesen `char.virtue`, Schreiben `char.virtue = X` (Quellcode-belegt: `m_charData->m_character.virtue` ist set/get).
  Plus Beziehungs-/H-Werte (Setter aus `triggers_supplemental.lua`). → Self-Value-Transfer (#9) + werte-basierter Status voll in Lua.
- **NICHT machbar:** Modul-/Trait-IN-USE-Liste einer Card zur Laufzeit aus Lua ändern (kein API, Wiki + Quellcode bestätigt).
- **→ KEIN Blocker.** Status-System (Prisoner/Ex-Prisoner/Heimkehrer, 4.6/4.8) NICHT über Modul-Toggle, sondern:
  (a) wo möglich direkt über schreibbare Werte, und/oder
  (b) Custom-Modul **einmalig** auf jeder Card vorinstallieren (Editor/AA2QtEdit) und seine Trigger-Logik per
  **Card-Storage-Flag** (`prisoner=active/ex/rehab`) gaten, das Lua/Python am Welt-Übergang setzt. Modul bleibt immer da, nur Wirkung schaltet.
- Einzig echt unmöglich: einem Char ein nie installiertes Modul zur Laufzeit geben → Mitigation: alle projekt-relevanten Custom-Module bei der Card-Einrichtung vorinstallieren, alle storage-gegated.

---

### 4.1 Vorlage existiert: Jailer-Modul
Beweist, dass NPC-Einsperrung mechanisch geht. Aus der Modulliste:
- Sperrt Charakter in einen Raum (das Dach). Fluchtversuch → wird zurückgebracht + bestraft.
- Gefangener: verliert Stärke, langsamere Bewegung, wird exploitable.
- Zurückbringen via **"follow me"-Aktion**.
- Confinement-Dauer je nach Vergehen.

### 4.2 Mechanismus (wichtig: reaktiv, nicht gatend)
- Funktioniert NICHT über Umhängen des Gender-Gates an der Tür.
- Funktioniert über **Room-change-Event** + reaktives Zurückzwingen.
- Trigger sind **global** ("absolutely global") → eingrenzen mit `If ThisCard == TriggerCard`.

### 4.3 Knoten sperren / progressiv freischalten ("Dungeon Master")
Bedingte Eject-Logik:
```
Wenn Raum betreten == Knoten_X
  UND CardStorage "Knoten_X_gebaut" == false
  → rauswerfen (+ Notification "noch nicht erschlossen")
```
- Flag umlegen ("Ausbau"-Event) → Eject feuert nicht mehr → Raum begehbar.
- **Card Storage** überlebt Sessions ("lasts even after the game is turned off") → Dungeon-Fortschritt persistent.
- PC/NPC unterscheidbar → DM (PC) läuft frei, NPCs gesperrt.

### 4.4 "Andere kommen nicht rein"
- Nicht durch Jailer belegt, aber baubar: dieselbe Room-change-Logik auf alle Nicht-Modul-Cards
  ("fremde Card betritt Zielraum → rauswerfen").
- **ACHTUNG Loop-Falle:** Eigenes Rauswerfen ist selbst ein Room-change → kann erneut feuern → Endlosschleife.
  Braucht Guard-Flag.

### 4.6 Dynamische Module / kontextabhängiger Status (Prisoner → Ex-Prisoner → Rehabilitated)

**User-Idee:** Beim Jail-Eintritt bekommt Char ein "Prisoner"-Modul (macht bestimmte Aktionen leichter),
beim Austritt wird es zu "Ex-Prisoner" / "Rehabilitated Prisoner".

**Belegt — Module sind DYNAMISCH, nicht fix:**
- Hinzufügen/Entfernen ist simpler Editor-Vorgang (Modul → "In Use" schieben / zurück). Module = Daten auf der Card, nicht eingebrannt.
- Kontextabhängige Status-Wechsel im Char existieren bereits als Vorbild: **Corruption** (pure↔corrupted Styles je nach Aktion),
  **Depression** (3 Stufen mit eigenen Styles), **Nine Lives** (Style-Wechsel bei "Tod"). → System kennt das Muster schon.

**Zwei Wege — EMPFEHLUNG: dediziertes Modul (Weg 2). Begründung unten.**
- **Weg 1 — vorhandene Module schalten:** `eve.status` in DB, beim Transfer vorhandene Module/Flags setzen.
  NACHTEIL: erbt deren Nebeneffekte (vorhandene Module tun oft mehr als den einen gewünschten Aspekt) + nicht präzise tunebar.
- **Weg 2 — dediziertes "Prisoner"-Custom-Modul (BESSER):** echte Trigger-Logik, kapselt GENAU die gewünschten
  Aktions-Erleichterungen, in genau der Stärke, mit genau den Bedingungen. Volle Kontrolle. Drei abgestufte Varianten möglich
  (Prisoner / Ex-Prisoner / Rehabilitated). Ableiten wie Cupid→Eris — **Jailer als Vorlage** (hat schon "schwächer/langsamer/exploitable").

**Schlüssel: Modul-Änderung geht NUR über Reload — und der passiert NUR beim Welt-Wechsel.**
- → Die "Live-Modul-Manipulation"-Frage ist IRRELEVANT, weil nie gebraucht. Status ändert sich nur an Schule↔Jail-Übergängen,
  dort wird ohnehin neu geladen. Modul-Schreiben fällt IMMER in den belegten "zwischen Sessions"-Fall. **Kein offener Punkt hier.**

**Saubere Schichtung (Einbahnstraße, keine Sync-Probleme):**
```
DB-Status (Wahrheit, persistent)   eve.status = prisoner / ex_prisoner / rehabilitated
        ↓ beim Welt-Wechsel (Reload-Moment)
Modul auf Card geschrieben         "Prisoner"-Modul in "In Use"
        ↓ Engine lädt
Spielmechanik aktiv                definierte Aktions-Erleichterungen
```
- DB führt, Modul wird bei JEDEM Übergang frisch aus dem Status abgeleitet (DB → Modul, nie umgekehrt).
- DB-Status und Card-Modul müssen nie gleichzeitig "live" konsistent sein → keine Sync-Probleme.

Ablauf:
1. Char → Jail (End-Day, Save-Write) → im selben Write "Prisoner"-Modul hinzufügen (aus `status` abgeleitet).
2. Jail-Instanz lädt frisch → Prisoner-Status aktiv.
3. Rücktransfer (End-Day) → `status` lesen → Prisoner entfernen, "Ex-Prisoner" hinzufügen, Schul-Save laden.

**✅ GEKLÄRT (2026-06-23):** Modul-Liste ist NICHT zur Laufzeit aus Lua schreibbar (kein API; Wiki + Quellcode). → Mechanismus angepasst:
das „Prisoner"-Modul wird **einmalig auf der Card vorinstalliert**, seine Wirkung per **Card-Storage-Flag**
(`prisoner_status = active/ex_prisoner/rehabilitated`) gegated, das beim Welt-Übergang gesetzt wird (Lua/Python).
Drei Stufen = drei Flag-Werte, EIN vorinstalliertes Modul mit verzweigter Trigger-Logik. Reine Werte-Effekte
(virtue/Stats-Shift) zusätzlich direkt aus Lua schreibbar (`char.virtue = X`). Kein Runtime-Modul-Toggle nötig. Siehe 3.4.


### 4.8 Heimkehrer-Szenario: Partner ist weitergezogen (Komposition aus 3 Schichten)

**User-Idee:** Char kommt mit Beziehung/Partnerschaft ins Jail. Jail dauert Tage/Wochen (Player ist derweil in der Schule).
Bei Rückkehr hat der zurückgebliebene Partner schon eine neue Beziehung → "freut sich auf Rückkehr, bekommt harte Realität".

**Fakt-Check — gibt es das?** Bausteine ja, Gesamt-Szenario nein:
- **Fickle**: verlässt Partner sobald neuer Lover kommt. **Calculating**: trennt sich erst wenn Ersatz bereit.
- **Cheating / Homewrecker / Polyamorous / Possessive / Controlling**: diverse Untreue-/Eifersuchts-Mechanik.
- NICHT vorhanden: "abwesender Char kehrt zurück, Partner ist weitergezogen". Neu.

**HARTE GRENZE (präzisiert):** Während Player im Jail ist, simuliert die Schul-Instanz nicht in ECHTZEIT.
ABER sie ist nicht tot — siehe 4.8a (täglicher Hintergrund-Tick). Ohne Resolver-Logik bliebe der Partner unverändert;
MIT täglichem Tick zieht er graduell weiter.

**Lösung = Komposition aus 3 Schichten (alle schon im System):**
1. **Untreue erzeugen → Offline-Resolver (Python), NICHT Engine.** Läuft am täglichen Tick (4.8a), nicht nur einmal bei Rückkehr.
   Resolver-Regel: pro Tag Abwesenheit graduelle Veränderung — **abhängig von B's Traits**
   (Loyal/Singleminded B bleibt treu; Fickle/Cheating B zieht schnell weiter). Akkumuliert über Tage: vermissen → Aufmerksamkeit wandert
   → Annäherung an C → zusammen. DB schreibt B's neuen Partner, kühlt B↔A ab. **PFLICHT: muss zu B's Traits passen.**
2. **Konfrontation beim Wiedersehen → EMERGENT (Kompatibilitäts-System, 2.4c).** A kommt mit Erwartung zurück, B ist vergeben
   → Engine sieht "B hat Lover, nicht verfügbar" → Ablehnung, niedrige Erfolgs-%, Eifersuchts-Trigger. Fällt von selbst raus.
3. **A's sichtbare emotionale Reaktion → dediziertes "Heimkehrer"-Modul (empfohlen).** Reagiert auf DB-Zustand "war weg + Partner vergeben":
   A wird instabil/depressiv/aggressiv gegen den Neuen/anfällig. Das ist die sichtbare Konsequenz, die nackte Engine-Ablehnung nicht liefert.

### 4.8a Täglicher Hintergrund-Tick (KORREKTUR zu "eingefroren")

**Präzisierung:** "Eingefroren" war zu absolut. Richtig: inaktive Welt **pausiert zwischen Tagen, wird an jedem Tageswechsel fortgeschrieben.**

**Mechanismus:** Sleep-Klick (egal welche Welt aktiv) → `CurrentPeriod` end/sleep → Tageswechsel-Routine:
1. Watcher fängt den Übergang.
2. Routine tickt **ALLE Welten** einen Tag weiter:
   - Aktive Welt: normaler Tageswechsel (Engine beim Laden des neuen Tags).
   - Inaktive Welt(en): **Hintergrund-Resolver über die DB** — schrittweise Fortschreibung der schlafenden Chars.
3. Ergebnisse in DB → beim nächsten Betreten injiziert.

**Was geht / was nicht:**
- **Geht:** regel-/wahrscheinlichkeitsbasierte Fortschreibung der DB-Werte pro Tag (Beziehungen kühlen, Loyalität sinkt, Partner wechselt ab Schwelle).
  Deine Logik, voll kontrolliert. Detailgrad skaliert mit Resolver-Aufwand (grob: Beziehungen/Partner; fein: Stats-Drift, Stimmungen, Klein-Ereignisse).
- **Geht NICHT:** dass die inaktive Welt die ECHTE AA2-Engine-Simulation durchläuft (emergente Modul-Wechselwirkungen, Gespräche, Erfolgs-%).
  Nur die geladene aktive Engine kann das. Der Resolver ist eine **Abstraktion** von "was passiert wäre", nicht die Vollsimulation.

**Vorteile:**
- Heimkehrer-Szenario wird **graduell** (über Tage akkumuliert) statt schlagartig (einmal würfeln bei Rückkehr) → glaubwürdiger.
- **Chronik möglich:** "während du weg warst: Tag 5 …, Tag 11 …" — weil Schritte einzeln berechnet.
- **Multi-Welten-tauglich:** bei N Welten tickt der Resolver alle inaktiven pro Tag mit. Kontrollierter Mittelweg zwischen
  "tot eingefroren" und "voll simuliert".

**Heimkehrer-Modul fügt sich ins Status-System:** temporärer Zustand, aus DB abgeleitet, beim Welt-Wechsel gesetzt (Muster wie Prisoner/Einsamkeit).
Kombinierbar: Heimkehrer + social_wealth-Verlust + Prisoner-Reststatus = durchgängig modellierter "gebrochener" Charakter.

**Aufteilung wer macht was:**
| Teil | Wer |
|---|---|
| Partner zieht weiter während Abwesenheit | **Offline-Resolver (Python)** — Engine schläft |
| B's Weiterziehen wenn präsent | vorhandene Module (Fickle/Calculating) ODER Resolver |
| Konfrontation beim Wiedersehen | **emergent** (Kompatibilitäts-System) |
| A's sichtbare emotionale Reaktion | **dediziertes Heimkehrer-Modul** |

→ Kein Engine-Feature, sondern Komposition der 3 vorhandenen Schichten (DB + Resolver + Module). Genau die natürliche Nutzung des gebauten Systems.
- **Events** bestimmen wann Code läuft (z. B. "Room change" feuert bei jedem Raumwechsel jeder Card).
- **Actions** verändern das Spiel, **Expressions** geben Werte zurück.
- **ThisCard** = Modul-Träger, **TriggerCard** = Auslöser des Events.
- Speicher: **Local Vars** (pro Trigger-Lauf), **Global Vars** (1 Session), **Card Storage** (permanent, an Seat gebunden).
- Debug: `WriteLog`-Action.
- Vorgehen: bestehende Module zerlegen & abwandeln (Vorbild: Cupid → Eris).

### 4.7 Persistente Progression: Training/Transformation über Welten (Aktivitäts-DB)

**User-Idee:** NPC kommt ins Jail, wird trainiert → buff. Beim Rückwechsel bekommt er z. B. "Martial Arts Prodigy".
Oder: chaste → sex addict durch erlebte Ereignisse. Braucht eine zweite DB-Ebene: **Stats/Aktivitäts-Tracking** (wie oft/erfolgreich).

**AA2 hat bereits ein Stat-/Ranking-System (BELEGT) — Grundlage vorhanden:**
- Stats: **Strength, Intelligence, Sociability, Stamina**, dazu Virtue.
- Module verändern sie gezielt + reagieren auf Aktions-Ergebnisse:
  - **Club Leader**: "raise Strength, reduce Stamina" beim Training, "increase Intelligence" anderswo.
  - **Weight Issues**: Aussehen über Stufen (`Weight_-100`…`Weight_100`) je nach Ess-/Trainingsverhalten.
  - **Corruption**: "loses virtue and eventually transforms into corrupted style" — abgestufte Transformation (`corruption1-4`).
- → Spiel trackt ohnehin Char-Entwicklung. "Training macht buff" = vorhandene Stat-Veränderung, persistent über Welt-Wechsel getragen.

**Zwei DB-Ebenen (User hat sie selbst benannt):**
1. **Zustands-DB** (schon vorhanden, 2.4d): *was ein Char IST* — Werte, Beziehungen, Status.
2. **Aktivitäts-DB** (NEU): *was ein Char GETAN hat* — training_count, sex_count, fights_won, … Handlungs-Historie → Schwellen.
   Die Aktivitäts-DB ist der **Auslöser** für Zustands-Änderungen.

**Beispiel buff:** `eve.training_count += 1` bei Trainings-Erfolg im Jail → Resolver am Welt-Wechsel:
"≥ Schwelle? → Martial Arts Prodigy setzen".

**Beispiel chaste → sex addict (sauber, da schwellenbasiert):**
- Aktivitäts-DB zählt relevante Ereignisse im Jail.
- Schwelle erreicht → Zustands-DB: `eve.disposition = sex_addict`.
- Welt-Wechsel: chaste-Module/Flags entfernen, Sex-Addict-Modul setzen.
- **Vorbild im Spiel: Corruption-Modul** macht genau diese Achse (virtue↓ → corrupted style). Du parametrisierst ein vorhandenes Muster.

**Gesamt-Architektur (Einbahnstraße wie Prisoner-Status, + vorgelagerte Zähl-Ebene):**
```
Aktivitäts-DB (zählt Handlungen)    eve.training_count, eve.sex_count, eve.fights_won …
        ↓ Schwellen-Resolver (Python, am End-Day)
Zustands-DB (leitet Status ab)      eve.disposition = sex_addict / eve.combat = prodigy
        ↓ beim Welt-Wechsel (Reload)
Module auf Card geschrieben         "Sex Addict" / "Martial Arts Prodigy"
        ↓ Engine lädt
Spielmechanik aktiv                 Transformation/Buff wirksam
```
- Schwellen-Logik (wieviel Training = Prodigy) = **freie Python-Design-Entscheidung**, voll tunebar. Macht aus Welt-Wandern ein echtes Progressions-System.

**Technik:**
- **Aktivität LESEN/ZÄHLEN:** Trigger zählt bei Erfolg ("on victory", "successful conversation") in Card Storage hoch,
  Python liest am End-Day aus. **Belegt machbar.**
- **Buff REALISIEREN — WICHTIG: über MODUL, nicht rohen Stat:** "Martial Arts Prodigy" liefert den Kampfvorteil,
  ohne dass man "Strength = 80" roh schreiben muss. → umgeht die Stat-Schreibfrage (Punkt 9) weitgehend.
- **Rohe Stat-Werte zurückschreiben** (falls doch nötig): hängt an Punkt 9 (Save-Schreibzugriff).
- **Zweite DB (Aktivitäts-Tracking):** trivial, User-Terrain.

---

## 5. Hint-System für versteckte Aktions-Combos

### 5.1 Problem
Diverse Module haben **versteckte Multi-Step-Combos** ("erst Aktion A, dann sofort Aktion B → Effekt C").
NPCs führen sie per AI automatisch aus — nur der **PC** sieht/weiß sie nicht.

### 5.2 Dokumentierte Combos (Stand jetzt — Dictionary-Startinhalt)
> User-Erinnerung "küssen→fight" war FALSCH. Korrekte Sequenzen:

| Modul | Combo | Effekt |
|---|---|---|
| **Banchou** (kiss of death) | `insult` → `kiss` | Gang-Mitglied ermordet das Ziel |
| **Banchou** (Gang-Befehl) | `get along with X` → erneut ansprechen → `Force` | Gang-Mitglied führt Aktion an X aus |
| **Banchou** (rauswerfen) | `insult` → `Go Away` | Mitglied aus Gang werfen |
| **Killer** | `apologize` → `nevermind` | NPC töten (PC Only) |
| **Gambler** | `encourage to study/train/club` → `get along with their lover` | Wett-Mechanik starten |

> TODO später: vollständige Combo-Tabelle aus der ganzen Modulliste extrahieren (~250 Module durchgehen).

### 5.3 Architektur des Hint-Systems (machbar, rein passiv)
**User-finale-Idee:** Bei Game-Start scannen, gefilterte Anzeige pro Char. KEINE Ausführung, KEIN Live-Polling.

Ablauf:
1. **Modul-Ordner scannen** (`data/override/module`) → Liste installierter Module. **Voll automatisch.**
2. **PC-Card auslesen** → welche Module der gespielte Char hat (AA2QtEdit-Parsing als Vorlage, Open Source).
3. **Schnittmenge** + Abgleich mit hand-gepflegtem Combo-Dictionary → gefilterte Hint-Anzeige.
4. **Lücken-Erkennung:** Modul vorhanden aber nicht im Dictionary → Flag "Combo-Eintrag fehlt".

**Arbeitsteilung:** Maschine erkennt *dass* Modul da/neu ist; Combo-Beschreibung bleibt **hand-gepflegt**
(Trigger-Code ist nicht als Datensatz auslesbar — Combo-Semantik steht nicht in der Card).

- Nur **PC-Card** nötig (NPCs machen Combos automatisch) → ein Lesevorgang.
- Anzeige als **Launcher-Overlay** → kein Engine-Eingriff.

### 5.4 NICHT empfohlen / unsicher: Klick-zum-Ausführen
- **Weg A (AAU/Lua Aktion programmatisch auslösen):** `geass` erzwingt nur das *Ergebnis* einer manuell
  gewählten Interaktion, nicht die *Auswahl*. Programmatisches Auslösen = **unbestätigt**.
- **Weg B (Input-Automation, Maus-Klicks simulieren):** technisch möglich, aber **fragil** (kontextabhängiges Menü).
- → Erst als optionalen Aufsatz angehen, NACHDEM die reine Anzeige steht.

---

## 6. Asset-/Optik-Layer (für Jail-Look)

- **Override-System** ersetzt Assets: Archive Overrides ("jede in einer pp gespeicherte Datei ersetzen"),
  Mesh-/Object-Overrides. Raum-Hintergründe, Props, Texturen → Kerker-Reskin möglich.
- **ABER global zur Installation, nicht pro Save** → deshalb getrennte Installationen (siehe 2.1).
- **Shadow Sets** (`!`-Präfix-Ordner) = toggle-barer Asset-Layer, falls man doch in einer Installation swappen will.
- "Dungeon-Gefühl" = bestehende Map + meiste Knoten gesperrt + Reskin der erlaubten Räume. KEIN Neubau.

---

## 7. Offene Punkte / vor dem Bau zu klären

| # | Punkt | Klärung via |
|---|---|---|
| 1 | ✅ **GELÖST — Heim-Screen = Period 9** ("home again"); Sleep → 10; "end" = 8 | Live geloggt 2026-06-23 (logperiod). Tagessequenz: 1→2→3→4→**7**→8→9→10→1. Phasen **5/6 (sports/2nd break) an dem Tag übersprungen** → Sequenz ist variabel (stützt #7) |
| 2 | ✅✅ **GELÖST & BEWIESEN — zwei Instanzen + ein PPeX-Server laufen gleichzeitig** | (1) PPeX single-client → multi-client gepatcht (`PPeXM64/Pipe.cs`, gebaut+getestet). (2) AA2-Single-Instance = benannter Mutex `__AA2Play_Class__` → per `DUPLICATE_CLOSE_SOURCE` geschlossen (versionsunabh., kein exe-Patch). 2026-06-23: 2× AA2Play.exe gleichzeitig, beide am einen Server. Siehe 2.2 |
| 3 | Verhalten versteckte Instanz bei Fokusverlust (pausiert?) | Test — aber egal, da Design "1 Welt aktiv" |
| 4 | AAU-Lua: Button auf Heim-Screen platzierbar? | Discord / Quellcode — ODER umgehen via Overlay (Weg B) |
| 5 | Programmatische Aktions-Auslösung (für Klick-Combo)? | Discord / Quellcode — optional, nicht kritisch |
| 6 | PC-Card Modul-Parsing-Format | ✅ Tool liegt vor: `AA2QtEdit.exe` in `jail/`, `school/` + `<AA2-clean-install>\`. Quellcode als Vorlage |
| 7 | ✅ **GELÖST — Phasen setzbar** | `on.period(new,old)`-Rückgabe setzt Ziel-Periode (`mod/timewarp.lua`). Offen nur: Teleport-ZIEL separat umleitbar (unkritisch). Siehe 3.4 |
| 8 | ✅ **GELÖST — "Time Warp" = `mod/timewarp.lua`** | Lokal gelesen. Ist der `on.period`-Set-Hook, kein Tempo-Regler. Siehe 3.4 |
| 9 | ✅ **weitgehend GELÖST — feldweise Trennung existiert** | `create/restoreRelationshipPointsDump` + `create/restoreHStatsDump` (`mod/triggers_supplemental.lua`); `GetCharInstData` trennt Selbst-Werte von Matrix. Siehe 3.4 |
| 10 | ✅ **GEKLÄRT — Modul-Liste NICHT aus Lua schreibbar; KEIN Blocker** | Verifiziert 2026-06-23 (Wiki „Lua character data fields" + „Lua cruft" + Quellcode): kein Lua-API für Module/Traits. ABER `virtue`/Stats/`fightingStyle`/Beziehungen **schreibbar** (`char.virtue=X`). Lösung: werte-basierter Status + Modul **einmalig** vorinstalliert, per Card-Storage-Flag gegated. Siehe 4.6 / 3.4 |

---

## 8. Python-Komponenten (Bau-Checkliste für später)

> **STAND 2026-06-23 — Orchestrator v1 läuft & bewiesen (`<project-root>\orchestrator.py`):**
> Ein Startpunkt (`py orchestrator.py`) → gemeinsamer gepatchter PPeX-Server starten → beide Welten auto-launchen
> (Env-Var `AA2_ORCH_AUTOLAUNCH=1` + Launcher-Auto-Launch, kein Klick) → je Welt `__AA2Play_Class__`-Mutex schließen →
> Fenster finden. **Sofort-Switch funktioniert** (ENTER-Demo): aktive Welt sichtbar+resumed, inaktive **SW_HIDE + Prozess SUSPENDIERT**
> (`NtSuspendProcess`) → kein doppelter Sound, keine CPU, Welt steht still. Sound einfach, Switch instant — bestätigt.
> **Nur stdlib + ctypes** (paketierbar, siehe 8b). Mutex-Closer aktuell noch externes .NET-Tool `_mutexfind` → für Paket nach Python portieren.
>
> **✅ In-Game-Switch-UX fertig (2026-06-23):** logperiod pollt `CurrentPeriod` alle 500 ms → Flag-Datei `<world>\_orch_period.flag`
> (0 = keine Klasse). Orchestrator zeigt: (a) **dauerhaftes Welt-Label** oben mittig (farbcodiert: school blau, jail rot) → Orientierung;
> (b) **„JAIL"/„SCHOOL"-Switch-Button** neben „sleep", nur bei Phase 9 (Heim-Screen), Position auflösungsrelativ → Klick = Sofort-Switch.
> Robustes Shutdown (q/Ctrl+C/Terminal-zu/Fenster-X/Crash → Watchdog räumt alles auf, keine Geister-Prozesse). Englisch, nur stdlib+ctypes.
> Getestet: Label sichtbar, Button erscheint+klickbar, Switch school↔jail sofort.
>
> **NÄCHSTE SCHICHTEN (noch offen):**
> 1. **Save-/Playthrough-Kopplung — RE-BEFUND 2026-06-23 (`_re\RE_LADEFUNKTION.md`):** Lade-Funktion gefunden & verstanden
>    (`0xF3C00`, Wrapper `0xB2680`, ganzes Save-Struct-Layout F1–F9). ABER zwei harte Befunde:
>    (a) **Live-Reload über eine laufende Klasse crasht** (`0x10E9C8`, globaler Manager `0xB6264` dangling) → Mid-Session-Save-Swap nur via **Kill+Restart**.
>    (b) **Cold-Load per Funktionsaufruf NICHT praktikabel:** am Hauptmenü ist die Container-Kette LEER (Container wird vom Lade-Vorgang SELBST erzeugt),
>    der Load ist **event-/dispatch-getrieben** (Queue um Global `0x767f48`), kein simpler Callable. Nachbau = zu tief/fragil.
>    **→ ENTSCHEIDUNG: den spiel-eigenen Menü-Load EINMAL beim Boot per UI-Automation auslösen** — einmalig im statischen Menü-Zustand = robust
>    (NICHT die verworfene Per-Frame-Automatik), nutzt den crashfreien game-eigenen Load, kein RE-Nachbau. Welt bleibt versteckt bis in-world, dann zeigen.
>    Save-Kopplung school↔jail = **triviales Python-Mapping**. Mid-Session-Wechsel = Kill+Restart (bootet ebenfalls über diese Boot-Automation).
>    Save-Struct-Layout (F1–F9) bleibt dokumentiert → hilft später beim DB-/Transfer-Lesen.
> 2. **Optik pro Welt** (Asset-Layer, Abschnitt 6): eigene Backgrounds/Reskin pro Welt (Override/Shadow-Set) — damit jail wirklich anders aussieht.
> 3. **Geteilte Basis** (Junctions school↔jail, 63 GB → 21 GB), dann **Paketierung** (ein Installer, 8b).


- [ ] **Launcher / Orchestrator**: startet beide Instanzen, Prozess-Management.
- [ ] **Fenster-Controller**: Win32 ShowWindow/SetForegroundWindow, Identifikation via PID/Titel.
- [ ] **Overlay-UI**: Topmost/Layered Window für Jail-Button + Hint-Panel; Sichtbarkeit an CurrentPeriod-Flag gekoppelt.
- [ ] **CurrentPeriod-Watcher**: liest Flag-File (vom Trigger geschrieben) oder Save-Timestamp.
- [ ] **Transfer-Modul**: Card-Copy Schule→Jail-Save, an End-Day gebunden. Write SYNCHRON + atomar (`os.replace`), DANN Reload fire-and-forget. File-Lock als Absicherung.
- [ ] **Reload-Strategie**: Kill+Restart der versteckten Instanz (robuster als Live-Save-Reload), im Hintergrund, fire-and-forget.
- [ ] **Modul-Scanner**: scannt `data/override/module`, Abgleich mit Combo-Dictionary, Lücken-Flagging.
- [ ] **Card-Parser**: liest PC-Card-Modulliste (AA2QtEdit als Referenz).
- [ ] **Combo-Dictionary**: hand-gepflegte JSON/YAML-Tabelle Modul→Combo→Effekt.
- [ ] **SQL-DB (Long-Term-Memory)**: **PRO PLAYTHROUGH** (nicht global). Tabellen: chars (Selbst-Werte), relationships (char_id↔char_id, präsenz-abhängig), world_state. Snapshot beim Welt-Verlassen, Inject beim Welt-Betreten/Roster-Einfügen.
- [ ] **Playthrough-Lifecycle-Manager**: neuer Save → Ordner + gekoppelter Jail-Save (Vorlage) + leere DB anlegen, Mapping registrieren. Save löschen → alles mitlöschen. Mapping (Hauptsave→Jail-Save→DB) als Config.
- [ ] **Save↔DB-Brücke**: Play-Data aus Save lesen → DB; DB-Historie → Play-Data injizieren. Hängt an Save-Format-Zugriff (Punkt 9). Timing am End-Day/Heim-Übergang.
- [ ] **Cross-Welt-Beziehungs-Übersetzer**: Regeln "Welt-Ereignis X → char-interne Wert-Änderung Y" für Beziehungen zu abwesenden Chars.
- [ ] **Aktivitäts-DB + Schwellen-Resolver**: zweite DB-Ebene (training_count, sex_count, fights_won …). Resolver am End-Day: Schwelle erreicht → Status/Modul in Zustands-DB ableiten (z. B. → Martial Arts Prodigy, → Sex Addict). Schwellen frei tunebar.

### 8b. VERTEILBARKEIT — ANFORDERUNG (User, 2026-06-23): „Alles in EINER Install-Datei"
**Vorgabe:** Der Endnutzer darf NICHTS selbst installieren. Eine einzige Installer-Datei läuft durch und konfiguriert alles; alle nötigen Laufzeiten werden **mitgeliefert**.
- **Python mitliefern:** Orchestrator + Setup mit PyInstaller/Nuitka zu **einer eigenständigen `.exe`** packen → kein Python auf dem Zielrechner nötig.
- **.NET:** PPeX braucht .NET — wird aber von Stock-AAU ohnehin vorausgesetzt (also vorhanden). Zur Sicherheit den **gepatchten `PPeXM64` self-contained** publishen (.NET gebündelt) → keine externe Abhängigkeit.
- **Mutex-Closer in Python (ctypes) integrieren** statt separates .NET-Tool → eine Abhängigkeit weniger im Paket. (`_mutexfind` war nur Dev-Hilfe.)
- **Installer-Schritte (automatisch):** AAU-Install finden → Welt-Ordner per Junction anlegen (geteilte schwere Daten, kein Duplikat) → Lua-Patches anwenden (Single-Server-`loadPPeX` + Auto-Launch) → gepatchte `PPeXM64.dll` einspielen (Original sichern) → Custom-Module + Welt-Assets/Backgrounds + Save-Vorlagen kopieren → DB anlegen → Config + Start-Verknüpfung schreiben.
- **Konsequenz für JETZT:** schlanke Abhängigkeiten wählen (Orchestrator nur stdlib/ctypes, keine pip-Pakete), damit das Bündeln später trivial bleibt. Mutex-Logik nach Python portieren.

## 9. AAU-Trigger-Komponenten (Bau-Checkliste)

- [ ] CurrentPeriod-Poller → schreibt Phase in Flag-File (Brücke zu Python).
- [ ] Confinement-Trigger (Jailer-Modul als Vorlage abwandeln).
- [ ] Bedingte Knoten-Eject-Logik + Bauzustand-Flags (Card Storage).
- [ ] "Andere raushalten"-Logik mit Loop-Guard.
- [ ] **Dediziertes Prisoner-Modul** (+ Ex-Prisoner / Rehabilitated Varianten): Jailer als Vorlage abwandeln. Kapselt die Aktions-Erleichterungen präzise. Wird beim Welt-Wechsel aus DB-`status` abgeleitet auf die Card geschrieben.
- [ ] **Einsamkeits-/Loner-Module**: aus DB-`social_wealth` abgeleitet. Hoher Reichtum + Isolation → Manipulations-Anfälligkeit; Loner → anderes Modul. (+ optional Beziehungs-Verfall bei Abwesenheit im Resolver.)
- [ ] **Heimkehrer-Modul**: reagiert auf DB-Zustand "war weg + Partner vergeben" → sichtbare emotionale Reaktion (instabil/aggressiv/anfällig).
- [ ] **Offline-Resolver (täglicher Hintergrund-Tick)**: läuft am Tageswechsel (Sleep/`CurrentPeriod` end-sleep), schreibt ALLE inaktiven Welten pro Tag einen Schritt fort (Beziehungen kühlen, Partner wechselt trait-konsistent, optional Stats-Drift). Graduell akkumuliert, nicht einmalig. Abstraktion, nicht volle Engine-Sim. Chronik-fähig.
- [ ] (Optional) Kontext-Hint-Notifications nach Aktion A.

---

## 9b. ZUKUNFT: Multi-Welten-Skalierung

**Kernidee:** Sobald das Jail-Konzept steht, ist es kein "Jail" — es ist ein **generisches Welten-System**.
Jail ist nur die erste Instanz. Weitere Welten (Beach, Resort, Apartment Complex, …) fallen fast gratis raus,
WENN das Framework von Anfang an generisch gebaut wird (**Welten als Config, nicht hardcoded**).

### Was skaliert (gratis bei generischem Bau)
| Aspekt | Skaliert? |
|---|---|
| Mehr Welten technisch anlegen | **Ja** — N vorkonfigurierte Installationen |
| Eigene Optik/Backgrounds pro Welt | **Ja** — Override-Layer pro Installation |
| Eigene Rosters/NPCs pro Welt | **Ja** — eigenes Save pro Welt |
| Gesperrte/freischaltbare Bereiche pro Welt | **Ja** — Eject-Logik pro Welt |
| Card-Transfer zwischen ALLEN Welten | **Ja** — parametrisiertes Mover-Script (Welt A → Welt B) |
| Switch | **Ja** — Welten-Wähler-Menü statt einzelnem Jail-Button |

### Was NICHT skaliert (Engine-Wände wandern mit, werden sichtbarer)
- **Keine echten neuen Map-Layouts:** Jede Welt = dieselbe AA2-Map, nur reskinnt + Knoten gesperrt.
  Ein "Beach" ist die Schul-Map mit Strand-Texturen, nicht ein echter Strand.
- **Keine welt-spezifischen neuen Aktionen:** Überall dasselbe Aktions-Vokabular (talk/club/exercise…).
- **Funktioniert für:** "dieselbe soziale Simulation an einem anderen Ort, anders eingekleidet/befüllt".
- **Funktioniert NICHT für:** Welten, die fundamental anderes Gameplay bräuchten.

### RAM-adaptive Lade-Strategie (Stand 2026: 16 GB Boden, Mehrheit Richtung 32 GB DDR5)
- Pro Instanz ~1–1,5 GB. 5 Welten vorgeladen ≈ 5–7,5 GB (reiner Standby, nur 1 Welt rechnet je).
- **32 GB:** alle Welten vorladen → Sofort-Switch überall, kein Nachdenken.
- **16 GB:** nur aktive + wahrscheinlichste nächste vorladen, Rest on-demand (Kill+Restart).
- **Bau:** Launcher liest RAM (`psutil.virtual_memory()`) → adaptiv vorladen vs. on-demand.
  Optional User-Setting "Performance- vs. Sofort-Modus". Wenig Mehraufwand (Bausteine existieren eh).

### Die echte Obergrenze
NICHT der RAM begrenzt die Welten-Zahl, sondern der **Einrichtungsaufwand**: jede Welt = separate,
vorkonfigurierte Installation (Overrides, Backgrounds, Roster, gesperrte Knoten) von Hand. Der RAM trägt
zehn Welten locker; die Setup-Zeit ist die Grenze. → Beim Bau Welten-Setup so weit wie möglich automatisieren/templaten.

### Konsequenz für den Bau JETZT
Das Jail-Framework **von Anfang an generisch** anlegen:
- Welten als Config-Einträge (Name, Installations-Pfad, Save-Pfad, Override-Set, erlaubte/gesperrte Knoten).
- Switch-, Transfer- und Reload-Logik **parametrisiert über Welt-ID**, nicht "school"/"jail" hardcoded.
- Dann ist die spätere Erweiterung "Config-Eintrag + Installation einrichten", kein Umbau.

---

## 10. Referenz-Links

**AAUnlimited Kern:**
- Repo: https://github.com/aa2g/AA2Unlimited
- Wiki Home: https://github.com/aa2g/AA2Unlimited/wiki
- Releases: https://github.com/aa2g/AA2Unlimited/releases
- Installation: https://github.com/aa2g/AA2Unlimited/wiki/Installation

**Trigger / Module (für Confinement + Combos):**
- Triggers (Making-Guide): https://github.com/aa2g/AA2Unlimited/wiki/Triggers
- Module-Liste (alle ~250 + Jailer/Banchou/Killer): https://github.com/aa2g/AA2Unlimited/wiki/Module-list
- Modules (Anwendung): https://github.com/aa2g/AA2Unlimited/wiki/Modules
- Module-Download (Dropbox): https://www.dropbox.com/sh/86wdxunajbjpi13/AAAR8ExVfV1Y3_rDm2gx0gPDa?dl=0

**Quellcode (für Verifikation der offenen Punkte):**
- CurrentPeriod / Expressions: https://github.com/aa2g/AA2Unlimited/blob/master/AAUnlimited/Functions/Shared/Triggers/Expressions.cpp
- Event.cpp: https://github.com/aa2g/AA2Unlimited/blob/master/AAUnlimited/Functions/Shared/Triggers/Event.cpp
- Module.cpp: https://github.com/aa2g/AA2Unlimited/blob/master/AAUnlimited/Functions/Shared/Triggers/Module.cpp

**Card-Tooling (für PC-Card Modul-Parsing):**
- AA2QtEdit (Open Source, AAU-aware, Card/Class-Save-Editor): https://github.com/geneishouko/AA2QtEdit
- AA2QtEdit Releases: https://github.com/geneishouko/AA2QtEdit/releases

**Overrides / Asset-Layer:**
- Wiki-Seiten: Archive Overrides, Mesh Overrides, Object Overrides, Global Overrides, Shadow Sets, Lua character data fields, Lua cruft
  (alle unter https://github.com/aa2g/AA2Unlimited/wiki )

**Lua / interne Funktionen:**
- Preview infodump (Lua-Architektur, Poser-als-Lua, REPL): https://github.com/aa2g/AA2Unlimited/wiki/Preview-infodump

**Community (für unbestätigte Punkte):**
- AAU Discord Invite-Code: `MqP8rwwSP4`
- /aa2g/ (Board)

**Installation Basis:**
- AA2MiniPPX Torrent-XML: https://tsukiyo.me/AAA/AA2MiniPPX.xml
- Card-DB (Bepis): https://db.bepis.io/aa2

---

## 11. Wichtige Wahrheiten (nicht vergessen beim Bau)

1. **25 ist hart.** Mehr Chars nur über getrennte Saves/Welten, nie gleichzeitig geladen.
2. **Keine neue Map-Geometrie, keine neuen Aktions-Verben.** Immer umwidmen, nie neu bauen.
3. **Prozess-Isolation:** zwei Instanzen teilen keinen Live-State. Python über Save-Dateien = einzige Brücke.
4. **Passiv geht, aktiv ist zäh.** Lesen/Anzeigen/Asset-Tausch problemlos; ins Spielgeschehen eingreifen = undokumentierte Interna.
5. **Trigger sind global** → immer eingrenzen, sonst betrifft Code alle 25.
6. **Card Storage überlebt Sessions** → für allen persistenten Fortschritt nutzen.
7. **Combo-Semantik ist nicht auslesbar** → Dictionary bleibt Handarbeit, nur die Lücken-Erkennung ist automatisch.
8. **Borderless-Windowed Pflicht** für den Fenster-Switch. (`mod/borderless.lua` vorhanden.)
9. **ARCHITEKTUR-PIVOT (2026-06-23):** State-Transfer läuft **in AAU-Lua** (Hooks `on.save_class`/`on.load_class`/`on.period`
   + `GetCharInstData`/Storage-API), NICHT über externes `.sav`-Binär-Parsing. Python = nur noch Orchestrator
   (Fenster-Switch, Prozesse, DB, Datei-Brücke, Overlay). Siehe Abschnitt 3.4.
10. **Lua schreibt Char-Werte + Beziehungen + virtue/Stats/fightingStyle** (belegt, `char.virtue = X`). **Modul-Liste NICHT aus Lua schreibbar** → Status per vorinstalliertem Modul + Card-Storage-Flag gaten. #10 geklärt, **kein Blocker**.


---

## 12. SSOT / SAVE-KONSISTENZ -- Befunde & TODO (2026-06-24, Transfer-Bau)

**Modell A gebaut (commit-on-save, derive-on-load, tag-datiert):** Versklaven = provisorisch (nur
Preview-KickCard in school). `on.save_class` committet `<nDays>	Name	Gender	Werte` ->
`_orch_slave_commits.flag` -> Orchestrator `transfer_sync` ingestet ins `transfers`-Journal
(`memory.db`) -> leitet jails Insassen fuer den AKTUELLEN school-Tag ab -> `jail_intake` filtert.

**HARTE KORREKTUR (User): pro Playthrough gibt es NUR EINEN Save-Slot.** Speichern ueberschreibt
IMMER die aktuell geladene Save. Es gibt KEINE mehreren Zeitstempel/Versionen einer Save (kein
"NEW HOPE @ Tag 2" UND "NEW HOPE @ Tag 5" gleichzeitig). -> Die fruehere Begruendung "jail rollt
zurueck, wenn man einen AELTEREN school-Save laedt" ist KEIN Spiel-Feature. Folge: **die DB ist der
EINZIGE Verlaufs-Speicher** (das Spiel hat keinen). Tag-Datierung im Journal bleibt korrekt + noetig,
aber ihr Zweck = Verlaufs-/Auto-Save-Substrat, NICHT "alte Save laden".

**TODO naechste Iteration -- Auto-Save im ~7-Tage-Fenster:** Was, wenn der Spieler NICHT speichert?
Aktuell = kein Commit = jail leer (provisorisch). Gewollt: eine **Auto-Save-Funktion**, die innerhalb
des ~7-Tage-Fensters greift (z.B. am Tageswechsel), damit Nicht-Speichern keine Daten/Konsistenz
verliert. Vermutlich: Orchestrator triggert an der Tagesgrenze einen Save der AKTIVEN Welt + Capture
der inaktiven -> Commit ins Journal. Dockt an Modell A an (capture-on-switch + commit-on-save).

**Beziehungs-Reconciliation (User-Praezisierung 2026-06-24) -- der Grund fuer die SSOT:** Beziehungs-/
H-Werte sind SEAT-indiziert. Airis school-Dump 1:1 in jail zu restaurieren wuerde auf LEERE/FALSCHE
Seats zeigen (die anderen NPCs sind nicht im jail-Roster). Darum: NIE den Dump blind restaurieren.
Regel (SSOT haelt Beziehungen char_id<->char_id, seat-unabhaengig -- relationships-Tabelle existiert):
beim Injizieren pro Beziehung:
  * Gegenpart ANWESEND -> char_id auf den AKTUELLEN Live-Seat aufloesen (Roster-Scan) -> echte Beziehung schreiben.
  * Gegenpart ABWESEND -> KEINE Seat-Referenz -> Zustand char-intern VERDICHTEN (Modul/Wert), Beziehung
    SCHLAEFT in der SSOT, wird reaktiviert sobald beide ko-praesent sind (Boyfriend kommt auch ins jail /
    Char kehrt nach school zurueck -> "sie weiss, wer er ist").
Beispiele: Airi->PC "hasserfuellt" -> PC immer da -> restauriert. Airi->Boyfriend (nicht in jail) ->
"ist gebunden"-Zustand (speist Einsamkeit), kein Seat-Pointer. = Notizen 2.4c/2.4d. Mechanik:
create/restoreRelationshipPointsDump + create/restoreHStatsDump, seat<->char_id ueber Live-Roster-Mapping.
WICHTIG: aktueller Stand (2a, AddCard Basis-Karte) ist genau die richtige Grundlage -- die Basis-Karte
hat KEINE jail-Beziehungen (keine dangling refs); self-values (2b) + Beziehungen werden DARAUF geschichtet.


---

## ★ GEPLANTE EVOLUTIONS-ACHSEN (Backlog, 2026-06-25) ★

> Zweck: Design-Absicht festhalten, damit die Foundation sie nicht verbaut. **Kein spekulativer Code.**
> Jede Achse ist eine Instanz des bestehenden Musters (DB-Wahrheit -> Schwellen-Resolve -> Custom-Modul
> per Card-Storage-Flag), also **Content, kein Engine-Bau** -> später billig einfügbar. Siehe `EVOLUTION_MAP.md`
> (Map-Format) + `MODULE_CATEGORIZATION.md` (developable-Module = Regel-Kandidaten).

**B1 — Rassen-Achse (Race-XP) — als Nächstes baubar.** Race-Subsystem kartiert: 24 Rassen × 5 Valenzen
(DESIGNATION innate; BIAS/PREJUDICE/HOSTILE/OBSESSION developable). Eskalations-Leiter:
`neutral -> PREJUDICE -> HOSTILE/hunter -> HOSTILE/natenemy -> HOSTILE/slayer` (negativ) und
`neutral -> BIAS -> OBSESSION` (positiv). Beispiel: Nicht-Mensch von Mensch dominiert -> `Human:PREJUDICE`,
eskaliert unter Missbrauch. **Braucht:** `chars.race` (extern aus Karten-Modulen an der Tagesgrenze gelesen,
da Module nicht Lua-lesbar) + Tabelle `char_race_xp(char_id, other_race, positive, negative)` (Dominanz ->
negativ gg. Master-Rasse; liebevolle H -> positiv gg. Partner-Rasse). Analog zur Aktivitäts-DB.

**B2 — Slave-Progression (`unbroken -> broken -> trained`).** KEIN bestehendes Modul -> Custom-Modul bauen
(verzweigte Logik, 3 Stufen), GENAU wie Prisoner-Status (4.6): Card-Storage-Flag-gegated, getrieben von einem
DB-Zähler (Dominanz-/Trainings-Akkumulation). Bauen, wenn die Status-/Modul-Schicht dran ist — NICHT vorab.

**B3 — Lineage / Reinkarnation.** "Als Nachkomme wieder aufwachen, nicht tötbar." Das EINZIGE genuin neue
Daten-Konzept: braucht Eltern->Kind-Verknüpfung der Char-Identität. **Invariante wahren:** `char_id`/`chars`
bleibt erweiterbar auf Abstammung (später `parent_id`/`lineage_id` ergänzbar, ohne Bestehendes zu brechen).
Baustein "nicht tötbar" existiert schon: **`Undying`**-Modul (GATE) + Lineage-Link komponieren dazu. Kein Code jetzt.

**B4 — Welt-Features auf der Datenschicht (weit downstream):** "Slave Market", "Breed Room". Reine Features
ueber B2/B3 — erst wenn diese Achsen stehen. Hier nur als Intent vermerkt.

**Disziplin:** B1 ist der naechste konkrete Bau (analog Aktivitaets-DB). B2 kommt mit der Status-Schicht.
B3 = nur Invariante. B4 = spaeter. Nichts davon wird jetzt spekulativ vorgebaut.
