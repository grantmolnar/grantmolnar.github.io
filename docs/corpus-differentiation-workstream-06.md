# Corpus Differentiation Workstream 6: Final Cadence, Naming, Fresh-Play Leakage, Validation, and Closure

## Judgment

Workstream 6 is complete. The final corpus sweep found no remaining structural convergence that justified another adventure-scale rewrite. It did find a bounded set of exact character-name collisions, three demonstration-party names that had become indistinguishable from authoritative nonplayer characters, one authoritative source that named a demonstration porter as though every fresh table inherited him, and three editorial verdict formulas whose repetition remained audible after the five substantive repair workstreams.

The repair is intentionally narrow. It changes names, one fresh-play role description, and selected explanatory sentences while preserving every authored object, graph relationship, route, clue, revelation, outcome, threshold, and mechanical procedure. All six workstreams are complete, and the corpus-wide differentiation program is closed.

## Naming audit

The final naming audit compared exact anchored character names across all thirteen authoritative adventures and separately compared titled first names. It then checked every named demonstration character against the complete authoritative corpus.

The following authoritative names were repaired:

- Glass Saint's **Mara Vale** became **Iria Vale**, preserving the Vale household while separating her from Aurelune's Mara Venn.
- Glass Saint's **Corven Ash** became **Halwen Gorse**, separating him from Harrowgate's Corven Ashe.
- Harrowgate's **Mara Venn** became **Rhea Colm**, eliminating an exact collision with Aurelune.
- Harrowgate's **Ansel Greve** became **Odran Greve**, eliminating a titled-first-name collision with another Ansel.
- Blackbriar's **Brann Cleft** became **Varro Cleft**, eliminating a titled-first-name collision with another Brann.

Two demonstration-only names were also changed so that validation parties remain unmistakably local artifacts:

- Bramblewick's **Elian Marr** became **Teren Malk**.
- Swine's **Mara Venn** became **Tessa Rane**.

After the repair, the exact anchored full-name collision set is empty, the repeated titled-first-name collision set is empty, and no named demonstration character appears in an authoritative adventure source. The shared object name **Deep Bell** remains deliberate: Harrowgate owns the encounter title while Swine uses the term only for an in-world machine whose encounter is **The Six-Line Bell**.

## Fresh-play leakage repair

Harrowgate's authoritative opening previously named **Torren Pike**, the porter used by its staged demonstration, as though every fresh playthrough inherited that person. The source now defines the function rather than the validation character:

- one Ember porter survived an earlier descent;
- a player character may be that survivor; and
- otherwise the porter briefs the commission, may guide the first descent, and remains available for surface rescue.

Torren Pike remains in Harrowgate's party design, full playthrough, and active demonstration journal. The source no longer requires him, names no demonstration party member, and does not bend the adventure around the recorded route.

## Cadence sweep

The final cadence sweep searched authoritative source for repeated editorial verdicts rather than broadly suppressing useful vocabulary. Three formulas had enough spread to sound like authorial adjudication rather than adventure-specific conduct:

- **“is not the same as”** occurred six times across five adventures;
- **“it does not erase”** occurred nine times across eight adventures; and
- **“does not decide”** occurred seven times across six adventures.

The repair leaves one deliberate use of “is not the same as” in Moss-in-Evening's spoken voice in *A Wedding for the River*. It removes the other five uses and removes every authoritative use of the other two formulas. The replacements assign judgment to concrete objects and actors: warrants remain in force, duties remain answerable, claims remain unresolved, roads and victims remain to be reckoned with, and successful interventions leave named aftermath work rather than receiving a repeated abstract qualification.

Historical construction and second-look records retain the language they actually reviewed. Replay archive snapshots are synchronized to current authoritative source, as required by their reproducibility contract, while their archived event streams and metadata remain unchanged.

## Authoritative repair

The repair changes exactly **forty-six authoritative fields** across twelve adventures:

- two in *A Wedding for the River*;
- nineteen in *The Bell Beneath Harrowgate*, including the two name repairs and role-based porter description;
- two in *The Cauldron of Nine Silences*;
- four in *The Concord of Aurelune*;
- one in *The Forest That Carries Dawn*;
- five in *The Glass Saint*;
- one in *The Last Bell of Bramblewick*;
- three in *The Mandate of Seven Reeds*;
- three in *The Princess on the Salt Road*;
- one in *The Siege of the Stone Lung*;
- four in *The Witch of Blackbriar Hall*; and
- one in *When the Swine Kneel*.

