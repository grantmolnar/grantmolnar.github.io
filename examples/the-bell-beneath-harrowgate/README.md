# The Bell Beneath Harrowgate

Three nights running, the Deep Bell has sounded beneath Harrowgate with no rope and no ringer. Dust rises before each toll. Wells climb their walls. People above wake holding memories lost by people below. The Ember Company descended under a secret, conditional recovery contract; Factor Orren Saye then trusted an abridged royal sequence and cut the chain carrying the Crown's live load. The buried house is now passing strain among water, ward-light, memory, command, and counterweight systems. The adventurers must rescue the scattered expedition, learn whom each system has been spending, and choose an ending: repair the old burden, replace it, divide it, collapse it, free the Crown, or bargain with the listener beneath the fault. Every answer needs a bearer and a route.

## Maintained source

`adventure.json` is the authoritative authored adventure. Stable internal names such as `clue` remain part of the compatibility contract; the maintained user-facing vocabulary is **Lead**.

`play-state.example.json` and any files under `archives/` are subordinate demonstration records. They illustrate one route through the adventure and do not constrain future authoring decisions.

`generated/` contains reproducible output derived from the authoritative source and the demonstration journal.

## Maintained companion material

- `BEASTS-GRAVE-AND-WELLS.md`
- `DESIGN-NOTES.md`
- `DUNGEON-STATE.md`
- `EXTRACTION-AND-CAMP.md`
- `FULL-PLAYTHROUGH.md`
- `GM-OPERATING-SHEET.md`
- `IRON-CHOIR-AND-FINAL-CHAMBERS.md`
- `LOW-CHOIR-AND-CHAPEL.md`
- `PARTY-DESIGN.md`
- `PRESSURE-AND-ENCOUNTERS.md`
- `WARDENS-AND-GARDEN.md`
- `WATER-AND-LIGHT.md`

Historical construction sessions, editorial audits, stress-test reports, and reference-extraction logs have been consolidated into the corpus completion records and removed from the maintained adventure directory.

## Regenerating the packet

From the repository root:

```bash
python -m adventure_graph validate examples/the-bell-beneath-harrowgate/adventure.json
python -m adventure_graph render examples/the-bell-beneath-harrowgate/adventure.json examples/the-bell-beneath-harrowgate/generated
```

See the [corpus quality record](../../docs/adventure-second-look-roadmap.md) and [reference-library completion record](../../docs/adventure-reference-defragmentation-roadmap.md) for the maintained corpus-wide status.
