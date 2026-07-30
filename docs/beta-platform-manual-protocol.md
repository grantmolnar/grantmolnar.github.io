# Private-beta desktop interaction protocol

## Purpose

Use this protocol to verify the parts of Adventure Graph 0.10.0 that require a real native launcher,
desktop browser, keyboard, display stack, and operating-system process lifecycle. The automated clean-
wheel smoke proves the installed CLI and browser workflows; the frozen-executable smoke proves that the
native bundle can start and stop the exact loopback application. This protocol supplements that evidence
with directory-choice, lifecycle, visual, JavaScript, local-storage, keyboard, and platform interaction
checks.

Execute the complete protocol once on each supported operating system:

- current supported Ubuntu desktop;
- current supported Windows desktop; and
- current supported macOS desktop.

Use the native bundle produced by the desktop workflow for that operating system. Record the exact
operating-system, bundle architecture, default-browser, browser-version, display-resolution, display-
scaling, archive hash, and manifest before beginning. Use the matching wheel only for CLI recovery checks.
Do not infer one platform result from another.

## Preconditions

1. Download the native archive and adjacent manifest produced from the intended source revision.
2. Run `python scripts/verify_desktop_artifacts.py <download-directory>` against the archive and
   adjacent manifest. Confirm it reports the expected platform, architecture, source revision, and native
   runner image; inspect the manifest's exact build dependency map and requirements digest, then extract
   the archive outside any adventure workspace.
3. Confirm the corresponding hosted frozen-executable smoke succeeded.
4. Keep the matching release-candidate wheel available in a fresh virtual environment for CLI recovery
   checks; run `python -m pip check`, `adventure-graph --version`, and `scripts/beta_smoke.py` there.
5. Create two disposable workspace directories outside synchronized cloud storage.
6. Use one Adventure Graph writer process at a time.

Record the following evidence:

```text
Operating system and version:
Bundle architecture:
Browser and version:
Display resolution and scaling:
Desktop archive filename:
Desktop archive SHA-256:
Manifest filename:
Build requirements SHA-256:
Native runner image and version:
Hosted frozen smoke result:
Wheel filename and SHA-256:
Clean-wheel smoke result:
Tester:
Date:
```

## 0. Native launcher lifecycle

1. Start the extracted application by double-clicking its ordinary platform entry point.
2. With no remembered workspace, confirm the native directory chooser opens without a terminal.
3. Choose the first disposable workspace and confirm the default browser opens Adventure Graph.
4. Close the browser tab, leave the launcher open, and use **Open in browser**. Confirm the same workspace
   returns without a second launcher or visible duplicate server.
5. Use **Choose workspace…** and select the second disposable directory. Confirm the first workspace is no
   longer served and the second opens normally.
6. Close the launcher. Confirm the browser page can no longer reload and no Adventure Graph process remains.
7. Start the launcher again. Confirm it remembers the second workspace and opens it.
8. Move or delete the remembered workspace, relaunch, and confirm the launcher asks for a replacement rather
   than silently choosing another directory.
9. Confirm neither extracted bundle directory contains newly created `adventure.json`, `play-state.json`,
   generated reports, archives, or launcher settings.

Pass criteria:

- no terminal is required for ordinary startup;
- directory selection and remembered selection are understandable;
- only one owned server remains active;
- reopening the browser does not duplicate application state;
- workspace replacement and launcher shutdown release former servers cleanly; and
- all user and launcher data remain outside the application bundle.

## 1. Launch, sample onboarding, and workspace discovery

1. Open the second disposable workspace while it is empty. Confirm the Adventures catalog offers
   **Add The Glass Saint sample**, **Create blank adventure**, and import actions without listing any
   pre-created adventure.
2. Choose **Add The Glass Saint sample**. Confirm exactly one project named *The Glass Saint* appears,
   is selected, and opens normally. Confirm its active playthrough is empty.
3. Return to **Adventures** and confirm no other sample adventure was added or advertised as included
   beta content.
4. Use the browser interface to create a separate title-only adventure in the selected desktop
   workspace.
5. Confirm the Adventures catalog shows both projects and no unrelated directories.
6. Use the wheel-backed CLI recovery surface to run `adventure-graph init` for a third project beneath
   the same workspace, then reopen the launcher browser.
