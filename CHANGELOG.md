## 0.10.0 — Beta-readiness audit (local code candidate)
- Audited source comments, docstrings, CSS section labels, and local static-analysis suppressions without
  changing runtime or persisted behavior: removed avoidable intentional-invalid-type suppressions; classified
  direct-module imports used by fault-injection tests and the standard-library request-handler override as
  deliberate; added explicit rationale to every remaining local suppression; replaced stale tranche-style CSS
  headings with structural labels; documented the user-facing Lead versus persisted `Clue` boundary at the
  domain seam; and added architecture guardrails against unexplained suppressions and untracked work-item
  comments.
- Reorganized repository documentation without changing product behavior: reduced the root README from an
  840-line combined manual to a concise product entry point; moved the complete stable CLI map and workflows
  into `docs/cli-reference.md`; moved source-snapshot, native desktop, and connected quality procedures into
  `docs/maintainer-guide.md`; added `docs/README.md` as the authoritative categorized index; removed
  consolidated session handoffs from the packaged repository root; and added documentation contracts for
  index completeness, README scope, and handoff hygiene.
- Extracted the complete revision-aware browser authoring POST family from the selected-adventure WSGI
  shell into `interfaces/web/authoring_action_workspace.py`. The collaborator now owns authoring form
  parsing, command construction, redirects, and server-side error reconstruction; `app.py` retains the
  request boundary, read routing, and report/archive/Play delegation. Added direct route-refusal and
  draft-key regressions plus an architecture contract preserving the seam. No route, form field, command,
  rendered response, schema, persisted value, or stable identifier changed.
- Consolidated repeated authored-corpus test mechanics without changing product behavior or editorial contracts: added narrowly typed helpers for stable `Clue` grouping by revelation and source encounter, centralized exact rendered-packet comparisons with aggregated drift diagnostics, migrated twenty-seven revelation-grouping call sites, five encounter-grouping call sites, and twenty-eight packet comparisons, retained every adventure-specific threshold, identity, route, and prose assertion inline, and added focused helper regressions.
- Reconciled documentation and evidence drift without changing runtime behavior: removed volatile test, corpus, coverage, and browser counts from the durable test-strategy document; marked the earlier release qualification as a frozen historical record rather than evidence for descendant revisions; updated the UI architecture to describe the completed application-seam extraction and minimal `bootstrap.py` dispatcher; clarified the Lead/`clue` presentation boundary; and added documentation regressions preventing the stale baseline and obsolete pressure-point claim from returning.
- Hardened the Lead/`clue` presentation boundary without changing compatibility tokens: removed the generic regex that rewrote arbitrary error prose, moved Lead vocabulary into explicit CLI, validation, authoring, and play-tracking messages, preserved authored names containing words such as **Clue**, and added a regression proving **The Clue Club** is never silently rendered as **The Lead Club**. Stable commands, selectors, routes, fields, event kinds, identifiers, and filenames remain unchanged.
- Completed the user-facing lead terminology migration: player-safe recap counters, banners, Markdown
  downloads, revelation support summaries, and risky-save summaries now use **lead** consistently.
  Persisted `clue` fields, routes, event kinds, CLI commands, and stable filenames remain unchanged.
- Rechristened authored clues as **leads** throughout the GM-facing browser and desktop interface,
  validation presentation, dependency previews, operational ledgers, and generated GM documents.
  This first phase preserved the player-safe recap term while retaining every `clue` JSON field, URL,
  Python type, event kind, CLI command, and stable filename; the follow-up entry above completes the
  user-facing vocabulary migration without a persisted-data migration.
- Completed post-reference-defragmentation beta maintenance triage: reconciled external release evidence,
  concrete correctness maintenance, conditional technical debt, tester-facing UI, internal content, and
  campaign research into one prioritized compatibility-aware queue; left campaign implementation deferred;
  and set the next checkpoint to connected qualification and native platform evidence.
- Corrected repository cleanup reproducibility after the final corpus package exposed nested editable-install
  metadata surviving the former root-only pattern. `make clean` now delegates to a tested portable Python
  cleaner that removes `*.egg-info` and `__pycache__` directories at any repository depth while preserving
  authored source. Portable source snapshots also exclude parallel `.coverage.*` data directly instead of
  relying on cleanup order.
- Added a restrained beta-feedback block to application-wide Help. Browser and desktop users can now report
  the installed Adventure Graph version without opening a terminal, alongside privacy-conscious guidance for
  sharing the smallest relevant project file.
