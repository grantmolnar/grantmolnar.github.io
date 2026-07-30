# Publication and Commercialization Strategy

## Status and purpose

This is a standing strategy note, not a launch plan and not legal advice. Publication is not an
immediate project objective. Adventure Graph should not be shipped merely because its current
features can be packaged and sold.

The project should first become a product we would trust with a long campaign, a body of adventures
we would be proud to publish, and a tool that has survived sustained use by GMs who were not involved
in its design. Commercial decisions should follow evidence from that work rather than dictate the
next development tranche.

This document records the current product thesis, legal and intellectual-property concerns,
architectural consequences of multi-system and campaign support, possible business models,
discovery strategy, readiness gates, and unresolved decisions. Storefront rules, game-system
licenses, and copyright guidance can change; the references at the end are a dated snapshot and must
be re-audited before publication.

## Long-term product thesis

Adventure Graph is potentially two connected products:

1. **A GM workbench** for designing, validating, revising, and running nonlinear adventures and
   campaigns.
2. **A first-party adventure line** containing polished, ready-to-run material that takes full
   advantage of that workbench.

The two sides strengthen one another. The authored adventures demonstrate what the software is for,
exercise its abstractions, and give running GMs an immediate reason to use it. The software gives the
adventures a distinctive table experience and creates a path from customer to author.

The product should not be described primarily as graph-editing software. Its practical promise is
closer to:

> Design robust, nonlinear adventures and run them without losing track of where the party went,
> what they discovered, what they concluded, or what remains unresolved.

The current dual audience is therefore:

- **running GMs**, who want trustworthy adventures and a low-friction table interface; and
- **designing GMs and publishers**, who want structural assistance without surrendering authorship
  or being forced into one rules system.

A later creator marketplace is possible, but it is not part of the initial thesis. First-party
content and a small number of deliberate publishing partnerships should precede any open marketplace.
A marketplace would add moderation, infringement procedures, revenue accounting, tax and payout
work, support expectations, fraud, and quality-control obligations that are largely independent of
making the core product good.

## Product maturity before publication

Publication should wait until four bodies of work are substantially beyond minimum viability.

### Adventure authoring

The authoring side should support the complete lifecycle of a serious adventure:

- initial structure and prose development;
- clue, revelation, reachability, and resilience review;
- optional and necessary material;
- system-neutral narrative material plus system-specific overlays;
- maps, handouts, images, and other media;
- reusable templates and defaults;
- deliberate revision after play;
- migration and compatibility across file-format changes;
- strong import, export, backup, and recovery; and
- documentation that teaches design judgment rather than merely describing fields.

The validator should remain advisory. Its defaults may encode a strong house standard, but the
software should not imply that every good adventure has one graph shape, one clue density, or one
style of play.

### Adventure play

The Play workspace should be proven under actual table pressure. The current implementation covers
the central single-adventure workflow, but commercial maturity requires repeated use across long,
messy sessions, including:

- revisits and skipped material;
- split parties;
- clues missed and later recovered;
- revelations established for unexpected reasons;
- improvisational encounters created during play;
- abandoned or foreclosed lines;
- interruptions, crashes, and stale browser sessions;
- sessions spanning several devices or operating systems;
- correction after mistakes; and
- useful post-session review without clerical cleanup.

The interface should make ordinary use obvious to a GM who has never read the architecture
documentation. Recovery paths may remain more technical, but the primary workflow should not expose
Python, Poetry, WSGI, raw JSON, revision hashes, or repository structure.

### Campaign support

A campaign is not merely a very large adventure. Campaign support will probably require a layer
above individual adventure files, with its own semantics and persistence boundaries.

Candidate campaign concepts include:

