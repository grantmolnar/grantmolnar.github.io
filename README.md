# Adventure Graph

Adventure Graph is a small, dependency-free Python application for authoring, validating, rendering, and
running lead-driven encounter-based adventures. It keeps two structural views synchronized automatically:

- the **lead list**, organized by source encounter; and
- the **revelation list**, organized by supported conclusion or destination.

The authored JSON document is the source of truth. Generated Markdown is disposable and can be rebuilt at
any time. Actual play is recorded in a separate append-only journal.

Adventure Graph uses **encounter** for each playable location, person, event, or higher-level situation.
Every user-facing interface presents authored clue records as **leads**, including player-safe recaps. The
persisted JSON fields, URLs, Python types, event names, CLI commands, and stable generated filenames retain
`clue` for backward compatibility. Existing adventures and playthroughs require no migration.

## Quick start

Adventure Graph 0.10.0 supports CPython 3.11 through 3.13. From the unpacked source archive:

```bash
python -m venv .venv
# Activate .venv for your shell, then:
python -m pip install -e .
adventure-graph init adventure-workspace/my-adventure
adventure-graph validate adventure-workspace/my-adventure/adventure.json
adventure-graph ui adventure-workspace
```

The installed `adventure-graph` command and `python -m adventure_graph` are equivalent. The runtime package
has no third-party dependencies. The desktop entry point is `adventure-graph-desktop`.

The `init` command creates a fresh UUIDv4 adventure identity, an empty journal, a `generated/` directory, and
an `archives/` directory. An almost-blank adventure is valid; a distinguished start encounter is optional.

For installation details, workspace layout, upgrades, and beta feedback, see the
[beta guide](docs/beta-guide.md). For command syntax and end-to-end CLI workflows, see the
[command-line reference](docs/cli-reference.md).

## Open a workspace

```bash
adventure-graph ui adventure-workspace
```

Passing a project directory containing `adventure.json` opens that project as a one-adventure workspace:

```bash
adventure-graph ui adventure-workspace/my-adventure
```

Passing the canonical `adventure.json` file opens the same project explicitly. Workspace discovery is
non-recursive, so opening the repository root does not implicitly expose the internal development corpus.
Maintainers can inspect that corpus deliberately with:

```bash
adventure-graph ui examples
```

The tester-facing wheel and native application package one sample adventure, *The Glass Saint*. The other
adventures under `examples/` are an internal development and regression corpus, not beta content.

## Author and Play

The browser and desktop application provide four primary surfaces:

1. **Adventures** selects, creates, imports, and exports projects and portable playthroughs.
2. **Author** maintains encounters, references, leads, revelations, relationships, and validation policy.
3. **Play** records sessions, visits, lead outcomes, revelation judgments, notes, consequences, transitions,
   and significant rolls without rewriting authored material.
4. **History, Trackers, Reports, and Archives** project the append-only journal, generate table documents,
   and preserve or restore self-contained playthroughs.

The ordinary table loop is:

1. Open **Play** and begin a session.
2. Focus an encounter and choose **Start visit** when play reaches it.
3. Use the encounter sections for opening description, GM orientation, encounter material, linked references,
   leads and supported paths, and encounter notes.
4. Record lead outcomes, revelations, consequences, rolls, or a transition.
5. End the session, review **History**, and archive the journal when appropriate.

Opening or pinning authored material is browser-local retrieval, not a journal event. Authoring from Play uses
the same encounter, reference, lead, and revelation lifecycle as Author mode; it does not create a second
ontology.

See the [local web interface guide](docs/ui-usage.md) and
[Play mode semantics](docs/play-mode-semantics.md) for the complete interaction and state contracts.

## The four data surfaces

Adventure Graph deliberately separates reusable authorship from one table's history:

1. **Authored adventure — `adventure.json`.** Discovery tags, encounters, references, persisted `clues`,
   revelations, validation policy, and prose.