- Completed the final example encounter-name ledger and deconfliction pass: rebuilt all 138 encounter titles and stable IDs from the thirteen authoritative adventure sources; confirmed zero exact and article-and-punctuation-insensitive cross-adventure duplicates; renamed The Shrine of the Open Door to **The Doorless Shrine**, The Black Cisterns to **The Cisterns of Black Breath**, The Hall of Petitions to **The Hall of Condemnations**, and The White Hart Gallery to **The Gallery of Silver Kin**; preserved all four stable encounter IDs, every UUID, all demonstration journals and historical archives, and the `deep-bell`/`the-deep-bell` compatibility boundary; reviewed eighteen current automated or practical ambiguity candidates with no unresolved disposition; regenerated all four affected packets; published the final ledger and machine-readable disposition record; and closed the reference-defragmentation workstream.
- Completed *When the Swine Kneel* Reference Defragmentation Coherence III: reconciled the closed twenty-one-record, 111-link library against all seven encounters, nine required and one optional revelation, thirty-eight clues, the civic clock, commission and evidence procedure, all three Bell approaches, four stress-tested routes, the thirty-five-document packet, the immutable historical archive, and the unchanged ninety-six-event demonstration; proved every required revelation retains at least two independent encounter sources after any one encounter is removed; preserved the separation among knowledge, physical access, communication, lawful authority, certified evidence, handlers, engineers, Bell state, remedy, and inhabited cost; found no canonical contradiction; retained the stable `the-deep-bell` identifier beneath **The Six-Line Bell**; closed the Swine sequence; and advanced the active checkpoint to the final example encounter-name ledger and deconfliction pass.
- Completed *When the Swine Kneel* Reference Defragmentation Voice III: repaired all seven post-extraction encounter seams; kept the ten person sheets byte-identical; replaced generic state inventories in the eleven second-pass sheets with subject-native limits; reduced encounter content from 5,764 to 5,592 words and the combined encounter/reference layer by 195 words; preserved every non-prose field, all twenty-one identities, one hundred eleven ordered links, the stable `the-deep-bell` identifier, and the ninety-six-event journal; regenerated the thirty-five-document packet; and advanced the active checkpoint to Swine Coherence III.
- Completed *When the Swine Kneel* Reference Extraction II: added the Hall of Petitions, Southgate Stockyards, the College of Civic Measure, Rillcross Farm Belt, the Chapel of the First Survey, the Nine-Mile Pump House, the Six-Line Bell, the Office of Waters, the Slaughterers' Compact, the First Survey, and bronze sounding pins after the ten frozen people; closed the library at twenty-one records and one hundred eleven ordered links; preserved all forty-eight Extraction I link objects as exact prefixes, the stable `the-deep-bell` identifier, every encounter, revelation, clue, authored prose field, graph edge, and all ninety-six demonstration events; kept supporting officers, current orders, herds, evidence, records, quarantine, pump state, Bell state, remedy, and settlement in stronger encounter and runtime instruments; regenerated a thirty-five-document packet; and advanced the active checkpoint to Swine Voice III.
- Completed *When the Swine Kneel* Reference Extraction I: retained Alda Mere, Corven Dast, Tamar Vey, Oren Salk, Harl Rill, Ina Rill, Selya Quill, Anja Veil, Jalen Orr, and Olyra Sen as ten bounded person records with forty-eight ordered contextual links; kept current herd readings, commission scope, command, custody, testimony, quarantine, records, measurements, station load, Bell operations, remedy, and the Ashlar Company route in encounter procedure and append-only play; preserved all seven encounters, ten revelations, thirty-eight clues, graph topology, the stable `the-deep-bell` identifier, and ninety-six demonstration events; regenerated a twenty-four-document packet; and advanced the active checkpoint to Swine Reference Extraction II.
- Completed *The Witch of Blackbriar Hall* Reference Defragmentation Coherence III: reconciled the closed twenty-nine-record, 185-link library against all ten encounters, eighteen required revelations, ninety-five clues, specialist ledgers and operating sheets, the forty-six-document packet, and the unchanged 200-event demonstration; proved every required revelation retains at least two independent encounter sources after any one encounter is removed; preserved directed reachability and the separation among knowledge, access, custody, care, routes, pact work, feast components, Judith state, and outcomes; found no canonical contradiction; closed the Blackbriar sequence; and advanced the active checkpoint to *When the Swine Kneel* Reference Extraction I.
- Completed *The Witch of Blackbriar Hall* Reference Defragmentation Voice III: repaired nine post-extraction encounter seams while preserving Saint Orra’s Gallows exactly; replaced the repeated stable/live endings in nineteen second-pass reference sheets with subject-native operational limits; reduced encounter prose from 28,330 to 28,086 words and the combined encounter/reference layer by 89 words; preserved all twenty-nine references, 185 ordered links, ninety-five clues, eighteen revelations, ten openings, graph topology, operating procedures, and the byte-identical 200-event journal; regenerated the forty-six-document packet; and advanced the active checkpoint to Blackbriar Coherence III.
- Completed *The Witch of Blackbriar Hall* Reference Extraction I: retained Judith Crowl, Canon Ysra Vale, Brother Caldus Merrow, Mara Sedge, Nell Sedge, Tomas Sedge, Reeve Ansel Pell, Beadle Odo Vane, Captain Varro Cleft, and Sister Harl as ten bounded person records with seventy ordered contextual links; kept current execution, custody, testimony, pact, retaliation, carrier, route, institution, feast, and family state in stronger dynamic instruments; preserved all ten encounters, eighteen revelations, ninety-five clues, graph topology, authored prose, and two hundred demonstration events; regenerated a twenty-seven-document packet; and advanced the active checkpoint to Blackbriar Hall Reference Extraction II.
- Completed *The Siege of the Stone Lung* Reference Defragmentation Coherence III: reconciled the closed nineteen-record, ninety-three-link library against all eight encounters, eleven required and one optional revelation, forty-six clues, the sector ledger, four priority routes, three Stone Lung approaches, command and technical authority, current resources and records, Heartstrike control, the thirty-four-document packet, and the unchanged eighty-five-event demonstration; proved every required revelation retains at least two independent encounter sources after any one encounter is removed; found no canonical contradiction; closed the Stone Lung sequence; and advanced the active checkpoint to *The Witch of Blackbriar Hall* Reference Extraction I.
- Completed *The Siege of the Stone Lung* Reference Defragmentation Voice III: repaired all eight post-extraction encounter seams; kept the six person sheets byte-identical; replaced repetitive boundary cadence in the thirteen second-pass reference sheets with Stone Lung-native command, wall, foundry, garden, refuge, water, tunnel, record, and weapon language; reduced encounter content from 5,266 to 5,162 words and total encounter-plus-reference content by fifty-eight words; preserved every non-prose field, all ninety-three ordered links, and all eighty-five journal events; regenerated the thirty-four-document packet; and advanced the active checkpoint to Stone Lung Coherence III.
- Completed *The Siege of the Stone Lung* Reference Extraction II: added thirteen bounded authority, place, organization, record, and weapon subjects after the six frozen people; closed the library at nineteen references and ninety-three ordered links; preserved all forty Extraction I contexts as exact prefixes; kept current sector state, supporting leaders, crews, testimony, custody, resources, routes, signals, command reach, machine state, and settlement in stronger encounter and runtime instruments; regenerated a thirty-four-document packet; preserved the eighty-five-event demonstration byte-for-byte; and advanced the active checkpoint to Stone Lung Voice III.
- Completed *The Siege of the Stone Lung* Reference Extraction I: retained Ilyra Dain, Edda Marr, Tamar Ohn, Brann Sile, Sera Venn, and Korr Bas as six bounded authority records with forty ordered contextual links; kept current sector state, orders, allocations, records, technical diagnosis, crews, prisoners, routes, signals, charge state, settlement, and the Basalt Hand route in stronger dynamic instruments; preserved all eight encounters, twelve revelations, forty-six clues, graph topology, and eighty-five demonstration events; regenerated a twenty-one-document packet; and advanced the active checkpoint to Stone Lung Reference Extraction II.
- Completed *The Princess on the Salt Road* Reference Defragmentation Coherence III: reconciled the closed fifteen-record, eighty-eight-link library against all nine encounters, twenty necessary revelations, ninety-three clues, eight specialist instruments, all route, pursuit, custody, resource, signal, sanctuary, and mixed-outcome states, the thirty-one-document packet, and the unchanged 136-event demonstration; proved every necessary revelation retains at least two independent encounter sources after any one encounter is removed; corrected current-facing README and changelog drift; made no canonical data or workflow change; closed the Salt Road sequence; and advanced the active checkpoint to Stone Lung Reference Extraction I.
- Completed *The Princess on the Salt Road* Reference Defragmentation Voice III: repaired eight post-extraction encounter seams, left the Dry Aqueduct and all fifteen reference bodies byte-identical, reduced encounter prose by 112 words, preserved every non-prose field and all 136 journal events, regenerated the thirty-one-document packet, and advanced the active checkpoint to Salt Road Coherence III.
- Completed *The Princess on the Salt Road* Reference Extraction II: added ten bounded organization, place, and object records after the five frozen person records; closed the library at fifteen references and eighty-eight ordered links; preserved all thirty-five Extraction I contexts as exact prefixes; kept current resources, routes, signals, custody, sanctuary, ship, and outcome state in stronger dynamic instruments; regenerated a thirty-one-document packet; and advanced the active checkpoint to Salt Road Voice III.
- Completed *The Princess on the Salt Road* Reference Extraction I: retained Ianthe, Kallias, Dorion, Naevan, and Serathiel as five bounded person records with thirty-five ordered contextual links; preserved all nine encounters, twenty revelations, ninety-three clues, route and state procedures, and the 136-event demonstration; regenerated a twenty-one-document packet; and advanced the active checkpoint to Salt Road Reference Extraction II.
- Completed *The March on Vossgard* Reference Defragmentation Coherence III: reconciled the closed fifteen-record, sixty-eight-link library against all eight encounters, twelve necessary revelations, fifty-one clues, campaign procedures, the thirty-document packet, and the unchanged seventy-eight-event demonstration; proved single-encounter removal resilience; found no canonical contradiction; closed the March sequence; and advanced the active checkpoint to Salt Road Reference Extraction I.
- Completed *The March on Vossgard* Reference Defragmentation Voice III: repaired post-extraction encounter seams while preserving all fifteen reference bodies, sixty-eight ordered links, campaign state, clue and revelation structure, and the seventy-eight-event demonstration; regenerated the thirty-document packet; and advanced the active checkpoint to March Coherence III.
- Completed *The March on Vossgard* Reference Extraction II: retained the Ash Warrant, Ashen Gate, Iron Causeway, Tithe Villages, Red Abbey, Black Bell, Drowned Sluice, and Vossgard as eight bounded instrument and place records; closed the library at fifteen references and sixty-eight ordered links; kept encounter-local commanders, formations, whole-region dossiers, current records, campaign state, and demonstration characters in their stronger local or dynamic instruments; preserved all seven Extraction I records, thirty-one prior contexts, eight encounter bodies, twelve revelations, fifty-one clues, graph topology, and the seventy-eight-event journal; regenerated a thirty-document packet; and advanced the active checkpoint to March Voice III.
- Completed *The Mandate of Seven Reeds* Reference Defragmentation Coherence III: reconciled the closed eighteen-record, 112-link library against all fifteen encounters, forty-four revelations, 221 clues, five specialist aids, route stress tests, the forty-document packet, and the unchanged 288-event demonstration; proved one-proceeding loss and optional moon-viewing omission remain playable; preserved the separation among attendance, consultation, burden, submission, dispatch, receipt, performance, amendment, and Imperial judgment; corrected the historical packet boundary in the final audit; made no canonical data or workflow change; closed the Mandate sequence; and advanced the active checkpoint to March on Vossgard Reference Extraction I.
- Completed *The Mandate of Seven Reeds* Reference Defragmentation Voice III: replaced five post-extraction dossier seams in the opening audience, Ministry of Divided Ink, Garden of White Gravel, Hall of Open Roads, and Guesthouse of the Bent Reed with handled objects and live court procedure; replaced all fifty-four internal headings across eighteen reference sheets with Mandate-native tablets, standards, routes, burdens, receipts, and review language while preserving every paragraph body; reduced encounter prose by twenty-seven words; preserved every opening, summary, clue, revelation, graph edge, link, specialist procedure, and all 288 journal events; regenerated the forty-document packet; and advanced the active checkpoint to Mandate Coherence III.
- Completed *The Mandate of Seven Reeds* Reference Extraction II: retained all seven Great Clan principals as bounded authority records; added the Seven Reeds, Reedwater Province, Cumulative Burden Ledger, and Submission Register; closed the library at eighteen records and 112 ordered links; kept all fourteen supporting delegates in the Court Ledger and dedicated proceedings; preserved all encounter prose, forty-four revelations, 221 clues, topology, live drafts, burdens, submissions, Imperial judgment, and the 288-event demonstration; regenerated a forty-document packet; and advanced the active checkpoint to Mandate Voice III.