- a campaign containing multiple adventures or scenario arcs;
- campaign-wide encounters, revelations, factions, people, places, and assets;
- shared clues and long-horizon revelations spanning several adventures;
- a campaign calendar and durable world state;
- consequences that affect later adventures;
- party and character rosters without becoming a character builder;
- reusable NPCs and locations with adventure-local views;
- campaign-wide session and narrative histories;
- active, dormant, completed, and abandoned arcs;
- importing a revised adventure without falsifying campaign history;
- promoting improvised play material into authored campaign material; and
- campaign-level reports, recaps, and preparation queues.

These concepts should not be added speculatively. They should be derived from running several
adventures in one continuing campaign and recording where the current single-adventure model breaks.
The campaign layer should coordinate adventures rather than dissolve their boundaries.

### Adventure catalog

The project needs a deeper well of adventures before launch. The catalog should demonstrate that the
model is useful beyond one mystery structure or one fantasy idiom. It should include adventures that
vary along several axes:

- mysteries, political negotiations, military operations, sieges, expeditions, horror, and social
  campaigns;
- compact one- or two-session scenarios and longer arcs;
- sparse and dense graph structures;
- conventional clues, social leverage, logistical opportunities, factional commitments, and other
  revelation-like structures;
- different degrees of player freedom and GM improvisation; and
- multiple rules-system treatments of at least some common narrative cores.

Every commercial adventure should receive a substantial human editorial pass, independent playtests,
clear maps or diagrams where useful, usable handouts, and system-appropriate mechanical review. The
catalog should be deep enough that a customer sees a continuing line rather than a technology demo
with one attached scenario.

## System neutrality and mechanical overlays

The core engine should remain system-agnostic even as adventures become system-tagged and receive
stronger mechanical support.

The preferred model is one narrative adventure with zero or more **system overlays**. The canonical
narrative layer would contain:

- encounters, revelations, clues, prose, relationships, and consequences;
- system-neutral difficulty and intent descriptions;
- encounter purposes and failure consequences;
- creature or NPC roles in the fiction;
- broad content and tone tags; and
- media and table aids.

A system overlay would contain only the material needed to run that narrative in a particular rules
system, such as:

- stat blocks or references;
- checks, target numbers, and degrees of success;
- encounter budgets and tactical assumptions;
- conditions, damage, spells, and equipment;
- system-specific handouts or character options;
- rulebook and license attribution; and
- compatibility metadata.

This separation has several advantages:

- one edited narrative can support several systems;
- system-specific intellectual property does not leak into the engine or unrelated exports;
- mechanical reviewers can work independently of narrative editors;
- customers can select the systems they use;
- unsupported systems can still receive a useful system-neutral edition; and
- changes to one rules system do not require rewriting the adventure's core identity.

System overlays must not become a lowest-common-denominator abstraction that erases meaningful
mechanical differences. A Call of Cthulhu treatment of an adventure should not merely replace armor
classes with percentages; it may need different clue procedures, failure expectations, pacing,
combat assumptions, sanity pressures, and player information. The shared narrative core is a source,
not a promise that every conversion will be mechanically isomorphic.

Each supported system should have a maintained licensing and provenance record covering:

- the legal basis for using its rules content;
- permitted and prohibited setting material;
- trademark and compatibility-language rules;
- required notices and attribution;
- whether commercial software support requires a separate license;
- marketplace exclusivity or reuse restrictions;
- current AI-content policies;
- sourcebook versions and errata used; and
- the reviewer responsible for the mechanical adaptation.

Rights available for one system must never be inferred for another. D&D material available in an
SRD, Pathfinder rules made available under the ORC ecosystem, and Call of Cthulhu material available
through a commercial license or community-content program are legally different routes. A setting
such as Rokugan should be treated as unavailable for commercial use unless an applicable license or
specific permission has been identified and reviewed. A generic samurai-court or mythic-horror
adaptation can be offered without claiming another publisher's setting identity.

## Intellectual-property and provenance posture

### Justin Alexander and encounter-based design

Adventure Graph was built specifically to facilitate a style of GMing learned in substantial part
from Justin Alexander's writing on the Three Clue Rule, revelation lists, node-based scenario design,
and node-based campaigns. That intellectual ancestry should be acknowledged openly.

