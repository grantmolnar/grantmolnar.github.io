# Example encounter-name ledger

## Status

Finalized after the thirteen adventure-level reference extraction, voice, and coherence sequences. The ledger is rebuilt from the authoritative `examples/*/adventure.json` sources; the earlier seeded Markdown matched those sources exactly before the four accepted title-only deconflictions below.

- Adventures: **13**
- Encounter titles: **138**
- Exact cross-adventure duplicates: **0**
- Article-and-punctuation-insensitive duplicates: **0**
- Accepted title-only deconflictions: **4**
- Reviewed current near-match and practical-ambiguity candidates: **18**
- Unresolved candidates: **0**

No stable encounter ID or UUID changed. Generated filenames therefore retain their stable-ID slugs even where the public title changed. Historical journals, archives, handoffs, and completed editorial records retain the title current when they were created; current adventure sources, generated packets, and operating aids use the deconflicted title.

## Detection method

Titles are Unicode-folded, lowercased, stripped of punctuation, and compared both with and without leading articles. The automated review queue contains any cross-adventure pair with a normalized character-sequence ratio of at least **0.72**, or a ratio of at least **0.60** together with meaningful-token Jaccard overlap of at least **0.33**. Function words are excluded from token overlap. Shared distinctive phrases and practical table ambiguity are also reviewed manually, including stable-ID similarities that do not appear in public titles.

Similarity is a review flag, not a rename instruction. Generic location words and ordinary motifs remain available across the corpus when the complete titles are easy to distinguish in conversation, search, generated indexes, and play.

## Accepted title-only deconflictions

| Adventure | Stable encounter ID | Previous title | Current title | Reason |
|---|---|---|---|---|
| A Wedding for the River | `shrine-of-the-open-door` | The Shrine of the Open Door | The Doorless Shrine | The former title was practically interchangeable with Bramblewick's Chapel of the Open Door. The new title preserves the shrine's defining architecture and open-clause theme without changing its stable identity. |
| The Siege of the Stone Lung | `the-black-cisterns` | The Black Cisterns | The Cisterns of Black Breath | The former title was easily confused with Harrowgate's Black Rain Cistern. The new title names the trapped gas that governs entry, rescue, and diagnosis. |
| When the Swine Kneel | `the-hall-of-petitions` | The Hall of Petitions | The Hall of Condemnations | The former title was easily confused with the Glass Saint's House of Petitions. The new title identifies the livestock condemnation docket that creates the encounter's immediate public crisis. |
| The Concord of Aurelune | `the-white-hart-gallery` | The White Hart Gallery | The Gallery of Silver Kin | The former title shared the distinctive White Hart phrase with Cauldron's White Hart Court. The new title names the gallery's silver relation plaques and House Maelith's kinship politics. |

## Retained current candidates