- Completed *The Mandate of Seven Reeds* Reference Extraction I: retained Otomo Kazetada, Seppun Tomoe, Miya Shun, Rei of Reed Bank, Brother Hojun, Saburo of the Three Crossings, and Natsugawa Kenta as seven bounded person records with forty-two ordered contextual links; kept clan comparison in the Court Ledger and all live drafting, coalition, office, command, route, burden, submission, inspection, remedy, and Imperial judgment state in the specialist aids, encounter procedures, and append-only play journal; regenerated a twenty-nine-document packet; preserved all fifteen encounters, forty-four revelations, 221 clues, graph topology, and 288 demonstration events; and advanced the active checkpoint to Mandate Reference Extraction II.
- Completed *The Last Bell of Bramblewick* Reference Defragmentation Coherence III: reconciled the closed sixteen-record, eighty-eight-link library against all eleven encounters, 123 clues, seventeen necessary and nine optional revelations, route and authority instruments, the thirty-four-document packet, and the unchanged 156-event demonstration; stress-tested skipped encounters, split groups, late evidence, absent and recused officials, child witnesses, two-key custody, weather, flight, accusation and remedy branches, runtime views, and compatibility; found no canonical contradiction; corrected the current final audit from its historical seventeen-document packet count; closed Bramblewick's sequence; and advanced the active checkpoint to *The Mandate of Seven Reeds* Reference Extraction I.
- Completed *The Last Bell of Bramblewick* Reference Defragmentation Voice III: repaired six post-extraction encounter seams in Hearth Hall, the Common Chest, Bramblewick School, the Chapel of the Open Door, the North Hedge, and the First-Bell Moot; replaced thirty-one generic headings across all sixteen reference sheets with Bramblewick-native books, keys, weather, household, and divided-office language; preserved every reference paragraph, clue, revelation, opening, summary, graph edge, link, and 156-event journal entry; regenerated the thirty-four-document packet; and advanced the active checkpoint to Bramblewick Coherence III.
- Completed *The Last Bell of Bramblewick* Reference Extraction II: retained Bram Alder, Mara Kettle, Cora Bramble, and Perrin Moss as bounded household and occupational records; added the Hearth Book, Common Chest, First-Bell Moot, Bramblewick School, Chapel of the Open Door, and North Hedge; closed the library at sixteen references and eighty-eight ordered links; kept supporting witnesses, evidence objects, the ghost-hearth scheme, beneficiary records, route use, accusations, and sample aftermath in stronger dynamic instruments; regenerated a thirty-four-document packet; preserved all twenty-six revelations, 123 clues, eleven encounter prose bodies, graph topology, and the 156-event journal; and advanced the active checkpoint to Bramblewick Voice III.
- Completed *The Last Bell of Bramblewick* Reference Extraction I: retained Merrit Alder, Orlo Vane, Hester Rowan, Wil Sloe, Sister Amity Thorne, and Nim Thatch as six bounded person records with thirty-seven ordered contextual links; kept guilt, hidden wrongdoing, alibi state, custody, testimony, privacy decisions, collateral findings, and the Lantern Measure route in clues, encounter procedure, ledgers, and append-only play; regenerated a twenty-four-document packet; preserved the 156-event journal byte-for-byte; and advanced the active checkpoint to Bramblewick Reference Extraction II.
- Completed *The Forest That Carries Dawn* Reference Defragmentation Coherence III: reconciled the closed nine-record, forty-two-link library against all ten encounters, ninety-four clues, eighteen necessary revelations, specialist ledgers, generated packet, 196-event demonstration, and immutable archive; stress-tested skipped encounters, late evidence, split groups, absent principals, exact roster and property state, all six currents, crown separation, divided departure, and journal-neutral reference views; found no canonical contradiction; clarified the archive's intentional pre-reference, pre-Voice-III boundary without changing authored JSON or journal history; closed the Forest sequence; and advanced the active checkpoint to *The Last Bell of Bramblewick* Reference Extraction I.
- Completed *The Forest That Carries Dawn* Reference Defragmentation Voice III: repaired dossier-like seams in Camp, Hollow, Root-Breath, Crown, and Glass Verge; retained every roster, route, ecology, burden, crown, consent, and departure procedure; gave seven reference sheets Forest-native headings while preserving all reference paragraph bodies; reduced encounter-body prose by seventy-six words; kept all nine references, forty-two ordered links, ninety-four clues, eighteen revelations, ten openings, the 196-event journal, and the immutable historical archive; and advanced the active checkpoint to Forest Coherence III.
- Corrected Play mode for intentionally title-only adventures: an adventure with no encounters now
  returns a friendly HTTP 200 empty state with direct Author and first-encounter actions instead of
  falling through focus resolution to a generic workspace HTTP 500. Added renderer and complete
  workspace regressions for the supported almost-blank creation path.