The current legal concern is limited. Copyright does not protect a game idea, procedure, system, or
method of play, although it can protect the particular prose, examples, diagrams, and artwork used to
explain that method. Adventure Graph may independently implement clue redundancy, revelation lists,
and encounter relationships. It should not copy or closely paraphrase Alexander's articles, reproduce his
diagrams or examples, or imply endorsement.

The product should normally call the feature **clue redundancy validation**, with a configurable
default that can implement the Three Clue Rule. Documentation can identify the source of the design
tradition. A possible acknowledgment is:

> Adventure Graph was inspired in substantial part by Justin Alexander's writing on the Three Clue
> Rule, revelation lists, and node-based scenario design. Adventure Graph is an independent product
> and is not affiliated with or endorsed by Justin Alexander or The Alexandrian.

Before public launch, it would be courteous and strategically valuable to contact Alexander with a
polished demonstration and the proposed acknowledgment. Any review quote, endorsement, affiliate
relationship, or co-promotion would require clear written permission. A positive relationship could
also provide unusually relevant discovery, but outreach should occur only after the product is good
enough to respect his time and reputation.

### Vibe-coded software and AI-assisted adventures

AI assistance does not by itself prevent publication. The practical obligations are to establish a
clean chain of title, understand the limits of copyright in unedited machine-generated expression,
avoid importing third-party material, and ship software that can actually be maintained.

The project should preserve:

- the original user-created template and its provenance;
- repository history and major architectural decisions;
- records of external code, assets, and snippets, if any;
- human revisions to adventure prose and documentation;
- licenses for fonts, art, maps, icons, and other media;
- contributor and contractor assignments; and
- a `THIRD_PARTY_NOTICES` file when distributable dependencies or assets require one.

Commercial adventures should receive extensive human editing before release. That work is important
both for quality and for establishing human creative authorship in the final expression. Storefront
AI-disclosure rules and publisher policies should be checked again at submission time; they differ
by venue and may change.

### Game-system and setting IP

The engine, schemas, default terminology, sample content, and marketing should avoid dependence on a
single publisher's brand. In particular:

- prefer **GM** to trademark-sensitive branded role names in product identity;
- do not use official logos, trade dress, setting names, characters, or art without permission;
- keep a source-and-attribution record for every system-derived mechanic or term;
- separate open rules content from closed setting content;
- provide required license notices with the relevant overlay or product; and
- review community-content agreements carefully, because some require platform exclusivity or limit
  reuse outside the program.

An adventure intended for several systems should begin as original setting and narrative material.
System-branded editions should be derived overlays, not the only canonical form of the adventure.

### User-created adventures

The eventual software license should state clearly that users own the adventures they create. A paid
or commercial authoring tier should expressly permit users to export, publish, and monetize their own
work. Adventure Graph should receive no ownership interest in authored content merely because the
software was used to create it.

A standard first-party adventure license should likely allow private play, table copies, ordinary
modification for personal use, actual-play streaming, and use by paid professional GMs, while
prohibiting redistribution or resale of the adventure files and text. These terms need legal review
before money changes hands.

## Business architecture

The most promising provisional model remains:

1. **Runner**: free or inexpensive access to Play mode and purchased or shared adventures.
2. **Studio**: a paid authoring and validation product, including commercial use of exported work.
3. **Adventure packs**: paid first-party content, including system-neutral material and selected
   mechanical overlays.
4. **Campaign products**: later bundles or long-form lines once campaign support is mature.

This is not a final pricing or packaging decision. Its central advantage is that an adventure buyer
does not need to purchase an expensive editor before using the content. A broad Runner install base
also makes the native adventure format more useful.

First-party adventures should come before an open creator marketplace. A small invited publisher
program may be appropriate once the format, licensing model, quality standard, and customer support
burden are known. Marketplace infrastructure should be considered only after third parties are
already asking to publish and the project has evidence that customers want to buy their work.

