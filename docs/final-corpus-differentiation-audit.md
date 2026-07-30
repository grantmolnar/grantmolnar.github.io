# Final Corpus-Wide Differentiation Audit

## Judgment

The thirteen adventure-specific second looks succeeded. The corpus is not a set of interchangeable plots wearing different setting nouns. Each adventure has a recognizable primary activity, evidence ecology, scale, pressure source, and mode of resolution.

The corpus is nevertheless not ready to close without a bounded comparative repair sequence. Side-by-side reading exposes several repetitions that were difficult to see while each adventure was being judged only against its own draft history. At the audit baseline, two encounter titles were exact duplicates. Workstream 1 has since resolved both collisions without identifier churn. More substantially, *The Siege of the Stone Lung* and *When the Swine Kneel* converge in their terminal procedure despite having different premises: both end inside an old civic machine with distributed crews, multiple stations, a short failure clock, incomplete prior preparation, and several materially valid remedies that allocate public cost. *The Glass Saint* shares enough commission, record, bell, and bounded-authority vocabulary with that pair to make the cluster more visible.

The right response is not another six-pass cycle for every adventure. Most adventures need no source revision. The remaining work should proceed through a small number of cross-adventure repair workstreams, each beginning with an explicit comparison target and ending with synchronized source, aid, demonstration, generated-packet, and test updates.

No authoritative adventure, journal, generated packet, or sample route changes in this audit session. The audit identifies and scopes later revisions.

## Scope and method

The comparison covered:

- thirteen authoritative `adventure.json` files;
- 138 encounters;
- 305 revelations;
- 1,385 clues;
- current READMEs and table-facing operating aids;
- all completed second-look records, especially Voice II image and register decisions; and
- demonstrated play only to verify that named parties, routes, discoveries, and outcomes did not leak back into authoritative source.

Historical build records were treated as evidence of development, not current table prose. Engine vocabulary such as `encounter`, schema keys, event names, and `party_size` metadata was excluded from editorial findings unless it appeared in a current player- or GM-facing document.

The audit used four comparative lenses:

1. **Narrative identity:** what the group actually does from opening commission to resolution.
2. **Evidence identity:** what kinds of facts the world produces and how those facts become actionable.
3. **Procedural identity:** clocks, route structures, authority boundaries, encounter progression, and finale operations.
4. **Voice identity:** sentence rhythm, moral vocabulary, recurring images, NPC archetypes, and the relation between physical action and explanatory prose.

The source corpus at the start of this audit has the aggregate SHA-256 fingerprint `a8f82a37549a10613d52e23ebead10c839b80f633e41de996fa2fa34d567b76c` across the thirteen authoritative adventure files. That fingerprint was unchanged by the audit session. Workstream 1 later changed only the two localized encounter identities and produced the current aggregate fingerprint `7e35dfa02667ea5867d7681fd6d71bb80b32bbdb6e7e8b53b8997813c6af46fe`; see `docs/corpus-differentiation-workstream-01.md`.

## What is already distinct

### Primary activities

The corpus sustains a broad range of table activity.

- *A Wedding for the River* is a nonviolent witness commission about consent, household meaning, and ceremony.
- *The Bell Beneath Harrowgate* is a large branching dungeon crawl driven by rescue, route danger, resource pressure, and buried royal violence.
- *The Cauldron of Nine Silences* is an infiltration and extraction heist whose central object can question the dead at their expense.
- *The Concord of Aurelune* is coalition construction through bargains, standing, side agreements, and constitutional drafting.
- *The Forest That Carries Dawn* is ecological route-finding and rescue inside a migrating living system.
- *The Glass Saint* is a civic-gothic investigation into copied memory, coerced voice, procession, and public ritual.
- *The Last Bell of Bramblewick* is a domestic village murder inquiry with alibis, private leverage, school money, and bounded disclosure.
- *The Mandate of Seven Reeds* is imperial governance under vacancy, provincial coercion, clan bargaining, and administrative legitimacy.
- *The March on Vossgard* is an offensive military operation in which battlefield control and surrender obligations matter more than inquiry procedure.
- *The Princess on the Salt Road* is an escort and pursuit adventure about custody, public authorship, route choice, and the protected principal's agency.
- *The Siege of the Stone Lung* is sector command under active siege, divided military authority, finite skilled labor, and a machine that distributes breathable air.
- *The Witch of Blackbriar Hall* is a villain hunt and captive-rescue horror adventure about hospitality converted into occult title.
- *When the Swine Kneel* is an ecological civic mystery in which ordinary livestock reveal a hidden hydraulic failure.