*The March on Vossgard* required no authoritative change. No encounter title, identifier, clue, revelation, route, outcome, edge, threshold, or validation rule changed in any adventure.

## Synchronization

The naming and cadence repairs are synchronized through:

- all affected authoritative adventure sources;
- Glass Saint's two source mirrors and packaged resource;
- current READMEs, operating aids, route audits, party designs, and full playthroughs where repaired names or cadence appear;
- all active demonstration journals whose recorded prose contains a renamed character;
- all five replay archive snapshots, refreshed to current authoritative source while preserving their event streams and metadata;
- all thirteen regenerated Markdown packets and play summaries;
- the changelog, roadmap, and final comparative audit; and
- permanent corpus-wide regression tests.

The archived event streams remain the same demonstrations. Wedding, Forest, and Swine archive event streams remain byte-identical. Glass Saint and Blackbriar archive event streams differ only by the documented character-name substitutions; all five archive metadata blocks remain byte-identical. Name-only journal updates do not change event types, order, targets, outcomes, routes, or authored state transitions.

## Fingerprints

The canonical corpus aggregate hashes each sorted `examples/*/adventure.json` path, a null separator, canonical sorted-key JSON, and another null separator:

- before Workstream 6: `1cf6b0ddebcdfca27ccc9d975fb6e1f6f84235cf7bb2704953498a6448d8ee50`;
- after Workstream 6: `6c3dc2b056aed9c1ca2aa7f1b78c1e334ced44e5d07cd01e5c67c682d810c1f5`.

Individual authoritative sources changed as follows:

- Wedding: `2664cd5ddef163157f1c36c6f309c3b281af26db17346688cc474bd6f4ca2bf5` → `56e4c9051725196fd97d93f8e5a5a7f4a5a602047075ed0a113ad88f309d5c6f`;
- Harrowgate: `cfcf9f632007446c492751c0d07a3f80b813fa44dea6a52ce9e8f6bb69fc0510` → `03c0e3ba8c0f71d1a6d89d19a3f5e15c207dd9e0ceaebc2aeba8d44f92076969`;
- Cauldron: `6bf728dfcda463922b4b6af59c724f1e2598a1f9461f9648b95a7246f57057b5` → `d795f551c086892cec7c91476ea3c3b3583afcc68abc7eb8bf4ae3dd6062fe42`;
- Aurelune: `b77728a3a3da1ec7fd893cf991993b3b963aeb9eb713ff7c2541e6128daa0811` → `504575e12b6228126b2aaa10ec706d8ec9012e93427a10974946f3f03050892a`;
- Forest: `16c10888c9ab7b666b786c4c0189168c166b96a90ede687daacfeb68f55350bb` → `1482da10f2b0bc90d6090d98cc36cfdbd6b588185370cedbcaf90f17703b42a4`;
- Glass Saint: `d8c4673dabab89774e8bb4c94f599129154529393df5519c686078cea9905df0` → `0add9b6dc72a0d2db99486439acc516edce8aff21de68cc40d4a17c162bbb6e6`;
- Bramblewick: `7d3c554925f3009f6f759b4b61c4eb19df81032b9ccc8350e81d8494de007ca0` → `c7ba4a4a36dccce9e58d00ebf5c7df359128d132fc14351204ed651412f7ea66`;
- Seven Reeds: `195d3c0fa6a7ab5a4a1f552fff1bc3e07ecb7235197fb96ee6cac9efaf9b8fea` → `9e3ef65cfc3a5f1b3833f639face6b97052ac06edf4280e49ddd70aa62bb218b`;
- Salt Road: `8ab46382f1daba431998dbb452253fdf0986e41db61b988cc6bdefe43c4e7f55` → `9e465d810b5f2dd8076d3dfd0b037e14fd69a6b5e12374d477f3d3ae653dd4fe`;
- Stone Lung: `aab312ad9618eb1d8a8ce0a73cce6bcfa1ff1f7bd9b3e8deca67328c7341518f` → `1cbe4844c406e973d08976448cfe3466173932f02f4898c80d483fff3baf629a`;
- Blackbriar: `3c74e2983927a2b38590d20bfc3304d12be77a3d8982fc2d331eeb42e34d5793` → `7feb2b4d377a56dfa4dd5ac6401fff41cbf9f405b00b21122f86e2fd3d16eaed`;
- Swine: `04cb1350004eb48ae0bc48818f24b4e83f17edfadc1bf869d292fece53b873e8` → `f8f2c3e0f9fa502abe18f44cd5801ba0da5c9bd3cb158818b1a67d8f2d2cb628`.