Subscription should not be assumed. A local-first GM tool and downloadable adventures fit one-time
software and content purchases naturally. A subscription might become defensible only if it funds a
continuous service customers actually value, such as synchronized multi-device campaigns, hosted
libraries, collaboration, or a substantial recurring content program.

## Discovery and distribution

Discovery is a first-order product requirement. A technically convenient storefront with no
relevant audience is not a sufficient launch venue, and no marketplace algorithm should be expected
to create demand from nothing.

The eventual distribution strategy should be multi-channel, with each venue serving a different
purpose.

### Steam

Steam is a plausible primary home for the packaged application. Steam accepts some non-game software
under categories including Player Tools, and provides application updates, demos or playtests, DLC,
bundles, reviews, community pages, tags, and recommendation surfaces.

A possible Steam structure is a Runner or full base application, a Studio upgrade, and adventure
packs as DLC. This maps well to the dual audience, but Steam visibility is driven by customer
interest and accurate tags rather than by mere presence on the store. Steam should amplify a launch
that already has an audience, proof, and compelling media; it should not be the only discovery plan.

Steam becomes appropriate after the application has a signed consumer installer, polished onboarding,
a strong trailer, reliable updates and support, several excellent adventures, and enough external
interest to produce wishlists, reviews, and meaningful early usage.

### DriveThruRPG

DriveThruRPG is a natural discovery venue for adventures because its audience is already shopping for
tabletop material. Its publishing-partner route is intended for creators selling their own titles and
provides control over listings, prices, and sales.

A first-party product there could contain:

- a polished PDF or printable edition;
- the native Adventure Graph package;
- maps and handouts;
- a clear statement that the free Runner can open the native package; and
- one or more legally reviewed system overlays.

Community-content programs for specific game lines are separate from ordinary independent publishing
and may impose exclusivity or reuse restrictions. They may be useful for deliberately system-specific
products, but they should not absorb the canonical original-IP edition of a flagship adventure.

### Foundry VTT and other virtual tabletops

Foundry's premium-content ecosystem is a strong integration and discovery opportunity because it
concentrates digitally engaged GMs and supports preconfigured adventures and publisher packages.
Adventure Graph should not try to replace a virtual tabletop. A companion or export integration could
let:

- Foundry handle maps, tokens, tactical encounters, sheets, and player display; and
- Adventure Graph handle scenario structure, clues, revelations, navigation, preparation, and
  campaign history.

A similar principle can guide later Roll20 or other VTT integrations. Each integration has a
maintenance cost and should follow demonstrated customer demand.

### itch.io and direct distribution

itch.io is useful for early builds, founder editions, direct bundles, download keys, and rapid
iteration. It offers search and browse surfaces, but its audience is broad and its discovery value is
less concentrated than a tabletop-specific marketplace. It is best treated as a flexible beta and
direct-sales channel rather than the sole commercial home.

The project should also build assets no storefront controls:

- a distinctive website and documentation site;
- an email list;
- public development notes and demonstrations;
- actual-play recordings showing the product at a real table;
- relationships with reviewers, adventure designers, and GM educators;
- convention and online-playtest presence; and
- a free, excellent sample adventure that demonstrates the complete workflow.

The most effective marketing artifact is likely not a feature list. It is a short demonstration in
which a GM opens an adventure, enters an encounter, records a discovery, sees a revelation become supported,
takes notes, transitions, and produces a useful recap.

## Readiness gates

Publication should be considered only after evidence satisfies gates like the following. These are
conditions, not a calendar.

### Gate 1: sustained internal use

- Complete the current GM cold read.
- Run several full adventures through Play mode.
- Run more than one adventure in a continuing campaign.
- Record friction and missing concepts before adding campaign abstractions.

### Gate 2: external field testing

- Recruit GMs who did not help design the application.
- Observe real sessions rather than relying only on surveys.
- Include technical and nontechnical users.
- Include different preparation styles and game systems.
- Confirm that users can recover from mistakes without developer assistance.

