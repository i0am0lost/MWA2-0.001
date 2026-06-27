# Mod-Kartographie — wiederverwendbare Mechaniken & relevante Positionen

> **Zweck:** Vollständige Karte aller AAUnlimited-Mods (`school|jail/AAUnlimited/mod/`) mit markierten
> relevanten Positionen (Hooks, RVAs, Globals, APIs) und Zuordnung zu den offenen Projekt-Items.
> Stand 2026-06-25. Quelle = direkte Code-Lesung. Legende der Relevanz: ⭐ = Schlüssel für ein offenes
> Item · 🔧 = nützliche API/Idiom · 🎯 = RE-Position (RVA/Global) · ◽ = kosmetisch/irrelevant.
> Verwandt: [[HANDOVER_transfer_2026-06-24]], `_re/RE_LADEFUNKTION.md`, `AA2_Jail_Projekt_Notizen.md`.

---

## A. PROJEKT-EIGENE MODS (Orchestrator)
| Mod | Hooks | Funktion |
|---|---|---|
| `master_slave.lua` | `on.answer`, `on.end_h`, `on.period`, `on.save_class` | ⭐ Dominanz-Combo INSULT→FIGHT→FORCE_H → slave; Commit-on-save |
| `rel_snapshot.lua` | `on.load_class`, `on.period`, `on.answer` | ⭐ Kontinuierlicher Beziehungs-Snapshot → SSOT `char_rels` |
| `logperiod.lua` | `on.period`, `on.load_class`, `on.keyup` | ⭐ Tag/Perioden-Flag (`_orch_day/period.flag`) + Live-Char-Dump |
| `jail_intake.lua` (nur jail) | Timer + load/period/room | ⭐ Roster-Rekonstruktion (KickCard+AddCard+Inject) |
| `orch_savename.lua` | `on.load_class` | 🔧 Meldet geladenen Save-Namen (jail-Kopplung) |
| `loadtest.lua` | `on.keyup` | 🎯 RE-Test-Mod (Detour 0xB2440/0xB2680, F6=dump) |

---

## B. WIEDERVERWENDBARE MECHANIKEN (für offene Items) ⭐

### B1. Aktions-Gating / Knoten blockieren — `nomurder.lua`, `butthurt.lua`, `triggers_supplemental.lua`
**→ offenes Item: „Map-Knoten/Aktionen blockieren (jail-Dungeon, progressiv)"**
- **`nomurder.lua` — `on.move(struct, user)`**: fängt **startende Aktion** ab, nullt sie:
  `struct.conversationId = -1; struct.target1 = 0`. Minimal-Vorlage fürs Gaten.
- **`butthurt.lua` — `on.plan(ok, e, who)`**: verhindert **geplante Aktion** mit **Chance + Cooldown**
  (`e.conversationId = -1; ok = false`). Zeigt Chance/Cooldown-Logik + `on.char_spawn_end`, `on.convo`.
- **`triggers_supplemental.lua` — `on.move(params,user)`, `on.card_expelled(actor0,actor1,murder_action)`**:
  Tracking gestarteter Aktionen + Erkennung, dass eine Karte entfernt wurde.
- Gegenstück Beweis: `on.move` ist read+write (Aktion umschreibbar). Whitelist-Quelle = `const.lua` (s. D1).

### B2. Zeit/Perioden steuern — `timewarp.lua`
**→ offenes Item: „jail = nur Nacht; erzwungener Rückwechsel an Tagesgrenze"**
- **`on.period(new, old)` gibt modifizierte Periode zurück** → lenkt den Fluss um.
- Poked `GetGameTimeData()`: `d.day = (d.day+7±1)%7`, `d.nDays`. Period-Raum = `1..10`.
- Muster: `return zielperiode` hält/erzwingt Phase.

### B3. Raum-/Node-Erkennung + KOMPLETTE RAUMKARTE — `cram_school.lua`, `music.lua`
**→ offenes Item: Knoten-Blocking (welcher Raum?) + Optik pro Welt**
- **`cram_school.lua` hat die VOLLSTÄNDIGE RAUMLISTE** (`getRoomName(idx)`, Index 0–52) + `isRoomInterior(idx)`
  Innen/Außen-Klassifikation. **Das ist das Knoten-Vokabular für jail-Gating.** (Liste s. Anhang E.)