- Narrowed the first private beta to one tester-facing sample adventure, *The Glass Saint*. The wheel and
  native package already carried only that runtime resource; the browser now exposes it directly from an
  empty catalog and the New Adventure page without silently modifying a workspace. Sample creation reuses
  a transport-neutral template-instantiation use case, assigns fresh UUIDv4 identity, creates an empty
  matching playthrough, and is protected by application, filesystem, packaging, and responsive-browser
  regressions. The other adventures remain source-development corpus and are no longer release blockers or
  represented as polished beta content.

- Added first-class playthrough notes for persistent references before external distribution. Play-state
  schema 6 introduces `reference_note_recorded` with stable reference identity and append-only text;
  revision-aware application, CLI, and browser workflows reuse the existing journal and correction
  machinery; selected references show their chronological note history; Journal, GM narrative, and
  generated summaries include the notes; the player-safe recap excludes them; and authored reference
  removal is blocked while related play history depends on that identity. All bundled active and archived
  journals were migrated atomically from schema 5 to schema 6.

- Closed the final pre-beta persisted-contract audit without broad restructuring: canonical JSON writers now
  enforce the same 8 MiB ceiling as readers, uploads, and transaction recovery before any mutation; journal
  archive identifiers are limited to 80 portable ASCII characters and unique without regard to case; derived
  identifiers and browser adventure download names are bounded; the five bundled archives remain valid; and
  schema shapes, stable adventure identity, workspace selection, transaction markers, and desktop settings
  remain unchanged. Recorded the rejected decompositions and future cleanup triggers separately.

