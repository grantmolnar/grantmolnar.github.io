# The Last Bell of Bramblewick

At Bramblewick's Founders' Supper, Merrit Alder—the keeper who remembers every birth, debt, burial, and borrowed chimney—announces that three village households never existed. He promises to name the hand behind them before breakfast. Minutes after the last bell, he is found dead beneath a clock stopped at nine. The bridge is unsafe, the reeve's own accounts are under suspicion, and Merrit's invited outsiders must keep one wet room from hardening into six convenient stories before first bell.

## Maintained source

`adventure.json` is the authoritative authored adventure. Stable internal names such as `clue` remain part of the compatibility contract; the maintained user-facing vocabulary is **Lead**.

`play-state.example.json` and any files under `archives/` are subordinate demonstration records. They illustrate one route through the adventure and do not constrain future authoring decisions.

`generated/` contains reproducible output derived from the authoritative source and the demonstration journal.

## Maintained companion material

- `FULL-PLAYTHROUGH.md`
- `GM-QUICKSTART.md`
- `PARTY-DESIGN.md`

Historical construction sessions, editorial audits, stress-test reports, and reference-extraction logs have been consolidated into the corpus completion records and removed from the maintained adventure directory.

## Regenerating the packet

From the repository root:

```bash
python -m adventure_graph validate examples/the-last-bell-of-bramblewick/adventure.json
python -m adventure_graph render examples/the-last-bell-of-bramblewick/adventure.json examples/the-last-bell-of-bramblewick/generated
```

See the [corpus quality record](../../docs/adventure-second-look-roadmap.md) and [reference-library completion record](../../docs/adventure-reference-defragmentation-roadmap.md) for the maintained corpus-wide status.