This range is real. It should be preserved rather than flattened into one Adventure Graph house plot.

### Evidence ecologies

The strongest adventures make their evidence native to their premise.

- Wedding evidence is carried by gifts, room use, work schedules, food, flood traces, spoken paraphrase, and withheld assent.
- Harrowgate evidence is carried by damaged architecture, bodies, tools, routes, pressure, beasts, and recoverable records inside a hostile dungeon.
- Cauldron evidence is carried by borrowed voices, ritual custody, death records, infiltration routes, and material handling of the vessel.
- Aurelune and Seven Reeds appropriately depend more heavily on filings, precedents, petitions, offices, seals, and spoken undertakings.
- Forest evidence is predominantly ecological: heat, root response, soil, pollen, fungi, breath, load, and migration behavior.
- Bramblewick uses chronology, rain, keys, books, work traces, food preparation, medicine, and village testimony.
- Vossgard uses battlefield possession, prisoners, reconnaissance, roads, gates, signals, and the conduct of forces under pressure.
- Salt Road uses public witnesses, travel records, mounts, signal systems, funeral custom, boats, and the principal's own speech.
- Stone Lung uses cracks, airflow, spores, shelling, cables, shifts, hammers, water, and command records.
- Blackbriar uses receipts, names, invitations, bodies, care arrangements, copied witness, and surviving pact carriers.
- Swine uses animal behavior, water channels, buried bronze, phase measurements, farm boundaries, and pump records.

The corpus therefore does not suffer from one universal clue idiom. Its weaker sameness appears mainly in the prose used to explain why evidence matters, not in the evidence itself.

### Scale and emotional register

The adventures also differ in scale and emotional temperature. Wedding and Bramblewick remain intimate. Harrowgate, Vossgard, and Stone Lung operate at military or city scale. Forest treats a moving ecology as both setting and actor. Aurelune and Seven Reeds are formally public but emotionally restrained. Blackbriar permits hatred and horror. Swine allows dread to grow from exact animal behavior without making the animals supernatural. These distinctions survive the second-look sequence.

## Material findings

### 1. Baseline encounter-title collisions

At the audit baseline, two pairs were exact duplicates across authoritative adventures.

#### The Deep Bell

- *The Bell Beneath Harrowgate*: `deep-bell`
- *When the Swine Kneel*: `the-deep-bell`

This is not a harmless generic room label. In both adventures the encounter is a terminal ancient bell beneath a settlement. The duplicate therefore reinforces a deeper structural overlap and makes Swine look derived from Harrowgate even where its animal investigation is original.

**Disposition:** repair in Swine. Harrowgate's title is integral to the adventure title and dungeon identity. Swine should retain the object and its bell function but give the terminal encounter a name specific to the six-line hydraulic resonator, civic survey tradition, or suspended crown. The stable encounter ID may remain unchanged if changing it would create needless journal and link churn; the player-facing and GM-facing title should change.

#### Chapel of the Open Door

- *The Last Bell of Bramblewick*: `chapel-of-the-open-door`
- *The Witch of Blackbriar Hall*: formerly matched Bramblewick; now `chapel-of-the-free-witness`

Both chapels also perform witness, record, refuge, and moral-boundary work. The shared title does not currently establish a deliberate setting connection, and the two adventures otherwise present independent worlds.

