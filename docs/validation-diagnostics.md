# Validation Diagnostics

Adventure Graph returns structured findings with stable codes, severity, an internal subject
reference when applicable, an explanation, and repair guidance. Warnings describe legibility or role
ambiguity; errors indicate broken structure.

## Adventure legibility and roles

The validator warns when:

- `premise` is empty;
- `explanation` is empty;
- no encounter is marked as the start;
- more than one encounter is marked as the start; or
- more than one encounter is marked as an end.

Multiple starts and ends remain legal for adventures that intentionally use them.

Start encounters are initial conditions: they need no clues pointing toward them, and directed
reachability begins from all marked starts. End encounters are conclusions: they are exempt from minimum
outgoing-clue and outgoing-destination requirements, though authors may still place clues there.

## Necessary and optional structure

Encounters and revelations default to necessary. Their flags are independent: a necessary conclusion may
unlock an optional scene, and an optional conclusion may be one of several routes into a necessary
scene.

Necessary revelations use the configured clue-count and source-diversity minima. Necessary non-start
encounters use the configured incoming locator-clue and source-encounter minima, aggregated across every
revelation that unlocks the encounter. Optional revelations and optional non-start encounters are exempt from
those configured incoming minima, but zero incoming clues produces a warning.

Every necessary encounter must be reachable from a start. An optional encounter with authored incoming clues
but no reachable route produces a warning. Outgoing requirements continue to apply to every non-end
encounter, whether necessary or optional.

## Exact connectivity diagnosis

For at least two necessary encounters, validation computes the exact minimum edge cut separating a pair
of necessary encounters on the simple undirected projection of the clue graph. Optional encounters may carry
alternate paths, but an optional spur does not lower the measured floor. Multiple clues between the
same encounter pair improve informational redundancy but do not increase structural connectivity.
Diagnostics provide the cut, the number of additional cross-cut pairs needed, and bounded
author-approved repair candidates.

## Reference-library diagnostics

Reference decoding fails before validation when a record has a malformed UUIDv4 identity, unsupported
kind, malformed title, aliases, prose, or tags, or when an encounter link has malformed values. Unknown
fields continue to fail closed at the persisted object boundary.

The validator reports errors for duplicate reference identifiers, dangling encounter links, and repeated
links from one encounter to the same reference. It warns when a reference has neither summary nor
detailed content, and when titles or aliases expose the same case-insensitive name for multiple records.
These warnings preserve reference-light and incrementally authored adventures while making ambiguous or
underdeveloped library records visible. Reference links do not contribute graph edges or alter clue,
revelation, reachability, or connectivity diagnostics.

## Other errors

The validator also reports:

- missing clue source, revelation, or unlocked-encounter references;
- duplicate internal identifiers;
- necessary non-start revelations with too few clues or source encounters;
- necessary non-start encounters with too few incoming clues or source encounters;
- optional revelations or encounters with no incoming clues, as warnings;
- non-end encounters with too few outgoing clues or destinations;
- necessary encounters unreachable from all starts, with optional unreachable encounters warned; and
- impossible edge-connectivity thresholds.

Repair suggestions never create prose or apply changes automatically.
