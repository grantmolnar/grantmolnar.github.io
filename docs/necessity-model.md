# Necessary and Optional Structure

Encounters and revelations each carry an independent `required` flag. The persisted field name remains
`required`, while the GM interface uses the clearer terms **necessary** and **optional**. Missing
`required` fields load as `true`, and canonical saves materialize the field explicitly.

The two flags answer different questions:

- a necessary **revelation** is a conclusion the adventure expects the players to establish;
- a necessary **encounter** is a playable location or encounter the adventure expects to remain
  discoverable and structurally integrated.

They are intentionally independent. A necessary revelation may unlock an optional scene, and an
optional revelation may unlock a necessary encounter when several alternative conclusions can lead to
that destination.

## Incoming-clue validation

Necessary revelations use the configured minimum number of supporting clues and distinct source
encounters. Optional revelations are exempt from those configured minima, but an optional revelation with
no supporting clue raises `optional-revelation-unclued` as a warning.

Necessary non-start encounters use the configured minimum number of incoming locator clues and distinct
source encounters, aggregated across every revelation that unlocks the encounter. Optional encounters are exempt
from those configured minima, but an optional encounter with no incoming locator clue raises
`optional-encounter-unclued` as a warning.

Start encounters remain exempt from incoming locator requirements regardless of necessity. This preserves
the earlier rule that the initial situation need not be discovered through play.

## Reachability and connectivity

Every necessary encounter must be reachable by directed clue flow from a start encounter. An optional encounter
that has authored incoming clues but is unreachable produces a warning rather than an error.

Edge connectivity is measured between necessary encounters. Optional encounters remain in the graph and may
provide alternate paths between necessary regions, but a fragile optional spur does not lower the
adventure's structural connectivity. If fewer than two encounters are necessary, connectivity is not
reported.

Outgoing clue and destination requirements are unchanged: every non-end encounter, necessary or optional,
uses the configured outgoing minima. Optional means the adventure need not route players into the
encounter with full redundancy; it does not mean the encounter may be empty once entered.

## Existing adventures

The bundled adventures were rewritten to materialize necessity explicitly. Existing authorial
intent was preserved rather than inferred from one canonical route: Bramblewick marks Moss
Apothecary and Bramble Mill optional; Aurelune marks the Twilight Laurel, Ashen Bough, Masque, and
Petition Chamber optional, with necessity still independent at the revelation level. Other bundled
encounters remain necessary until their own governing material identifies them as dispensable. Authors
can change these roles through the browser or CLI without weakening the standards applied to the
necessary structure.
