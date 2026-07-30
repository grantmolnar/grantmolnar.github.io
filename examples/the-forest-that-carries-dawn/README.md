# The Forest That Carries Dawn

At middle watch, the Cairnroad caravan wakes inside a forest walking east across the White Salt. Five wagons, thirteen travelers, and three draft teams hang in divided roots behind the surviving camp. At dawn the Bearer will reach the Glass Waste, harden the eastern forest, and lift the last ordinary road home. Merewash, the caravan's destination, has endured six failed rainy seasons; two damaged records suggest this migration can make a living rain-seed. No seed waits to be picked. Old ground, borrowed dawn, returning rain, a remembered river, bounded blackgrass heat, and the Bearer's one deep exhale must meet in the crown. The wagons have broken the beetle road that feeds it. Rescue, repair, departure, and the hope of rain now spend the same hands before the last salt disappears.

## Maintained source

`adventure.json` is the authoritative authored adventure. Stable internal names such as `clue` remain part of the compatibility contract; the maintained user-facing vocabulary is **Lead**.

`play-state.example.json` and any files under `archives/` are subordinate demonstration records. They illustrate one route through the adventure and do not constrain future authoring decisions.

`generated/` contains reproducible output derived from the authoritative source and the demonstration journal.

## Maintained companion material

- `AFTERMATH-AND-SEASONAL-STATES.md`
- `CARAVAN-AND-RESCUE-LEDGER.md`
- `CROWN-VERGE-OPERATING-SHEET.md`
- `DESIGN-NOTES.md`
- `ECOLOGY-OPERATING-SHEET.md`
- `FULL-PLAYTHROUGH.md`
- `GM-OPERATING-SHEET.md`
- `MEMORY-FIRE-AND-BREATH.md`
- `MIGRATION-LEDGER.md`
- `PARTY-DESIGN.md`

Historical construction sessions, editorial audits, stress-test reports, and reference-extraction logs have been consolidated into the corpus completion records and removed from the maintained adventure directory.

## Regenerating the packet

From the repository root:

```bash
python -m adventure_graph validate examples/the-forest-that-carries-dawn/adventure.json
python -m adventure_graph render examples/the-forest-that-carries-dawn/adventure.json examples/the-forest-that-carries-dawn/generated
```

See the [corpus quality record](../../docs/adventure-second-look-roadmap.md) and [reference-library completion record](../../docs/adventure-reference-defragmentation-roadmap.md) for the maintained corpus-wide status.
