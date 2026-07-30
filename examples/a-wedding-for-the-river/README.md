# A Wedding for the River

Three evenings before Tomas Vale marries Neris Reed-in-Rain, Mera Quill opens the two sealed readings of their compact. The ceremonial lines match. The marriages in the margins do not. Tomas and Neris settled rooms, work, water, and care in ordinary speech, then let their elders choose public words large enough to honor both houses. Both households chose a formula shaped by the flood that killed Perrin Vale. The Vales hear a river bride entering the mill and keeping its dead. The river kin hear a miller entering the current and becoming answerable to warnings that once stopped at his gate. Their gifts carry the same double edge: a white veil honors the dead and buries a river bride; a closed iron ring records a brother's labor and promises captivity; a handstone offers steadiness and a fixed course. Meanwhile, twelve protected trout leak across the market because a cousin embroidered a joke until somebody believed him. The adventurers serve as free witnesses. They may question, compare, pause, and propose. They may not choose the marriage. Their task is to discover what each word, gift, duty, and public act will do, return every choice to Tomas and Neris, and sign no more than they can honestly witness. No villain opposes the wedding. Love, haste, old grief, and good intentions are enough.

## Maintained source

`adventure.json` is the authoritative authored adventure. Stable internal names such as `clue` remain part of the compatibility contract; the maintained user-facing vocabulary is **Lead**.

`play-state.example.json` and any files under `archives/` are subordinate demonstration records. They illustrate one route through the adventure and do not constrain future authoring decisions.

`generated/` contains reproducible output derived from the authoritative source and the demonstration journal.

## Maintained companion material

- `AFTERMATH-AND-SEASONAL-STATES.md`
- `CEREMONY-LEDGER.md`
- `DESIGN-NOTES.md`
- `FULL-PLAYTHROUGH.md`
- `GM-OPERATING-SHEET.md`
- `HOSPITALITY-LEDGER.md`
- `PARTY-DESIGN.md`
- `REHEARSAL-AND-WITNESS-RECORD.md`
- `TERMS-OF-BELONGING.md`
- `WEDDING-LEDGER.md`
- `WITNESS-QUICKSTART.md`

Historical construction sessions, editorial audits, stress-test reports, and reference-extraction logs have been consolidated into the corpus completion records and removed from the maintained adventure directory.

## Regenerating the packet

From the repository root:

```bash
python -m adventure_graph validate examples/a-wedding-for-the-river/adventure.json
python -m adventure_graph render examples/a-wedding-for-the-river/adventure.json examples/a-wedding-for-the-river/generated
```

See the [corpus quality record](../../docs/adventure-second-look-roadmap.md) and [reference-library completion record](../../docs/adventure-reference-defragmentation-roadmap.md) for the maintained corpus-wide status.