**Disposition:** repair in Blackbriar unless a later setting decision intentionally unifies the institutions. Blackbriar already has Saint Orra, Mercy House, the vale's burial economy, and Judith's pact history available for a more local chapel identity. Bramblewick's title is more deeply integrated into its village vocabulary and should remain the baseline.

**Workstream 1 resolution:** Swine's encounter is now **The Six-Line Bell** at stable ID `the-deep-bell`; Blackbriar's institution is now **Chapel of the Free Witness** at `chapel-of-the-free-witness`. The permanent duplicate-title allowlist is empty. Full rationale and fingerprints are recorded in `docs/corpus-differentiation-workstream-01.md`.

### 2. Stone Lung and Swine converge at the finale

The two adventures begin differently but approach the same terminal grammar.

Both finales include:

- an old civic machine beneath or within the settlement;
- distributed stations that one small company cannot occupy alone;
- allied crews continuing bounded work in parallel;
- several approach routes whose advantages depend on prior encounters;
- a short, visible multi-cycle failure sequence;
- evidence converted into operational capability;
- remedies that remain available under imperfect preparation;
- remedies distinguished mainly by how they allocate public cost;
- a culpable official whose technical knowledge may still be necessary; and
- an ending that separates technical success from later legal or political accounting.

These are individually sound design choices. Their concentration in adjacent adventures makes the dramatic movement interchangeable: investigate distributed symptoms, restore an old system model, gather crews and authority, enter the machine, survive three escalating phases, and choose which population bears the remedy.

The distinction in setting nouns is not enough. Stone Lung should feel like a siege command problem whose machine is one contested front. Swine should feel like an interpretation problem in which animal behavior exposes civic self-deception and the final intervention remains answerable to living surface corridors.

**Disposition:** high-priority comparative repair.

- In Stone Lung, preserve enemy initiative, command conflict, sector loss, battlefield timing, and the possibility that the machine operation succeeds or fails because the siege is still actively attacking it. Avoid making the Lung read primarily as a neutral engineering puzzle with three costed settings.
- In Swine, preserve the pigs as the investigation's irreplaceable measure. The terminal procedure should depend more explicitly on interpreting changing herd behavior across the surface and less on a generic sequence of station operations. The exact three-cycle structure, approach language, and remedy presentation should be reviewed against Stone Lung line by line.
- Do not remove multiple remedies or allied crews merely to create difference. Change the dramatic center, not the resilience.

### 3. The civic-machine cluster extends into The Glass Saint

*The Glass Saint* does not share Stone Lung and Swine's engineering finale, but the three adventures form a visible civic-procedure cluster through repeated use of:

- bounded commissions;
- seals and overlapping offices;
- records that must be copied or placed under multiple custodians;
- bells as timing and public reach;
- distributed helpers and preserved stations;
- old systems whose original purpose was partially forgotten; and
- a distinction between a technically effective act and legitimate authority to perform it.

Glass Saint remains substantially distinct because its central concerns are voice, memory, repetition, and coercive public ritual. That distinction should become stronger during the cluster repair rather than subjecting Glass Saint to another broad rewrite.

**Disposition:** complete in Workstream 3. After Stone Lung and Swine were separated, Glass Saint received a seven-field diction repair confined to its overview explanation and the summaries and bodies of the Bell Chapel, Grand Belfry, and Vale Manor. Every route, clue, authority boundary, counterkey use, bell operation, and outcome remains; the current instructions now proceed through procession, page, pane, vow, voice, breath, door, peal, and public reckoning rather than generic stations, approaches, zones, states, and ledgers.

### 4. Aurelune and Seven Reeds share a court-administration skeleton

The two large court adventures are not duplicates, but they have the corpus's second-strongest structural resemblance.

Both contain:

- a formal central court and a deadline;
- a commission whose standing is recorded and contested;
- many factional encounters that produce commitments, conditions, and leverage;
- side agreements that later constrain the public settlement;
- a finale built around a second or culminating audience;
- a need to distinguish lawful form from practical execution; and
- a vocabulary dense with authority, office, record, undertaking, petition, and public consequence.

