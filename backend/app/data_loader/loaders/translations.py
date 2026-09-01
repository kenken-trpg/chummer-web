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


def load_ui_strings() -> dict[str, str]:
    path = LANG_DIR / "ja-jp.xml"
    strings: dict[str, str] = {}
    if path.exists():
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            log.warning("ja-jp.xml parse failed: %s", exc)
        else:
            for node in root.findall(".//string"):
                key = node.get("key") or _text(node.find("key"))
                text = _text(node.find("text")) or _text(node.find("translate")) or _text(node)
                if key and text:
                    strings[key] = text
    overrides = _load_ja_overrides("ui.json")
    if overrides:
        log.info("applied %d ja_overrides/ui.json entries", len(overrides))
        strings.update(overrides)
    return strings
