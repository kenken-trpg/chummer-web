/** 作成の流れ: プライオリティ・能力値・技能・資質・設定 — English。 */
export const EN_CHARGEN = {
  "engine.life.ratingCap":
    "Module grants raise “{name}” to {rating}, above its cap of {cap}. Excess-rating compensation is not yet supported; this combination is unavailable.",

  "engine.life.skillGrantInvalid": "Cannot resolve the life-module skill grant: {name}.",
  "engine.life.skillExcessLost":
    "The grant to {name} exceeds the cap; {lost} levels are not granted ({stage}).",
  "engine.life.transferPending": "Assign the overflow from {name} ({remaining} levels remaining).",
  "engine.life.transferOrphan":
    "Transfer {transfer} no longer has an overflow source. Remove or repair it.",
  "engine.life.transferInvalidTarget":
    "The destination of transfer {transfer} does not meet the requirements.",
  "engine.life.transferSourceChanged": "The grant to {name} changed. Update its transfer choices.",
  "engine.life.transferOverallocated":
    "Transfers from {name} request {requested} levels, exceeding the {total} available.",
  "engine.life.transferDuplicate": "Transfer {transfer} duplicates an ID or destination.",
  "engine.life.transferCapacity":
    "{name} can receive {capacity} levels, but {requested} were requested.",
  "engine.life.transferUnallocatable":
    "{lost} overflow levels from {name} cannot be assigned because eligible skills have no capacity.",

  "engine.life.purchaseInvalid": "Invalid skill purchase: {name}.",
  "engine.life.purchaseCap":
    "The requested rating {requested} for {name} exceeds the cap {cap}. Update the purchase.",
  "engine.life.groupPurchaseUnequal":
    "The free ratings in {group} differ. Purchase its skills individually.",

  "life.transfer.title": "Overflow from {name}",
  "life.transfer.source":
    "Before {before} + grant {grant} (kept {kept}). Transfer {total} levels; {remaining} remaining.",
  "life.transfer.provisional": "Earlier unresolved history choices may change this overflow.",
  "life.transfer.invalid":
    "This allocation contains invalid choices. Remove and replace the affected transfers.",
  "life.transfer.lost":
    "{count} levels cannot be granted because eligible skills have no capacity.",
  "life.transfer.unknown": "Unknown skill",
  "life.transfer.remove": "Remove transfer",
  "engine.life.policyInvalid": "Life-module creation skill caps must be integers from 1 to 1000.",
  "life.transfer.target": "Destination skill",
  "life.transfer.knowledgeTarget": "Destination knowledge or language skill",
  "life.transfer.knowledgeCategory": "Knowledge category",
  "life.transfer.specific": "Specific skill target",
  "life.transfer.ranks": "Levels to transfer",
  "life.transfer.add": "Add transfer",
  "life.transfer.failed": "Could not save. Check the input and retry.",
  "life.transfer.caps": "Module caps: active skills {active}; knowledge skills {knowledge}.",
  "life.transfer.capsLabel": "Module caps",
  "life.transfer.orphan": "A transfer of {ranks} levels has no matching acquisition or overflow.",
  "life.transfer.loss": "{count} levels of {name} are not granted because of the cap.",
  "life.moveEarlier": "Earlier in this stage",
  "life.moveLater": "Later in this stage",
  "life.freeSkill": "Module grant: {count}",
  "life.groupUnequal": "Unequal module grants prevent a group purchase.",
  "life.groupConvert": "Convert to individual purchases",

  "engine.life.snapshotRequired":
    "The life-module creation skill snapshot is missing or inconsistent. Review creation before entering career mode.",
  "engine.life.careerFrozen":
    "Creation history, transfers and purchase inputs are frozen. Use skill advancement to grow skills.",
  "engine.life.advancementInvalid":
    "Skill advancement has inconsistent starting ratings, caps, requirements or history. Undo from the last advancement to repair it.",
  "engine.life.creationIncomplete":
    "Resolve creation errors and unassigned skill overflow before entering career mode.",
  "engine.life.skillGrowthLine": "Skill advancement +{levels} levels",
  "engine.life.legacyCareer":
    "This career uses legacy life-module calculations. Review it in creation mode to migrate to the new rules.",

  "life.growth.title": "Career skill advancement",
  "life.growth.note":
    "Creation grants, transfers and purchases are frozen. Buy advancement from the current rating. The purchase controls below show creation inputs.",
  "life.growth.kind": "Advancement type",
  "life.growth.target": "Skill or group to advance",
  "life.growth.levels": "Levels to add",
  "life.growth.add": "Buy advancement",
  "life.growth.undo": "Undo last skill advancement",

  "life.kind.attributes": "attribute",
  "life.kind.skills": "skill",
  "life.kind.skill_groups": "skill group",
  "life.kind.knowledge_skills": "knowledge skill",
  "life.kind.knowledge_categories": "knowledge category",
  "life.kind.specializations": "specialization",
  "life.kind.qualities": "quality",

  "life.experimental":
    "Experimental support. A module is unavailable only if it uses mechanics this app does not support yet. Characters saved in Chummer import as career snapshots, because Chummer does not keep the module choices.",
  "engine.life.chum5StateInvalid":
    "The life-module state and standard skill values in this .chum5 disagree, or its format is unsupported. Restore a JSON backup.",
  "engine.life.chum5Unsupported":
    "This character uses the LifeModule method but has no module records or saved choices. Restore the original .chum5 or a JSON backup.",
  "engine.life.chum5Snapshot":
    "Imported the Chummer resave as a career snapshot, preserving saved skill and attribute ratings. Module choices and overflow transfer history cannot be recovered. The modules remain as provenance, and new growth is priced from this saved state.",
  "engine.export.chum5LifeModuleSetup":
    "Life modules export as a ZIP containing the character, matching settings XML and instructions. Close Chummer, copy the settings XML into its settings directory, then enable Life Modules in global options. Desktop resaves discard module choices and overflow transfer history and cannot be re-imported. Keep a JSON backup.",
  "engine.life.chum5ModuleUnknown":
    "The module “{name}” in this .chum5 is not in this app’s data. Dropping one module would shift every later module’s choices onto the wrong module, so the import stopped.",

  "life.method": "Life modules",
  "life.note":
    "Choose a history for each stage. Further education and real life can repeat. Attribute and skill inputs are purchased ratings; module grants are added to the computed results.",
  "life.total": "Module karma: {karma}",
  "life.totalLabel": "Module karma",
  "life.nuyen": "Module bonus funds: ¥{amount}",
  "life.freeQuality": "Free quality points: Positive {positive} / Negative {negative}",
  "life.pick": "Choose a module",
  "life.candidates": "Module candidates",
  "life.browseHint":
    "Select a candidate to review its details. Your history changes only when you press Add.",
  "life.previewHint": "Select a candidate to review its description, cost, and requirements.",
  "life.unavailable": "Cannot add (see details)",
  "life.choiceCount": "Choices to complete after adding: {count}",
  "life.stageFull": "This stage already has a module. Remove it first if you want to change it.",
  "life.add": "Add this module",
  "life.description": "Module description",
  "life.stageSelected": "Selected",
  "life.stagePending": "Not selected",
  "life.repeatable":
    "You can choose different modules for this stage. Each module, including its versions, can only be taken once.",
  "life.search": "Search modules (name, parent, description, source)",
  "life.noMatches": "No modules match your search. Try another search term.",
  "life.requires": "Requires: {requirements}",
  "life.requirementUnmet": "Requirements are not met",
  "life.remove": "Remove this module",
  "life.choice": "{name}: choose {kind}",
  "life.pending": "Choose an option",
  "life.unsupported": "Unavailable: contains unsupported effects",
  "life.empty": "No modules for this stage. Check the enabled rulebooks.",
  "engine.life.unknown": "Unknown life module: {name}",
  "engine.life.unsupported": "Life module “{name}” has unsupported mechanics: {tags}",
  "engine.life.duplicateModule":
    "Life module {name} can only be taken once, including its versions",
  "life.alreadyTaken": "This module or one of its versions is already taken",
  "engine.life.duplicateStage": "Duplicate life stage: {stage}",
  "engine.life.missingStage": "Choose a module for life stage: {stage}",
  "engine.life.choice": "Complete a choice in life module “{name}” ({slot})",
  "engine.life.specializationConflict":
    "The life module specialization for “{name}” conflicts with the existing selection",
  "engine.life.qualityUnknown": "Life module quality “{name}” was not found",
  "engine.life.qualityChoiceConflict":
    "The extra selection for life module quality “{name}” conflicts with an existing selection. Different selections for the same quality are not yet supported together.",
  "engine.life.qualityLevelUnknown":
    "Quality “{name}” for a life module quality level was not found",
  "engine.life.requirement": "The requirements for life module “{name}” are not met",

  "meta.booksHidden":
    "{count} of the metatypes this row offers are left out by the ruleset’s book list",
  "meta.innate": "Innate to {name} (no additional karma)",
  "meta.innateFixed": "Innate grant · cannot be removed",
  "meta.innateQualities": "Innate qualities",
  "meta.innateQualitiesHint":
    "These also appear in the qualities tab. They cost no karma and cannot be removed",
  "meta.critterPowers": "Critter powers",
  "meta.critterPowersHint":
    "Powers this metatype has as a critter. They are not qualities, so the qualities tab does not list them",
  "meta.retained":
    "The current metatype, {name}, is not available as a new choice under these conditions. It is kept until you choose another metatype",
  "skills.points": "Skills {skills} · Groups {groups} · Knowledge {knowledge}",
  "skills.careerNote": " · career advances with karma (max R{max})",
  "skills.chargenNote": " · a specialisation costs 1 point",
  "skills.granted": "Skills that come with something",
  "skills.grantedNote":
    "Skills a quality, a piece of ware, an adept power or a mentor spirit brings with it. Picking one here is the same as picking it on that thing's own tab.",
  "skills.talentLabel": "Skills from your talent",
  "skills.talent": "Skills from your talent ({qty} at R{rating})",
  "skills.talentGroup": "Skill group from your talent ({qty} at R{rating})",
  "skills.talentPick": "Pick {n}",
  "skills.groups": "Skill groups",
  "skills.softBit": "softR{rating}",
  "skills.default": "default {pool}",
  "skills.defaultFree": "default {pool} (no −1)",
  "skills.defaultBlocked": "cannot default",
  "skills.defaultHint": "Unlearned: rolled at {attr} − 1 (SR5 p.130)",
  "skills.specBit": "spec+{bonus}",
  "skills.specDisabled": "specialisation inactive",
  "skills.active": "Active skills",
  "skills.rowHint": "{category} / linked attribute {attr} / chargen max {max}",
  "skills.attrSwap": "linked attribute {attr} (swapped by {source})",
  "skills.specAttrSwap": "{attr} with {spec}",
  "skills.groupHint": "{group}: raises every skill in the group at once (chargen max {max})",
  "skills.ratingHint": "Rating (chargen max {max})",
  "skills.exotic": "Exotic skills",
  "skills.exoticNote":
    "The target is part of the skill itself. You can take the same Exotic for different targets, and no extra point is needed for a specialisation.",
  "skills.emptyExotic": "None yet. Add one with the buttons below.",
  "skills.addNamed": "Add {name}",
  "skills.knowledge": "Knowledge skills",
  "skills.knowDefault":
    "A knowledge skill you do not have still defaults: INT {int} / LOG {log} (−1, SR5 p.130)",
  "skills.knowDefaultBlocked": " / {categories} cannot default",
  "skills.knowledgeFree": "Free points are (INT + LOG) × 2; one native language is free.",
  "skills.knowledgeCareerRange": "Career ratings run 1–{max}",
  "skills.knowledgeChargenRange": "Chargen ratings run 1–6",
  "skills.rangeSuffix": ". ",
  "skills.knowledgeCareerCost": "More cost karma.",
  "skills.karmaHint":
    "How many of this skill's top levels were bought with karma. They use no skill (knowledge) points and cost the new rating × 2 karma each (× 1 for knowledge).",
  "skills.karmaSpent": "Skills raised with karma: {karma} karma (knowledge {knowledge} karma)",
  "skills.knowledgeChargenCost": "A specialisation costs 1 knowledge point.",
  "skills.specKarma": "karma",
  "skills.specKarmaHint":
    "Buy this specialisation with karma instead of a skill (knowledge) point.",
  "skills.custom": " (custom)",
  "skills.free": "free",
  "skills.native": "Native",
  "skills.emptyKnowledge": "None yet. Add one from the catalog, or make one with a custom name.",
  "skills.searchKnowledge": "Search knowledge skills",
  "skills.customName": "Custom knowledge name",

  // --- vehicles / drones --------------------------------------------------
  "skills.addCustom": "Add custom",
  "qual.negativeKarma": "Karma from negatives {used}",
  "qual.career": "Career",
  "qual.metagenic": "Metagenic qualities: positive {positive} / negative {negative}",
  "qual.metagenicLimit": " / limit {limit}",
  "qual.metagenicNoChangeling": " (no Changeling taken)",
  "qual.metagenicUnbalanced": " · unbalanced (negatives must equal positives, or positives − 1)",
  "qual.owned": "Taken",
  "qual.positive": "Positive quality",
  "qual.negative": "Negative quality",
  "qual.karmaLabel": "karma",
  "qual.karmaBase": " (adjusted; table {base})",
  "qual.freeAttached": " / attached (free)",
  "qual.disabledBy": " / switched off by {ware}",
  "qual.optionalPower": "Choose an optional power",
  "qual.careerTaken": " / taken in career ({cost} karma)",
  "qual.careerTakenNegative": " / taken in career (no karma)",
  "qual.buyoffHint": " / buying it off costs {cost} karma",
  "qual.careerPrice": " / {cost} karma in career",
  "qual.careerPriceNegative": " / no karma in career",
  "qual.removed": "Qualities dropped in career",
  "qual.removedBuyoff": "bought off for {cost} karma",
  "qual.removedPositive": "no refund",
  "qual.grantedLevels": " / {count} free levels held (count toward the cap)",
  "qual.restore": "Restore",
  "qual.restoreLabel": "Restore: {name} (as it was before it was dropped in career)",
  "qual.innateRemove": "Remove ({cost} karma)",
  "qual.innateRemoveRefund": "Remove ({cost} karma back)",
  "qual.innateRemoved": "Innate qualities removed",
  "qual.innateRemovedCost": "innate to {metatype} / removed for {cost} karma",
  "qual.innateRemovedRefund": "innate to {metatype} / removed, {cost} karma back",
  "qual.innateRestoreLabel": "Restore: {name} (back as an innate quality, karma and all)",
  "qual.rebaseline": "Treat the current qualities as chargen",
  "qual.rebaselineConfirm":
    "Treat the current qualities as chargen and cancel the career purchase and buy-off karma?",
  "qual.attached": "attached",
  "qual.empty": "None yet. Filter by positive / negative and add one.",
  "qual.filter.positive": "Positive",
  "qual.filter.negative": "Negative",
  "qual.filter.metagenic": "Metagenic",
  "qual.search": "Search qualities",
  "qual.taken": " / taken {count}",
  "qual.level": "Level",
  "qual.pickLevel": "{name} purchase level",
  "qual.ownedLevel": "{name} owned level",
  "qual.maxLevel": " / max level {max}",
  "qual.changeLevel": "Change level",
  "qual.needsTarget": " / needs a target",
  "qual.wayExclusive": " / exclusive with other Ways",
  "qual.replacesNote": " / adding this removes the qualities it conflicts with",

  // --- quality target editors -------------------------------------------
  "qual.replace": "Replace",
  "quality.addSpirit": "Choose an extra spirit",
  "quality.addSpiritN": "Choose extra spirit {index}",
  "quality.marketCategory": "Choose a goods category",
  "quality.marketContact": "Choose a contact",
  "quality.marketBonus": "Availability test +{bonus} (effective Avail −{bonus})",
  "quality.marketInactive": "Applies once both are picked",
  "quality.side": "Choose a side",
  "quality.matrixAction": "Choose a Matrix action",
  "quality.matrixActionFree": "Type a Matrix action",
  "quality.orType": "or type one",
  "quality.expertise": "Choose a {skill} expertise",
  "quality.expertiseAny": "Choose an expertise",
  "quality.expertiseFree": "Type an expertise",
  "quality.expertiseNote": "specialisation +3 (free)",
  "quality.weaponSkill": "Choose a skill",
  "quality.spellCategory": "Choose a spell category",
  "quality.spirit": "Choose a spirit",
  "quality.attachedQuality": "Choose the attached quality",
  "quality.skillGroup": "Choose a skill group",
  "quality.attribute": "Choose an attribute",
  "quality.target": "Choose a target",
  "quality.targetFree": "Type a target",

  // --- shared across the gear / catalog panels --------------------------
  "quality.targetPlaceholder": "what it is",
  // What each family of free-text quality is asking for. See
  // lib/character/quality-placeholder.ts for which quality maps to which.
  "quality.ph.addiction": "the drug or habit (Novacoke, BTL, …)",
  "quality.ph.allergy": "the allergen (pollen, sunlight, …)",
  "quality.ph.phobia": "what is feared (heights, insects, …)",
  "quality.ph.group": "the group (a metatype, a corp, the Awakened, …)",
  "quality.ph.code": "what the code demands",
  "quality.ph.dayJob": "the employer and the work",
  "quality.ph.sinIssuer": "who issued the SIN (a nation, a corp)",
  "quality.ph.rank": "the organisation and the rank",
  "quality.ph.place": "the place",
  "quality.ph.compulsion": "the compulsion",
  "quality.ph.brand": "the manufacturer or product",
  "quality.ph.pursuer": "who is after you (a person, an organisation)",
  "qual.sharedLimit": " / max {max} together with {names}",
  "grade.label": "Grade {grade}",
  "grade.summary": "Grade {grade} · karma {karma}",
  "grade.karma": "{karma} karma",
  "grade.named": " · {name}",
  "grade.discount": " ({list} discount)",

  "contact.free": "Free CHA×{mult} = {used}/{free}",
  "contact.over": " · {paid} over ({karma} karma)",
  "contact.minimum": ". Connection and Loyalty are at least 1",
  "contact.careerCap": ". Career has no combined cap",
  "contact.chargenCap": ", and chargen caps the pair at 7",
  "contact.perPoint": ". Each point over costs {karma} karma",
  "contact.perPointFree": " (free, from Networker or similar)",
  "contact.points": "{points} pts",
  "contact.group": " / group",
  "contact.billable": " / billed {points} pts",
  "contact.connection": "Connection",
  "contact.loyalty": "Loyalty",
  "contact.name": "Name",
  "contact.role": "Role",

  "contact.roleOptional": "Role (optional)",
  "martial.styles": "Styles {styles}/{max}",
  "martial.techniques": " · techniques {used}/{max}",
  "martial.karma": " · karma {karma}",
  "martial.note":
    " (a style costs 7 karma and includes one technique; each further technique costs 5. Chargen allows one style and five techniques. Styles from qualities do not count.)",
  "martial.unarmedReach": " · unarmed Reach +{reach}",
  "martial.freeQuality": " / free (quality)",
  "martial.cost": " / {karma} karma (style {style} + techniques)",
  "martial.oneTech": " / one technique only",
  "martial.techIncluded": " / included",
  "martial.search": "Search martial arts",
  "martial.rowCost": "{karma} karma (one technique included)",
  "martial.techCount": "{count} techniques",
  "martial.specOptions": " / specialisations {list}",
  "martial.owned": "Taken",
  "martial.capped": "At cap",

  "martial.take": "Take",
  "prio.sumTotal": "Total {used}/{max}",
  "prio.karmaNuyenRate": " · 1K = {rate}¥ (max {max}K)",
  "prio.leftoverToNuyen": "Leftover karma → ¥, max {max}K",
  "prio.leftoverSlider": "Leftover karma → nuyen ({k}K = {nuyen}¥)",
  "prio.leftoverSliderLabel": "Leftover karma converted to nuyen",
  "settings.folder": "Load a ruleset folder",
  "settings.customDataFailed": "That custom data could not be loaded.",
  "settings.zipNotAZip":
    "That did not read as a zip. A .zip name is no guarantee the archive inside is intact.",
  "settings.zipUnsupported":
    "This zip cannot be read here (password-protected, ZIP64, or a compression method this does not implement). Rebuild it, or pick the folder itself.",
  "settings.customDataNotAFolder":
    "Pick the customdata folder itself rather than individual files — several files share a name and there is no way to tell which directory each belongs to.",
  "settings.customDataApplied": "Applied {count} custom-data rules",
  "settings.customDataSkipped": "{count} not applied: {items}",
  "settings.customDataIgnored": "{files} is not data this app loads, so it was left out",
  "settings.mergeShow": "Show what changed",
  "settings.mergeHide": "Hide what changed",
  "settings.mergeAdded": "added",
  "settings.mergeRemoved": "removed",
  "settings.mergeEdited": "changed {fields}",
  "settings.mergeCount": "{count}",
  "settings.mergeTruncated":
    "Too many to itemise; the breakdown stops here. The count above is still exact.",
  "settings.customDataNeeded":
    "This ruleset names {count} custom-data directories. Until they are loaded, nothing they add or change applies at all — the character is worked out from the stock data.",
  "settings.customDataPick": "Load it with its customdata",
  "settings.groupLoaded": "Loaded files",
  "settings.groupShipped": "Shipped with Chummer",
  "settings.load": "Load settings file",
  "settings.loadFailed": "That settings file could not be read.",
  "settings.forget": "Remove this ruleset",
  "settings.knob.allowbiowaresuites":
    "Allow bioware suites (this app has no suites, so their bundled entries never appear)",
  "settings.knob.alloweditpartofbaseweapon":
    "Let weapon accessories and mods change the base weapon's own stats (a Chummer editor setting)",
  "settings.knob.allowskilldicerolling": "Roll dice from a dice pool (a Chummer UI setting)",
  "settings.knob.allowskillregrouping":
    "Let active skills be re-grouped when every rating matches (SR5 FAQ)",
  "settings.knob.armordegredation": "Apply armor degradation",
  "settings.knob.autobackstory": "Generate a backstory automatically (a Chummer UI setting)",
  "settings.knob.boundspiritexpression":
    "The formula for bound spirits (only a single attribute is understood)",
  "settings.knob.chargenkarmatonuyenexpression":
    "The karma-to-nuyen formula (only `{Karma} * n + {PriorityNuyen}` is understood)",
  "settings.knob.contactpointsexpression":
    "The free contact points formula (only `{CHAUnaug} * n` is understood)",
  "settings.knob.cyberlimbattributebonuscapoverride":
    "Override the cap on a cyberlimb's Strength / Agility bonus",
  "settings.knob.dicepenaltysustaining":
    "Dice penalty per sustained spell or complex form (a number rolled at the table)",
  "settings.knob.enableenemytracking":
    "Treat enemies as a contact type (SR4 rules; this app has no enemies)",
  "settings.knob.enemykarmaqualitylimit":
    "Count karma from enemies towards the negative quality limit (this app has no enemies)",
  "settings.knob.essenceformat":
    "How many decimals Essence prints with (a Chummer display setting)",
  "settings.knob.exceednegativequalitieslimit":
    "No karma for negative qualities taken past the limit",
  "settings.knob.extendanydetectionspell":
    "Any detection spell may be taken as its extended version (SM 179)",
  "settings.knob.karmacomplexformoption": "Karma for a complex form option (SR4 legacy)",
  "settings.knob.karmacomplexformskillsoft": "Karma for a complex form skillsoft (SR4 legacy)",
  "settings.knob.karmacontact": "Karma per contact point",
  "settings.knob.karmaenemy": "Karma per point of enemy (this app has no enemies)",
  "settings.knob.karmaimprovecomplexform": "Karma to raise a complex form",
  "settings.knob.karmajoingroup": "Karma to join a magical group or network",
  "settings.knob.karmaleavegroup": "Karma to leave a magical group or network",
  "settings.knob.karmamaneuver": "Karma per maneuver (SR4 legacy)",
  "settings.knob.karmametamagic":
    "Karma for an additional metamagic or echo (this app offers one per initiation grade)",
  "settings.knob.karmanewaiadvancedprogram": "Karma for an AI advanced program",
  "settings.knob.karmanewaiprogram": "Karma for an AI program",
  "settings.knob.karmaquality": "Karma per quality point",
  "settings.knob.karmaspiritfettering": "Karma per point of Force when fettering a spirit",
  "settings.knob.knowledgepointsexpression":
    "The knowledge points formula (only attributes and arithmetic are understood)",
  "settings.knob.morelethalgameplay": "More lethal gameplay (SR4 75)",
  "settings.knob.mysadeptsecondmagattribute":
    "Mystic adepts use a second MAG attribute instead of the power point rules",
  "settings.knob.nuyenformat": "How many decimals nuyen prints with (a Chummer display setting)",
  "settings.knob.priorityspellsasadeptpowers":
    "Spend the free spells from the Magic priority as power points",
  "settings.knob.registeredspriteexpression":
    "The formula for registered sprites (only a single attribute is understood)",
  "settings.knob.reverseattributepriorityorder": "Spend karma on attributes before priority points",
  "settings.knob.specialkarmacostbasedonshownvalue":
    "Karma for special attributes (mystic adept power points included) is not reduced by Essence loss",
  "settings.unsupportedHere":
    "{count} of this ruleset's house rules are not implemented. Numbers and pick lists differ from Chummer by this much:",
  "settings.unsupportedHarmless":
    "{count} further setting(s) have no bearing on anything worked out here: {items}",
  "settings.preset": "Ruleset",
  "settings.presetNone": "Unrestricted (all rulebooks)",
  "settings.booksAll": "All rulebooks available",
  "settings.booksCount": "Rulebooks {count} / {total}",
  "settings.custom": "Custom",
  "settings.booksShow": "Choose rulebooks",
  "settings.booksHide": "Close",
  "settings.booksAllOn": "All on",
  "settings.booksAllOff": "All off",
  "settings.booksNote":
    "Entries from an unticked book drop out of the buy lists. Gear and qualities you already own are kept. Unticking every book means no restriction.",
  "prio.karmaSliderLabel": "Karma converted to nuyen",
  "prio.karmaSlider": "Karma → nuyen ({k}K = {nuyen}¥)",
  "prio.karmaNote":
    "No priority table here — metatype, attributes, skills and spells are all bought with karma (starting from {pool}). MAG / RES unlock with the talent you pick and are bought up from 1. There are no free spell slots.",
  "prio.talent": "Talent",
  "prio.breakdownA":
    "Spent: metatype {meta} / attributes {attrs} / skills {skills} / knowledge {knowledge} / specialisations {specs}",
  "prio.breakdownB": "Qualities {qualities} / nuyen exchange {nuyenKarma} / other {other}",
  "prio.sumHint":
    "The same priority may be used in several categories. The costs must add up to exactly 10.",

  "prio.priorityHint": "A–E once each. Click to swap two categories.",
  "life.comforts": "Comforts +",
  "life.area": "Neighborhood +",
  "life.security": "Security +",
  "life.base": "base {cost}¥",
  "life.multiplier": " / ×{pct}%",
  "life.qualityCost": " / qualities +{cost}¥",
  "life.lpUsed": " / LP {used}/{max}",
  "life.lp": " / LP {lp}",
  "life.quality": "Lifestyle quality",

  "life.freeGrids": " / {count} free grids",
  "attrs.wareBonus": " ware +{bonus}",
  "attrs.meat": " meat {value}",
  "attrs.essenceRange": " / essence loss: min {min}, max {max}",
  "attrs.essenceRangeHint":
    "Essence loss lowers the minimum and the maximum by the same amount (the minimum stops at 0). The slider stays on what was bought; the points and karma spent stack on the lowered minimum.",
  "attrs.points": "Attribute points {used}/{max} · special {specialUsed}/{specialMax}",
  "attrs.rowHint": "Metatype minimum {min} / chargen max {max} / augmented max {aug}",
  "attrs.karmaLevels": "by karma",
  "attrs.karmaHint":
    "How many of this attribute's top levels were bought with karma. They use no attribute points and cost the new rating × 5 karma each.",
  "attrs.karmaSpent": "Attributes raised with karma: {karma} karma",
  "attrs.activeForm": "Current form",
  "attrs.activeFormHint":
    "Dice pools, limits, condition monitors, initiative and movement are worked out from the chosen form's attributes. Both forms share the points spent.",
  "attrs.formValue": " / metahuman form {value}",
  "attrs.formNote":
    "Attributes are bought in the {animal} ranges. The metahuman form ({form}) has the same points in its own ranges, shown on each row.",
  "attrs.minNote":
    "Every attribute starts at its metatype minimum (the amber tick). That much is free — points are only spent above it.",

  "attrs.replacedRanges": "These ranges come from {list}, not from the metatype.",
  "prio.cell.anyMetatype": "Any metatype",
  "prio.cell.humanDwarfElfOrkAi": "Human, Dwarf, Elf, Ork, or A.I.",
  "prio.cell.humanOrElf": "Human or Elf",
  "prio.cell.human": "Human",
  "prio.cell.magicianOrTechnomancer": "Magician or Technomancer",
  "prio.cell.adeptMagicianTechnomancer": "Adept, Magician, or Technomancer",
  "prio.cell.adeptOrAspectedMagician": "Adept or Aspected Magician",
  "talent.magician": "Magician",
  "talent.mysticAdept": "Mystic Adept",
  "talent.adept": "Adept",
  "talent.aspectedMagician": "Aspected Magician",
  "talent.technomancer": "Technomancer",
  "talent.mundane": "Mundane",
  "talent.magicSpells": "{magic} Magic/{spells} Spells",
  "talent.magic": "{magic} Magic",
  "talent.resonanceForms": "{resonance} Resonance/{forms} Complex Forms",
  "talent.depth": "{depth} Depth",
  "prio.cell.attributes": "{points} ({special}) Attributes",
  "prio.cell.skills": "{skills} Skills/{groups} Skill Groups",
  "prio.method.priority": "Priority",
  "prio.method.sumToTen": "Sum to Ten",

  "prio.method.karma": "Karma",
  "prio.cat.heritage": "Heritage",
  "prio.cat.attributes": "Attributes",
  "prio.cat.talent": "Magic / Resonance",
  "prio.cat.skills": "Skills",

  "prio.cat.resources": "Resources",
  "qual.blockPrereq": "Prerequisites not met",

  "qual.blockForbidden": "Not available to this character",
};