Their actual political questions differ. Aurelune asks whether a coalition assembled through exact bargains can remain governable after victory. Seven Reeds asks who may govern provinces, labor, rice, shrines, roads, and armed clans during an imperial vacancy. Their native materials also differ: Aurelune's law is visibly performed through leaves, plaques, mirrors, banners, and magical recognition; Seven Reeds should remain grounded in officers, storehouses, roads, dikes, rice, shrines, hostage structures, and provincial compliance.

**Disposition:** complete in Workstream 4. Aurelune now presents its court as a living coalition: banner encounters ask what houses can truthfully recognize, the Petition Chamber renders compatible bargains as seasonal light, and the Sunseed reads the coalition at the Conclave. Seven Reeds now presents its court as provincial administration under incomplete sovereignty: consultations produce allocations and submissions, the Chamber builds one field-capable command chain, and the Second Audience is dispatch rather than ratification. Thirty-three authoritative fields changed; all clues, identifiers, routes, outcomes, and journal events remain unchanged.

### 5. The compromised-but-necessary official recurs too often

The corpus repeatedly uses an adversarial or culpable official whose diagnosis is partly right, whose institution performs real public work, and whose expertise may remain necessary after exposure.

Important examples include:

- Corven Dast in Swine;
- Kest Mourne and divided command in Stone Lung;
- Dorion Vey in Salt Road;
- Orlo Vane in Bramblewick;
- Mael's custodial and institutional position in Cauldron; and
- Judith Crowl's genuinely useful care institutions in Blackbriar.

Moral complexity is a corpus strength. The repetition becomes a weakness when the same explanatory cadence recurs: the antagonist is culpable, the warning or institution remains correct, utility explains but does not excuse, and later accounting remains necessary.

The characters are not equally similar. Dorion is an honorable officer enforcing a bad warrant. Orlo murders to protect a beneficial fraud. Dast conceals evidence to avoid rationing. Judith deliberately creates and renews predatory occult claims. These differences must be dramatized through conduct rather than recovered in the final audit paragraph.

**Disposition:** medium-high voice and characterization repair.

- Preserve mixed institutions and non-cartoon motives.
- Reduce repeated verdict formulas such as “X can help and still answer for Y,” “utility explains but does not excuse,” and “technical success does not decide lawful authority.”
- Give each adversary a distinct relationship to concession, self-knowledge, bargaining, violence, and public exposure.
- Protect Judith's exceptional hateability. Her utility should explain dependency, not invite the same balanced-administrator reading used for Dast or Dorion.

### 6. Bell, chapel, hall, house, and open-door imagery is overconcentrated

Some shared architectural vocabulary is ordinary fantasy language. The present concentration nevertheless creates a recognizable naming habit:

In the post-Workstream 1 authoritative sources:

- six encounter titles contain **bell**;
- six contain **chapel**;
- ten contain **hall**;
- ten contain **house**; and
- four use **open**, including two Open Door institutions.

The corpus also contains *The Bell Beneath Harrowgate*, *The Last Bell of Bramblewick*, *The Bell Chapel*, *The Black Bell Redoubt*, Harrowgate's *The Deep Bell*, Swine's *The Six-Line Bell*, and numerous bell-based clocks or warnings elsewhere.

Not all of this should be removed. Bells perform materially different work in Harrowgate, Glass Saint, Bramblewick, Swine, Wedding, and Vossgard. They are part of Adventure Graph's emerging identity: public sound, warning, timing, memory, and reach. The problem is exact duplication and unexamined default naming, not the motif itself.

**Disposition:** low-to-medium. The exact collisions are repaired; retain deliberate bell family resemblance and rename only where a title or description still fails to carry adventure-specific work.

### 7. A shared explanatory cadence remains visible

Across otherwise distinct adventures, the prose repeatedly uses a recognizable argumentative pattern:

- physical or procedural statement;
- semicolon or contrast;
- “does not,” “cannot,” “rather than,” or “merely” qualification;
- a final sentence separating practical success from moral, legal, or political legitimacy.

