# Beta installation and feedback guide

## Supported environment

Adventure Graph 0.10.0 supports CPython 3.11 through 3.13. The application binds only to loopback
and
has no third-party runtime dependencies.

## Private beta terms

The archive and wheel are provided under the repository-root [private beta terms](../BETA-TERMS.md).
They permit installation, reasonable backup copies, evaluation, and feedback by a direct recipient.
They do not permit redistribution, publication, resale, hosted-service use, or code reuse without
separate written permission. Adventures and play data created by a tester remain that tester's material.

## Install from the source archive

Unpack the archive, open a terminal in its root, and create an isolated environment.

**macOS or Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

**Windows PowerShell**

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Use this editable source installation for development and recovery. Poetry is not required. The local code-candidate wheel is rebuilt from the same source, contains no development payload, and has passed
the clean installed lifecycle. The whole-application local GM cold-read and the focused Play-panel
convergence cold-read are complete. The current local qualification matrix and every unavailable gate are
recorded in the [private-beta release qualification report](private-beta-release-qualification.md).
Native Linux, Windows, and macOS bundles plus real-platform launcher protocols remain external evidence
rather than local claims and are tracked in the beta-readiness roadmap.

## Launch the desktop bundle

A native beta bundle, when supplied for your operating system, does not require Python installation.
Extract it outside your adventure workspace and open the ordinary **Adventure Graph** application. On
first launch, choose an existing directory that will contain one or more adventure projects. An empty
directory is valid; the browser offers either an editable copy of *The Glass Saint*, the beta's included
sample, or a blank new adventure. The application does not write the sample until the user chooses that
action.

Keep the small launcher window open while using Adventure Graph in the browser. **Open in browser**
reopens the current local interface, **Choose workspace…** replaces the served workspace, and closing
the launcher stops its owned server. The launcher remembers only the workspace path in the user's
platform configuration directory. Adventure files, journals, archives, and generated reports remain in
the selected workspace and are never stored in the application bundle.

Maintainers should verify the supplied archive against its adjacent JSON manifest with `python scripts/verify_desktop_artifacts.py <download-directory>` before handing it to testers. Unsigned or unnotarized
local builds may trigger operating-system warnings and are not represented as final public releases.
See the [desktop distribution guide](desktop-distribution.md) and the
[manual desktop protocol](beta-platform-manual-protocol.md).


## Beta sample scope

The tester-facing beta includes one sample adventure: *The Glass Saint*. Adding it from the Adventures
catalog or New Adventure page creates a separate editable project with fresh UUIDv4 identity and an empty
playthrough. The CLI `init` command uses the same packaged template and the same fresh-identity rule.

The other adventures under the source repository's `examples/` directory are maintainer development
material. They are intentionally absent from the wheel and native application bundle, are not represented
as human-polished beta content, and are outside this beta's acceptance boundary.

## Create and launch a workspace

```bash
adventure-graph init adventure-workspace/my-adventure
adventure-graph ui adventure-workspace
# Or open one project directory directly:
adventure-graph ui adventure-workspace/my-adventure
```

Each initialization assigns fresh UUIDv4 adventure identity, creates a matching empty journal, and
prepares the project's `generated/` and `archives/` directories.

A workspace may contain `adventure.json` at its root and visible direct child directories containing
their own `adventure.json`. Discovery is not recursive. Use one project directory per adventure; do not
place browser projects in root-level `<name>.adventure.json` files. One loadable project with no
malformed project diagnostics opens automatically. Several projects without a saved selection open the catalog,
and a saved project that is removed, renamed, or malformed is never replaced silently. New browser-created directory names avoid
case-insensitive collisions and Windows device names and remain at most 80 ASCII characters.

The browser opens `http://127.0.0.1:8765/`. Open the exact loopback address printed by the command;
requests using another HTTP host authority are rejected. Reverse proxies, alternate host aliases, IPv6
loopback, LAN exposure, and hosted-service deployment are outside the private-beta security contract.
Malformed or oversized query strings and forms are rejected before project work, and every browser
mutation requires the page-owned CSRF token. Unexpected local file errors are reported in the server
terminal without placing filesystem paths in the browser response. Stop the server with `Ctrl+C`. If
that port is occupied, launch with `--port 9000`. Use `--no-browser` when you prefer to open the address
yourself.

