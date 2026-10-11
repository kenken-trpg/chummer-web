"""Quality-level groups used by Chummer's ``<qualitylevel>`` improvement."""

from __future__ import annotations

from .._xml import _text, data_root


def load_quality_levels() -> dict[str, dict[int, str]]:
    root = data_root("qualitylevels.xml")
    if root is None:
        return {}
    groups: dict[str, dict[int, str]] = {}
    for group in root.findall("./qualitygroups/qualitygroup"):
        name = _text(group.find("name"))
        if not name:
            continue
        levels: dict[int, str] = {}
        for node in group.findall("./levels/level"):
            value = node.get("value")
            try:
                rating = int(value or "")
            except ValueError:
                continue
            quality = _text(node)
            if rating > 0 and quality:
                levels[rating] = quality
        if levels:
            groups[name] = levels
    return groups
