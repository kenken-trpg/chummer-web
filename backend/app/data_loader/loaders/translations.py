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
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            log.warning("ja-jp_data.xml parse failed: %s", exc)
        else:
            for node in root.iter():
                name = _text(node.find("name"))
                trans = _text(node.find("translate"))
                if name and trans:
                    mapping[name] = trans
    overrides = _load_ja_overrides("data.json")
    if overrides:
        log.info("applied %d ja_overrides/data.json entries", len(overrides))
        mapping.update(overrides)
    return mapping


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
            root = ET.parse(path).getroot()
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
