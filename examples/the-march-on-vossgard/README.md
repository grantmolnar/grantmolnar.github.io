# The March on Vossgard

The Ashen Gate opens at dawn. By dusk, the Dawn Compact has an army in the Shadowfell and one road home. Count Othmar Voss holds the Gloam March with living levies, grave infantry, vampire cavalry, and blood enough to carry war across the mortal border. Marshal Aveline Rusk issues the Ash Warrant: authority to cross between columns, redirect scarce formations, receive surrenders, and bind the Compact when written orders arrive too late. The commission has three orders—break Voss's field army, take Vossgard, and deny him an organized remnant.

## Maintained source

`adventure.json` is the authoritative authored adventure. Stable internal names such as `clue` remain part of the compatibility contract; the maintained user-facing vocabulary is **Lead**.

`play-state.example.json` and any files under `archives/` are subordinate demonstration records. They illustrate one route through the adventure and do not constrain future authoring decisions.

`generated/` contains reproducible output derived from the authoritative source and the demonstration journal.

## Maintained companion material

- `DESIGN-NOTES.md`
- `FULL-PLAYTHROUGH.md`
- `PARTY-DESIGN.md`

Historical construction sessions, editorial audits, stress-test reports, and reference-extraction logs have been consolidated into the corpus completion records and removed from the maintained adventure directory.

## Regenerating the packet

From the repository root:

```bash
python -m adventure_graph validate examples/the-march-on-vossgard/adventure.json
python -m adventure_graph render examples/the-march-on-vossgard/adventure.json examples/the-march-on-vossgard/generated
```

See the [corpus quality record](../../docs/adventure-second-look-roadmap.md) and [reference-library completion record](../../docs/adventure-reference-defragmentation-roadmap.md) for the maintained corpus-wide status.