Three active journals changed only because their named demonstration characters were renamed:

- Harrowgate, 366 events: `03204741054ba8d4e8c1c247011eaaf4fe8f64e661a5a5598d8482b97d0373c5` → `95fd707eb25b139667d028f9c9103c29759530d9992912c1af9c4a42e2d55922`;
- Glass Saint, 116 events: `5046dffd2ce02396d44b0ffbba356022b1d3f2d4c320143a29adf85cd79e423b` → `010d04b64310d0d6e8ed87cc81a5470d8e56dfb6ff64888fe3fb67a22869f4e7`; and
- Blackbriar, 200 events: `823470c3837eac3616dd9c6ff114598ecbfbce57e2e16e41d9af011a2b377688` → `41fdf1c45673a3a0e408849e2ae02478b642330116b4a614c04ec664cb783d6c`.

The other ten active journals remain byte-identical.

## Permanent regressions

The corpus integration suite now requires:

- no exact anchored full character name to occur in more than one authoritative adventure;
- no titled first-name combination to recur across authoritative adventures;
- no named demonstration character to appear in authoritative source;
- the Harrowgate survivor role to remain playable by a player character or assignable to an unnamed porter rather than requiring Torren Pike;
- every retired repeated name to be absent from its complete current project tree, including source, aids, journals, archives, and packets;
- Glass Saint's three authoritative source mirrors to remain byte-identical;
- “is not the same as” to occur in authoritative source only in the retained Moss-in-Evening dialogue;
- “it does not erase” and “does not decide” to remain absent from authoritative source;
- all three retired formulas to remain absent from the twelve current operating aids repaired in this workstream; and
- the roadmap and final audit to remain closed after Workstream 6.

These tests derive names from the corpus and demonstration headings rather than protecting only a hand-maintained list of known collisions.

## Preserved invariants

The final repair preserves:

- all thirteen adventure titles and all encounter, revelation, and clue identifiers;
- every encounter count, revelation count, clue count, graph edge, route, threshold, and formal resilience property;
- every opening view except where a repaired character name appears;
- every mechanical option, custody rule, clock, remedy, partial success, and aftermath state;
- all active demonstration event counts, event order, targets, outcomes, and state transitions;
- all historical construction records as historical records; and
- the principle that fresh-play source outranks demonstration continuity.

## Verification

- `603` executable repository tests pass with the unchanged seven-test Hypothesis graph module excluded because Hypothesis is unavailable.
- Every authoritative adventure passes structural validation.
- All 38 repository JSON files parse successfully.
- Fresh regeneration of all thirteen packets matches the checked-in packets exactly.
- Semantic comparison against Workstream 5 finds exactly the forty-six documented authoritative field changes.
- The three changed active journals preserve event-for-event identity apart from the documented proper-name substitutions; the other ten remain byte-identical. Five replay archive metadata blocks remain byte-identical; three archive event streams remain byte-identical and two differ only by the same documented name substitutions.
- Python compilation passes for `src` and `tests`.
- Ruff, Pyright, Poetry, and Hypothesis remain unavailable in this environment.

## Closure

The six-workstream comparative repair program is complete:

1. exact identity collisions and comparative baselines;
2. Stone Lung and Swine terminal differentiation;
3. Glass Saint residual separation;
4. Aurelune and Seven Reeds court differentiation;
5. adversary and institutional voice differentiation; and
6. final cadence, naming, fresh-play leakage, validation, and closure.

No further corpus-wide repair workstream is scheduled. Future changes should arise from fresh play, a newly identified defect, or a deliberately scoped product requirement rather than from continuation of this editorial sequence.