High-spread corpus vocabulary includes `route`, `record`, `authority`, `named`, `custody`, `living`, `answer`, `preserve`, `ordinary`, `exact`, `pressure`, `remains`, and `cannot`. Much of that vocabulary is useful and often precise. The sameness appears when several adventures use it in the same sentence architecture.

Representative house formulations include:

- a route or skipped encounter “does not forbid” an option;
- a technical act “does not decide” authority or guilt;
- evidence “matters when” it moves an office or command;
- a valid concern “does not authorize” concealed harm;
- a partial success “remains a real state”; and
- a named cost “must” survive the remedy.

These formulations are excellent editorial invariants but should not all remain as diegetic prose in every adventure.

**Disposition:** completed in Workstream 6. The final sweep retained one character-voice use of ‘is not the same as,’ removed the other five authoritative uses, and removed every authoritative use of ‘it does not erase’ and ‘does not decide.’ Procedures and tests retain the underlying distinctions without repeating the same editorial verdict.

### 8. Encounter openings are differentiated but share a house closing habit

The two introduction passes succeeded: openings generally begin with an encounter already acting, use concrete sensory or procedural pressure, and avoid giving away the supported revelation. They also avoid a repeated explicit question-mark ending.

The remaining family resemblance is a controlled closing beat: a clerk waits, an object moves, a route narrows, a named speaker asks for a decision, or a mechanism begins to fail. This is mostly a desirable Adventure Graph convention because it hands the scene to the table.

**Disposition:** no independent repair workstream. Recheck openings only when a targeted source revision changes the encounter's dramatic center.

### 9. Demonstration-party separation is successful

The authoritative adventures do not depend on their named demonstration parties. The later second-look work consistently restored fresh-play subjects, moved named roles back into subordinate party-design and playthrough records, and treated unseen clues as available alternatives rather than missed obligations.

The comparative audit found no reason to reopen the demonstrations merely for route variety. Future source repairs must continue the established rule: improve the authoritative adventure first, then update or regenerate demonstrations only where the source change invalidates them.

**Disposition:** verified and permanently guarded in Workstream 6. Harrowgate's named demonstration porter was removed from authoritative source and replaced with a role that a player character or unnamed porter may fill. No named demonstration character now appears in authoritative source.

## Adventure-by-adventure dispositions

### A Wedding for the River — retain

Wedding is one of the corpus's strongest differentiators. No villain, nonviolent authority limits, consent that can remain incomplete, and a finale assembled from accepted ceremonial functions give it a unique dramatic movement. Its records and witnesses belong to the premise rather than to a generic civic style.

Closed in Workstream 6 after a two-field cadence repair. No structural or further source rewrite is planned.

### The Bell Beneath Harrowgate — retain with collision protection

Harrowgate's scale, dungeon density, hostile geography, rescue pressure, monsters, and branching terminal danger remain unique. Preserve *The Deep Bell* here and repair the Swine collision instead.

Closed in Workstream 6 after naming, fresh-play-role, and cadence repairs. Harrowgate's titles, graph, packet structure, and dramatic ownership remain intact.

### The Cauldron of Nine Silences — retain

The heist, borrowed dead, custody chain, extraction route, and contested sacred institution remain distinctive. Its darkness overlaps Harrowgate and Blackbriar only at the genre level.

Closed in Workstream 6 after the final cadence check. Mael's Workstream 5 conduct and all structural invariants remain intact.

### The Concord of Aurelune — targeted comparison with Seven Reeds

Aurelune's materialized law, magical recognition, coalition bargains, and constitutional aftermath remain strong. Its risk is that the large court graph and agreement language can read like Seven Reeds at a different palace.

Completed in Workstream 4 and closed after the Workstream 6 cadence and naming sweep.

### The Forest That Carries Dawn — retain

Forest has the corpus's clearest noninstitutional evidence ecology and one of its most distinctive modes of action. Its route and cost language is grounded in living systems rather than offices.

Closed after Workstream 6. No further source rewrite is planned.

### The Glass Saint — protect ritual identity

