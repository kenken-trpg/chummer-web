"""Japanese translation + UI-string overlays."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET

from .._xml import LANG_DIR, OVERRIDE_DIR, _text, log


def _load_ja_overrides(filename: str) -> dict[str, str]:
    """Read a Git-tracked JSON overlay of {key: japanese}. Missing or malformed
    files are ignored so a bad edit never breaks catalog loading."""
    path = OVERRIDE_DIR / filename
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        log.warning("ja override %s load failed: %s", filename, exc)
        return {}
    if not isinstance(raw, dict):
        log.warning("ja override %s is not a JSON object", filename)
        return {}
    result: dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(key, str) and isinstance(value, str) and value.strip():
            result[key] = value
    return result


def load_translations() -> dict[str, str]:
    mapping: dict[str, str] = {}
    path = LANG_DIR / "ja-jp_data.xml"
    if path.exists():
        try:
            root = ET.parse(path).getroot()  # noqa: S314 -- vendored lang file
        except ET.ParseError as exc:
            log.warning("ja-jp_data.xml parse failed: %s", exc)
        else:
            # file each name's translation came from, e.g. "gear.xml"
            origin: dict[str, str] = {}
            for section in root:
                file = section.get("file") or ""
                for node in section.iter():
                    name = _text(node.find("name"))
                    trans = _text(node.find("translate"))
                    if not (name and trans):
                        continue
                    # An untranslated supplement repeats the English as its
                    # "translation". Within one file that is the same thing
                    # again, and must not undo the real translation found
                    # earlier (Vampire ヴァンパイア, Matches マッチ). Across files
                    # it is a different thing — the gear Shade is not the
                    # critter 翳り — so there the last one still wins.
                    if trans == name and origin.get(name) == file and mapping[name] != name:
                        continue
                    mapping[name] = trans
                    origin[name] = file
    overrides = _load_ja_overrides("data.json")
    if overrides:
        log.info("applied %d ja_overrides/data.json entries", len(overrides))
        mapping.update(overrides)
    return mapping


def load_skill_group_names() -> dict[str, str]:
    """English skill-group name -> Japanese, from `<skillgroups>` in the lang
    file, with `ja_overrides/data.json` layered on top.

    This is deliberately *not* part of `load_translations`. That table is keyed
    by English name alone, and the group names collide with unrelated entities:
    "Influence" and "Stealth" are also spells, "Firearms" and "Engineering" are
    also knowledge skills. The flat table therefore rendered the Influence group
    as the spell's 感化 rather than 対人, and folding these 15 entries into it
    would break the collision the other way. A separate map lets the skills UI
    ask for the group reading without disturbing anything else.

    The upstream entries use `<name translate="運動">Athletics</name>` — the
    translation is an *attribute* and the English is the element text, which is
    why `load_translations`, which reads child `<name>`/`<translate>` elements,
    never saw them.
    """
    path = LANG_DIR / "ja-jp_data.xml"
    names: dict[str, str] = {}
    if path.exists():
        try:
            root = ET.parse(path).getroot()  # noqa: S314 -- vendored lang file
        except ET.ParseError as exc:
            log.warning("ja-jp_data.xml parse failed: %s", exc)
        else:
            for node in root.findall(".//skillgroups/name"):
                english = (node.text or "").strip()
                japanese = (node.get("translate") or "").strip()
                if english and japanese:
                    names[english] = japanese
    overrides = _load_ja_overrides("data.json")
    return {en: overrides.get(en, ja) for en, ja in names.items()}


def load_book_names() -> dict[str, str]:
    """Book `<id>` -> the title the Japanese lang file gives it.

    Kept out of `load_translations` for the same reason as the skill groups:
    that table is keyed by English name alone, and "Lockdown" is both a book
    and the core-rulebook program. The program's ロックダウン came later in the
    file and won, so an untranslated supplement showed a katakana title. By
    `<id>` the two cannot meet.

    `ja_overrides/data.json` still applies by English title — that is where
    ラン＆ガン and シャドウラン 第5版 come from, since the lang file leaves every
    title in English. Book titles do not collide with anything in the overlay.
    """
    path = LANG_DIR / "ja-jp_data.xml"
    if not path.exists():
        return {}
    try:
        root = ET.parse(path).getroot()  # noqa: S314 -- vendored lang file
    except ET.ParseError as exc:
        log.warning("ja-jp_data.xml parse failed: %s", exc)
        return {}
    overrides = _load_ja_overrides("data.json")
    names: dict[str, str] = {}
    for node in root.findall(".//books/book"):
        book_id = _text(node.find("id"))
        title = _text(node.find("name"))
        trans = overrides.get(title) or _text(node.find("translate"))
        if book_id and trans:
            names[book_id] = trans
    return names


#: The kinds `ja_overrides/by_kind.json` may name. The UI picks one per
#: screen (the skills tab, the ware tab, …) — see `scopeTr` in lib/ui-strings.ts.
TRANSLATION_KINDS = (
    "armor",
    "critter_power",
    "cyberware",
    "gear",
    "knowledge_skill",
    "power",
    "skill",
)


def load_translations_by_kind() -> dict[str, dict[str, str]]:
    """`{kind: {english: japanese}}` for the names `load_translations` gets
    wrong because another kind of thing shares them: the magic skill Binding
    is 束縛, but the flat table holds the critter power's 接着.

    Hand-curated in `ja_overrides/by_kind.json` rather than derived from the
    lang file by section. Split mechanically, the critter power Fear would lose
    the spirit power's 恐怖 and go back to English, and most of the ~90
    cross-section collisions are that kind — a borrowed reading that is right.
    Only the ones that name a different thing are listed.
    """
    path = OVERRIDE_DIR / "by_kind.json"
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        log.warning("ja override by_kind.json load failed: %s", exc)
        return {}
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, str]] = {}
    for kind, names in raw.items():
        if kind not in TRANSLATION_KINDS or not isinstance(names, dict):
            log.warning("ja override by_kind.json: unknown kind %r", kind)
            continue
        result[kind] = {k: v for k, v in names.items() if isinstance(k, str) and isinstance(v, str) and v.strip()}
    return result


#: Locale -> the vendored Chummer lang file it comes from. `en-us.xml` was
#: already being fetched by scripts/fetch_chummer_data.py; nothing read it.
LANG_FILES = {"ja": "ja-jp.xml", "en": "en-us.xml"}

#: The app reads `ui_strings` through `attrShort` / `attrName` / `attrLabel`
#: only, and those build exactly `String_Attribute<KEY>Short|Long`. The lang
#: files carry ~2,600 keys each; shipping both locales whole would put ~330 KB
#: of never-read text in a catalog that is already 2.9 MB, so the projection
#: keeps this prefix and drops the rest.
UI_STRING_PREFIXES = ("String_Attribute",)


def shipped_ui_keys() -> set[str]:
    """The keys `public_catalog` carries: the prefix above, plus every key in
    `ja_overrides/ui.json`.

    The overlay is a hand-curated set — someone chose those 25-odd strings and
    wrote a Japanese term for each — so dropping them for being unread today
    would quietly throw that work away, and it costs a few hundred bytes to
    keep. Adding a key to ui.json therefore also ships it.

    Widen `UI_STRING_PREFIXES` (or add to ui.json) before reading a new key:
    a miss is not fatal, since `makeT` falls back to the caller's default and
    then to the key itself, but it renders as a raw `String_Foo`.
    """
    return set(_load_ja_overrides("ui.json"))


def load_ui_strings(locale: str = "ja") -> dict[str, str]:
    """Every UI string for `locale`, unnarrowed. The Japanese overlay in
    `ja_overrides/ui.json` is merged on top of `ja` only — it exists to correct
    the vendored Japanese, and has nothing to say about the English original."""
    filename = LANG_FILES.get(locale)
    if filename is None:
        log.warning("no lang file for locale %r", locale)
        return {}
    path = LANG_DIR / filename
    strings: dict[str, str] = {}
    if path.exists():
        try:
            root = ET.parse(path).getroot()  # noqa: S314 -- vendored lang file
        except ET.ParseError as exc:
            log.warning("%s parse failed: %s", filename, exc)
        else:
            for node in root.findall(".//string"):
                key = node.get("key") or _text(node.find("key"))
                text = _text(node.find("text")) or _text(node.find("translate")) or _text(node)
                if key and text:
                    strings[key] = text
    if locale != "ja":
        return strings
    overrides = _load_ja_overrides("ui.json")
    if overrides:
        log.info("applied %d ja_overrides/ui.json entries", len(overrides))
        strings.update(overrides)
    return strings


def load_ui_strings_by_locale() -> dict[str, dict[str, str]]:
    """`{locale: {key: text}}`, narrowed to `shipped_ui_keys`."""
    curated = shipped_ui_keys()
    return {
        locale: {
            key: text
            for key, text in load_ui_strings(locale).items()
            if key.startswith(UI_STRING_PREFIXES) or key in curated
        }
        for locale in LANG_FILES
    }
