# Evolution Map — das „Gehirn": Zustand → Modul (Schwellen-Regeln)

> Das hand-kuratierte Regelwerk, das **DB-Zustand in Modul-Zuweisungen übersetzt** — am End-of-Day-Resolve
> ausgewertet. Prinzip: Module werden **verdient, nicht vergeben** — ein Char wird durch seine akkumulierte
> DB-Trajektorie in ein Modul **getrieben**, wenn eine Schwelle überschritten wird (und es nicht schon innate ist).
>
> Verwandt: `MODULE_CATEGORIZATION.md` (welche Module developable = Regel-Kandidaten; 259 yes) ·
> `AA2_Jail_Projekt_Notizen.md` §4.6/4.7 (Architektur) + Backlog · `playthrough_db.py` (die DBs).

---

## 1. Einordnung — Einbahnstraße (Notizen §4.6/4.7)

```
Aktivität/Erfahrung (Engine-Events)         on.end_h, on.move, master_slave, …
        ↓ Capture-Mods schreiben Flags -> Orchestrator ingestet
DB / SSOT (Wahrheit)                          char_activity, char_rels, char_race_xp, chars
        ↓ End-of-Day-Resolve wertet DIESE Map aus  (Python, am Tageswechsel)
Zustand abgeleitet                            disposition=sex_addict, race_att[Human]=prejudice, …
        ↓ beim Welt-Wechsel (Reload-Moment): Card-Storage-Flag setzen
vorinstalliertes Custom-Modul rendert         "Sex Addict" / "Prejudice-Human" / "Prisoner"
```

**DB -> Modul, nie umgekehrt.** Der Flag ist ein Output der DB. Module sind vorinstalliert + flag-gegated
(Module nicht aus Lua zur Laufzeit schreibbar — §4.6). Reine Werte-Effekte (virtue/Stats) zusätzlich direkt
aus Lua (`char.virtue = X`).

## 2. Die DBs, die die Map speist

| DB-Quelle | Status | speist Achse |
|---|---|---|
| `char_activity` (kumulative H-Zähler: climax, totalH, cumIn*, riskyCum…) | ✅ gebaut (school) | Sexual/Corruption |
| `char_rels` + `social_wealth` (Beziehungs-Graph, positive Bindungen) | ✅ gebaut | Sozial/Einsamkeit |
| `char_race` (eigene Rasse) + `char_race_xp(char_id, other_race, positive, negative)` | 🔶 **DB-Layer gebaut** (set/get-race, `add_race_xp`, `accrue_domination`, `race_attitude`-Leiter, unit-getestet) | Rassen-Achse |
| Status-/Zähler-Flags (Dominanz/Training) | ⬜ B2 (mit Status-Schicht) | Slave-Progression, Prisoner |

## 3. Regel-Schema (das Map-Format)

```yaml
rule: <id>
  axis:     sexual | social | race | status | stats        # nur zur Gruppierung
  outcome:  <Modul oder Modul-Stufe>                        # was zugewiesen/geschaltet wird
  when:     <Bedingung über DB-Werte>                       # Schwelle(n); AND/OR erlaubt
  escalate: [<höhere Schwelle> -> <stärkeres Modul>]        # optional: Stufenleiter
  unless:   already innate/present                          # nie doppelt/gegen Designation
  apply:    end-of-day resolve  ->  Card-Storage-Flag beim nächsten Welt-Wechsel
```

Schwellenwerte (`THRESH_*`) sind **freie Tuning-Entscheidungen** (Python-Konstanten), später kalibrierbar.

## 4. Beispiel-Regeln (Vorlage, je Achse)

### 4.1 Sexual / Corruption — Inputs liegen schon in `char_activity`
```yaml
rule: corruption_via_H
  axis: sexual
  outcome:  Corruption (corrupted style)        # AA2-Vorbild: Corruption-Modul (virtue↓ -> corrupted1-4)
  when:     activity.climax + activity.cumSwallowed + activity.cumInVagina  >  THRESH_CORRUPT
            AND  char.virtue is dropping
  escalate: > THRESH_CORRUPT_HI -> Sex Addict
  unless:   already innate (z.B. startet schon als Sex Addict / Hoe)
```
Beispiel-Trajektorie (User): Attractive + nicht-Addict -> in jail „covered in cum" (cumSwallowed/cumInVagina
akkumuliert) -> Schwelle -> Persönlichkeits-Evolution (-> Corruption -> Sex Addict).

