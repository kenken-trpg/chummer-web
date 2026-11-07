"""Exotic skills, contacts and martial arts."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class ExoticSkillInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    skill_name: str
    extra: str = ""
    rating: int = 1


class ContactInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    role: str | None = None
    connection: int = 1
    loyalty: int = 1
    group: bool = False
    free: bool = False
    forced_loyalty: int | None = None
    force_group: bool = False
    source_quality_id: str | None = None
    free_connection: int = 0
    free_loyalty: int = 0
    #: the player's own description of the contact, kept as Chummer saves it
    #: (`Contact.Save`): where they are, who they are, what they want, and notes.
    #: Nothing is computed from these; like the character's own notes, no
    #: length cap, so a Chummer save with long notes still comes in.
    location: str = ""
    metatype: str = ""
    gender: str = ""
    age: str = ""
    contact_type: str = ""
    preferred_payment: str = ""
    hobbies_vice: str = ""
    personal_life: str = ""
    notes: str = ""


#: those fields, each under the element Chummer saves it in
CONTACT_DETAIL_TAGS: dict[str, str] = {
    "location": "location",
    "metatype": "metatype",
    "gender": "gender",
    "age": "age",
    "contact_type": "contacttype",
    "preferred_payment": "preferredpayment",
    "hobbies_vice": "hobbiesvice",
    "personal_life": "personallife",
    "notes": "notes",
}


class MartialArtInstall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    art_id: str
    techniques: list[str] = Field(default_factory=list)
    free: bool = False
    source_quality_id: str | None = None