## Recommended first test

After launch in an empty workspace, choose **Add The Glass Saint sample**, then exercise this compact
path before importing important material:

1. open **Play adventure** and begin an explicit session;
2. enter the distinguished starting encounter;
3. read the six focused-encounter boxes and collapse or reopen at least one by clicking its header;
4. record one encounter note and one lead outcome;
5. use **Add to adventure** to inspect a return-safe authoring form, then cancel back to the same encounter;
6. end the session and inspect **History** and **Journal**; and
7. stop the server, relaunch the same workspace, and confirm the session and browser-local section
   preference remain present.

Keep the generated project as a disposable smoke project. Use a separate backed-up copy for real table
material. Release auditors should also execute the
[private-beta desktop interaction protocol](beta-platform-manual-protocol.md) once on each supported
operating system; the automated wheel smoke does not substitute for JavaScript, keyboard, visual, or
display-scaling checks in a real browser.

Run only one Adventure Graph writer process against a workspace at a time. Stale browser requests are
revision-checked, but the private beta does not provide a cross-process lock between a browser, a CLI
command, an external editor, or synchronization software. Browser-owned project files and the
`.adventure-graph`, `generated`, and `archives` trees must use ordinary files and directories rather
than symlinks; an unsafe layout is rejected instead of followed. After an abnormal process termination,
reopen the workspace normally so hidden transaction markers can recover the canonical files before
you inspect or edit them. Do not edit, move, or delete those hidden files manually.

Canonical adventure, journal, archive, and settings JSON documents are limited to 8 MiB and 64 object
or array nesting levels. Writers enforce the byte ceiling before replacing any file, and a play journal may
contain at most 10,000 events. These ceilings are far above the bundled examples, but importing or trying
to save a larger or more deeply nested hand-edited file fails closed.
Preserve the original file and reduce it outside the active workspace rather than repeatedly opening it.
Journal archive filenames are also canonical: keep each file named `<archive-id>.journal.json`. Archive
identifiers use at most 80 ASCII filename-safe characters and are unique without regard to case. A renamed,
duplicated, or case-colliding archive file is rejected so restore and deletion can never select the wrong copy.

## 0.10.0 beta compatibility target

The intended private-beta compatibility surface is limited to:

- adventure schema 3, play-state schema 6, and workspace-settings schema 1;
- documented CLI command names and options;
- documented user-visible loopback browser workflows;
- root/direct-child workspace discovery and persisted selection/defaults behavior; and
- installation and launch from the 0.10.0 wheel, with the one-click bundle reusing the same runtime; and
- the desktop launcher contract for workspace choice, remembered path, one owned loopback server, and
  clean shutdown.

The internal Python import graph is not a stable public API. Raw HTTP paths, hidden form fields,
CSRF and revision tokens, DOM structure, CSS selectors, and browser-local storage keys are likewise
internal implementation details, not a supported remote-control or extension API. Entity links use
stable identifiers so title edits do not invalidate them within a release, but cross-release bookmark
preservation is best-effort. Use the CLI and published JSON schemas for automation. These surfaces are locally frozen for the code candidate; hosted and manual platform signoff remains
open in the beta-readiness roadmap. Current-version files may omit documented
optional fields, but an unknown field fails closed with its source and object boundary rather than being silently discarded.
Preserve the original file when that diagnostic appears. After beta distribution, a breaking change
to any supported surface requires an explicit versioned migration decision rather than a silent cleanup.

## Pre-beta migration boundary

Version 0.10.0 expects adventure schema 3, play-state schema 6, and workspace settings schema 1. The
pre-beta 0.6–0.8 formats are not supported migration contracts. Before testing with older material, keep
a backup and move the content manually into a project created by this version.

## Useful feedback

For a reproducible report, include:

- Adventure Graph version from the browser **Help** page or `adventure-graph --version`;
- operating system and `python --version`;
- the command or browser workflow used;
- exact steps, expected behavior, and observed behavior; and
- the smallest relevant `adventure.json` or `play-state.json`, after removing private table notes.

Do not send `.adventure-graph/settings.json` unless the problem concerns discovery, selection, or
workspace defaults. Keep an untouched copy of any project that triggers a write or migration concern.