7. Confirm the catalog discovers the new direct-child project.
8. Create another disposable adventure through **New adventure** using only its title.
9. Open **Play** and confirm a friendly no-encounters page appears with **Add first encounter** and
   **Return to Author mode** actions; no generic workspace error should appear.
10. Choose **Add first encounter**, create the encounter, confirm the start role is selected by default,
    and confirm the new encounter opens in Play mode.
11. Switch among the projects.
12. Stop the server, rename the selected project directory, and relaunch the workspace. Confirm the
    catalog reports the unavailable prior selection and does not open another project automatically.
13. Select the renamed project explicitly, close the desktop launcher, relaunch it, and confirm the new
    selection persists.

Pass criteria:

- the empty workspace presents one explicit packaged sample and does not write it before consent;
- adding the sample creates only *The Glass Saint*, with a fresh project identity and empty journal;
- no firewall, permission, or browser-warning dialog blocks ordinary loopback use;
- only root and visible direct-child projects are discovered;
- a title-only project enters Play through an explicit no-encounters state and can create and reopen
  its first encounter without CLI intervention;
- a missing or malformed saved selection never redirects into another project;
- project selection persists after restart; and
- launcher shutdown returns cleanly without an orphaned process.

## 2. Authoring and protected saves

1. Open one encounter editor.
2. Change its title, summary, opening description, Markdown body, and tags.
3. Save with the visible button, reload the page, and confirm every field persists.
4. Make a second change and save with `Ctrl+S` on Windows/Linux or `Cmd+S` on macOS.
5. Begin a third unsaved change, leave the page, return to the editor, and confirm the browser-local draft
   recovery prompt or restored draft behaves as documented.
6. Open the same project in an external text editor, make one harmless canonical change, then attempt to
   save the stale browser form.

Pass criteria:

- button and keyboard saves behave identically;
- Markdown renders without exposing raw HTML;
- unsaved browser-local work is not silently discarded; and
- stale revision refusal preserves the submitted browser values without overwriting the external edit.

## 3. Play navigation and keyboard behavior

1. Open **Play adventure** and begin an explicit session.
2. Focus an encounter without recording a visit; confirm the page distinguishes focused material from the
   current recorded visit.
3. Start a visit and confirm the optional **Split-party label** says that it identifies a subgroup acting
   separately.
4. Enter notebook text and confirm the direct notebook action says **Save note only**.
5. In **Current visit actions**, leave the destination blank and confirm the button says **Save outcomes
   without moving**. Select an available destination and confirm it changes to **Save visit and move**.
6. Outside a text field, exercise `/`, `P`, `G`, `[`, `]`, and `Escape`.
7. While a text field is active, press the same keys and confirm they enter text or retain their ordinary
   field behavior rather than triggering Play shortcuts.
8. Pin an encounter, focus several others, reload the page, and confirm pins and recent focus remain in
   that browser but do not appear in `play-state.json`.

Pass criteria:

- focus and recorded visit state remain visibly distinct;
- the note-only, outcome-only, and move actions remain visibly distinct;
- keyboard shortcuts do not steal input from text fields;
- pins and recent focus survive reload through browser-local storage; and
- read-only navigation never appends a journal event.

## 4. Encounter reader and responsive layout

1. At normal desktop width, resize the divider between **Encounter reference** and **Encounter notes**.
2. Paste a long multi-paragraph draft into the notebook and confirm its status, guidance, and save action
   remain below the editor rather than crossing it.
3. Save several long notes, expand **Committed notes for this visit**, and scroll from the working
   notebook into the committed history without any text or controls overlapping.
4. Give the notes panel both the smallest and largest divider allocations, then minimize and restore each
   panel and double-click the divider to reset it.
5. Use the divider with keyboard arrows, Home, and End.
6. Repeat the long-draft and expanded-history check in the alternate appearance theme.
7. Narrow the browser until route and utility rails become drawers and repeat the overlap check.
8. Open and close each drawer with its button, the scrim, and `Escape`.
9. Restore desktop width and confirm the ordinary three-region layout returns.
10. Reload and confirm the selected layout and appearance persist locally.

Pass criteria:

- the notebook form and committed history remain sequential in normal flow at every tested pane size;
- long note content scrolls within the notes workspace rather than expanding through or beneath controls;
- no panel overlaps its controls or becomes unreachable;
- the notebook remains usable at the supported narrow layout;
- drawer focus and closing behavior are predictable; and
- browser-local layout and appearance preferences survive reload without changing canonical files.

## 5. Graph interaction

1. Open **Structure** and expand the encounter graph.
2. Exercise toolbar zoom, mouse-wheel zoom, `+`, `-`, and `0`.
3. Pan by dragging and with arrow keys.
4. Focus or hover several encounters and confirm incident paths remain legible.
5. Follow an encounter or edge link and return with browser navigation.

Pass criteria:

- labels remain readable at ordinary zoom levels;
- graph controls work without scrolling the page unexpectedly; and
- linked navigation retains the normal application shell.

## 6. Dice behavior

1. Record the current byte hash or modification time of `play-state.json`.
2. Roll `2d8 + 1d4 - 3` with a label.
3. Confirm every die, subtotal, modifier, and final total is visible.
4. Reload without recording and confirm the canonical journal did not change.
5. Roll again, choose **Insert in notebook**, and confirm the exact textual result enters the local notebook
   without yet changing the journal.
6. Commit the notebook, then make another roll and choose **Record in journal**.
7. Inspect **History** and **Journal** and confirm the displayed result was stored without rerolling.

Pass criteria:

- throwaway rolls are ephemeral;
- notebook insertion uses the displayed result exactly;
- explicit recording stores that same result and label; and
- recent expressions remain browser-local conveniences rather than authored or journal data.

## 7. Archive lifecycle

1. End the active session and open **Archives**.
2. Create a labeled archive with an explicit archive identifier.
3. Confirm the active journal resets and the archive detail page shows its event counts and adventure
   snapshot comparison.
4. Attempt restore while the active journal is nonempty and confirm the browser refuses safely.
5. Empty or archive the active journal as appropriate, then restore the original archive.
6. Confirm the archive remains present and byte-identical after restore.
7. Enter an incorrect deletion confirmation and confirm deletion is refused.
8. Enter the exact identifier and delete the disposable archive.

Pass criteria:

- archive, reset, restore, and deletion each require explicit revision-aware forms;
- restore never consumes or rewrites the archive;
- incompatible or unsafe restoration explains the required next action; and
- deletion requires an exact identifier match.

## 8. Restart, relocation, and malformed-file recovery

1. Stop the server immediately after a successful browser write and relaunch the same workspace.
2. Confirm the last authored edit, note, recorded die roll, and archive state remain present.
3. Stop the server, copy the project directory, rename the copy, and reopen the copied workspace.
4. Add one unknown field to a copy of `adventure.json` and launch that project explicitly.
5. Confirm startup fails closed with an actionable diagnostic, then restore the original bytes and relaunch.

Pass criteria:

- ordinary shutdown and restart lose no committed data;
- copied and renamed directories preserve adventure identity and journal references;
- malformed current-schema documents are not silently rewritten; and
- browser error pages do not disclose absolute local filesystem paths.

## 9. Result classification

Classify every finding before closing the platform run:

- **Release-blocking:** data loss, corruption, unsafe overwrite, inaccessible primary workflow, security
  boundary failure, installation failure, or supported-platform crash.
- **Follow-up:** noncritical friction, unclear wording, minor visual defect, or optional workflow issue
  with a safe workaround.
- **Accepted limitation:** behavior already outside the documented private-beta contract, provided the
  limitation remains explicit and does not undermine a supported workflow.

For each defect, record exact reproduction steps, expected and observed behavior, screenshots when
visual, terminal output when operational, and the smallest sanitized project that reproduces it.

## Completion record

```text
Hosted frozen-executable smoke: PASS / FAIL
Automated clean-wheel smoke: PASS / FAIL
Native launcher lifecycle: PASS / FAIL
Launch and workspace discovery: PASS / FAIL
Authoring and protected saves: PASS / FAIL
Play navigation and keyboard behavior: PASS / FAIL
Encounter reader and responsive layout: PASS / FAIL
Graph interaction: PASS / FAIL
Dice behavior: PASS / FAIL
Archive lifecycle: PASS / FAIL
Restart, relocation, and malformed-file recovery: PASS / FAIL
Release-blocking findings:
Follow-up findings:
Accepted limitations:
Overall platform result: PASS / FAIL
```