- Added first-class portable transfer workflows to the local browser: adventure cards export canonical `*.adventure.json` documents, the catalog imports them into new empty-journal projects while preserving authored identity, active and archived playthroughs export self-contained `*.journal.json` snapshots, and matching playthrough archives import into the selected fixed adventure with revision, identity, collision, size, schema, and path-safety checks.

- Corrected the Adventures catalog before private-beta packaging: the filter controls now lay out against the bounded content column without desktop overflow, card actions wrap cleanly, and every adventure card provides a revision-aware **Playthroughs** action that selects that exact adventure before opening its archive import/export workspace. Added executable browser coverage at desktop, intermediate, tablet, and compact widths.

- Added workspace-level **Import playthrough** to the Adventures catalog. A transport-neutral application service resolves the archive's embedded stable adventure identity to exactly one project, then reuses the existing project-level importer and its revision, schema, collision, compatibility, and path-safety checks. Missing or duplicate adventure identities are rejected without changing selection, active journals, or archive catalogs.

- Hardened the complete browser transfer workflow before private beta: catalog and selected-adventure imports now have distinct wording, one clear submit action, visible 8 MiB guidance, compact-width containment, and alert semantics; empty journals explain unavailable export and archive actions; malformed, oversize, stale, mismatched, duplicate, and local-storage failures return bounded actionable responses without disclosing workspace paths.

- Corrected compound Play transitions that began with already-supported revelations: a visit may now
  establish several revelations, apply their automatic unlocks, and move once as one atomic operation.
  Rejected-action notices replace internal operation indexes and authored IDs with GM-facing substance.
  The visit form now shows a concise pending-action summary only for unusually broad or mixed updates,
  and redundant notebook explanation was removed.

- Closed the source-snapshot portability interruption after the replacement archive passed an ordinary
  Windows Explorer extraction without error `0x80010135`: retained the deterministic source ZIP builder and
  verifier, stable `adventure-graph/` internal root, explicit path budgets, local-artifact exclusions,
  fail-closed safety checks, Makefile and CI integration, and focused regression evidence; preserved every
  Aurelune and corpus artifact unchanged and resumed Forest Reference Extraction I.

- Corrected the aggregate desktop-artifact verifier after a native macOS bundle exposed a valid chained
  Python-framework link: verification now resolves symbolic links encountered inside another link's target
  path, still rejects absolute targets, root escape, cycles, and missing final members, and includes focused
  macOS-chain and cycle regressions. Updated the WSL export instructions to use the `gh run list` form
  supported by the maintainer's installed GitHub CLI.

- Completed *The Concord of Aurelune* Reference Defragmentation Coherence III: reconciled all fourteen canonical records and seventy-two ordered links against the complete court source, Court Ledger, petition-clause matrix, six coalition stress tests, route and revelation audits, thirty-five-document packet, and 158-event demonstration; exercised skipped encounters, split delegations, absent principals, nine banners without the Ashen Bough, scoped-regency amendments, certification without an Eiral seal, acceptance without seven banners, seven banners without royal joinder, and royal relief after petition failure; found no canonical contradiction; clarified the historical scope of the original consistency audit; preserved every authored JSON and journal object; closed the Aurelune sequence; and advanced the active checkpoint to *The Forest That Carries Dawn* Reference Extraction I.

- Completed *The Concord of Aurelune* Reference Defragmentation Voice III: removed four bounded post-extraction seams from the Noon Spear Court, Golden Sheaf Exchange, Twilight Laurel Apartments, and Ashen Bough Hearing; replaced generic taxonomic headings on all fourteen reference sheets with Aurelune-native court language while preserving every underlying reference paragraph; corrected the inherited revelation count to fifteen necessary and three optional; preserved all fourteen stable identities, seventy-two ordered links, clues, revelations, graph edges, outcomes, and the 158-event demonstration; and advanced the active checkpoint to Aurelune Coherence III.

- Completed *The Concord of Aurelune* Reference Extraction II: retained four specialist authorities, Orison, the Ashen Bough, the Pall, the Concord of Open Hands, the Oath of the Unbroken Word, and the Lantern Road Compact; expanded the complete library to fourteen records and seventy-two ordered links; preserved the Court Ledger as the comparative authority for the remaining banner principals and the petition documents as the authority for changing state; kept all clues, revelations, graph edges, outcomes, and the 158-event demonstration unchanged; and advanced the active checkpoint to Aurelune Voice III.

