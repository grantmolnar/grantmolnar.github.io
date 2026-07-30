# Corpus Differentiation Workstream 1: Identity Collisions and Comparative Baselines

## Judgment

Workstream 1 is complete. The two accidental encounter-title collisions identified by the final corpus-wide audit have been resolved. A follow-up identity decision renamed Blackbriar's witch **Judith Crowl** and migrated every affected Blackbriar identifier because the adventure has no live play history requiring compatibility. Swine's terminal identifier remains stable; Blackbriar's current source, synthetic archive, aids, tests, and generated packet use the new identities throughout.

## Baseline preservation

Before editing, the repository recorded the following SHA-256 baselines. Aggregate fingerprints hash each relative path and file body in sorted order with null separators.

- Thirteen authoritative adventure sources: `a8f82a37549a10613d52e23ebead10c839b80f633e41de996fa2fa34d567b76c`.
- Thirteen active example journals: `38b932bb6ce2faccc13aef9ebf3407a26759c65531ba79f44b659256b9c2acb0`.
- Five archived demonstration journals: `95b1dc3437c3e8538f5d3cf57779700a028d94ee242627b2489a5a11e39abb2c`.
- All eighteen active and archived journals: `c301003eb31ca6d061d1f451af5ee545487e1c718c694ad440ce698ad3bc3f76`.

The two source files began at:

- `examples/when-the-swine-kneel/adventure.json`: `befe5868eae08c7436e78a49ed0129db011525a8f18e2aa62e1e99d01a1a2e55`.
- `examples/the-witch-of-blackbriar-hall/adventure.json`: `4b514faf2fd1e79eeba4992f45ed457441cc640b71cc2334917484c3b039399a`.

## Encounter identity decisions

### When the Swine Kneel

The terminal encounter title changes from **The Deep Bell** to **The Six-Line Bell**. The stable encounter ID remains `the-deep-bell`.

The change names the encounter by the adventure's distinctive six-line survey and hydraulic system rather than by the generic depth of its bell. The ancient object inside the chamber may still be called the Deep Bell in setting prose. Its physical nature, routes, clues, remedies, and operating procedures are unchanged.

### The Witch of Blackbriar Hall

The chapel title changes from **Chapel of the Open Door** to **Chapel of the Free Witness**. Its encounter ID is now `chapel-of-the-free-witness`, and the synthetic demonstration was migrated with it.

The new name foregrounds Blackbriar's native doctrine: shelter, burial, and returned names become valid through free and distributed witness rather than clerical possession. It separates the institution from Bramblewick's memorial chapel without changing the doorless threshold, honest bell, refuge roll, rites, routes, or clue graph.

### Judith Crowl

The witch formerly shared Hester Rowan's first name. Because Blackbriar has no live table history, the corpus now names her **Judith Crowl** and migrates every name-derived clue, revelation, event, and source-snapshot identifier. The change removes the avoidable recurrence without preserving compatibility that no actual play record needs. Hester Rowan remains unchanged in Bramblewick.

## Synchronization

The title and identity repairs were synchronized through:

- both authoritative adventure sources;
- current READMEs, operating sheets, route tests, demonstration-company notes, and full playthroughs where the encounter title is used;
- source-dependent archived adventure snapshots;
- regenerated Markdown packets and play summaries; and
- integration tests and the corpus comparison baseline.

Because the Blackbriar demonstration is synthetic and unplayed, its build records, completed audits, source snapshot, and event identifiers were migrated as one corpus. Bramblewick's Hester Rowan records remain untouched. Swine's active journal remains byte-identical; the Blackbriar archive changes only where its unplayed identities require migration.

## Permanent collision guard

`docs/intentional-shared-encounter-titles.json` is the explicit allowlist for deliberate shared institutions. It is currently empty. The integration suite now compares every exact encounter-title duplicate in the thirteen authoritative sources against that allowlist. Any future duplicate must therefore be either removed or documented with the adventures involved and a rationale.

## Post-repair fingerprints

- Thirteen authoritative adventure sources: `7e35dfa02667ea5867d7681fd6d71bb80b32bbdb6e7e8b53b8997813c6af46fe`.
- Thirteen active example journals: `38b932bb6ce2faccc13aef9ebf3407a26759c65531ba79f44b659256b9c2acb0`.
- Five archived demonstration journals: `84f8ae2979a17509dc74e5bcfb910a009745d50351d885d8754d84d329062210`.
- All eighteen active and archived journals: `af2ce0d3bb3ffa23790d2b21e2219f1ec5725bfdd27fdb2861b045efff6c0014`.

The two revised source files end at:

- `examples/when-the-swine-kneel/adventure.json`: `20d7fa5e1889032c32da36a0a82574ddc2d23879584a6acf9544f736b717391e`.
- `examples/the-witch-of-blackbriar-hall/adventure.json`: `b23f382508834c92189410883bb3a06fc5b37be6c92e42a5e2de9af72999c4cd`.

## Follow-up identity migration

After the initial title-only repair, the user directed a complete Blackbriar identity migration. The resulting pre-Workstream-2 fingerprints were:

- Thirteen authoritative adventure sources: `fd09753e1a2b0c8e19db98d6a9b805add8038e7dce1d02073de127bd6e177eaa`.
- `examples/the-witch-of-blackbriar-hall/adventure.json`: `b68ec56ac3f6f38a8e04122787b18d895c4d2aed58e12033fc6de4fe5a37aa45`.
- Five archived demonstration journals: `48b87bb0b1d57e6d1b29f8c078bd641e9e662525d1b731ae4ba6600a034c3d66`.
- All active and archived journals: `5e442b9f8fdd8ba9f653339fcda43d7d3d99931a565cf7ea68ef2cbc9f6ef6c3`.

The integration suite now scans every Blackbriar Markdown, JSON, and Python-facing fixture for the superseded name and chapel identity. A second repository-wide guard permits the superseded first name only as **Hester Rowan** or within Bramblewick's own project tree.

## Preserved invariants

- Thirteen adventures, 138 encounters, 305 revelations, and 1,385 clues.
- Every Swine identifier and every graph edge and validation threshold.
- Blackbriar graph topology and semantics, with all renamed entity references migrated consistently.
- All active-journal events; synthetic Blackbriar archive events were migrated because no live compatibility contract applies.
- Swine's three finale approaches and Blackbriar's chapel functions.
- Bramblewick's **Chapel of the Open Door** and Harrowgate's **The Deep Bell**.
- Fresh-play priority over the two named demonstrations.

## Verification

- 68 focused corpus, Swine, Blackbriar, Bramblewick, and Harrowgate integration checks passed.
- All 583 executable repository tests passed with the unchanged seven-test Hypothesis graph module excluded because Hypothesis is not installed.
- All thirteen authoritative adventures passed structural validation.
- All 38 JSON files parsed successfully, including the new allowlist.
- Fresh regeneration of both affected Markdown packets matched the checked-in packets byte for byte.
- Semantic source comparison found one changed Swine field and five changed Blackbriar fields, all confined to the localized encounter identities and references to them.
- Both active example journals remained byte-identical. Both archive metadata records and archived event streams remained unchanged.
- Python compilation passed for `src` and `tests`. Ruff, Pyright, Poetry, and Hypothesis were unavailable in the environment.

## Disposition

Workstream 1 is closed. Workstream 2 should compare and differentiate the terminal procedures of *The Siege of the Stone Lung* and *When the Swine Kneel*, using the new **The Six-Line Bell** identity as the stable Swine baseline.