2. **Active journal — `play-state.json`.** Sessions, visits, lead outcomes, revelation judgments, unlocks,
   notes, consequences, recorded rolls, and append-only corrections.
3. **Generated packet — `generated/`.** Disposable Markdown views of the adventure and, when requested, the
   active journal.
4. **Journal archives — `archives/*.journal.json`.** Immutable play journals stored with the exact adventure
   snapshot against which they were recorded.

Authoring changes the first surface. Table processing changes the second. Rendering derives the third.
Archiving preserves or restores the fourth without rewriting the authored adventure.

## Compatibility and beta status

This 0.10.0 source snapshot is governed by the [private beta terms](BETA-TERMS.md). It permits evaluation and
feedback but does not grant an open-source or redistribution license.

The supported beta contracts are:

- the installed CLI;
- user-visible loopback browser and desktop workflows;
- the documented workspace layout; and
- current persisted schemas: adventure schema 3, play-state schema 6, and workspace-settings schema 1.

Adventure Graph does not promise a stable library-level Python import API. Raw HTTP paths, hidden form
fields, DOM structure, CSS selectors, and JavaScript storage keys are implementation details rather than an
automation API. Current-version readers default omitted known fields but reject unknown fields rather than
silently discarding data written by a newer release.

The [test strategy](docs/test-strategy.md) defines durable quality policy. Revision-specific evidence belongs
in qualification records and maintenance handoffs outside the repository artifact. The historical
[private-beta release qualification](docs/private-beta-release-qualification.md) applies only to the source
snapshot named there; descendant snapshots require fresh evidence.

## Capabilities

Adventure Graph can:

- create almost-blank adventures or structured starter projects;
- browse and edit encounters, references, leads, revelations, and validation settings;
- maintain contextual encounter/reference links with generated backlinks;
- validate incoming redundancy, outgoing choices, directed reachability, and exact necessary-encounter edge
  connectivity;
- diagnose limiting cuts and suggest structural repair locations without inventing fiction;
- record explicit sessions, party-labelled visits, lead outcomes, revelation judgments, unlocks, notes,
  consequences, significant rolls, and latest-operation corrections;
- maintain chronological notes on persistent people, places, organizations, objects, and other references;
- generate overview, encounter, reference, lead, revelation, validation, and play-summary documents;
- export and import canonical adventures and portable playthroughs; and
- archive, compare, restore, and deliberately delete journals.

## Documentation

The [documentation index](docs/README.md) separates tester guidance, durable contracts, maintainer procedures,
active product plans, and historical evidence. Common starting points are:

- [Beta guide](docs/beta-guide.md)
- [Local web interface](docs/ui-usage.md)
- [Command-line reference](docs/cli-reference.md)
- [File format](docs/file-format.md)
- [Runtime state](docs/runtime-state.md)
- [Architecture](docs/architecture.md)
- [Maintainer guide](docs/maintainer-guide.md)

The future [campaign graph initiative](docs/campaign-graph-roadmap.md) is documented but intentionally not
implemented in the current beta. The accepted adventure reference-library design is recorded in
[its roadmap](docs/adventure-reference-library-roadmap.md); remaining exploratory campaign questions live in
the [graph-scale design notebook](docs/graph-scale-design-notebook.md).

## Development

Create and activate a virtual environment, then run:

```bash
make install
make test-fast
make test
make lint
make format-check
make validate
make validate-all
```

`make validate` is the required connected deterministic gate and includes property testing and branch-aware
coverage. Native packaging, source snapshots, browser setup, and platform-evidence procedures are collected in
the [maintainer guide](docs/maintainer-guide.md).

The package uses clean-architecture layering:

```text
interfaces / infrastructure
          ↓
      application
          ↓
        domain
```

`adventure_graph.bootstrap` is the minimal process entry point. Package-root CLI modules and
`web_composition.py` wire outer adapters to application use cases; the domain does not depend on JSON,
Markdown, the CLI, the browser, or filesystem state.
