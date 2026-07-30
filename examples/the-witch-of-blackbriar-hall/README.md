# The Witch of Blackbriar Hall

Blackbriar Vale remembers Judith Crowl by what arrived when no one else would send it: grain during the famine, beds during the pox, burial money when a household could not pay. Fifteen years later, each kindness has a receipt. Judith selects the vale's witches, removes their children, stores inconvenient dead, and keeps every household close enough to answer her knock. She bought that power through three chosen betrayals: nineteen refugees barred inside a burning granary for the Guest in Ash, thirty-one plague dead erased in quicklime for the Worm in White, and stolen children's names lowered into Moonless Mere for the Child Behind Glass. Canon Ysra's examiners were already approaching when Mara Sedge linked seven false prosecutions and Nell Sedge mapped the mirror dormitory. Judith took Nell, moved Mara's burning before the customary answer-night, and turned the annual Renewal of Mercy into the Hollow Feast. At first light she places the torch in eleven-year-old Tomas Sedge's hands. By midnight, the Mercy Book, household carriers, and four controlled living voices can join every door still answering Judith's claim. The commissioned company must keep the Sedge family alive, find the people and records Judith has moved, expose the roads behind her apparent omniscience, complete the material obligations she inverted, and break a feast built to continue after its hostess dies.

## Maintained source

`adventure.json` is the authoritative authored adventure. Stable internal names such as `clue` remain part of the compatibility contract; the maintained user-facing vocabulary is **Lead**.

`play-state.example.json` and any files under `archives/` are subordinate demonstration records. They illustrate one route through the adventure and do not constrain future authoring decisions.

`generated/` contains reproducible output derived from the authoritative source and the demonstration journal.

## Maintained companion material

- `AFTERMATH-AND-SURVIVING-CLAIMS.md`
- `BLACKBRIAR-VALE-LEDGER.md`
- `DESIGN-NOTES.md`
- `FULL-PLAYTHROUGH.md`
- `GM-OPERATING-SHEET.md`
- `HALL-WOOD-AND-FEAST-OPERATIONS.md`
- `PACT-SITE-OPERATIONS.md`
- `PARTY-DESIGN.md`
- `PUBLIC-RESISTANCE-AND-RETALIATION.md`
- `SAINT-MERCY-HOUSE-OPERATIONS.md`

Historical construction sessions, editorial audits, stress-test reports, and reference-extraction logs have been consolidated into the corpus completion records and removed from the maintained adventure directory.

## Regenerating the packet

From the repository root:

```bash
python -m adventure_graph validate examples/the-witch-of-blackbriar-hall/adventure.json
python -m adventure_graph render examples/the-witch-of-blackbriar-hall/adventure.json examples/the-witch-of-blackbriar-hall/generated
```

See the [corpus quality record](../../docs/adventure-second-look-roadmap.md) and [reference-library completion record](../../docs/adventure-reference-defragmentation-roadmap.md) for the maintained corpus-wide status.
