"""The tags `AddImprovementCollection` handles alike, as the improvement types
they make."""

from __future__ import annotations

#: `armor` and the elemental armor tags, as the types they make
_ARMORS = {
    "armor": "Armor",
    "firearmor": "FireArmor",
    "coldarmor": "ColdArmor",
    "electricityarmor": "ElectricityArmor",
    "acidarmor": "AcidArmor",
}

#: Tags whose improvement names the owner's pick, as the types they make:
#: a Fake License's license, the tradition of a magical supply
_PICKS = {"selectrestricted": "Restricted", "selecttradition": "Tradition"}


#: The weapon category tags `CreateWeaponCategoryImprovement` handles, as the
#: types they make
_WEAPON_CATEGORY = {
    "weaponcategorydv": "WeaponCategoryDV",
    "weaponcategorydice": "WeaponCategoryDice",
    "weaponcategoryap": "WeaponCategoryAP",
    "weaponcategoryaccuracy": "WeaponCategoryAccuracy",
    "weaponcategoryreach": "WeaponCategoryReach",
}


#: Tags whose improvement carries no value, as the types they make
_FLAGS = {
    "ambidextrous": ("Ambidextrous", ""),
    "fame": ("Fame", ""),
    "mademan": ("MadeMan", ""),
    "unarmeddvphysical": ("UnarmedDVPhysical", ""),
    "adapsin": ("Adapsin", "adapsin"),
    # Resonant Stream: Technoshaman: Chummer lets a sprite be fettered only
    # while this improvement is there, and nothing here fetters one
    "allowspritefettering": ("AllowSpriteFettering", ""),
    **{
        f"{kind}{vector}immune": (f"{kind.title()}{vector.title()}Immune", "")
        for kind in ("toxin", "pathogen")
        for vector in ("contact", "ingestion", "inhalation", "injection")
    },
}


#: (type, the field naming the category or the descriptor) for the tags that
#: change the drain or the damage of some spells.
_SPELL_DRAIN = {
    "spellcategorydrain": ("SpellCategoryDrain", "category"),
    "spellcategorydamage": ("SpellCategoryDamage", "category"),
    "spelldescriptordrain": ("SpellDescriptorDrain", "descriptor"),
    "spelldescriptordamage": ("SpellDescriptorDamage", "descriptor"),
}

#: The karma and point cost tags, (type, whether `<name>` is the improved
#: name): every one of them is a single `CreateImprovement` of its `<name>`,
#: `<val>`, `<min>`, `<max>` and `<condition>`.
_COSTS = {
    "attributekarmacost": ("AttributeKarmaCost", True),
    "activeskillkarmacost": ("ActiveSkillKarmaCost", True),
    "skillgroupkarmacost": ("SkillGroupKarmaCost", True),
    "knowledgeskillkarmacost": ("KnowledgeSkillKarmaCost", True),
    "knowledgeskillkarmacostmin": ("KnowledgeSkillKarmaCostMinimum", False),
    "skillgroupcategorykarmacost": ("SkillGroupCategoryKarmaCost", True),
    "skillcategorykarmacost": ("SkillCategoryKarmaCost", True),
    "skillcategoryspecializationkarmacost": ("SkillCategorySpecializationKarmaCost", True),
    "attributepointcost": ("AttributePointCost", True),
    "activeskillpointcost": ("ActiveSkillPointCost", True),
    "skillgrouppointcost": ("SkillGroupPointCost", True),
    "knowledgeskillpointcost": ("KnowledgeSkillPointCost", True),
    "skillgroupcategorypointcost": ("SkillGroupCategoryPointCost", True),
    "skillcategorypointcost": ("SkillCategoryPointCost", True),
    "attributekarmacostmultiplier": ("AttributeKarmaCostMultiplier", True),
    "activeskillkarmacostmultiplier": ("ActiveSkillKarmaCostMultiplier", True),
    "skillgroupkarmacostmultiplier": ("SkillGroupKarmaCostMultiplier", True),
    "knowledgeskillkarmacostmultiplier": ("KnowledgeSkillKarmaCostMultiplier", True),
    "skillgroupcategorykarmacostmultiplier": ("SkillGroupCategoryKarmaCostMultiplier", True),
    "skillcategorykarmacostmultiplier": ("SkillCategoryKarmaCostMultiplier", True),
    "skillcategoryspecializationkarmacostmultiplier": ("SkillCategorySpecializationKarmaCostMultiplier", True),
    "attributepointcostmultiplier": ("AttributePointCostMultiplier", True),
    "activeskillpointcostmultiplier": ("ActiveSkillPointCostMultiplier", True),
    "skillgrouppointcostmultiplier": ("SkillGroupPointCostMultiplier", True),
    "knowledgeskillpointcostmultiplier": ("KnowledgeSkillPointCostMultiplier", True),
    "skillgroupcategorypointcostmultiplier": ("SkillGroupCategoryPointCostMultiplier", True),
    "skillcategorypointcostmultiplier": ("SkillCategoryPointCostMultiplier", True),
}

