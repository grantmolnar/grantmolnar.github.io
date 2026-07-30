# Demonstration Company: The Ashlar Company

**Status:** Finalized and exercised by `play-state.example.json`.

## Purpose of the showcase journal

The checked-in play journal demonstrates the package under plausible table conditions rather than presenting an
omniscient tour of every authored clue. The company makes partial observations, forms conclusions
before exhausting all support, revisits an encounter when evidence changes its usefulness, and leaves some
material undiscovered. Notes record what the company did and thought at the time. Consequences
record durable changes to the adventure.

The journal therefore differs from the archived synthetic playthrough in four ways:

1. It follows named specialists with stable motives and disagreements.
2. It establishes revelations when the company actually articulates them, not whenever the data model
   permits it.
3. It allows missed or deferred clues and records why attention moved elsewhere.
4. It lets the final remedy emerge from the company’s values and accumulated relationships.

## The company

The **Ashlar Company** is a small Veyr-based group hired for work that lies between civic inspection,
ruin delving, and emergency recovery. They are known enough to receive a narrow commission, but not
important enough to command an office by reputation alone. Their name comes from an early job
stabilizing a collapsed tenement wall while residents were still trapped behind it. They do not use a
motto.

### Tessa Rane

Mara is a former ward sergeant who now negotiates contracts and conducts interviews for the company.
She keeps a numbered notebook, copies the wording of warrants, and asks who possessed a document
before asking what it says. She left the watch after a lawful quarantine she enforced caused three
avoidable deaths. She still believes public authority is necessary; she no longer believes lawful
orders excuse incuriosity.

**Useful habits**

- Preserves chains of custody and exact language.
- Can keep a hearing, crowd, or frightened official focused on a narrow decision.
- Recognizes when two offices are using overlapping jurisdiction to avoid responsibility.

**Pressure point**

Mara is tempted to solve institutional problems by acquiring broader authority. That can save lives,
but it can also make the company dependent on the same machinery that concealed the danger.

**Likely concern in this adventure**

She will want the Hall revisited once the company has evidence strong enough to secure stays,
records, and evacuation authority. She will resist accusing Dast before she can distinguish criminal
concealment from an ugly emergency decision.

### Nell Harth

Nell grew up among tenant drovers north of Rillcross and learned animal medicine from her mother. She
joined the company after guiding it through flooded grazing tunnels during a fever year. She is not a
mystic interpreter of animals. She knows normal fear, heat stress, herd contagion, bad water, and the
ways people project intention onto livestock.

**Useful habits**

- Reads herd movement as physical evidence.
- Wins practical trust from drovers and farm families by working before questioning.
- Notices when an official remedy destroys the evidence it claims to control.

**Pressure point**

Nell assumes city offices will protect city residents by exporting cost to the farms. She is often
right, but her contempt can turn a persuadable official into an enemy.

**Likely concern in this adventure**

She will oppose the Southgate cull immediately and press to visit Rillcross before the College can
reframe the pigs as laboratory specimens. At the Deep Bell, she will reject any remedy that quietly
sacrifices an unnamed rural tract.

### Orris Cale

Orris is an instrument maker and failed student of civic acoustics. He left the College without a
degree after refusing to certify a bridge-resonance model whose missing measurements had been hidden
for budgetary reasons. The model was later corrected; the bridge never failed; the College remembers
him chiefly as a difficult apprentice who was technically right and professionally ruinous.

**Useful habits**

- Builds tests that separate correlation from mechanism.
- Can read calibration traces, survey diagrams, and old machine tolerances.
- Treats contradictory measurements as an invitation rather than an inconvenience.

**Pressure point**

Orris wants the buried system to be intelligible. Once he sees that the Deep Bell can be retuned, he
may treat retuning as the morally superior answer because it is the most technically complete one.
He needs the others to keep human exposure visible in the model.

**Likely concern in this adventure**

He will want the College early, but Nell may pull the company toward Rillcross first. He is likely to
find common ground with Dast over the need to keep pumps and hospitals operating, which may alarm the
rest of the company.

### Sera Dain

Sera served as a sapper during the canal wars and now handles dangerous entry, bracing, and extraction
for the company. She does not dislike complex plans; she distrusts plans whose failure mode cannot be
explained to the people standing beneath them. She carries wedges, line, chalk, and a short iron maul
before she carries a weapon.

**Useful habits**

- Reads subsidence, load paths, and failing structures quickly.
- Turns abstract danger into evacuation distances, bracing tasks, and named fallback positions.
- Remains effective when machinery, animals, or crowds begin moving at once.

**Pressure point**