Glass Saint's reconstruction succeeded. Its central sequence of broken display, copied memory, opened doors, stolen voices, procession, and public compulsion is distinctive. Its risk comes from shared civic-procedure vocabulary with Stone Lung and Swine.

Workstream 3's ritual grammar was preserved. Workstream 6 repaired two character-name collisions and three cadence fields without structural or broad prose revision.

### The Last Bell of Bramblewick — retain, protect local chapel identity

Bramblewick's domestic scale, chronology, privacy, school fund, food labor, and village record keep it distinct. Its Chapel of the Open Door should remain the baseline unless a deliberate shared setting is later adopted.

Completed in Workstreams 1 and 5 and closed in Workstream 6. Bramblewick retained its chapel identity, Orlo's conduct grammar, and fresh-play source; its demonstration-only Elian Marr became Teren Malk.

### The Mandate of Seven Reeds — targeted comparison with Aurelune

Seven Reeds remains differentiated by provincial administration, rice, roads, dikes, shrines, coercive holding structures, clan power, and an incomplete imperial center. Its risk is court-procedure convergence with Aurelune.

Completed in Workstream 4 and closed after the Workstream 6 cadence and naming sweep.

### The March on Vossgard — retain

Vossgard's direct battlefield verbs, possession of terrain, active enemy force, mass combat, surrender obligations, and heavy-combat identity are clearly separate from the rest of the corpus.

Closed after Workstream 6. No further source rewrite is planned. Use it as a reference when strengthening active enemy initiative in Stone Lung.

### The Princess on the Salt Road — retain

Salt Road's protected principal, pursuit, divided custody, witnesses as both shield and signal, and sanctuary threshold make its route structure distinctive. Dorion participates in the compromised-official pattern, but his conduct under a bounded bad warrant differs materially from concealment-based antagonists.

Completed in Workstream 5 and closed after the Workstream 6 cadence sweep. Dorion retains literal warrant discipline.

### The Siege of the Stone Lung — high-priority comparative repair

Stone Lung must foreground siege, command, enemy action, sector allocation, and finite military opportunity at every stage of the finale. The Lung should remain a machine that makes divided survival physical, not become the same old-system repair chamber used by Swine.

Completed in Workstream 2 and closed after one Workstream 6 cadence repair. Stone Lung retains enemy initiative, contested command, sectors, and military roads.

### The Witch of Blackbriar Hall — identity collision resolved; villainy protected

Blackbriar is distinct in villain intent, captive rescue, occult carriers, invitation, bodies, and care converted into title. Workstream 1 localized its institution as **Chapel of the Free Witness** and subsequently renamed its witch **Judith Crowl**, migrating every name-derived Blackbriar identifier because no live play record required compatibility.

Completed in Workstream 5 and closed in Workstream 6 after Varro Cleft's name repair and one cadence repair. Judith's engineered dependency and victim substitution remain unchanged.

### When the Swine Kneel — high-priority comparative repair

Swine's premise, animals, farm evidence, public panic, and hydraulic interpretation are highly distinctive. Its remaining weakness appears only after the investigation reaches the terminal chamber, where the repaired title now separates it from Harrowgate but the procedure still converges with Stone Lung.

Completed in Workstream 2 and closed in Workstream 6 after the demonstration-only Mara Venn became Tessa Rane and one cadence repair. The finale's live herd reports and hydraulic response remain unchanged.

## Ordered repair program

### Workstream 1 — identity collisions and comparative baselines — complete

Completed in `docs/corpus-differentiation-workstream-01.md`.

1. Preserved source and journal fingerprints before editing.
2. Renamed Swine's terminal encounter while retaining its stable ID.
3. Localized Blackbriar's chapel identity while retaining its stable ID.
4. Renamed the Blackbriar witch Judith Crowl and migrated every affected unplayed identifier.
5. Added tests that prevent exact encounter-title duplicates unless an allowlist documents an intentional shared institution.

This workstream now supplies stable encounter identities and comparative baselines for the deeper prose repairs.

