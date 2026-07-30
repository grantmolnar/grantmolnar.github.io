# The Cauldron of Nine Silences

After Red Fen killed or scattered a third of the vale's field command, emergency work beneath Dunwarren's western gate opened the sealed chamber where King Branoc died. His oath-ring is the first true anchor recovered since his death—and the first chance to ask what he told Edric Taran before the gate closed. During the renewal feast, a crew must remove the Cauldron of Nine Silences or conduct Branoc's Full Asking before Lord Mael turns the households' memorial rolls into a Great Muster. Wax requires witnesses, kitchen bells open old roads, severed counsel guards the underkeep, and every escape ends in a dispute over who may keep what no one should own alone.

## Maintained source

`adventure.json` is the authoritative authored adventure. Stable internal names such as `clue` remain part of the compatibility contract; the maintained user-facing vocabulary is **Lead**.

`play-state.example.json` and any files under `archives/` are subordinate demonstration records. They illustrate one route through the adventure and do not constrain future authoring decisions.

`generated/` contains reproducible output derived from the authoritative source and the demonstration journal.

## Maintained companion material

- `DESIGN-NOTES.md`
- `EXTRACTION-AND-AFTERMATH.md`
- `FULL-PLAYTHROUGH.md`
- `GM-OPERATING-SHEET.md`
- `HEIST-LEDGER.md`
- `PARTY-DESIGN.md`
- `UNDERKEEP-OPERATIONS.md`
- `VAULT-OPERATIONS.md`

Historical construction sessions, editorial audits, stress-test reports, and reference-extraction logs have been consolidated into the corpus completion records and removed from the maintained adventure directory.

## Regenerating the packet

From the repository root:

```bash
python -m adventure_graph validate examples/the-cauldron-of-nine-silences/adventure.json
python -m adventure_graph render examples/the-cauldron-of-nine-silences/adventure.json examples/the-cauldron-of-nine-silences/generated
```

See the [corpus quality record](../../docs/adventure-second-look-roadmap.md) and [reference-library completion record](../../docs/adventure-reference-defragmentation-roadmap.md) for the maintained corpus-wide status.
