# The Glass Saint

A museum reliquary bursts on the eve of Saint Olyra’s procession. Before sunset, independent witnesses must recover its stolen petition-bed, expose the lie beneath the city’s obedient saint, and decide whether grief may borrow a body and command through every bell.

## Maintained source

`adventure.json` is the authoritative authored adventure. Stable internal names such as `clue` remain part of the compatibility contract; the maintained user-facing vocabulary is **Lead**.

`play-state.example.json` and any files under `archives/` are subordinate demonstration records. They illustrate one route through the adventure and do not constrain future authoring decisions.

`generated/` contains reproducible output derived from the authoritative source and the demonstration journal.

## Maintained companion material

- `DESIGN-NOTES.md`
- `FULL-PLAYTHROUGH.md`
- `GM-ROUTE-AND-CONTINUITY-SHEET.md`
- `PARTY-DESIGN.md`
- `PUBLIC-PRESSURE-AND-WITNESS-LEDGER.md`
- `RITUAL-AND-BELL-OPERATING-SHEET.md`
- `VALE-MANOR-AND-AFTERMATH-OPERATING-SHEET.md`

Historical construction sessions, editorial audits, stress-test reports, and reference-extraction logs have been consolidated into the corpus completion records and removed from the maintained adventure directory.

## Regenerating the packet

From the repository root:

```bash
python -m adventure_graph validate examples/the-glass-saint/adventure.json
python -m adventure_graph render examples/the-glass-saint/adventure.json examples/the-glass-saint/generated
```

See the [corpus quality record](../../docs/adventure-second-look-roadmap.md) and [reference-library completion record](../../docs/adventure-reference-defragmentation-roadmap.md) for the maintained corpus-wide status.
