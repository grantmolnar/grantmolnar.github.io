# Play interface panel convergence cold-read

## Status

The Play interface panel refactor is locally complete. The accepted implementation keeps one authored
encounter ontology, uses Play only as a projection and recording layer, and presents the focused encounter
through six peer sections without restoring the former viewport-bound split pane.

No additional product or domain defect was found during the convergence cold-read. Native desktop,
platform screen-reader, and real operating-system launcher checks remain external release evidence.

## Scope and boundaries

The read did not change the adventure schema, journal schema, application commands, authored entity types,
journal events, projection rules, or persistence format. It used the production server-rendered HTML and
production CSS and JavaScript through an inline browser harness because local and file navigation were
administratively blocked in that execution environment.

Chromium was exercised at 390×844, 900×1000, and 1600×1200. The source-level read also used the in-process
WSGI adapter and real bundled adventure and journal files.

## Reference-light cold-read

*When the Swine Kneel* exercised **The Six-Line Bell** with:

- no persistent references and an explicit, compact reference-light empty state;
- a long GM-reference section requiring internal scrolling;
- three encounter-local clues and their supported conclusions;
- committed notes and earlier persistent notes; and
- the complete route and utility rails, including the dice tray above Current visit actions.

The empty Linked references section remained informative without inventing records or forcing a reference
workflow. Long encounter material and clue content stayed bounded inside their sections while the page
remained scrollable. No horizontal overflow, overlap, or hidden canonical content was found.

## Reference-rich cold-read

*The Concord of Aurelune* exercised **The Crown Conclave** with:

- Theron Eiral and the Sunseed linked in authored order with distinct encounter-local context;
- a long GM-reference section;
- nine encounter-local clues and their paths and conclusions;
- committed and earlier persistent notes; and
- the complete Add to adventure menu for clue, revelation-plus-clue, linked-reference, and encounter
  authoring.

The dossiers remained subordinate to the encounter rather than narrowing or replacing encounter material.
The center used the available width, while prose measure remained readable inside prose content. The clue
section remained scannable despite its density, and the notes section remained a peer box rather than a
fixed lower pane.

## Ontology and state-boundary finding

The cold-read confirmed that **Add to adventure** communicates the correct boundary. An encounter made while
Play is open is an ordinary authored encounter with the same schema, identity, validation, and editing
lifecycle as one created before play. The same is true for clues, revelations, and references. Creation
context does not define a second ontology.

The Play journal records visits, outcomes, judgments, notes, and deliberately retained rolls. It does not
record a second Play-owned encounter type. Section disclosure state, internal scroll positions, page
position, search, pins, recent focus, drafts, and drawer state remain ephemeral browser concerns.

## Interaction and presentation findings

The cold-read confirmed:

- the six sections appear in the intended order and begin expanded;
- each header is a single-click disclosure control, with no double-click requirement;
- internal scrolling is used only when content exceeds the bounded section height;
- the surrounding page remains scrollable;
- the desktop center uses the width left by the two stable rails;
- compact and tablet layouts have no horizontal document overflow;
- the fixed compact navigation does not change authored or journal state;
- Linked references works both as an explicit empty state and as a populated dossier list;
- the dice tray precedes Current visit actions; and
- Add to adventure explains that it creates ordinary authored entities rather than runtime subtypes.

No new behavior correction was accepted during convergence. Documentation was synchronized instead of
introducing another layout model or speculative provenance system.

## Evidence boundary

The current deterministic, browser, property, mutation, package, and desktop evidence is maintained in
[`test-strategy.md`](test-strategy.md). This cold-read records the specific reference-light and reference-rich
GM usability finding rather than duplicating changing suite counts or artifact hashes.

Native bundles, operating-system directory chooser behavior, launcher lifecycle, display scaling, native
keyboard behavior, signing, notarization, and platform screen-reader checks remain governed by the
[beta-readiness roadmap](beta-readiness-roadmap.md) and
[desktop interaction protocol](beta-platform-manual-protocol.md).