Sera prefers a bounded loss to an elegant risk. At the finale she may favor controlled collapse too
quickly, especially if the retuning sequence depends on damaged instruments or divided command.

**Likely concern in this adventure**

She will care less than Mara about proving Dast’s guilt and more about whether his operators can be
trusted during the repair. She will insist that every proposed remedy name its collapse zone and the
people responsible for clearing it.

## Company dynamics

The company works because its disagreements are legible.

- Mara asks what can be authorized and preserved.
- Nell asks who is being made to bear the cost.
- Orris asks what the system is actually doing.
- Sera asks what happens when the proposed answer fails.

No one owns an encounter. Nell’s knowledge does not solve Rillcross without testimony and mapping. Orris’s
training does not make the College cooperative. Mara’s commission does not control the Pump House.
Sera’s structural judgment does not determine which district may be sacrificed. Their expertise
changes the questions they ask and the consequences they can mitigate; it does not replace clues.

Two relationships should matter in the journal:

1. **Mara and Nell:** Mara sees authority as leverage; Nell sees it as the mechanism by which rural
   losses become administratively invisible. Their return to the Hall should be a negotiated choice,
   not an automatic procedural step.
2. **Orris and Sera:** Orris will become increasingly confident that the Bell can be retuned. Sera
   will become increasingly certain that confidence is not a safety margin. The finale should force
   them to produce one plan rather than merely state rival preferences.

## Opening disposition

The Ashlar Company enters the Hall of Petitions because Alda Mere has previously hired them to recover
records from an unsafe customs cellar. Mara expects a narrow inspection contract. Nell attends because
Rillcross petitioners have been waiting outside the chamber and one recognizes her family name. Orris
is interested in the bronze pin carried into evidence. Sera expects a crowd-control job and becomes
concerned when the floor itself carries a faint periodic vibration.

The company accepts the commission without becoming a single-minded unit. Mara wants written powers.
Nell wants an immediate stay on slaughter. Orris wants custody of the pin long enough to measure it.
Sera wants access to whatever underground works lie beneath the affected wards.

## Route decision

The Ashlar Company follows this route:

```text
Hall -> Southgate -> Rillcross -> College -> Hall -> Chapel -> Pump House -> Deep Bell
```

The order follows the company’s priorities rather than a prescribed scene sequence. Southgate comes
first because the cull threatens people, animals, and evidence. Rillcross comes before the College
because Nell insists that the field pattern should determine the experiment. The return to the Hall
occurs only after the company has three independent legal grounds for widening its commission. The
Chapel precedes Nine-Mile so the company learns the history and moral cost of the remedies before
hearing Dast’s practical defense.

The Six-Line Bell becomes available at Rillcross, but the company deliberately defers entry until it has
operating doctrine, pump control, live field readings, and evacuation authority.

## Journal-writing rules

The checked-in journal uses the package surfaces literally.

- Record a `encounter_visited` event when the company enters an encounter, not whenever it passes
  through the location. The event name retains the engine's internal `encounter` vocabulary.
- Record `clue_spotted` only for information the company actually notices and retains.
- Record `revelation_established` when the company states or acts upon the conclusion. A single strong
  clue may be enough.
- Use establishment notes to capture the company’s reasoning in its own terms, including mistaken or
  incomplete emphasis when the conclusion itself remains valid.
- Use visit notes for immediate decisions, promises, suspicions, and unresolved disagreements.
- Use `encounter_consequence_recorded` only for durable changes another encounter visit would find.
- Do not force all thirty-eight clues into the journal. Unspotted clues demonstrate that the graph remains
  robust without exhaustive play.
- Do not establish the optional return-to-Hall revelation merely because three supporting clues are
  present. Establish it only if the company consciously recognizes the Hall as useful again.

## Resolved decisions

1. **The Chapel precedes the Pump House.** The company enters the confrontation with Dast already
   aware that controlled collapse is an old civic choice with named victims.
2. **Dast remains an adviser under guard.** Tamar Vey and Oren Salk hold operational command; Dast
   contributes undocumented technical knowledge without regaining authority.
3. **The company chooses a bounded five-line retuning.** It isolates the failing Southgate line,
   evacuates the threatened warehouses and pens, accepts reduced water service and local subsidence,
   and refuses to sacrifice an inhabited district in secret.
4. **Thirteen clues remain unseen.** The company misses or declines the five original alternatives and all
   eight clue-density additions, preserving substantial fresh-play evidence outside the demonstration.

The complete narrative is in `FULL-PLAYTHROUGH.md`; the canonical event record is
`play-state.example.json`.
