# Confinement-Modul — Spezifikation (Trigger-Editor)

> Hält NPCs auf einem Map-Knoten (= jail-Zelle). Wenn ein NPC den erlaubten Raum verlässt (egal ob normales
> Wandern oder „Weglaufen"/Flee), wird er per `NpcMoveRoom` zurückgeschickt. Reaktiv (Jailer-Prinzip), nicht
> präventiv — ein präventiver Hebel existiert in der Engine nicht (recherchiert: AI-Bewegung = undokumentierte
> Arrays, Gender-„Gate" ist nur eine weiche Reaktion, kein hartes Gate). Reiner Lua-Eject geht nicht
> (`m_forceAction` nicht Lua-erreichbar — Probe bestätigt) → Trigger-System ist der stabile Weg.

## Verifizierte Trigger-Bausteine (aus AAU-Quelle)
| Rolle | Trigger-Editor | intern (Quelle) |
|---|---|---|
| Event | **Room Change** | room-change event |
| Aktueller Raum eines NPC | **„Npc Current Room"** (Param: seat) | `GetNpcCurrentRoom(seat)` → int |
| Spieler-Seat (für NPC-Filter) | **„PC"** / Get PC | `GetPC()` → seat (−1 wenn keiner) |
| Diese Karte (Modul-Träger) | **This Card** | `GetThisCard()` → seat |
| Auslösende Karte | **Triggering Card** | `GetTriggeringCard()` → seat |
| **Action: zurückschicken** | **„Make Npc Move to Room"** (seat, room) | `NpcMoveRoom(seat, roomId)` |

> Hinweis: Die fettgedruckten Namen sind die wahrscheinlichen **Anzeige-Namen** im Editor-Dropdown — falls
> leicht abweichend, identifiziere sie über die Funktion (aktueller Raum / NPC zu Raum bewegen).

---

## STUFE 1 — MVP (fester Zell-Raum, beweist die Mechanik)

**Wo:** Modul auf jeden einzusperrenden jail-NPC installieren (AA2QtEdit → Module „In Use").
**Konstante:** `CELL` = **39** (Outside Station — der Stern-Knoten/feste Ausgangspunkt unten rechts).
**← VERIFIZIEREN:** stell den PC in jail auf genau diesen Knoten und prüfe `jail/_orch_probe.flag` →
die Zeile `Cox Robert ... room=<X>`. Ist X ≠ 39, ist das der echte Zell-Index → mir sagen, ich korrigiere.

**Trigger:**
```
EVENT:  Room Change

CONDITIONS (alle AND):
  1.  This Card  ==  Triggering Card          # nur reagieren, wenn ICH mich bewegt habe
  2.  This Card  !=  PC                         # GetThisCard() != GetPC()  -> nur NPCs, nie der Spieler
  3.  Npc Current Room (This Card)  !=  CELL    # ich bin außerhalb der Zelle

ACTIONS:
  1.  Make Npc Move to Room ( This Card , CELL )   # zurück zur Zelle (NPC läuft hin)
```

**Loop-Verhalten:** kein echter Endlos-Loop nötig — Bedingung 3 ist selbst-begrenzend: sobald der NPC wieder
in `CELL` ist, ist `Room != CELL` falsch → kein erneutes Feuern. Während er zurückläuft, kann das Event durch
Zwischenräume mehrfach feuern → es setzt nur dasselbe Ziel erneut (idempotent, harmlos). Optional sauberer:
ein Card-Storage-Flag `returning=1` setzen und Bedingung „nur wenn returning≠1" — meist nicht nötig.

**Flee-Fall:** wird automatisch abgedeckt — egal WARUM der NPC den Raum verließ (Schock/Flee oder normales
Wandern), die Bedingung „Room != CELL" greift. Er zappelt evtl. kurz raus-und-zurück; das dämpfen die schon
gesetzten Corruption-Werte (virtue=0 → weniger Schock-Flee).

---

## STUFE 2 — generisch + SSOT-getrieben (später)

Statt fester `CELL`-Konstante: den Zell-Raum (und ob das Modul aktiv ist) aus **Card Storage** lesen, das WIR
aus dem Orchestrator/Lua setzen (`setCardStorage`). Damit ist es:
- **pro NPC** konfigurierbar (verschiedene erlaubte Räume),
- **storage-gated** (Modul vorinstalliert auf allen Karten, aktiv nur wenn `in_jail=1`) — passt zum globalen Pool,
- **welt-/zukunftssicher** (andere Knoten/Welten = anderes Storage, kein Modul-Umbau).

**Trigger-Anpassung:**
```
CONDITIONS:
  1.  This Card == Triggering Card
  2.  This Card != PC
  3.  CardStorage(This Card, "in_jail")  ==  1                       # nur wenn als Insasse markiert
  4.  Npc Current Room (This Card)  !=  CardStorage(This Card,"cell") # außerhalb des erlaubten Raums
ACTIONS:
  1.  Make Npc Move to Room ( This Card , CardStorage(This Card,"cell") )
```
Brücke: Orchestrator schreibt wie gewohnt ein Flag → ein kleiner Lua-Mod überträgt es per `setCardStorage`
auf die präsenten NPCs (`in_jail`, `cell`). Mehrere erlaubte Räume = Liste in Storage + Bedingung „Room in Liste".

---

## Was DU jetzt brauchst
1. **Zell-Raum-Index festlegen** (aus `jail/_orch_probe.flag`: welcher `room=<idx>` soll die Zelle sein?).
2. Modul im Trigger-Editor anlegen (Stufe-1-Trigger oben) und auf einen Test-NPC installieren.
3. Testen: NPC aus der Zelle laufen lassen → er sollte zurückkehren; `_orch_probe.flag` zeigt die Raumwechsel.

Sobald Stufe 1 in-game greift, ziehe ich Stufe 2 (Card-Storage-Brücke aus der SSOT) nach.
