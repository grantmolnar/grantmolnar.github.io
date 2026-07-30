# The Concord of Aurelune

The Shadowfell army that raised the Pall has been driven from Orison, but its siege-work now feeds itself. At moonrise after the seventh court day, it will close the last Fey road into the city. A paving stone carried from Orison remembers noon beneath Aurelune's Sunseed, proving the relic can restore the sky if it crosses in time. King Caelir III refuses the proposed loan. Seven of the ten Great Banners, with all four seasons represented, can compel joint custody for one named undertaking. Orison's petitioners must win those seals and make their rival bargains govern one exact instrument before the road closes.

## Maintained source

`adventure.json` is the authoritative authored adventure. Stable internal names such as `clue` remain part of the compatibility contract; the maintained user-facing vocabulary is **Lead**.

`play-state.example.json` and any files under `archives/` are subordinate demonstration records. They illustrate one route through the adventure and do not constrain future authoring decisions.

`generated/` contains reproducible output derived from the authoritative source and the demonstration journal.

## Maintained companion material

- `COURT-LEDGER.md`
- `DESIGN-NOTES.md`
- `FULL-PLAYTHROUGH.md`
- `PARTY-DESIGN.md`
- `PETITION-CLAUSE-MATRIX.md`

Historical construction sessions, editorial audits, stress-test reports, and reference-extraction logs have been consolidated into the corpus completion records and removed from the maintained adventure directory.

## Regenerating the packet

From the repository root:

```bash
python -m adventure_graph validate examples/the-concord-of-aurelune/adventure.json
python -m adventure_graph render examples/the-concord-of-aurelune/adventure.json examples/the-concord-of-aurelune/generated
```

See the [corpus quality record](../../docs/adventure-second-look-roadmap.md) and [reference-library completion record](../../docs/adventure-reference-defragmentation-roadmap.md) for the maintained corpus-wide status.