### Workstream 2 — Stone Lung and Swine terminal differentiation — complete

1. Build a paragraph-level comparison of both final encounters.
2. Mark shared functions: approaches, station staffing, clocks, failure escalation, contribution carryover, remedies, partial success, and later accounting.
3. Assign each shared function a distinct dramatic owner:
   - Stone Lung: enemy initiative, command conflict, sector survival, military timing.
   - Swine: live animal interpretation, surface communication, civic denial, hydraulic phase, inhabited line corridors.
4. Rewrite only the fields needed to make those centers operational.
5. Update current aids and demonstrations only where the authoritative change affects them.
6. Regenerate packets and validate all graph and journal invariants.

Completed in `docs/corpus-differentiation-workstream-02.md`. Stone Lung now assigns escalation to enemy initiative, command conflict, military roads, and named sectors. Swine now assigns escalation to live herd reports, inhabited surface corridors, civic denial, and hydraulic response; its fixed three-cycle/station procedure is removed.

### Workstream 3 — Glass Saint residual separation — complete

Completed in `docs/corpus-differentiation-workstream-03.md`. The repair changed seven authoritative fields and no authored object. The Chapel now reads as four speaking workings and a three-piece answer to the rite; the Belfry assigns every choice to named hands, ropes, bronze, and notes that cannot be unsounded; the Manor organizes the finale through doors, household, joined relic materials, an already-existing public hearing, body, voice, reach, and five public reckonings.

### Workstream 4 — Aurelune and Seven Reeds court differentiation — complete

Completed in `docs/corpus-differentiation-workstream-04.md`. Aurelune now owns coalition composition, magical recognition, banner relations, seasonal light, and the Sunseed's reading of the final instrument. Seven Reeds now owns office allocation, acts of submission, named field recipients, command chains, delayed receipt, correction, and Imperial dispatch.

### Workstream 5 — adversary and institutional voice audit — complete

Completed in `docs/corpus-differentiation-workstream-05.md`. Dast now turns evidence into named service cuts and transferred signatures; Kest Mourne admits facts through ledgers, maps, command tubes, and divided keys; Dorion writes literal concessions and stops at recorded jurisdiction; Orlo retreats through revised grammar and beneficiary exposure; Mael annexes safeguards into custody claims; and Judith answers exposure by substituting victims rather than conceding title.

### Workstream 6 — final corpus cadence and name sweep — complete

Completed in `docs/corpus-differentiation-workstream-06.md`. The final sweep removed exact character-name reuse and repeated titled first names, separated two demonstration-only names, converted Harrowgate's named demonstration porter into a fresh-play role, reduced three repeated editorial verdict formulas, regenerated all thirteen packets, and added derived corpus-wide regressions for naming, party leakage, cadence, and closure.

## Guardrails for all repair work

- Do not change infrastructure, schemas, or runtime semantics to solve editorial overlap.
- Do not regularize clue counts or route structures merely to make two adventures look different.
- Do not weaken formal resilience.
- Do not remove morally mixed institutions merely because complexity recurs.
- Do not turn Blackbriar's hateable antagonist into another necessary expert whose later usefulness dominates the harm.
- Do not make Stone Lung less of a siege or Swine less of an animal investigation.
- Do not preserve a demonstration route at the expense of fresh play.
- Keep source, current aids, demonstrations, generated packets, tests, changelog, and roadmap synchronized after every source repair.
- Treat historical construction records as history; annotate rather than silently rewriting their past-tense facts.

## Completion state

The comparative audit and all six workstreams are complete. The later reference-defragmentation naming
closure rebuilt the complete 138-title ledger, accepted four title-only deconflictions, reviewed eighteen
current near-match or practical-ambiguity candidates, preserved every stable encounter ID, and left no
unresolved duplicate or deconfliction candidate. Its final record is
`docs/example-encounter-name-ledger.md`.

No further corpus-wide repair workstream is scheduled. Future revisions should be prompted by fresh play, a newly demonstrated defect, or a separately scoped product requirement.