- Cleaned maintainer documentation before resuming corpus work: consolidated completed test-hardening
  diaries into one durable test strategy, removed duplicate top-level handoffs, clarified the active
  Aurelune checkpoint, centralized Play-renderer lint rationale, repaired beta-guide wording, and added
  README and desktop-guide procedures for exporting verified Linux, Windows, and macOS bundles from WSL
  through native hosted runners or from the current operating system locally.

- Completed the bounded pre-shipping test-hardening sequence with twenty-seven reviewed mutations across
  graph, dice, Play, persistence, and transaction seams; added focused tests for all nine meaningful
  survivors; classified three equivalent or redundant mutants; covered every non-Tk desktop-launcher
  branch; documented native manual evidence; and restored *The Concord of Aurelune — Reference Extraction
  I* as the active content checkpoint.

- Continued the pre-shipping test-hardening sequence by classifying corpus assertions as structural,
  semantic, exact generated-artifact, or deliberate editorial locks; added shared corpus-contract helpers;
  loosened incidental voice phrasing without weakening legal, ritual, identity, ordering, or packet
  contracts; and added fail-closed feature-local property suites for canonical persistence, dice, and
  append-only Play projection.

- Began the pre-shipping test-hardening sequence with a dedicated executable Chromium gate for the six
  Play encounter sections, browser-local drafts and dice state, mobile drawer focus, and journal-neutral
  Play authoring; added direct exact-boundary tests and split bundled-adventure corpus contracts into a
  separately targetable test tier without weakening the full release suite.

- Converged the Play interface panel refactor through a reference-light/reference-rich GM cold-read at
  compact, tablet, and desktop widths. The six-box center, independent disclosure and scroll behavior,
  wider workspace, dice/current-visit rail order, and return-safe **Add to adventure** language required
  no further product correction. Documentation, deterministic suites, schema and asset checks, clean
  wheel construction, and the installed beta lifecycle were refreshed from the converged source.

- Continued the bounded Play interface panel refactor: Author entity groups use one accessible,
  browser-local disclosure behavior and begin collapsed; authored search temporarily reveals matching
  groups; the dice tray precedes current-visit actions; and **Add to adventure** offers return-safe
  authoring paths for ordinary encounters, clues, revelation-plus-clue pairs, and encounter-linked
  references without changing the active journal or current visit. The viewport-locked reference/notes
  split, divider behavior, and saved layout key are removed. The center now uses a widened page-scrolling
  stack of six expanded-by-default, independently collapsible, internally scrollable sections, backed by
  a dedicated encounter renderer rather than extending the Play shell renderer.

- Completed *The Cauldron of Nine Silences* Reference Defragmentation Coherence III: reconciled all nineteen persistent records and 127 ordered links against the constitutional, ritual, custody, transport, route, and aftermath systems; restored the Gate Compact's complete one-authenticated-leaf-plus-two-witness contradiction threshold; standardized Branoc's exact recovered command across the operating sheet, consistency audit, and demonstrated play; corrected the Green Lark carrying headcount; preserved every stable identity, clue, revelation, graph edge, possible ending, and all 149 journal events; closed the Cauldron sequence; and advanced the active checkpoint to *The Concord of Aurelune* Reference Extraction I.

- Completed *The Bell Beneath Harrowgate* Reference Defragmentation Coherence III: reconciled all twenty-three persistent records and 160 ordered links against the complete adventure, operating aids, generated packet, and 366-event demonstration; restored the Chain Scriptorium's three distinct genealogy jurisdictions, bounded Queen Avarra's coerced surrender to the authority it actually conveyed, corrected one Pell Varo pronoun heading, preserved every stable identity, clue, revelation, route, operating choice, outcome, and journal event, closed the Bell sequence, and advanced the active checkpoint to *The Cauldron of Nine Silences* Reference Extraction I.

- Completed *The Bell Beneath Harrowgate* Reference Defragmentation Voice III: removed 403 words of post-extraction dossier repetition from the Chain Scriptorium, Reliquary Under Water, Feast of Empty Chairs, King's Narrow Grave, Counterweight Wells, and Deep Bell; replaced generic limit headings on twenty-two reference sheets with subject-specific Harrowgate language; reconciled the authoritative Session 10 source as twenty-three records and 160 ordered links; preserved every opening, clue, revelation, route, operating rule, possible outcome, and all 366 journal events; and advanced the active checkpoint to Bell Coherence III.

- Completed *The Bell Beneath Harrowgate* Reference Extraction II: retained Chief Factor Halren Coss, Councilor Samet Rhun, Prefect Ardel Quoin, Keeper Odran Greve, Tavia Hest, Rhea Colm, Nara-of-the-Seventh-Name, the Ember Company, the Low Choir, six cross-route places, the Crown of Measure, and the Common Measure; expanded the complete library to twenty-three records and 160 ordered links; preserved specialist ledgers as the authority for changing dungeon state; synchronized the accepted Mara Venn→Rhea Colm and Ansel Greve→Odran Greve migrations; regenerated a forty-eight-document packet; and advanced the active checkpoint to Bell Voice III.

- Completed *The Bell Beneath Harrowgate* Reference Extraction I: retained Lady Merrow Vey, Captain Maelin Rook, Factor Orren Saye, Engineer Pell Varo, and Queen Avarra as five bounded person records; re-audited the existing Salt Wardens record unchanged; expanded the Bell library to six records and forty-seven ordered links; preserved the changing state of Avarra's divided faculties, survivor locations, repair capacity, claims, and finale operations; and advanced the active checkpoint to Bell Reference Extraction II.

