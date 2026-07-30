# The Mandate of Seven Reeds

Six weeks after the eastern dike drowned Reedwater’s governor and every lawful successor to the Seven Reeds, district deputies still keep granaries, patrols, ferries, shrines, and accounts moving inside commissions too narrow to govern the province. Great Clan relief commands overlap beneath a common Imperial holding order that expires in seven days. The Emperor names the adventurers Witnesses of the Broken Dike and orders them to turn rescue into government before gratitude, possession, and the next rains harden emergency service into title.

## Maintained source

`adventure.json` is the authoritative authored adventure. Stable internal names such as `clue` remain part of the compatibility contract; the maintained user-facing vocabulary is **Lead**.

`play-state.example.json` and any files under `archives/` are subordinate demonstration records. They illustrate one route through the adventure and do not constrain future authoring decisions.

`generated/` contains reproducible output derived from the authoritative source and the demonstration journal.

## Maintained companion material

- `COURT-LEDGER.md`
- `DRAFTING-AND-IMPERIAL-JUDGMENT.md`
- `FULL-PLAYTHROUGH.md`
- `GRAIN-AND-SWORD-SETTLEMENT.md`
- `MOON-VIEWING-AND-PUBLIC-OBLIGATION.md`
- `PARTY-DESIGN.md`
- `ROADS-WATERS-AND-BURDENS.md`
- `SETTING-AND-CANON-NOTES.md`
- `SHRINES-JUDGMENT-AND-ACCOUNTS.md`

Historical construction sessions, editorial audits, stress-test reports, and reference-extraction logs have been consolidated into the corpus completion records and removed from the maintained adventure directory.

## Regenerating the packet

From the repository root:

```bash
python -m adventure_graph validate examples/the-mandate-of-seven-reeds/adventure.json
python -m adventure_graph render examples/the-mandate-of-seven-reeds/adventure.json examples/the-mandate-of-seven-reeds/generated
```

See the [corpus quality record](../../docs/adventure-second-look-roadmap.md) and [reference-library completion record](../../docs/adventure-reference-defragmentation-roadmap.md) for the maintained corpus-wide status.