### 4.2 Rassen-Achse — Eskalations-Leiter (Backlog B1)
```yaml
rule: racial_prejudice
  axis: race
  outcome:  <DominatorRace>:PREJUDICE                       # z.B. Human:PREJUDICE  (Prejudice-Human)
  when:     char.race != DominatorRace
            AND  race_xp[char][DominatorRace].negative  >  THRESH_PREJ
  escalate: > THRESH_HOST1 -> <Race>:HOSTILE/hunter         # Hunter-X   (emotionaler Hass)
            > THRESH_HOST2 -> <Race>:HOSTILE/natenemy       # Natural Enemy-X (kampfstark)
            > THRESH_HOST3 -> <Race>:HOSTILE/slayer         # Slayer-X   (tödlich)
  unless:   char.race == DominatorRace      # man entwickelt keine Prejudice gg. die eigene Rasse

rule: racial_bond
  axis: race
  outcome:  <PartnerRace>:BIAS  ->  :OBSESSION              # positive Richtung
  when:     race_xp[char][PartnerRace].positive  >  THRESH_BIAS
  escalate: > THRESH_OBSESS -> <PartnerRace>:OBSESSION
```
Quelle der race_xp: Dominanz-Event (master_slave) -> negativ gg. Master-Rasse · liebevolle H -> positiv
gg. Partner-Rasse. `chars.race` extern aus den Karten-Modulen an der Tagesgrenze gelesen.

### 4.3 Sozial / Einsamkeit — Inputs liegen schon (`social_wealth`)
```yaml
rule: loneliness
  axis: social
  outcome:  Einsamkeits-/Exploitable-Modul
  when:     was social_wealth=high  AND  present_bonds == 0 (isoliert in jail)  für  >= N Tage
```
Notizen 2.4c: hoher sozialer Reichtum + jetzt isoliert -> starker Manipulations-Effekt; Loner (low) -> andere Regel.

### 4.4 Status — GATE (am Übergang gesetzt, nicht zähler-getrieben)
```yaml
rule: prisoner_status
  axis: status
  outcome:  Prisoner -> Ex-Prisoner -> Rehabilitated      # EIN Modul, 3 Flag-Werte (§4.6)
  when:     world transition school->jail  (Prisoner) / jail->school (Ex-Prisoner) / Schwelle (Rehab)
  note:     GATE — per Rolle/Meilenstein, NICHT per akkumuliertem Zähler
```

### 4.5 Slave-Progression — Custom-Modul nötig (Backlog B2)
```yaml
rule: slave_progression          # PLATZHALTER -- Modul existiert noch nicht, muss gebaut werden (wie Prisoner)
  axis: status
  outcome:  Slave: unbroken -> broken -> trained
  when:     domination/training counter crosses tier thresholds
  status:   BACKLOG — bauen wenn die Status-/Modul-Schicht dran ist
```

## 5. Resolve-Ablauf (am Tageswechsel)

1. Capture-Mods haben tagsüber Aktivität/Erfahrung in die DB geschrieben (`char_activity` ✅, später `char_race_xp`).
2. **End-of-Day-Resolve (Python)** liest pro Char die DB-Werte, wertet die Regeln hier aus, schreibt den
   abgeleiteten Zustand (`disposition`, `race_att[…]`, `status`) in die Zustands-DB.
3. **Beim nächsten Welt-Wechsel** (Reload-Moment) wird pro Char das passende **Card-Storage-Flag** gesetzt;
   das vorinstallierte Custom-Modul rendert die Wirkung. Reine Werte (virtue/Stats) direkt geschrieben.

## 6. Nächste Bau-Schritte (aus dieser Map)

1. **Race-DB (B1):** `chars.race` + `char_race_xp` + Capture (Dominanz/H -> Rasse) — analog Aktivitäts-DB.
2. **Resolve-Engine:** Python-Modul, das diese Regeln am End-Day auswertet (liest DBs -> schreibt Zustand).
3. **Custom-Module + Card-Storage-Gating:** Prisoner zuerst (Vorbild), dann Slave-Progression (B2).
4. **Schwellen-Kalibrierung:** die `THRESH_*` einstellen (freie Design-Entscheidung).