- Completed *The Glass Saint* Reference Defragmentation Coherence III: reconciled all fifteen records and ninety-three links against the investigation, operating sheets, generated packet, 116-event demonstration, and historical archive; required authenticated provenance for House-copy evidence; made the ordinary mouth stage explicitly require both a living Vale inside the outer pane circle and a hand closing the inner line; and preserved all identities, clues, revelations, graph edges, routes, journal events, reference content, and possible outcomes. The Glass sequence is closed, and the active checkpoint is now *The Bell Beneath Harrowgate* Reference Extraction I.

- Completed *The Glass Saint* Reference Defragmentation Voice III: removed post-extraction dossier repetition from the Archive Vault, West Infirmary, House of Petitions, and Grand Belfry; gave four non-person sheets headings native to petitions, fever doors, panes, ropes, and bronze; corrected the belfry opening to the fixed Mela Fen, Rian Voss, and Karel Venn roster; and preserved all fifteen records, ninety-three links, graph contracts, operating states, and 116 demonstrated-play events.

- Completed *The Glass Saint* Reference Extraction II with nine supporting person, organization, and place records; resolved the stale curator-name synchronization defect; expanded the complete library to fifteen records and ninety-three backlinks; and added the seed encounter-name ledger plus final Session 53 deconfliction pass.

- Reopened the bundled corpus for a user-authorized reference-defragmentation sequence before native
  platform signoff: two extraction sessions, one voice pass, and one coherence pass for each of thirteen
  adventures. The completed *A Wedding for the River* extraction now has eleven canonical records: the
  five primary people from Session 01 plus Mara Vale, Orren Underbridge, Rain-at-Noon, the House of Open
  Measure, Vale Mill and Hearth, and the House Beneath the Willows. Sixty-six ordered contextual links
  and generated reference sheets preserve the complete restrained library without changing clues,
  revelations, topology, journals, or outcomes. The subsequent Wedding Voice III pass removed repeated
  stable biography from the House, mill, and willow-house encounter bodies, retained every live procedure
  and authority matrix, and gave the three non-person sheets headings drawn from the adventure's own
  doors, wheel, hearth, lease, current, and shifts. The closing Coherence III pass reconciled all eleven
  records and sixty-six links against the ledgers, generated packet, route fallbacks, and 140-event
  demonstration; it corrected one narrow recorder/certifier wording defect without changing any identity,
  clue, revelation, graph edge, journal event, archive, or outcome. The user then moved *The Glass
  Saint* ahead of the remaining corpus. Its first extraction tranche adds Saint Olyra, Iria Vale, Edrin
  Vale, Tavia Sorn, Provost Helian Dorr, and Captain Ors Renn as six stable person records with forty-five
  ordered contextual links, while deferring supporting actors, places, organizations, ritual objects, and
  the unresolved Mara/Iria identity boundary to the second extraction session.

- Implemented the adventure reference-library lifecycle accepted by the fixture review: immutable
  adventure-owned reference records and encounter links, additive schema-version-3 decoding and
  canonical writing, strict object boundaries, structural diagnostics, archive preservation, sparse
  compatibility, ordinary project revisions, revision-aware create/edit/link/unlink/remove operations,
  dependency projections, CLI recovery workflows, a unified browser Author library with contextual
  create-and-link and cascade previews, read-only Play retrieval and search, bounded typed encounter/
  reference pins with legacy migration, and generated reference indexes and stable UUID-named sheets.
  The selective corpus audit retained Theron Eiral, the Sunseed, and the Salt Wardens, left two sampled
  adventures reference-light, and verified Author/Play retrieval, generated output, relocation, clean
  export, and archive preservation. The whole-application local GM cold-read is now complete; it found
  and corrected one tablet-width Author top-bar overflow without changing product semantics.

- Rebuilt and exercised the clean source wheel through an isolated installed lifecycle covering CLI,
  browser, archive, relocation, Unicode paths, recovery, and the installed desktop-launcher entry point.
  Native Linux, Windows, and macOS artifact builds remain explicit external evidence because the complete
  exact PyInstaller build lock was unavailable in this execution environment; the lock was not weakened.

- Recorded the remaining campaign-structure questions and working recommendations in an explicitly
  provisional design notebook. Persistent campaign entities should use campaign-owned stable identities
  and explicit bindings to adventure-local references rather than live merging. Campaign chronology
  should use a display-independent absolute coordinate to index encounter occurrences and external events
  and derive backlinks to persistent entities. Exact binding lifecycle, precision, and calendar-display
  choices remain fixture-backed campaign decisions; no campaign schema or runtime was adopted.

- Clarified the campaign clue scale boundary: a campaign clue may use an encounter-level source
  placement inside a campaign-owned adventure snapshot without becoming an ordinary encounter clue;
  source placement does not require a new revelation kind, and campaign consequences should use typed
  revelation effects.

- Documented the post-beta campaign graph initiative: adventures remain portable aggregates placed as
  campaign entries; campaign clues support campaign revelations that expose or unlock adventures;
  first-version import uses copy semantics; clean standalone export is mandatory; and campaign runtime
  remains layered above detailed adventure journals.

- Hardened native desktop reproducibility with an exact checked-in build dependency lock, pre-freeze environment verification, and manifest-recorded dependency and runner provenance.
- Established stable opaque identity for adventures and nested authored entities, independent of title
  changes and portable across workspace relocation.
- Routed ordinary CLI and browser mutations through revision-aware application/project boundaries and
  retained one canonical mutation path for each behavior.
- Made archive restoration non-destructive, canonicalized archive identity, and added crash-recoverable
  coordinated local-file transactions.