| Adventure A | Encounter A | Adventure B | Encounter B | Sequence | Token overlap | Disposition | Reason |
|---|---|---|---|---:|---:|---|---|
| A Wedding for the River | The House of Open Measure | The Glass Saint | The House of Petitions | 0.72 | 0.25 | harmless generic overlap | House is generic; Open Measure and Petitions identify different institutions and table procedures. |
| The Bell Beneath Harrowgate | The Hall of Bent Knees | When the Swine Kneel | The Hall of Condemnations | 0.72 | 0.25 | harmless generic overlap | Hall is generic; Bent Knees and Condemnations are distinct in speech and search. |
| The Bell Beneath Harrowgate | The Lantern Cistern | The Forest That Carries Dawn | Lantern Canopy | 0.61 | 0.33 | deliberate motif | Lantern describes stored or routed light in both adventures, while cistern and canopy make the locations unambiguous. |
| The Bell Beneath Harrowgate | The Lantern Cistern | The Siege of the Stone Lung | The Lantern Court | 0.78 | 0.33 | harmless generic overlap | Lantern is a functional object in both titles; cistern and court separate hydraulic routing from civic command. |
| The Bell Beneath Harrowgate | The Inverted Chapel | The Glass Saint | The Bell Chapel | 0.71 | 0.33 | harmless generic overlap | Chapel is generic; the distinctive modifiers describe different ritual spaces. |
| The Cauldron of Nine Silences | The Chapel of the Last Word | When the Swine Kneel | The Chapel of the First Survey | 0.77 | 0.20 | harmless generic overlap | The opposed Last Word and First Survey epithets are memorable and point to unrelated institutions. |
| The Cauldron of Nine Silences | The Cauldron Vault | The Glass Saint | The Archive Vault | 0.63 | 0.33 | harmless generic overlap | Vault is generic; Cauldron and Archive identify different objects and functions. |
| The Cauldron of Nine Silences | The Reed Weir | The Princess on the Salt Road | The Reed Villages | 0.67 | 0.33 | deliberate motif | Reed is ordinary wetland material; weir and villages are distinct locations with different play functions. |
| The Concord of Aurelune | The Argent Canopy | The Forest That Carries Dawn | Lantern Canopy | 0.65 | 0.33 | harmless generic overlap | Canopy is a spatial form; Argent and Lantern remain clear adventure-native identifiers. |
| The Forest That Carries Dawn | Lantern Canopy | The Siege of the Stone Lung | The Lantern Court | 0.65 | 0.33 | deliberate motif | Lantern marks light-bearing structures, while canopy and court distinguish ecological transmission from military allocation. |
| The Glass Saint | The Shattered Gallery | The Siege of the Stone Lung | The Shattered Gate | 0.87 | 0.33 | harmless generic overlap | Shattered is a condition; gallery and gate identify a museum crime scene and a siege breach. |
| The Glass Saint | The Procession Court | The Siege of the Stone Lung | The Lantern Court | 0.65 | 0.33 | harmless generic overlap | Court is generic; Procession and Lantern identify different civic functions. |
| The March on Vossgard | The Ashen Gate | The Princess on the Salt Road | The Cypress Gate | 0.67 | 0.33 | harmless generic overlap | Gate is generic; Ashen and Cypress are distinct and remain easy to retrieve with their adventures. |
| The March on Vossgard | The Ashen Gate | The Siege of the Stone Lung | The Shattered Gate | 0.75 | 0.33 | harmless generic overlap | Gate is generic; Ashen and Shattered identify different military problems. |
| The March on Vossgard | The Tithe Villages | The Princess on the Salt Road | The Reed Villages | 0.80 | 0.33 | harmless generic overlap | Villages is generic; Tithe and Reed clearly separate requisition politics from channel transport. |
| The March on Vossgard | The Red Abbey | The Princess on the Salt Road | The Red Bridge | 0.74 | 0.33 | harmless generic overlap | Red is a common modifier; abbey and bridge are unmistakably different locations. |
| The Princess on the Salt Road | The Cypress Gate | The Siege of the Stone Lung | The Shattered Gate | 0.65 | 0.33 | harmless generic overlap | Gate is generic; Cypress and Shattered remain distinct in ordinary use. |
| The Bell Beneath Harrowgate | The Deep Bell | When the Swine Kneel | The Six-Line Bell | Manual | Manual | compatibility distinction | The public titles The Deep Bell and The Six-Line Bell are distinct. Their historically similar stable IDs are compatibility boundaries, not a user-facing naming collision. |

## Complete final ledger

