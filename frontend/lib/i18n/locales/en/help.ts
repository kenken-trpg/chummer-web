/** Tooltip help — the formula and breakdown of computed values. English. */
export const EN_HELP = {
  "help.open": "About {label}",
  "help.base": "Base",
  "help.bonus": "Modifiers (qualities, ware, gear, …)",
  "help.bonusOther": "Other (non-stacking bonuses, …)",
  "help.total": "Total",
  "help.limit.physical": "Physical limit = (STR×2 + BOD + REA) ÷ 3, rounded up",
  "help.limit.mental": "Mental limit = (LOG×2 + INT + WIL) ÷ 3, rounded up",
  "help.limit.social": "Social limit = (CHA×2 + WIL + ceil(ESS)) ÷ 3, rounded up",
  "help.limit.note": "Caps the hits that count on a skill test (SR5 p.47)",
  "help.cm.physical": "Physical track = 8 + BOD ÷ 2, rounded up",
  "help.cm.stun": "Stun track = 8 + WIL ÷ 2, rounded up",
  "help.cm.note": "−1 to tests for every 3 boxes filled (SR5 p.169)",
  "help.cm.vehicle":
    "Physical track = the home node {name}'s (12 for a vehicle, 6 for a drone, 8 anthroform, + Body ÷ 2 + mods)",
  "help.cm.homeNode":
    "Matrix condition monitor = 8 + the home node {name}'s Device Rating ÷ 2, rounded up",
  "help.cm.core": "Core damage track = 8 + DEP ÷ 2, rounded up; an A.I. has no Stun track",
  "help.soak.what": "Damage resistance dice = BOD + armor + modifiers",
  "help.soak.body": "BOD (an A.I.: the Body of the vehicle it uses as its home node, or 0)",
  "help.soak.armor": "Armor",
  "help.spellResist.what":
    "Added to every test that resists a spell, except dodging an indirect one",
  "help.spellResist.sheet": "The sheet's Spell defense box has the total dice for each kind",
  "help.def.directMana": "Resisting a direct mana spell = WIL + modifiers",
  "help.def.detection": "Resisting a detection spell = LOG + WIL + modifiers",
  "help.def.mentalManipulation": "Resisting a mental manipulation spell = LOG + WIL + modifiers",
  "help.def.manaIllusion": "Resisting a mana illusion spell = LOG + WIL + modifiers",
  "help.def.physicalIllusion": "Resisting a physical illusion spell = LOG + INT + modifiers",
  "help.def.bonus": "Modifiers (spell resistance included)",
  "help.test.fatigue": "Resisting fatigue = BOD + WIL + modifiers",
  "help.test.memory": "Memory = LOG + WIL + modifiers",
  "help.test.composure": "Composure = CHA + WIL + modifiers",
  "help.test.judge": "Judge Intentions = CHA + INT + modifiers",
  "help.test.dodge": "Dodge (defense test) = REA + INT + modifiers",
  "help.test.surprise": "Surprise = REA + INT + modifiers",
  "help.unarmedDv.what": "Unarmed DV = STR + modifiers; it lands on the gear tab's Unarmed Attack",
  "help.actionPool.what": "Dice added to tests for this action",
  "help.actionPool.source": "From",
  "help.init.value": "Initiative = REA + INT",
  "help.init.dice": "Initiative dice = 1D6 + extra dice (max 5D6)",
  "help.init.note": "Subtract 10 at the end of each Initiative Pass (SR5 p.159)",
  "help.attr.BOD": "Body. Damage resistance, the Physical track and the physical limit",
  "help.attr.AGI": "Agility. Most physical skills, shooting and melee",
  "help.attr.REA": "Reaction. Initiative, defense tests and piloting; part of the physical limit",
  "help.attr.STR":
    "Strength. Melee damage, throwing range and carrying; doubled in the physical limit",
  "help.attr.WIL": "Willpower. The Stun track, drain resistance and the mental and social limits",
  "help.attr.LOG": "Logic. Technical skills and the Matrix; the main source of the mental limit",
  "help.attr.INT": "Intuition. Initiative, perception and defense tests; part of the mental limit",
  "help.attr.CHA":
    "Charisma. Social skills such as negotiation; the main source of the social limit",
  "help.attr.EDG": "Edge. Points per session to reroll, push the limit and so on",
  "help.attr.MAG": "Magic. The strength of spells, spirits and adept powers; drops with Essence",
  "help.attr.RES": "Resonance. The strength of complex forms and sprites; drops with Essence",
  "help.attr.DEP": "Depth. An A.I.'s special attribute; it caps Edge",
  "help.avail.what": "Availability: how hard an item is to get. Higher is harder",
  "help.avail.suffix":
    "A trailing R means a licence is needed (Restricted); F means it is illegal to own (Forbidden)",
  "help.avail.chargen":
    "At creation you cannot buy items above this availability (12 by default). In career play you roll to acquire them",
  "help.deviceRating": "The highest device rating you can buy at creation (6 by default)",
  "help.gradeHint":
    "Ware quality. Better grades cost less Essence but more nuyen and availability. Which grades are banned at creation depends on the settings (betaware and up by default)",
  "help.skill.pool": "Dice pool = skill rating + linked attribute (+ modifiers)",
  "help.skill.spec": "Specialization: +2 dice on that use. 1 karma at creation, 7 in career",
  "help.skill.expertise": "Expertise: replaces the specialization for +3 dice (career only)",
  "help.skill.default":
    "A skill you have not learned can still be defaulted: the linked attribute −1 (SR5 p.130)",
  "help.skill.cap": "The rating cap at creation. One skill may sit at the cap (+1 with Aptitude)",
  "help.group.members": "Skills in it: {skills}",
  "help.group.sep": ", ",
  "help.group.cost":
    "At creation, one skill group point per rating. With karma, the new rating × 5 (SR5 p.107)",
  "help.group.break":
    "Raising one skill in it on its own or taking a specialization breaks the group; bringing them all back to one rating restores it",
  "help.matrix.attack":
    "Attack: breaking into or damaging another icon. It also answers attacks made on you",
  "help.matrix.sleaze": "Sleaze: getting in and staying unnoticed; it opposes Matrix Perception",
  "help.matrix.dataprocessing":
    "Data Processing: quiet work — editing, searching, holding marks. It also drives the deck initiative",
  "help.matrix.firewall":
    "Firewall: defence against attacks and intrusions; the value that opposes them",
  "help.matrix.array":
    "A deck comes with a fixed set of four values that you assign to these slots; swapping two is a free action once per turn (SR5 p.222)",
  "help.knowledge.what":
    "Knowledge skill: linked to LOG or INT. Categories are academic, professional, interest, street and language",
  "help.knowledge.free":
    "Creation gives (INT + LOG) × 2 free points, plus one free native language",
  "help.knowledge.cost":
    "Past the free points, one karma buys one rating; a specialization is one as well",
  "help.exotic.what":
    "Exotic skill: one skill per target (a weapon type, say); the same skill can be held for several targets",
  "help.exotic.nodefault":
    "It cannot be defaulted — you need a rating to use it at all (SR5 p.130)",
  "help.essence.what":
    "Essence: how much of you is still flesh. Everyone starts at 6; cyberware and bioware spend it",
  "help.essence.magic":
    "Magic and Resonance lose what Essence loses (rounded up, one step at a time)",
  "help.essence.zero": "At 0 you die; a character must leave creation above 0",
  "help.essence.grade": "The grade multiplier (the C / B figures) changes what the same ware costs",
  "help.quality.positive": "Positive qualities cost karma — 25 karma worth at creation by default",
  "help.quality.negative": "Negative qualities give karma back, also capped at 25 karma worth",
  "help.quality.career":
    "In career play, buying or buying off a quality costs double karma (SR5 p.72)",
  "help.qualityRow.of": "{name}'s karma",
  "help.qualityRow.karma": "A positive quality costs this karma; a negative one gives it back",
  "help.qualityRow.base":
    "It differs from the table because a condition in the data (metatype, another quality…) moves the price",
  "help.qualityRow.free":
    "Attached: it comes with the metatype or another item, costs no karma and cannot be removed here",
  "help.quality.expertiseFree": "The chosen specialization comes free: no skill points, no karma",
  "help.quality.expertiseBonus": "Tests it applies to get +3 instead of the usual +2",
  "help.quality.expertiseNeeds":
    "It only works while the skill is rated 1 or more (a skillsoft counts)",
  "help.quality.expertiseReplace": "It replaces any specialization the skill already had",
  "help.quality.matrixAction":
    "The quality's bonus goes to the dice pool of the Matrix action picked here",
  "help.quality.matrixActionFree":
    "An action not on the list can be typed into the box beside it; the bonus goes to the action of that name",
  "help.vehicle.statsLabel": "Stats",
  "help.vehicle.stats":
    "HND handling / SPD speed / ACC acceleration / BOD body / ARM armor / PLT pilot / SNR sensor",
  "help.vehicle.pilot":
    "Pilot is the autopilot\u2019s skill: it rolls when the vehicle acts on its own",
  "help.vehicle.body":
    "Body is toughness: damage resistance, and how many mod slots the vehicle has",
  "help.vehicle.slots":
    "Mod slots are per R5 category (Powertrain, Protection, Weapons, Body, Electromagnetic, Cosmetic); each category's cap is Body plus whatever the model adds",
  "help.vehicle.slotsDrone":
    "A drone has one pool instead of categories, capped at Body; a mod that hands slots back raises that cap",
  "help.weapon.statsLabel": "Stats",
  "help.weapon.acc": "Accuracy caps the hits that count on an attack with this weapon",
  "help.weapon.dv": "DV is the damage on a hit; a trailing P is physical, S is stun",
  "help.weapon.ap":
    "AP lowers the target\u2019s armor by that much \u2014 \u22122 means 2 less armor to resist with",
  "help.weapon.rc": "RC cancels that much of the recoil a burst builds up",
  "help.weapon.mode": "Firing modes: SS single shot, SA semi-auto, BF burst fire, FA full auto",
  "help.weapon.ammo":
    "How many rounds it holds and how it reloads: (c) clip, (m) magazine, (b) break action, (d) drum, (ml) muzzle",
  "help.weapon.reach": "Reach: in melee, the difference over your opponent is a dice bonus",
  "help.armor.statsLabel": "Armor",
  "help.armor.value": "Armor adds to the dice you resist damage with (SR5 p.169)",
  "help.armor.stack":
    "Only the highest-rated piece worn counts; the rest bring their mods along, not their rating",
  "help.armor.capacity": "Capacity is how much this piece can hold, shown as used / maximum",
  "help.armor.equipped": "A piece that is not worn does not count towards armor",
  "help.contact.statsLabel": "Ratings",
  "help.contact.connection":
    "Connection is the contact\u2019s reach and clout: what they can get you (SR5 p.388)",
  "help.contact.loyalty":
    "Loyalty is how much they care: what they will risk, and how hard they are to turn",
  "help.contact.cost":
    "At creation a contact costs Connection + Loyalty out of your contact points",
  "help.contact.pointsLabel": "Contact points",
  "help.contact.pointsFree":
    "The free points are Charisma \u00d7 {mult}; each contact uses its Connection + Loyalty",
  "help.contact.pointsQuality":
    "A contact a quality gave you counts less the part that quality pays for",
  "help.contact.pointsOver":
    "Points past the free ones are paid in karma; settings and qualities change the karma per point",
  // Life Module panel (#565)
  "help.lifeModule.karma":
    "Module karma is what the modules cost together. It comes out of the same creation karma as everything else: 750 unless the settings give another pool",
  "help.lifeModule.freeQuality":
    "Free quality points: positive qualities cost no karma up to the Positive figure, and negative qualities give none back up to the Negative one",
  "help.lifeModule.caps":
    "Skill levels from modules count only up to these ratings. Your own purchases are priced from the rating the grants leave",
  "help.lifeModule.overflow":
    "What a module grants an individual skill past the cap is overflow. Move it to another skill linked to the same attribute; levels with no room anywhere are lost",
  "help.lifeModule.knowledgeOverflow":
    "Knowledge and language grants stop at rating 9. This app lets you assign excess levels to another knowledge or language skill as a house rule; Run Faster does not specify this redistribution",
  "help.spell.statsLabel": "Spell",
  "help.spell.drain":
    "Drain is what the caster takes; F is the Force chosen when casting, so F\u22123 is Force \u2212 3 (minimum 2)",
  "help.spell.drainResist":
    "Resist drain with Willpower + your tradition\u2019s attribute; the rest is damage",
  "help.spell.force":
    "At Force up to your Magic the drain is stun damage, above it physical (SR5 p.281)",
  "help.spell.range": "Range (LOS, touch, area) and duration (instant, sustained, permanent)",
  "help.spell.pointsLabel": "Free spells",
  "help.spell.pointsFree":
    "The free spells are those of the talent picked in the priority table\u2019s Magic column, plus any a quality adds",
  "help.spell.pointsTouch": "Some qualities add slots that only touch-range spells can use",
  "help.spell.pointsPaid":
    "Each spell past them is bought with karma; qualities can change how much",
  "help.spell.pickAttr":
    "Each attribute picked counts as a spell of its own: pick another and the same spell can be learned again, each taking a free slot or karma",
  "help.spell.pickText":
    "Each pick (what the [ ] names, such as the kind of life form to detect) counts as a spell of its own: name another and the same spell can be learned again, each taking a free slot or karma",
  "help.spell.pickSame": "A second one with the same pick is dropped as a duplicate",
  "help.ware.statsLabel": "Ware",
  "help.ware.essence": "ESS \u2212n is the essence this piece costs, after its grade multiplier",
  "help.ware.capacity":
    "Capacity is how much this piece can hold, shown as used / maximum \u2014 cyberlimbs and housings have it",
  "help.cyber.statsLabel": "This tab's totals",
  "help.cyber.essence":
    "Essence is what is left in all, and the figure in brackets is the cyberware part of it",
  "help.cyber.spent":
    "The spent ¥ is every purchase, gear and qualities included, not this tab alone",
  "help.cyber.limbLabel": "Limb average",
  "help.cyber.limb":
    "With cyberlimbs fitted, the body's STR / AGI is the average over six locations — both arms, both legs, torso and skull — rounded up. A location without a cyberlimb counts at the meat value",
  "help.cyber.limbCount":
    "Limb average is cyber locations / locations averaged; meat is the body's own STR / AGI",
  "help.cyber.redliner":
    "What Redliner (CF p.55) and Cyberseeker do depends on how many cyberlimbs are counted. By default only arms and legs count",
  "help.cyber.redlinerParts": "Tick these to count a cyber torso or skull as well",
  "help.bio.statsLabel": "This tab's totals",
  "help.bio.what":
    "Bioware: cultured tissue grown and implanted; it spends essence just as cyberware does (SR5 p.459)",
  "help.bio.essence":
    "Essence is what is left in all, and the figure in brackets is the bioware part of it",
  "help.bio.spent":
    "The spent ¥ is every purchase, gear and qualities included, not this tab alone",
  "help.cf.statsLabel": "Complex form",
  "help.cpower.what":
    "Opened by an Infected or a Dracoform quality. Buys powers in the category the quality names (Infected, Drake), each at its own karma",
  "help.cpower.offer":
    "Only the powers whose requirements (the Infected type, another power) are met are listed",
  "help.cpower.granted":
    "The powers a quality grants are not here: they are listed on the quality, on the Qualities tab",
  "help.aiprog.price":
    "5 karma each, 8 for an Advanced Program (DT). The same price after creation",
  "help.aiprog.inherent": "The one Inherent Program picks is free, and goes when the quality does",
  "help.aiprog.statsLabel": "Program",
  "help.aiprog.category": "The category sets the price: only Advanced Programs cost more",
  "help.aiprog.required": "Needs one of the programs after “Requires” first",
  "help.aiprog.extra": "An autosoft names what it is for: a model, a weapon or a skill",
  "help.aiprog.free": "A quality gave it, so it cannot be removed here; it goes with the quality",
  "help.cpower.statsLabel": "Power",
  "help.cpower.stats": "Type / action / range / duration. Type P is physical, M is mana",
  "help.cpower.blank": "A blank is a value the data does not give",
  "help.mentor.what":
    "Shown once the Mentor Spirit quality is taken (Paragon for a technomancer). The spirit's fixed effects and the options picked below are computed",
  "help.mentor.choices":
    "The checkboxes are the advantage's options. One per group applies; with none picked, the group's first does. Options the talent cannot use are not shown",
  "help.mentor.disadvantage":
    "The disadvantage comes up in certain situations, so it is not computed — it is for the table",
  "help.mentor.text":
    "The advantage and disadvantage are the rulebook's own text, so only the page is given",
  "help.cf.fv":
    "FV is the fading; L is the Level chosen when threading, so L\u22121 is Level \u2212 1 (minimum 2)",
  "help.cf.fade": "Resist fading with Willpower + Resonance; the rest is damage",
  "help.cf.level": "At Level up to your Resonance the fading is stun damage, above it physical",
  "help.cf.target": "What it acts on (persona, device, file, sprite, …) and how long it lasts",
  "help.cf.pointsLabel": "Free complex forms",
  "help.cf.pointsFree":
    "The free complex forms are those of the talent picked in the priority table\u2019s Resonance column",
  "help.cf.pointsPaid": "Each complex form past them is bought with karma",
  "help.cf.pickAttr":
    "Each Matrix attribute picked counts as a complex form of its own: pick another and the same form can be learned again, each taking a free slot or karma",
  "help.cf.pickSame": "A second one with the same attribute is dropped as a duplicate",
  "help.spirit.statsLabel": "Spirit",
  "help.spirit.force":
    "Force is the spirit\u2019s strength: its attributes and its dice pools follow from it",
  "help.spirit.services": "Services are the tasks it still owes you \u2014 one job spends one",
  "help.spirit.bound":
    "A bound spirit can be called again but costs reagents; a summoned one leaves at dawn",
  "help.sprite.statsLabel": "Sprite",
  "help.sprite.level":
    "Level is the sprite\u2019s strength: its matrix attributes and dice pools follow from it",
  "help.sprite.tasks": "Tasks are the jobs it still owes you \u2014 one job spends one",
  "help.sprite.registered": "A registered sprite persists; a merely compiled one is gone on reboot",
  "help.initiation.statsLabel": "Grade and karma",
  "help.initiation.karma":
    "Each grade costs 10 + grade\u00d73 karma (13 for the first, 16 for the second, …)",
  "help.initiation.discount":
    "A group, an ordeal and schooling each take 10% off, and they stack (SR5 p.325)",
  "help.initiation.metamagic": "Every grade picks one metamagic or art",
  "help.life.statsLabel": "Lifestyle",
  "help.life.monthly": "Monthly = base \u00d7 (1 + modifier %) + what the lifestyle qualities add",
  "help.life.months": "That monthly figure times how long you pay for is the total",
  "help.life.lp":
    "LP is what a lifestyle you build yourself may spend on qualities, used / maximum",
  "help.matrix.statsLabel": "Matrix",
  "help.matrix.deviceRating":
    "DR is the device\u2019s own rating \u2014 what it rolls when nobody is driving it",
  "help.matrixmod.statsLabel": "Electronic modification",
  "help.matrixmod.what":
    "Electronic modifications (DT p.66) have no fee beyond parts and tools. Allocate materials and register successful construction to enable their effects.",
  "help.matrixmod.array":
    "On a deck some of them move a point between two array slots instead (+1 on one, \u22121 on the other); the total does not grow",
  "help.matrixmod.included": "One marked as standard came with the device and costs nothing",
  "help.prio.statsLabel": "Reading the table",
  "help.prio.attrCell":
    "In the attributes column, \u201c6 (2)\u201d is 6 attribute points and 2 special points",
  "help.prio.special":
    "Special points buy Edge, Magic and Resonance, and do not mix with ordinary ones",
  "help.prio.skillCell":
    "In the skills column, \u201c24/2\u201d is 24 skill points and 2 skill-group points",
  "help.prio.magicCell":
    "The magic/resonance column is the talent, plus the free spells or complex forms it brings",
  "help.adept.statsLabel": "Power points",
  "help.adept.pp": "An adept has as many power points as Magic; each power takes some",
  "help.adept.mystic":
    "A mystic adept buys them at 5 karma each; the Magic not spent that way stays for spells",
  "help.adept.way":
    "A Way quality makes its powers cheaper, up to Magic \u00f7 4 (rounded up) of discount",
  "help.adept.qiCost": "It costs Force × 3,000¥",
  "help.adept.qiBinding":
    "Binding takes Force × 2 karma (a table's settings may change it); The Artisan's Way lowers it",
  "help.adept.qiPower":
    "Each point of Force holds 0.25 power points of the power; a higher power rating needs more Force",
  "help.adept.enhancementKarma": "An enhancement costs 2 karma (a table's settings may change it)",
  "help.adept.enhancementWay":
    "Each needs a particular Way quality; dropping the Way drops the enhancement",
  "help.adept.enhancementPower": "It needs its power too; without it, a warning shows",
  "help.martial.statsLabel": "Styles and techniques",
  "help.martial.style": "A style costs 7 karma (some list a price of their own)",
  "help.martial.technique": "Each technique costs 5 karma; the ones a quality brings are free",
  "help.martial.chargen":
    "At creation: one style and up to five techniques; career play has no cap",
  "help.gear.statsLabel": "Stats",
  "help.gear.rating":
    "Rating is the step of performance; raising it usually raises the price and the availability too. The cap is per item",
  "help.gear.capacity":
    "Capacity n/m is how much this item can hold (m) and how much is in use (n)",
  "help.gear.qty": "\u00d7n is the quantity; the price is multiplied by it",
  "help.points.attr":
    "Attribute points n/m: spent / available; what is left cannot go anywhere else",
  "help.points.special":
    "Special points n/m buy Edge, Magic and Resonance only, and do not mix with ordinary ones",
  "help.points.skills": "Skill points n/m: one point per rating; group points are a separate pool",
  "help.points.knowledge":
    "Knowledge points n/m: the free pool is (INT + LOG) \u00d7 2, plus one free native language",
  "help.points.contacts":
    "Contacts n/m (+k): the free pool m is CHA \u00d7 3 (settings may change it); +k was bought beyond it, at connection + loyalty in karma",
  "help.points.martial":
    "Styles n/m and techniques n/m are the limits at creation; anything beyond is bought with karma",
  "help.points.advancement":
    "Advancement karma: what has been spent raising attributes and skills since career started",
  "help.points.negativeKarma":
    "The cap on karma handed back by negative qualities; settings may change it",
  "help.points.spells":
    "Spells n/m (+k): the talent\u2019s free slots m, plus k bought with karma (5 each by default)",
  "help.points.complexForms":
    "Complex forms n/m (+k): the talent\u2019s free slots, plus what karma bought (4 each by default)",
  "help.livingPersona":
    "A technomancer is their own deck: DR is Resonance, ATK is CHA, SLZ is INT, DP is LOG, FW is WIL",
  "help.attr.wareBonus":
    "\u201cware +n\u201d is what cyberware and bioware add; it sits on top of the natural maximum",
  "help.attr.limbAverage":
    "With \u201climb average\u201d shown, STR and AGI are the average across all limbs \u2014 each cyberlimb\u2019s own value, the meat ones at the natural rating",
  "help.attr.unimplemented":
    "Unimplemented bonuses are modifiers this calculator does not handle yet; they are not in the totals",
  "help.flag.ambidextrous": "Ambidextrous: no off-hand penalty when shooting or striking",
  "help.flag.erased": "Erased: what the matrix holds about you fades on its own over time",
  "help.flag.excon": "Ex-Con: a criminal record, worse social footing in return for karma back",
  "help.flag.overclock":
    "Overclocker: +1 to one matrix attribute (Attack where there is one) on the best deck",
  "help.flag.specialMod":
    "Special modifications n/m: the slots a quality grants, counting the weapon accessories that ask for one",
  "help.flag.fihp": "Friends in High Places: favours where a connection is what is needed",
  "help.flag.madeMan":
    "Made Man: a member of the organisation \u2014 backing you cannot walk away from",
  "help.flag.trustfund":
    "Trust Fund: the monthly cost of a lifestyle is covered (1 Medium, 2 Low, 3 High, 4 Medium)",
  "help.flag.dealer": "Dealer Connection: vehicles of this category cost 10% less",
  "help.career.rewards":
    "Karma and nuyen added here count as career income, not as creation budget",
  "help.career.log": "Each is kept as its own row, so you can trace what came from which run",
  "help.career.edit":
    "An extra the GM awarded, added by hand on top of what the formula gives; the formula itself does not move",
  "help.granted.what":
    "Skills granted by a quality, ware, adept power or mentor \u2014 picking one here spends no skill points",
  "help.granted.where":
    "The same pick as the one beside what grants it; either place changes the same thing",
  "help.talent.what":
    "The skills the priority talent hands out \u2014 naming them costs no skill points",
  "help.talent.rating": "Each is free up to the rating shown; skill points may buy on top of that",
  "help.talent.change":
    "Change a pick and the old skill loses the free levels; whatever was bought on top stays",
  "help.heldGear.statsLabel": "Gear held inside",
  "help.heldGear.what":
    "What a piece of ware carries \u2014 a chemical gland\u2019s chemical, an auto-injector\u2019s drug; it is priced apart from the ware",
  "help.drug.statsLabel": "Drug stats",
  "help.drug.effect": "The effect applies only while the drug is in use; clear it and it lifts",
  "help.drug.onset": "Onset is how long it takes to start working; 0 is immediate",
  "help.drug.vector":
    "Vector (injection, inhalation, ingestion, contact) \u2014 the same drug takes hold at different speeds",
  "help.drug.testLabel": "Addiction test",
  "help.drug.pool":
    "The addiction test is BOD + WIL for a physiological habit, LOG + WIL for a psychological one (SR5 p.414)",
  "help.drug.threshold":
    "The addiction threshold is the hits that test needs; fall short and the habit deepens a step",
  "help.drug.addicted":
    "The figure in brackets is the pool once addicted; some qualities change only the first test (Drug Tolerant is +2 then, CF p.54)",
  "help.drug.rating":
    "Addiction rating is what you roll against to kick the habit \u2014 the higher, the harder",
  "help.drug.speed": "Seconds until it takes hold; 0 is immediate",
  "help.drug.duration": "How long the effect lasts; some drugs crash when it ends",
  "help.drug.crash": "Crash is the damage taken when the effect wears off",
  "help.drug.grade":
    "The grade multiplier applies to the price; a better grade also raises availability",
  "help.drug.parts":
    "One Foundation, with blocks and enhancers stacked on it; the foundation decides what may go on (CF p.190)",
  "help.sensor.statsLabel": "Sensor stats",
  "help.sensor.nest":
    "Three levels: housing \u2192 sensor \u2192 function, and the functions fit inside the housing\u2019s capacity",
  "help.sensor.capacity": "Capacity n/m: what the housing holds (m) and what is in it (n)",
  "help.sensor.rating":
    "R is the sensor\u2019s rating \u2014 the limit on a perception test made with it",
  "help.optics.statsLabel": "Vision and audio stats",
  "help.optics.nest":
    "Enhancements go into this device; cyberware eyes and ears are a separate pool and share no capacity",
  "help.optics.capacity": "Capacity n/m: what this device holds (m) and what is in it (n)",
  "help.optics.rating":
    "R is the enhancement\u2019s rating; the same enhancement twice does not add up",
  "help.program.statsLabel": "Stats",
  "help.program.deckSlot":
    "Installed copies have no count limit. Only running programs use simultaneous execution slots. New purchases and newly loaded copies start stopped; use the checkbox to run them.",
  "help.program.slot":
    "Each program takes one program slot on the device running it, shown as n/m on the deck or RCC",
  "help.program.rating":
    "Where a program has a rating, the step changes what it does. The cap is per item",
  "help.program.loose":
    "Programs loaded nowhere collect here; owning a copy does nothing on its own",
  "help.vehmod.statsLabel": "Stats",
  "help.vehmod.slots":
    "Slots n is what this mod takes from the chassis, against its category's cap",
  "help.vehmod.rating":
    "Rating is the step of the mod; for some, the price or the slot cost moves with it",
  "help.vehmod.capacity":
    "Capacity n/m is what this mod itself can hold (the ones that carry sensors or ware)",
  "help.vehmod.included":
    "Anything marked as included comes with the model and costs neither slots nor nuyen",
  "help.vehmount.statsLabel": "Mount stats",
  "help.vehmount.slots":
    "Slots n is what the mount itself takes from the chassis; the weapon in it takes none",
  "help.vehmount.weapon":
    "Only a weapon already bought on the weapons tab can be mounted \u2014 this picks one, it does not buy one",
  "help.vehmount.included": "A mount marked as standard came with the model and cannot be removed",
  "help.vehgear.statsLabel": "Interior gear",
  "help.vehgear.what":
    "Gear carried inside the vehicle rather than bolted to it; it takes no slots",
  "help.vehgear.rating": "R is the gear\u2019s rating; the price follows it",
  "help.meta.statsLabel": "Choosing a metatype",
  "help.meta.special":
    "Special points buy Edge, Magic and Resonance only, and are counted apart from ordinary attribute points",
  "help.meta.karma":
    "In karma build, the metatype itself costs karma (50 for an ork, 100 for a troll, and so on)",
  "help.meta.variant":
    "A metavariant is a strain of the same metatype: it changes the attribute bounds and the qualities that come with it",
  "help.meta.talent":
    "The talent is the magic or resonance aptitude; changing metatype does not make you pick it again",
  "help.foci.statsLabel": "Focus limits",
  "help.foci.count": "You may have as many foci bonded as your Magic (qi foci count towards it)",
  "help.foci.force":
    "The Force of every bonded focus adds up to at most Magic \u00d7 2; go over and none of them work",
  "help.foci.bind":
    "Bonding costs karma equal to the Force. Buying or crafting one does nothing until it is bonded",
  "help.foci.craft":
    "Crafting costs the formula plus Force \u00d7 20\u00a5 of reagents \u2014 cheaper than retail, but a failed test is spent for nothing",
  "help.sub.statsLabel": "Grade and karma",
  "help.sub.karma":
    "Each grade costs 10 + grade \u00d7 3 karma (13 for the first, 16 for the second\u2026)",
  "help.sub.discount": "Network, task and schooling each take 10% off, and they stack",
  "help.sub.echo": "Every grade picks one echo, and raises the cap on Resonance by one",
  "help.gear.homeNode1":
    "The device the A.I. lives in. Only one: marking another device moves the mark",
  "help.gear.homeNode2":
    "Its Data Processing goes to the Matrix initiative and the mental and social limits",
  "help.gear.homeNode3": "Its Matrix condition monitor stands in for the Stun track",
  "help.gear.blackMarket1": "Takes 10% off this item, through the Black Market Pipeline",
  "help.gear.blackMarket2": "Only items in the category picked on the quality, one item at a time",
  "help.parts.stockLabel": "Counting parts",
  "help.parts.quarter": "A pack is counted in quarters, 0.25 at a time",
  "help.parts.remaining": "Remaining = bought and supplied \u2212 used by completed work",
  "help.parts.reserved":
    "Reserved is what pending work has been allotted: still in the remainder, but no other work can take it",
  "help.parts.qty":
    "Using parts leaves the bought row's quantity alone; the sheet and exports show the remainder",
  "help.parts.kindLabel": "The sources",
  "help.parts.salvaged": "Salvaged: parts come by without buying. Enter the amount and a note",
  "help.parts.equipment":
    "Comes with a facility: a Tool Shop (Hardware) gives 2 packs each, a Tool Facility (Hardware) 10",
  "help.parts.equipmentOnce":
    "Each facility can be entered once, and owning one does not refill the stock",
  "help.parts.gm": "GM-given: parts the GM handed over. Enter the amount and a note",
  "help.parts.correct":
    "Correct a mistake by withdrawing the record with a reason: the effect goes and the allotment is freed, the purchase stays",
  "help.parts.noRefund":
    "Removing a modification or deleting a device does not give its parts back",
  "help.construction.pending": "Pending: no effect yet. Saving the allotment reserves the parts",
  "help.construction.completed":
    "Completed: the parts are used and the modification has its effect",
  "help.construction.unverified":
    "No parts record: read from old JSON or a .chum5, and working as before. Allot parts, or confirm with a note that they were paid for",
  "help.construction.complete": "It can be completed once exactly the parts it needs are allotted",
  "help.construction.success":
    "Enter work that succeeded: lost parts from a failed test or a glitch are not counted",
  "help.construction.requiredLabel": "Parts needed",
  "help.construction.increase": "Increase Matrix Attribute: the new value \u00d7 2 packs",
  "help.construction.modify": "Modify Matrix Attribute: 4 packs",
  "help.construction.add": "Add Attack / Sleaze: DR \u00d7 2 packs",
  "help.construction.module": "Add Module: 2 packs (DT pp.64\u201366)",
  "help.construction.frozen":
    "Set by the device's own values before the work, and fixed when it is completed",
  "help.gear.price": "This item's price is set within {lo}\u2013{hi}\u00a5",
  "help.gear.stackWith":
    "Worn with the armor it was tailored to, this piece adds its + value on top of that armor (RG p.59)",
  "help.gear.inUse": "In use, its effects reach the attributes, initiative and skills",
  "help.gear.putInto1": "Carry this inside another piece of gear",
  "help.gear.putInto2":
    "Several of the container means several of what is in it, as Chummer counts it",
  "help.life.raiseLabel": "Raising points",
  "help.life.raise": "Points raised above what this lifestyle starts with",
  "help.life.raiseCost":
    "Each costs 1 LP and 10% of the base cost, plus its own price where it has one (RF p.219)",
  "help.prio.nuyenRate": "1 karma = {rate}\u00a5",
  "help.prio.nuyenOneWay": "Only while creating, and nuyen cannot be turned back into karma",
  "help.ware.essDiscount": "An essence discount the GM allowed; negative costs more",
  "help.ware.essDiscountWhen": "Only offered when the settings file allows essence discounts",
  "help.side.chummerAdjust":
    "What a Chummer save\u2019s balance leaves apart from the build and the rewards",
  "help.side.chummerAdjustWhy":
    "Rent paid, purchases at their own prices \u2014 added to what is left",
  "help.prio.methodLabel": "The build methods",
  "help.prio.methodPriority":
    "Priority: one of A\u2013E to each of the five categories, the standard method (SR5 p.65)",
  "help.prio.methodSum":
    "Sum to Ten: the same table, picked so that A=4 / B=3 / C=2 / D=1 / E=0 add up to 10; letters may repeat",
  "help.prio.methodKarma": "Karma: no priority table, everything bought from 800 karma (SR5 p.94)",
  "help.prio.methodLife": "Life Module: built up from birth, one stage of a life at a time",
  "help.prio.swap": "Picking a letter another category holds swaps the two",
  "help.side.scBurn": "Burn two points of Street Cred to take one off Notoriety (SR5 p.373)",
  "help.qual.rebaseline": "For a creation mistake put right after entering career",
  "help.qual.rebaselineEffect": "Cancels every career charge for taking or buying off a quality",
  "help.qual.marketAvail":
    "Items of the picked category get +2 on the Availability test, and chargen checks their Availability 2 lower",
  "help.qual.marketDiscount":
    'Items of that category can each be bought at 10% off (the item row\'s "Black market")',
  "help.qual.marketNeeds":
    "Nothing applies until both the category and the contact are picked (RF p.145)",
  "help.toolbar.import":
    "Four things can be read: this app\u2019s own JSON, a Foundry VTT (shadowrun5e) actor\u2019s Export Data JSON, a Chummer5a .chum5/.chum5lz save, and the 「［SR5］キャラシテンプレート」 Google Sheet by 音の兔 (Nenousa), the one the Japanese Shadowrun 5th unofficial wiki links to, downloaded as .xlsx. An ordinary Excel workbook or any other JSON cannot be read.",
  "help.toolbar.share":
    "Copy a read-only share link. The character rides in the URL and is never stored on the server (the portrait is left out).",
  "help.toolbar.exportChum5": "Export as .chum5 (XML), which Chummer5a can open",
  "help.toolbar.exportXlsx":
    "Export an .xlsx with the same sheets and the same input cells as the 「［SR5］キャラシテンプレート」 Google Sheet by 音の兔 (Nenousa), the one the Japanese Shadowrun 5th unofficial wiki links to (the template itself is not bundled)",
  "help.toolbar.exportFvtt":
    "Export JSON for Foundry VTT's Chummer/Data Import (shadowrun5e 0.34.5) — the system builds the actor. Innate metatype powers do not become items, so they are listed before the file is written",
  "help.toolbar.cocofolia":
    "Copy a Cocofolia piece as JSON (paste to import). Rolls use BCDice's ShadowRun5.",
  "help.toolbar.udonarium":
    "Download an Udonarium character piece as .zip — drop it straight on the table. The chat palette targets BCDice ShadowRun5; attributes, weapons, magic and the Matrix are variables, so the table can retune a pool without re-exporting.",
  "help.toolbar.chatPalette": "Copy the chat palette (BCDice ShadowRun5 commands)",
  "help.toolbar.cocoUntrained":
    "Add the unlearned skills you can default on (attribute − 1) and the knowledge skills you have to the Cocofolia piece and chat palette",
  "help.toolbar.conjured":
    "Export each bound spirit / registered sprite as its own Cocofolia piece (a JSON array)",
  "help.toolbar.udonariumConjured":
    "Download every bound spirit, registered sprite, vehicle and drone as a piece, one .zip per kind. Udonarium reads every xml an archive holds, so each kind lands on the table in one drop.",
  "help.toolbar.career": "Go back to character creation",
  "help.toolbar.toCareer": "Finish creation → spend leftover karma / nuyen to advance",
  "help.toolbar.print":
    "Switch to the print layout and print. The dialog can also \u201cSave as PDF\u201d.",
  "help.settings.preset":
    "A settings file shipped with Chummer. Sets the rulebooks and the build method",
  "help.settings.load":
    "Read an .xml from your Chummer settings folder, or a .zip of the folder holding settings and customdata. The file is not stored anywhere but this browser (the zip is also the way in on a device that cannot pick a folder, such as Android)",
  "help.settings.folder":
    "Pick the folder holding settings and customdata — the folder itself, not a file. Every settings file in it joins the pulldown, and picking one merges the custom data it names. The files stay in this browser; only the merged result is held on the server, and only for a while",
  "help.settings.books": "Narrow what can be bought to the books you own",
  "help.settings.forget": "Remove {name} from this browser (characters are untouched)",
  "help.settings.customDataPick":
    "Pick the folder that holds settings and customdata side by side — the folder itself. A settings file on its own does not bring its custom data with it",
  "help.settings.booksAllOn": "Tick every rulebook",
  "help.settings.booksAllOff": "Untick every rulebook but the core one (SR5)",
  "help.toolbar.sheetUrl":
    "Read the 「［SR5］キャラシテンプレート」 Google Sheet by 音の兔 (Nenousa), the one the Japanese Shadowrun 5th unofficial wiki links to straight from its Google Sheets URL. Only that template\u2019s sheet can be read \u2014 no other spreadsheet and no other site.",
  "help.settings.booksBulkLabel": "Switching them all",
} as const;
