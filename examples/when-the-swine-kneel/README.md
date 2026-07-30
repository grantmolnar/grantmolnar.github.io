# When the Swine Kneel

Three days into Veyr's uninterrupted drought pumping, pigs across Rillcross refuse particular channels, root bronze survey pins from the soil, and kneel toward the city at the sixth evening bell. The same pulse reaches thousands of animals inside Southgate as condemnation, quarantine, and evidence-seizure orders move toward execution. The Hall of Condemnations grants an independent company a resonance cycle to preserve the witnesses, trace the buried warning, and return with a choice the city can lawfully carry out.

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
python -m adventure_graph validate examples/when-the-swine-kneel/adventure.json
python -m adventure_graph render examples/when-the-swine-kneel/adventure.json examples/when-the-swine-kneel/generated
```

See the [corpus quality record](../../docs/adventure-second-look-roadmap.md) and [reference-library completion record](../../docs/adventure-reference-defragmentation-roadmap.md) for the maintained corpus-wide status.