| Adventure | Encounter title | Stable encounter ID |
|---|---|---|
| A Wedding for the River | The House of Open Measure | `house-of-open-measure` |
| A Wedding for the River | Vale Mill and Hearth | `vale-mill-and-hearth` |
| A Wedding for the River | The House Beneath the Willows | `house-beneath-the-willows` |
| A Wedding for the River | The Market of Seven Baskets | `market-of-seven-baskets` |
| A Wedding for the River | The Doorless Shrine | `shrine-of-the-open-door` |
| A Wedding for the River | The Reedwright's Yard | `reedwrights-yard` |
| A Wedding for the River | The Bridge of Three Tunes | `bridge-of-three-tunes` |
| A Wedding for the River | The Flood Meadow and Old Ford | `flood-meadow-and-old-ford` |
| A Wedding for the River | The Wedding Between the Banks | `wedding-between-the-banks` |
| The Bell Beneath Harrowgate | The Cracked Chapterhouse | `cracked-chapterhouse` |
| The Bell Beneath Harrowgate | The Quarry Cleft | `quarry-cleft` |
| The Bell Beneath Harrowgate | The Hall of Bent Knees | `hall-of-bent-knees` |
| The Bell Beneath Harrowgate | The Ropeworks of Three Burdens | `ropeworks-of-three-burdens` |
| The Bell Beneath Harrowgate | The Chain Scriptorium | `chain-scriptorium` |
| The Bell Beneath Harrowgate | The Lantern Cistern | `lantern-cistern` |
| The Bell Beneath Harrowgate | The Reliquary Under Water | `reliquary-under-water` |
| The Bell Beneath Harrowgate | The Salt Barracks | `salt-barracks` |
| The Bell Beneath Harrowgate | The Garden of Teeth | `garden-of-teeth` |
| The Bell Beneath Harrowgate | The Feast of Empty Chairs | `feast-of-empty-chairs` |
| The Bell Beneath Harrowgate | The Inverted Chapel | `inverted-chapel` |
| The Bell Beneath Harrowgate | The Menagerie of Quiet Beasts | `menagerie-of-quiet-beasts` |
| The Bell Beneath Harrowgate | The Counterweight Wells | `counterweight-wells` |
| The Bell Beneath Harrowgate | The King's Narrow Grave | `kings-narrow-grave` |
| The Bell Beneath Harrowgate | The Choir of Iron Tongues | `choir-of-iron-tongues` |
| The Bell Beneath Harrowgate | The Black Rain Cistern | `black-rain-cistern` |
| The Bell Beneath Harrowgate | The Deep Bell | `deep-bell` |
| The Bell Beneath Harrowgate | The Mouth Below | `mouth-below` |
| The Cauldron of Nine Silences | The Crooked Magpie | `crooked-magpie` |
| The Cauldron of Nine Silences | The White Hart Court | `white-hart-court` |
| The Cauldron of Nine Silences | The Smoke Kitchens | `smoke-kitchens` |
| The Cauldron of Nine Silences | The Rookwalk | `rookwalk` |
| The Cauldron of Nine Silences | The Chapel of the Last Word | `chapel-last-word` |
| The Cauldron of Nine Silences | The Widow's Solar | `widows-solar` |
| The Cauldron of Nine Silences | The Barrow Stair | `barrow-stair` |
| The Cauldron of Nine Silences | The House of Borrowed Voices | `house-borrowed-voices` |
| The Cauldron of Nine Silences | The Cauldron Vault | `cauldron-vault` |
| The Cauldron of Nine Silences | The Reed Weir | `reed-weir` |
| The Concord of Aurelune | The Argent Canopy | `the-argent-canopy` |
| The Concord of Aurelune | The Unfurling Branch | `the-unfurling-branch` |
| The Concord of Aurelune | The Gallery of Silver Kin | `the-white-hart-gallery` |
| The Concord of Aurelune | The Noon Spear Court | `the-noon-spear-court` |
| The Concord of Aurelune | The Red Rose Pavilion | `the-red-rose-pavilion` |
| The Concord of Aurelune | The Golden Sheaf Exchange | `the-golden-sheaf-exchange` |
| The Concord of Aurelune | The Amber Quill Archive | `the-amber-quill-archive` |
| The Concord of Aurelune | The Hall of First Frost | `the-hall-of-first-frost` |
| The Concord of Aurelune | The Silent Fir Lodge | `the-silent-fir-lodge` |
| The Concord of Aurelune | The Twilight Laurel Apartments | `the-twilight-laurel-apartments` |
| The Concord of Aurelune | The Ashen Bough Hearing | `the-ashen-bough-hearing` |
| The Concord of Aurelune | The Masque of Plain Faces | `the-masque-of-plain-faces` |
| The Concord of Aurelune | The Chamber of the Fourfold Petition | `the-chamber-of-the-fourfold-petition` |
| The Concord of Aurelune | The Crown Conclave | `the-crown-conclave` |
| The Forest That Carries Dawn | Camp Under New Leaves | `camp-under-new-leaves` |
| The Forest That Carries Dawn | Wagons in the Forked Roots | `wagons-in-the-forked-roots` |
| The Forest That Carries Dawn | Soilbearer Road | `soilbearer-road` |
| The Forest That Carries Dawn | Lantern Canopy | `lantern-canopy` |
| The Forest That Carries Dawn | Warm Rain Basins | `warm-rain-basins` |
| The Forest That Carries Dawn | Hollow of Kept Voices | `hollow-of-kept-voices` |
| The Forest That Carries Dawn | Blackgrass Burn | `blackgrass-burn` |
| The Forest That Carries Dawn | Root-Breath Chamber | `root-breath-chamber` |
| The Forest That Carries Dawn | Crown of Unfallen Rain | `crown-of-unfallen-rain` |
| The Forest That Carries Dawn | Glass Verge | `glass-verge` |
| The Glass Saint | The Shattered Gallery | `the-shattered-gallery` |
| The Glass Saint | The Procession Court | `the-procession-court` |
| The Glass Saint | The Archive Vault | `the-archive-vault` |
| The Glass Saint | The Trustees’ Chamber | `the-trustees-chamber` |
| The Glass Saint | The West Infirmary | `the-west-infirmary` |
| The Glass Saint | The House of Petitions | `the-house-of-petitions` |
| The Glass Saint | The Bell Chapel | `the-bell-chapel` |
| The Glass Saint | The Grand Belfry | `the-grand-belfry` |
| The Glass Saint | Vale Manor | `vale-manor` |
| The Last Bell of Bramblewick | Hearth Hall and the Map Room | `hearth-hall-and-the-map-room` |
| The Last Bell of Bramblewick | Merrit Alder's Burrow | `merrit-alder-s-burrow` |
| The Last Bell of Bramblewick | The Copper Kettle and Long Pantry | `the-copper-kettle-and-long-pantry` |
| The Last Bell of Bramblewick | Moss Apothecary | `moss-apothecary` |
| The Last Bell of Bramblewick | Alder Orchard | `alder-orchard` |
| The Last Bell of Bramblewick | Bramble Mill | `bramble-mill` |
| The Last Bell of Bramblewick | The Common Chest | `the-common-chest` |
| The Last Bell of Bramblewick | Chapel of the Open Door | `chapel-of-the-open-door` |
| The Last Bell of Bramblewick | Bramblewick School | `bramblewick-school` |
| The Last Bell of Bramblewick | The North Hedge | `the-north-hedge` |
| The Last Bell of Bramblewick | The First-Bell Moot | `the-first-bell-moot` |
| The Mandate of Seven Reeds | Hall of the Chrysanthemum Throne | `hall-of-the-chrysanthemum-throne` |
| The Mandate of Seven Reeds | Ministry of Divided Ink | `ministry-of-divided-ink` |
| The Mandate of Seven Reeds | Garden of White Gravel | `garden-of-white-gravel` |
| The Mandate of Seven Reeds | Hall of Open Roads | `hall-of-open-roads` |
| The Mandate of Seven Reeds | Pavilion of First Rain | `pavilion-of-first-rain` |
| The Mandate of Seven Reeds | Hall of Red Standards | `hall-of-red-standards` |
| The Mandate of Seven Reeds | Shrine of Listening Water | `shrine-of-listening-water` |
| The Mandate of Seven Reeds | Stone-and-Moss Court | `stone-and-moss-court` |
| The Mandate of Seven Reeds | Theater of a Thousand Sleeves | `theater-of-a-thousand-sleeves` |
| The Mandate of Seven Reeds | Courtyard of Bells | `courtyard-of-bells` |
| The Mandate of Seven Reeds | Hall of Joined Timbers | `hall-of-joined-timbers` |
| The Mandate of Seven Reeds | Guesthouse of the Bent Reed | `guesthouse-of-the-bent-reed` |
| The Mandate of Seven Reeds | Evening of the Chrysanthemum Moon | `evening-of-the-chrysanthemum-moon` |
| The Mandate of Seven Reeds | Chamber of Seven Reeds | `chamber-of-seven-reeds` |
| The Mandate of Seven Reeds | The Second Audience | `the-second-audience` |
| The March on Vossgard | The Ashen Gate | `the-ashen-gate` |
| The March on Vossgard | The Iron Causeway | `the-iron-causeway` |
| The March on Vossgard | The Tithe Villages | `the-tithe-villages` |
| The March on Vossgard | The Thorn Barrows | `the-thorn-barrows` |
| The March on Vossgard | The Red Abbey | `the-red-abbey` |
| The March on Vossgard | The Black Bell Redoubt | `the-black-bell-redoubt` |
| The March on Vossgard | The Drowned Sluice | `the-drowned-sluice` |
| The March on Vossgard | Vossgard | `vossgard` |
| The Princess on the Salt Road | The House of Blue Lamps | `house-of-blue-lamps` |
| The Princess on the Salt Road | The Gate of Horns | `gate-of-horns` |
| The Princess on the Salt Road | The Dry Aqueduct | `dry-aqueduct` |
| The Princess on the Salt Road | The Cypress Gate | `cypress-gate` |
| The Princess on the Salt Road | The House at Three Cypresses | `house-at-three-cypresses` |
| The Princess on the Salt Road | The Red Bridge | `red-bridge` |
| The Princess on the Salt Road | The Reed Villages | `reed-villages` |
| The Princess on the Salt Road | The Beacon Hill | `beacon-hill` |
| The Princess on the Salt Road | Myrine Harbor | `myrine-harbor` |
| The Siege of the Stone Lung | The Lantern Court | `the-lantern-court` |
| The Siege of the Stone Lung | The Shattered Gate | `the-shattered-gate` |
| The Siege of the Stone Lung | The Cinder Foundry | `the-cinder-foundry` |
| The Siege of the Stone Lung | The Pale Gardens | `the-pale-gardens` |
| The Siege of the Stone Lung | The Refuge Galleries | `the-refuge-galleries` |
| The Siege of the Stone Lung | The Cisterns of Black Breath | `the-black-cisterns` |
| The Siege of the Stone Lung | The Countermine | `the-countermine` |
| The Siege of the Stone Lung | The Stone Lung | `the-stone-lung` |
| The Witch of Blackbriar Hall | Saint Orra's Gallows | `saint-orra-gallows` |
| The Witch of Blackbriar Hall | Sedge Croft | `sedge-croft` |
| The Witch of Blackbriar Hall | Saint Mercy House | `saint-mercy-house` |
| The Witch of Blackbriar Hall | Blackbriar Hall | `blackbriar-hall` |
| The Witch of Blackbriar Hall | The Burned Refuge | `burned-refuge` |
| The Witch of Blackbriar Hall | The White Pits | `white-pits` |
| The Witch of Blackbriar Hall | Chapel of the Free Witness | `chapel-of-the-free-witness` |
| The Witch of Blackbriar Hall | Moonless Mere | `moonless-mere` |
| The Witch of Blackbriar Hall | Crow Wood | `crow-wood` |
| The Witch of Blackbriar Hall | Underhall of the Hollow Feast | `underhall-of-the-hollow-feast` |
| When the Swine Kneel | The Hall of Condemnations | `the-hall-of-petitions` |
| When the Swine Kneel | Southgate Stockyards | `southgate-stockyards` |
| When the Swine Kneel | The College of Civic Measure | `the-college-of-civic-measure` |
| When the Swine Kneel | Rillcross Farm Belt | `rillcross-farm-belt` |
| When the Swine Kneel | The Chapel of the First Survey | `the-chapel-of-the-first-survey` |
| When the Swine Kneel | The Nine-Mile Pump House | `the-nine-mile-pump-house` |
| When the Swine Kneel | The Six-Line Bell | `the-deep-bell` |