### Gate 3: product depth

- Author and Play workflows are beyond MVP quality.
- Campaign support has a coherent, tested boundary.
- Media, packaging, import, export, backup, and migration are dependable.
- Consumer use does not require a development environment or terminal.

### Gate 4: content depth

- A substantial catalog covers several structures and genres.
- At least some adventures have genuinely reviewed multi-system editions.
- Every release candidate has human editing, playtests, maps or aids where needed, and mechanical
  review.
- The free sample is representative of the paid line rather than a stripped-down toy.

### Gate 5: legal and provenance readiness

- The project name and marks receive a professional clearance search.
- The software and adventure licenses are drafted and reviewed.
- All contributors and commissioned creators have written rights agreements.
- Every system overlay has a current licensing record and required notices.
- Third-party assets and dependencies have documented commercial rights.
- AI-assisted material has been substantially reviewed and disclosed where required.

### Gate 6: commercial operations

- Signed installers and update channels exist for supported platforms.
- Crash reporting or support diagnostics are privacy-conscious and usable.
- Customer support, refunds, backups, and migration promises are defined.
- Store pages, screenshots, trailer, documentation, and onboarding are polished.
- The launch has an audience plan outside the storefront itself.

## Principal risks

### The audience may be real but narrow

Many GMs do not prepare in explicit clue-and-revelation graphs, and some who do will prefer paper,
Obsidian, generic graph software, or a VTT. The product must prove that its integrated running and
history workflow saves enough effort to justify a dedicated tool.

### Multi-system support may multiply work

Every supported system adds design, legal, testing, documentation, and maintenance obligations.
System overlays and shared narrative sources reduce duplication, but they do not eliminate the need
for expert adaptation. It may be better to support a few systems deeply than many systems nominally.

### Content production may dominate software development

High-quality adventures require writing, editing, maps, layout, mechanics, playtesting, and art. The
catalog may become the largest ongoing cost. This is not necessarily a weakness: the content line may
also create the strongest recurring demand and the clearest differentiation.

### Campaign features can dissolve the product's focus

Campaign management is an enormous category. Character builders, encounter trackers, calendars,
wikis, VTTs, and campaign journals already exist. Adventure Graph should extend its structural model
where campaigns expose genuine needs, not become a generic all-purpose GM database.

### AI provenance may create customer or platform resistance

Even where AI-assisted code or prose is legally distributable, some customers, artists, publishers,
or storefronts may reject it. Human editing, commissioned art, transparent disclosure, and an
accurate provenance record are both ethical and practical safeguards.

### Discovery may fragment the product

Steam, DriveThruRPG, Foundry, itch.io, and system-specific community programs each create different
packages, policies, metadata, and customer expectations. The canonical adventure package and build
pipeline should generate channel-specific products rather than allowing each channel to become a
separate source of truth.

### Support and compatibility can become the hidden product

A local-first application earns trust only if users can keep years of authored and played material
safe. Backward migration, backups, export, readable formats, and clear support promises are core
commercial features, not release polish.

## Standing decisions

The following are the current provisional decisions unless later evidence overturns them:

- Publication is not the next project phase.
- The engine remains system-neutral.
- System mechanics live in explicit overlays rather than the core narrative model.
- Original-IP editions are canonical; branded editions are derived and separately licensed.
- Campaign concepts will be derived from actual continuing play before they are formalized.
- First-party adventures precede an open creator marketplace.
- Users retain ownership and commercial rights in adventures they create.
- Justin Alexander's influence will be acknowledged without implying affiliation.
- Commercial adventures receive substantial human editorial and playtest passes.
- Discovery requires several coordinated channels and an audience outside any storefront.
- Steam is a plausible eventual application venue, not an immediate destination or complete marketing
  strategy.
- DriveThruRPG is a plausible primary discovery venue for adventure products.
- VTT integrations should complement rather than replace Adventure Graph.

