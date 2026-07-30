# Design Notes: When the Swine Kneel

The authoritative adventure contains thirty-eight leads; the demonstration remains subordinate to that current source.

## Design goals

This example tests whether Adventure Graph can support a substantial encounter-based adventure without turning each encounter into a clue dispenser. The constraints were:

- exactly seven encounters;
- a serious premise that begins in a large city and expands into its farmland;
- alternating social, physical, analytical, rural, historical, industrial, and climactic modes;
- three independent clue sources for every necessary revelation;
- at least three outgoing clues and three distinct encounter targets from every nonterminal encounter;
- directed reachability from the opening encounter;
- global edge connectivity of at least three; and
- a finale improved by investigation but never locked behind one route.

## Structural model

The source contains:

- 7 encounters;
- 10 revelations: 9 required and 1 optional;
- 30 clues;
- 12 distinct undirected encounter connections; and
- exact global edge connectivity 3.

Clue and revelation lists are dual views of the same records. A clue cannot appear in an encounter sheet without also appearing in the revelation audit.

## Encounter rhythm

Each encounter changes the mode of play:

1. The Hall opens with testimony, jurisdiction, and public pressure.
2. Southgate turns the reports into a physical crowd and animal crisis.
3. The College slows the pace for exact experiment and archival conflict.
4. Rillcross widens the scale from one herd to a regional pattern.
5. The Chapel turns lost infrastructure into remembered civic violence.
6. The Pump House puts the responsible policy maker inside a live engineering emergency.
7. The Deep Bell combines social authority and technical resources in a multi-station finale.

The graph does not require this order. The sequence describes a repertoire of encounter modes, not a plot.

## Topology

```text
Urban triangle:
  Hall — Stockyards
  Stockyards — College
  College — Hall

Outer triangle:
  Rillcross — Chapel
  Chapel — Pump House
  Pump House — Rillcross

Layer bridges:
  Hall — Rillcross
  Stockyards — Chapel
  College — Pump House

Finale approaches:
  Rillcross — Deep Bell
  Chapel — Deep Bell
  Pump House — Deep Bell
```

The two triangles create interlocking investigative layers. Each urban encounter has a distinct bridge outward. The Deep Bell has three approaches corresponding to field observation, historical doctrine, and active infrastructure.

The minimum cut has size three. Several degree-three encounters supply limiting cuts. This is enough resilience to prevent a single missed connection from controlling the adventure without making the graph so dense that navigation becomes meaningless.

## Revelation architecture

Six revelations unlock encounters:

- Southgate carries the anomaly inside Veyr;
- the College can test the buried pulse;
- Rillcross reveals the warning’s geography;
- the Chapel keeps the lost doctrine;
- Nine-Mile is driving the crisis; and
- the Deep Bell lies beneath the city.

Three required conceptual revelations answer the adventure’s central questions:

- **What are the pigs doing?** Reading the danger.
- **Who created the immediate crisis?** Dast knowingly drove the pumps beyond tolerance and suppressed the readings.
- **What can be done?** The Bell admits several remedies, each with a different human cost.

The optional return-to-Hall revelation makes the opening institution useful after the first visit. Evidence can stay culls and seizures, suspend quarantine, preserve archives, and widen the commission.

## Clue independence

Supporting clues differ in kind, not merely encounter. The conclusion that the pigs are warning instruments can arise from:

- anticipatory behavior at Southgate;
- a controlled resonance experiment at the College; or
- a six-herd geographic map at Rillcross.

The remedies can be learned from theoretical models, historical doctrine, or direct inspection of the pump controls. Redundancy therefore crosses modes of play as well as encounters.

## Finale design

The Deep Bell is terminal and has no outgoing clues. Its encounter converts prior investigation into leverage:

- the Hall supplies authority, evacuation, and ration priorities;
- Southgate preserves an urban animal readout and control of a threatened district;
- the College supplies measurements and models;
- Rillcross supplies live distributed readings and rural evacuation;
- the Chapel supplies doctrine and the history of controlled collapse; and
- Nine-Mile supplies load control and trained operators.

A short route can reach the Bell with little understanding. Missing knowledge becomes time, danger, collateral damage, or morally blind decision-making—not an invisible wall.

## Voice decisions

The final prose pass follows four rules:

1. Describe pressure through objects, bodies, orders, and machinery before naming an abstraction.
2. State NPC positions without apologizing for them; let play reveal where their reasons fail.
3. Keep GM instructions direct and brief.
4. Keep the pigs natural. Their precision, not anthropomorphism, carries the uncanny tone.


## Second-look coherence repair

The publication coherence pass fixes the recent catalyst and divided-knowledge model without changing the graph or clue matrix. Nine-Mile ran an intermittent drought schedule for weeks; Dast's uninterrupted Convocation load begins three days before play and produces the first coordinated warnings. Water Office plans retain auxiliary load and phase controls, the College can measure the pulse, and the chapel families retain the lost six-line doctrine. No one institution starts with the whole system.

The six radial lines pass beneath the city edge and outward through Rillcross. Southgate is an urban station on the third line, not a seventh network branch. The pigs are natural pressure indicators rather than designed instruments.

The Hall's commission is fresh-company compatible and bounded. Named local crews may continue prepared work in parallel, but delegation remains vulnerable and recorded. Retuning must address all six lines while allowing a damaged line to be deliberately isolated.

## Dogfooding findings

The example exposed one document-generation weakness: encounter sheets originally printed clue descriptions without discovery procedures or supported revelations. The renderer now includes both, allowing an encounter sheet to function at the table without constant reference to the master lists.

## Second-look Voice II

Voice II completes the adventure-specific sequence with three local source revisions: the causal explanation, the optional Hall revelation description, and the Deep Bell body. The pass replaces the final generic commission actor and residual game-design vocabulary with the Hall hearing, inspection authority, observable phase and load, station consequences, and accumulated structural loss.

The current README, demonstration-company record, route stress test, and full playthrough now use **encounter**, **commission**, **company**, or **Ashlar Company** according to context. This document remains a historical thirty-clue construction checkpoint and retains its dated `encounter` vocabulary. Engine keys and generated paths likewise retain `encounter` for compatibility.

The roadmap records all thirteen adventure-specific second looks as complete and advances to the **Final corpus-wide differentiation pass**.