- Aligned runtime decoding with the published schemas: omitted known fields receive documented defaults,
  while unknown fields, invalid values, excessive nesting, oversized files, and excessive journals fail
  closed.
- Hardened the loopback browser boundary against Host ambiguity, DNS rebinding, malformed targets,
  unsafe paths, oversized forms and queries, CSRF misclassification, error disclosure, and unescaped
  rendered values.
- Defined deterministic workspace discovery, explicit initial selection, safe portable project names,
  fresh starter identity, and direct project-directory launch.
- Froze the private-beta compatibility surface around schema 3 adventures, schema 6 play journals,
  schema 1 workspace settings, the installed CLI, documented browser workflows, and the root/direct-
  child workspace layout.
- Added an enforced runtime-only wheel contract with a 2 MiB ceiling, clean installed CLI/browser
  lifecycle smoke, and CPython 3.11–3.13 platform jobs.
- Cleaned the tester-facing interface: clarified split-party and recording terminology, separated global
  and Table-local navigation, demoted the exceptional Recovery console, added journal-preserving
  improvisational authoring, repaired long-note responsive layout, and added a global Help/Introduction
  page with node-based preparation guidance, Justin Alexander resource links, and explicit independent-
  project attribution.
- Consolidated obsolete progress diaries and session reports into durable architecture, maintenance,
  corpus, release, and active-roadmap documentation.
- Added a thin desktop launcher that remembers a workspace outside the bundle, owns one ephemeral-port
  loopback server, reopens the ordinary browser UI, switches workspaces without accumulating servers, and
  shuts down cleanly.
- Added a native PyInstaller one-folder build pipeline, frozen-executable smoke, canonical-user-data
  exclusion, deterministic archive normalization, a 100 MiB compressed ceiling, strict SHA-256 and
  inventory manifests, Linux/Windows/macOS hosted build jobs, and an aggregate provenance and archive-
  safety verifier for the complete uploaded artifact set.
- Local deterministic verification remains separated from hosted and manual platform evidence; native
  hosted and real Windows, macOS, and Ubuntu interaction results remain unclaimed until executed.

### The Witch of Blackbriar Hall — Reference Voice III

- Repaired nine encounter/reference seams while preserving Saint Orra’s Gallows and the ten first-pass person records exactly.
- Recast nineteen second-pass reference boundaries in subject-native terms, preserved the complete 185-link order and every non-prose field, and kept the 200-event demonstration byte-identical.
- Regenerated the forty-six-document packet and advanced the corpus roadmap to Blackbriar Coherence III.

### The Witch of Blackbriar Hall — Reference Extraction II

- Closed the Blackbriar reference library at twenty-nine records and one hundred eighty-five ordered links.
- Added two recurring people, eight persistent sites, two organizations, three patrons, and four instruments while preserving the ten Session 01 records and seventy links as exact prefixes.
- Preserved the reference-free semantic adventure and the byte-identical 200-event demonstration; advanced the corpus roadmap to Blackbriar Voice III.

## 0.9.0 — First beta candidate

- Standardized setuptools/venv/pip packaging, embedded private-beta terms, and published the first clean
  offline-installable wheel.
- Defined the supported beta workspace layout and surfaced malformed projects instead of omitting them.
- Added branch-aware coverage, architecture/import contracts, dependency and security gates, and
  installed-wheel smoke across the supported operating-system matrix.
- Unified CLI authoring behind the revision-aware project boundary, made compound Play operations atomic
  by construction, and replaced concentrated projection/dispatch procedures with cohesive owners.

## 0.8.0 — Pre-beta encounter contract

- Replaced the former `node` vocabulary with `encounter` across schemas, Python, CLI, browser routes,
  assets, tests, generated documents, and bundled data.
- Advanced authored adventures to schema 3 and play journals to schema 5, intentionally retiring older
  pre-beta formats rather than publishing a permanent dual-format migration layer.

## 0.7.0 — Pre-beta API contraction and rendering ownership

- Retired broad package re-export barrels and obsolete compatibility modules.
- Moved callers to direct owner imports and completed the authoring-renderer ownership split.

## 0.6.0 — Adventure schema and GM-interface cleanup

- Added richer adventure metadata, encounter roles and openings, stable nested identity, revision-aware
  browser editing, workspace discovery/settings, appearance and draft recovery, graph interaction, and
  the browse-first adventure library.
- Migrated the bundled corpus, journals, archives, generated packets, and fixtures to the new contract.

## 0.5.2 — Named-party full playthrough

- Added a complete named-party demonstration journal and synchronized generated summary.

## 0.5.1 — Workflow-oriented README

- Reorganized the primary documentation around authoring, table use, validation, and archives.

## 0.5.0 — Journal archive lifecycle

- Added immutable journal archives with adventure snapshots, compatibility comparison, restore, and
  confirmed deletion.

## 0.4.3 — Adventure voice pass

- Revised bundled adventure prose for clarity, differentiation, and table utility.

## 0.4.2 — Complete long-form example

- Added the first complete long-form adventure with operating aids and demonstrated play.

## 0.4.1 — Repository cleanup

- Removed obsolete generated and migration residue and tightened repository hygiene.

## 0.4.0 — Safe authoring lifecycle

- Added dependency-aware editing/removal, coordinated journal safety, and stable authored identity.

## 0.3.0 — Structural diagnostics

- Added directed reachability, exact edge-connectivity diagnostics, limiting cuts, and repair candidates.

## 0.2.0 — Runtime semantics

- Added append-only play events, deterministic projections, reports, and correction behavior.

## 0.1.0 — Initial vertical slice

- Added the authored model, JSON persistence, validation, Markdown rendering, CLI, and initial example.
