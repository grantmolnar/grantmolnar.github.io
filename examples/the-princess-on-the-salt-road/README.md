# The Princess on the Salt Road

Before midnight, Kallias’s soldiers wrench the Assembly’s bronze speaking rail from its sockets and hang white command lamps over Aulon. Princess Ianthe—half-elven heir to the old royal house—refuses to name him protector and leaves with the city seal beneath her cloak. Her bodyguards have until the second sunset to carry her thirty-six miles to neutral Myrine, where seven white stones, three magistrates, and the waiting Sea-Lark can place her beyond Kallias’s lawful reach. The open Salt Road buys speed with witnesses. The dry aqueduct hides people but strands horses. Funeral peace binds every blade. Bridge remounts may carry rescue or pursuit, and every reed boat taken from the bank is one a household cannot use. Kallias needs Ianthe alive, the Ash Knives need the last heir dead, and her mother’s kin offer a road so safe that she may reach the coast as their ward rather than Aulon’s free petitioner.

## Maintained source

`adventure.json` is the authoritative authored adventure. Stable internal names such as `clue` remain part of the compatibility contract; the maintained user-facing vocabulary is **Lead**.

`play-state.example.json` and any files under `archives/` are subordinate demonstration records. They illustrate one route through the adventure and do not constrain future authoring decisions.

`generated/` contains reproducible output derived from the authoritative source and the demonstration journal.

## Maintained companion material

- `AFTERMATH-AND-SETTLEMENT.md`
- `BEACON-AND-HARBOR-OPERATIONS.md`
- `BRIDGE-AND-CHANNEL-OPERATIONS.md`
- `DESIGN-NOTES.md`
- `ESCORT-LEDGER.md`
- `FULL-PLAYTHROUGH.md`
- `GM-OPERATING-SHEET.md`
- `PARTY-DESIGN.md`
- `PURSUIT-AND-CUSTODY.md`

Historical construction sessions, editorial audits, stress-test reports, and reference-extraction logs have been consolidated into the corpus completion records and removed from the maintained adventure directory.

## Regenerating the packet

From the repository root:

```bash
python -m adventure_graph validate examples/the-princess-on-the-salt-road/adventure.json
python -m adventure_graph render examples/the-princess-on-the-salt-road/adventure.json examples/the-princess-on-the-salt-road/generated
```

See the [corpus quality record](../../docs/adventure-second-look-roadmap.md) and [reference-library completion record](../../docs/adventure-reference-defragmentation-roadmap.md) for the maintained corpus-wide status.