#: Tags whose improvement is their number and nothing else — every
#: `AddImprovementCollection` method that is one `CreateImprovement` of the
#: tag's text as the value.
_NUMBERS = {
    "surprise": "Surprise",
    "spellresistance": "SpellResistance",
    "mentalmanipulationresist": "MentalManipulationResist",
    "physicalmanipulationresist": "PhysicalManipulationResist",
    "manaillusionresist": "ManaIllusionResist",
    "physicalillusionresist": "PhysicalIllusionResist",
    "detectionspellresist": "DetectionSpellResist",
    "directmanaspellresist": "DirectManaSpellResist",
    "directphysicalspellresist": "DirectPhysicalSpellResist",
    "decreasebodresist": "DecreaseBODResist",
    "decreaseagiresist": "DecreaseAGIResist",
    "decreaserearesist": "DecreaseREAResist",
    "decreasestrresist": "DecreaseSTRResist",
    "decreasecharesist": "DecreaseCHAResist",
    "decreaseintresist": "DecreaseINTResist",
    "decreaselogresist": "DecreaseLOGResist",
    "decreasewilresist": "DecreaseWILResist",
    "nuyenmaxbp": "NuyenMaxBP",
    "unarmeddv": "UnarmedDV",
    "unarmedap": "UnarmedAP",
    "unarmedreach": "UnarmedReach",
    "initiative": "Initiative",
    "initiativediceadd": "InitiativeDiceAdd",
    "matrixinitiative": "MatrixInitiative",
    "biowareessmultiplier": "BiowareEssCost",
    "biowaretotalessmultiplier": "BiowareTotalEssMultiplier",
    "cyberwareessmultiplier": "CyberwareEssCost",
    "cyberwaretotalessmultiplier": "CyberwareTotalEssMultiplier",
    "biowareessmultipliernonretroactive": "BiowareEssCostNonRetroactive",
    "biowaretotalessmultipliernonretroactive": "BiowareTotalEssMultiplierNonRetroactive",
    "cyberwareessmultipliernonretroactive": "CyberwareEssCostNonRetroactive",
    "cyberwaretotalessmultipliernonretroactive": "CyberwareTotalEssMultiplierNonRetroactive",
    "nativelanguagelimit": "NativeLanguageLimit",
    "freepositivequalities": "FreePositiveQualities",
    "freenegativequalities": "FreeNegativeQualities",
    "freespiritpowerpoints": "FreeSpiritPowerPoints",
    "adeptpowerpoints": "AdeptPowerPoints",
    "armorencumbrancepenalty": "ArmorEncumbrancePenalty",
    "damageresistance": "DamageResistance",
    "judgeintentions": "JudgeIntentions",
    "judgeintentionsoffense": "JudgeIntentionsOffense",
    "judgeintentionsdefense": "JudgeIntentionsDefense",
    "composure": "Composure",
    "liftandcarry": "LiftAndCarry",
    "memory": "Memory",
    "fatigueresist": "FatigueResist",
    "radiationresist": "RadiationResist",
    "sonicresist": "SonicResist",
    "toxincontactresist": "ToxinContactResist",
    "toxiningestionresist": "ToxinIngestionResist",
    "toxininhalationresist": "ToxinInhalationResist",
    "toxininjectionresist": "ToxinInjectionResist",
    "pathogencontactresist": "PathogenContactResist",
    "pathogeningestionresist": "PathogenIngestionResist",
    "pathogeninhalationresist": "PathogenInhalationResist",
    "pathogeninjectionresist": "PathogenInjectionResist",
    "physiologicaladdictionfirsttime": "PhysiologicalAddictionFirstTime",
    "psychologicaladdictionfirsttime": "PsychologicalAddictionFirstTime",
    "physiologicaladdictionalreadyaddicted": "PhysiologicalAddictionAlreadyAddicted",
    "psychologicaladdictionalreadyaddicted": "PsychologicalAddictionAlreadyAddicted",
    "stuncmrecovery": "StunCMRecovery",
    "physicalcmrecovery": "PhysicalCMRecovery",
    "concealability": "Concealability",
    "drainresist": "DrainResistance",
    "fadingresist": "FadingResistance",
    "notoriety": "Notoriety",
    "streetcred": "StreetCred",
    "streetcredmultiplier": "StreetCredMultiplier",
    "complexformlimit": "ComplexFormLimit",
    "spelllimit": "SpellLimit",
    "throwrange": "ThrowRange",
    "throwrangestr": "ThrowRangeSTR",
    "throwstr": "ThrowSTR",
    "essencepenalty": "EssencePenalty",
    "essencepenaltyt100": "EssencePenaltyT100",
    "essencepenaltymagonlyt100": "EssencePenaltyMAGOnlyT100",
    "essencepenaltyresonlyt100": "EssencePenaltyRESOnlyT100",
    "essencepenaltydeponlyt100": "EssencePenaltyDEPOnlyT100",
    "specialattburnmultiplier": "SpecialAttBurn",
    "specialatttotalburnmultiplier": "SpecialAttTotalBurnMultiplier",
    "essencemax": "EssenceMax",
    "publicawareness": "PublicAwareness",
    "metageniclimit": "MetageneticLimit",
    "specialmodificationlimit": "SpecialModificationLimit",
    "contactkarma": "ContactKarmaDiscount",
    "contactkarmaminimum": "ContactKarmaMinimum",
}

#: `livingpersona`'s children, as the types they make
_PERSONA = {
    "devicerating": "LivingPersonaDeviceRating",
    "programlimit": "LivingPersonaProgramLimit",
    "attack": "LivingPersonaAttack",
    "sleaze": "LivingPersonaSleaze",
    "dataprocessing": "LivingPersonaDataProcessing",
    "firewall": "LivingPersonaFirewall",
}

#: `AttributeSection.AttributeStrings`, plus the `BOX` `cyberseeker` takes
_SEEKER = {"BOD", "AGI", "REA", "STR", "CHA", "INT", "LOG", "WIL", "EDG", "MAG", "MAGAdept", "RES", "ESS", "DEP", "BOX"}


#: `AddImprovementCollection.enabletab`: the tab names it knows, as it saves them
_TABS = {
    "MAGICIAN": "Magician",
    "ADEPT": "Adept",
    "TECHNOMANCER": "Technomancer",
    "ADVANCED PROGRAMS": "Advanced Programs",
    "CRITTER": "Critter",
}