- Hooks: `on.roomChange(seat, room, action)` (cram_school) und **`on.room_change(inst)`** (music).
- APIs: `GetCharInstData(i)`, `character:IsPC()`, `character:GetCurrentRoom()`, `GetPlayerCharacter()`,
  `inst.m_char`, `count_charas_in_room()`.
- **Reskin-via-Ordner-Umbenennen**: cram_school tauscht Lighting-Sets per `os.rename` in `data\sets\!lighting_night\`
  → Idiom für „Optik pro Welt / jail=Nacht" ohne Binär-Eingriff.

### B4. H-/Aktivitäts-Introspektion — `climaxbutton.lua`, `facecam.lua`, `music.lua`
**→ offenes Item: „Aktivitäts-DB (H/Climax-Zähler → Schwellen → Zustände)"**
- Hooks: **`on.start_h(hInfo)`**, **`on.end_h()`**, `on.change_h(hi,currpos,active,passive,aface,pface)` (facecam).
- `hInfo.m_currPosition`, `hInfo.m_activeParticipant`/`m_passiveParticipant.m_charPtr.m_charData.m_gender`.
- Handover nennt zusätzlich `m_climaxCount` als Zähler-Quelle. → on.end_h + Zähler = Aktivitäts-DB-Aufhänger.

### B5. Obedience / Antwort erzwingen — `geass.lua`
**→ offenes Item: jail-Dominanz / „Gehorsam"-RPG-Schicht; Combo-Zuverlässigkeit**
- **`on.answer(resp, as)`**: `resp = 1` erzwingt „ja"; `as.answerChar.m_lastConversationAnswerPercent = 999`.
- `as.askingChar.m_thisChar == GetPlayerCharacter()` = PC-Check-Idiom.

### B6. Custom-Text-Overlay — `subtitles.lua` (KORREKTUR ggü. früherer Einschätzung)
**→ offenes Item: Node-Block-Feedback („du kannst da nicht hin")**
- **`AddSubtitles(text, fname)` zeigt beliebigen Text** (+ `InitSubtitlesParams(...)` fürs Styling).
  Bisher an `on.load_audio(fname)` gekoppelt — als generischer Text-Push-Kandidat zu verifizieren.
- `notifications.lua` = NUR Styling (`InitNotificationsParams`), kein eigener Push → subtitles ist der Weg.

### B7. PC-Steuerung — `toggleautopc.lua`
**→ offenes Item: PC/NPC autonom in jail laufen lassen**
- `setPcAuto/getPcAuto` über 🎯 `peek_walk(GameBase+0x376164, 0x38) + 0x2e3` (PC-Auto-Flag-Byte).
- 🎯 Enthüllt **Game-State-Context-Global `0x376164`** (≠ Save-Context `0x767f48`).

### B8. Autosave-Netz — `extsave.lua`
**→ offenes Item: „Auto-Save im ~7-Tage-Fenster"**
- `bAutosave` + `sAutosave` „1 4 6 8 9": `on.period` ruft auto `quicksave()` bei gewählten Phasen.
- ⭐ Save-Funktionsaufruf: 🎯 `proc_invoke(GameBase+0xF36D0, 0, data)`; g_var-Patch @ `0x470B0`.

---

## C. ENGINE-/RE-POSITIONEN (RVAs & Globals, gesammelt) 🎯
> Laufzeit-`GameBase` ASLR-variabel (alles GB-relativ). `peinfo.py` nutzt File-Base `0x400000`.

| RVA / Global | Quelle | Bedeutung |
|---|---|---|
| `0xF36D0` | extsave | **SAVE-Funktion** `proc_invoke(GB+.., 0, data)` |
| `0xF3C00` | RE F5 | **LOAD-Funktion** (Spiegel von Save; `ret 4`, ECX=Name) |
| `0xB2680` | RE F7 | Load-**Wrapper** (Reset+Load+Housekeeping; this=EAX) |
| `0xB2440` | RE | **`enqueueLoad(context)`** (reiht Lade-Aktion ein) |
| `0xB24D0` | RE | Thunk `H` → `this=[context+0xE29C]`, jmp 0xB2680 |
| `0x413FF0` | RE F7 | Container-**Reset** (esi=container) |
| `0x10E9C8` | RE R4 | **Live-Reload-CRASH** (`cmp [esi+0x3c],edx`, dangling) |
| `0xB6264` | RE R4 | ⚠️ **Dangling Manager-Global** (Teardown-Frage!) |
| `0x767f48` | RE | Save/Load-**Context-Global** (`+0xE21C`=container, `+0xE2A0`=name, `+0xE29C`=action-slot) |
| `0x470B0` | extsave | g_var-Patch-Stelle (Save-Struct-Anker) |
| `0x376164` | toggleautopc | **Game-State-Context-Global** (walk 0x38 +0x2e3 = PC-Auto) |
| `0x167413`,`0x167C24` | music | Musik-Auto-Change-Patch-Stellen (NOP-Override) |
| `0x36f638` | strutil | String-Helper-Anker |
| `0x3100A4`,`0x353180` | dx/edit | Edit-GUI Prop/Window |
| `0x1ADF70`/`0x1CB7D0` | poser | Eyetrack-Funktion (play/edit) |
| `0x353290`/`0x376298` | poser | Prop-Listen-Anker (play/edit) |
| `0xA913A→0x32540A`, `0x9F77A→0x30568E` | patches | .bmp→.png Konstanten-Swap |
| Save-Struct | RE F3 | `+0x64`=Name(utf16), `+0x394`=CharArray, `+0x398`=Valid-Ptr |

---

## D. HILFS-/REFERENZ-MODS
### D1. `const.lua` 🔧 — **Aktions-Vokabular** (essentiell fürs Gating)
Vollständige Aktions-IDs 0–113, u.a.: `INSULT=33, FIGHT=34, FORCE_H=38` (unsere Combo), `MURDER=82`,
`TOGETHER_FOREVER=81`, `TALK_*=15-19`, `STUDY_TOGETHER=20`, `INTERRUPT_*=63-65`, `H_END=66`, `BREAK_H=113`,
`KISS=46, HUG=45, HEADPAT=44, SLAP=83`, `FOLLOW_ME=49, GO_AWAY=50, COME_TO=51`.

### D2. Bibliotheken 🔧 (kein eigenes Verhalten)
`memory.lua` (poke/peek), `strutil.lua`, `com.lua`, `dx.lua`, `pp2util.lua`, `json.lua`, `opt.lua`,
`musicconfig.lua`, `patches.lua`/`patcher.lua` (Pre-Launch-Patches), `fakereg.lua` (Portabilität, genutzt).

### D3. `triggers_supplemental.lua` 🔧 — Dump/Restore-Backbone (2176 Z.)
`createRelationshipPointsDump`/`restoreRelationshipPointsFromDump`, `createHStatsDump` etc. = SSOT-Fundament
(genutzt von rel_snapshot/jail_intake). Hooks: `on.dispatch_*_trigger`, `on.move`, `on.card_expelled`, `on.ui_event`.

---

## E. ANHANG — Engine-Grenzen-Bestätigung aus den Mods
- **Raster fix 25 Seats** (`for i=0,24` in cram_school, climaxbutton 0..0x18). Roster-Cap bestätigt.
- **53 Räume fix** (cram_school `getRoomName`): School gates(0)…Machine Room(52). Keine neue Geometrie →
  jail-„Knoten" = Teilmenge dieser 53, per Gating gesperrt/freigeschaltet. Innen/Außen klassifiziert.
- **Reskin = Ordner-/Set-Tausch** (cram_school lighting, override/shadow-set) — kein Binär-Eingriff nötig.

---

## F. KOSMETISCH/IRRELEVANT fürs Projekt ◽
`borderless`, `facecam`, `hirestex`, `reshade`, `wined3d`, `win10fix`, `cram_school`(Lighting-Teil),
`aaface`, `JMCP`, `fixlocale`, `playtrans`/`makertrans`/`subtitles`(Übersetzung), `nobra`, `homosex`(disabled),
`unlocks`, `jizou`, `poser/*` (Studio), `edit/*` (Card-Editor-GUI — aber s. Modul-Editor-RE separat).
