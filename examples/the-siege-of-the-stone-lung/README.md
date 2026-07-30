# The Siege of the Stone Lung

On the nineteenth day of the siege, Kest Mourne's right gate tower splits from parapet to foundation and the civic lantern above the Pale Gardens burns blue. The Host of the Lower Road has closed every caravan route and driven sappers beneath the walls. First Warden Ilyra Dain answers with a temporary six-lantern commission: cross the city's defensive sectors, spend its last reserves where they can still matter, and carry field truth back into command before the Stone Lung reaches its next crisis.

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
python -m adventure_graph validate examples/the-siege-of-the-stone-lung/adventure.json
python -m adventure_graph render examples/the-siege-of-the-stone-lung/adventure.json examples/the-siege-of-the-stone-lung/generated
```

See the [corpus quality record](../../docs/adventure-second-look-roadmap.md) and [reference-library completion record](../../docs/adventure-reference-defragmentation-roadmap.md) for the maintained corpus-wide status.