## Open questions

These should remain visible rather than being answered prematurely:

- What is the smallest coherent campaign model demonstrated by real play?
- Which two or three systems should receive the first deep mechanical overlays?
- Should system overlays be bundled with an adventure, sold separately, or both?
- How much system-neutral mechanical guidance is useful before it becomes vague?
- What media model is needed for maps, portraits, handouts, and player-safe assets?
- What is the durable consumer brand, and is `Adventure Graph` distinctive enough?
- Is Runner genuinely separate from Studio, or should there be one application with capability tiers?
- Which features belong in the free product so shared adventures remain easy to run?
- Should the native file format be publicly documented for third-party tooling before a publisher
  program exists?
- What forms of collaboration or cloud synchronization, if any, justify an ongoing service?
- How should published adventures receive errata without disturbing active campaign history?
- What level of Foundry or other VTT integration produces real value without duplicating their role?
- What evidence would justify a creator marketplace?
- What support burden can one small publisher responsibly promise?

## Reference snapshot

The following references informed this note as of July 15, 2026. They are starting points, not a
substitute for counsel or for reviewing the exact agreement in effect at publication time.

### Copyright, methods, and AI authorship

- U.S. Copyright Office, [Games](https://www.copyright.gov/register/tx-games.html)
- U.S. Copyright Office,
  [Copyright and Artificial Intelligence](https://www.copyright.gov/ai/)
- U.S. Copyright Office,
  [Part 2: Copyrightability](https://www.copyright.gov/ai/Copyright-and-Artificial-Intelligence-Part-2-Copyrightability-Report.pdf)

### Encounter-based design

- Justin Alexander,
  [The Three Clue Rule](https://thealexandrian.net/wordpress/1118/roleplaying-games/three-clue-rule)
- Justin Alexander,
  [Node-Based Scenario Design](https://thealexandrian.net/wordpress/7949/roleplaying-games/node-based-scenario-design-part-1-the-plotted-approach)
- Justin Alexander,
  [*So You Want to Be a Game Master*](https://thealexandrian.net/so-you-want-to-be-a-game-master)
- Justin Alexander,
  [The Secret Life of Nodes: Node-Based Campaigns](https://thealexandrian.net/wordpress/45268/roleplaying-games/the-secret-life-of-nodes-part-2-node-based-campaigns)

### Rules-system licensing examples

- Wizards of the Coast,
  [System Reference Document 5.2.1](https://www.dndbeyond.com/srd)
- Paizo,
  [Licenses](https://paizo.com/licenses)
- Paizo,
  [ORC License](https://paizo.com/orclicense)
- Chaosium,
  [Fan-Use and Licensing Q&A](https://www.chaosium.com/fan-use-and-licensing-q-a/)
- Chaosium,
  [Miskatonic Repository](https://www.chaosium.com/miskatonic-repository/)

### Distribution and discovery

- Steamworks,
  [Steamworks Partner Program](https://partner.steamgames.com/steamdirect)
- Steamworks,
  [Visibility on Steam](https://partner.steamgames.com/doc/marketing/visibility)
- Steamworks,
  [Steam Tags](https://partner.steamgames.com/doc/store/tags)
- DriveThruRPG,
  [Partner Inquiries](https://help.drivethrurpg.com/hc/en-us/articles/12723254805527-Partner-Inquiries)
- DriveThruRPG,
  [How to Create and Sell a PDF](https://help.drivethrurpg.com/hc/en-us/articles/33395033102615-How-to-Create-and-Sell-a-PDF)
- Foundry VTT,
  [Premium Content](https://foundryvtt.com/article/premium-content/)
- Foundry VTT,
  [Publisher Handbook](https://foundryvtt.com/article/publisher-handbook/)
- itch.io,
  [Content Creator Quality Guidelines](https://itch.io/docs/creators/quality-guidelines)
- itch.io,
  [Getting Indexed on Search and Browse](https://itch.io/docs/creators/getting-indexed)
