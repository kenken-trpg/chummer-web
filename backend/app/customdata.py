"""Apply Chummer `customdata/` directories on top of the vendored XML.

A settings file names custom-data directories by `<guid>>version`; each holds a
`manifest.xml` plus `custom_*.xml` (new entries) and `amend_*.xml` (edits to
existing ones). Chummer merges them into the base data before anything is read,
and so does this: the merge happens on the XML tree, upstream of every loader,
so a martial art added here is indistinguishable from one that shipped.

## The amend dialect

Chummer's amend engine is large — xpath filters, `replace`, `recurse`,
`regexreplace`. This implements the part real custom data uses, which turns out
to be four things:

* a node with an `<id>` (or `<name>`) edits the base node with that id: each
  child element in the amend replaces the base's child of the same tag,
* `amendoperation="addnode"` appends the child instead of replacing,
* `amendoperation="remove"` deletes the base's child of that tag,
* `pathfilter="field='value'"` selects the nodes to edit by a field rather than
  by id, so one rule can touch a whole category.

Anything else is skipped and reported rather than half-applied — a house rule
that silently did nothing is the failure mode this whole feature exists to
avoid.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .data_loader._xml import data_root

#: `<technique amendoperation="addnode">` etc.
_OP = "amendoperation"
#: `pathfilter="category='Cultured'"` — the only predicate shape seen in the
#: wild, and the only one worth guessing at.
_PATHFILTER = re.compile(r"^\s*(\w+)\s*=\s*'([^']*)'\s*$")

#: Elements that identify a node rather than describe it. Present in an amend
#: to say *which* node is meant, so writing them back is a no-op — but they
#: must not be treated as edits, or a `pathfilter` rule would stamp its
#: selector onto every node it matched.
_SELECTORS = ("id", "name")


@dataclass
class MergeReport:
    """What a merge did, and what it could not do.

    Surfaced to the user: custom data that half-applied is worse than custom
    data that refused, because the sheet still looks right.
    """

    applied: int = 0
    #: `(file, reason)` for rules that were skipped.
    skipped: list[tuple[str, str]] = field(default_factory=list)

    def skip(self, source: str, reason: str) -> None:
        self.skipped.append((source, reason))


def dataset_hash(files: dict[str, bytes]) -> str:
    """A content address for one custom-data set.

    The client sends this instead of the files; the server keeps merged
    catalogs under it. Path and content both feed the digest, so renaming a
    file is a different dataset — it can change load order, which changes the
    result.
    """
    digest = hashlib.blake2b(digest_size=16)
    for path in sorted(files):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(files[path])
        digest.update(b"\0")
    return digest.hexdigest()


def _fold(value: str) -> str:
    """The form two names are compared in.

    Case, because a manifest writes `5682BC90-…` where the settings file that
    refers to it writes `5682bc90-…`. Unicode normalisation, because a
    directory named in Japanese arrives NFD from a macOS filesystem and NFC
    from the XML that names it — the same directory, byte-different.
    """
    return unicodedata.normalize("NFC", value).strip().casefold()


def manifest_key(raw: bytes) -> str | None:
    """`manifest.xml` -> the `<guid>>version` a settings file refers to it by."""
    try:
        root = ET.fromstring(raw.decode("utf-8-sig", errors="replace"))
    except ET.ParseError:
        return None
    guid = (root.findtext("guid") or "").strip()
    version = (root.findtext("version") or "").strip()
    return _fold(f"{guid}>{version}") if guid else None


def _matches(node: ET.Element, key: str, value: str) -> bool:
    return (node.findtext(key) or "").strip() == value


def _targets(base_list: ET.Element, rule: ET.Element) -> list[ET.Element]:
    """The base nodes one amend rule applies to."""
    predicate = rule.get("pathfilter")
    if predicate:
        found = _PATHFILTER.match(predicate)
        if not found:
            return []
        key, value = found.group(1), found.group(2)
        return [n for n in base_list if n.tag == rule.tag and _matches(n, key, value)]
    for key in _SELECTORS:
        wanted = (rule.findtext(key) or "").strip()
        if wanted:
            return [n for n in base_list if n.tag == rule.tag and _matches(n, key, wanted)]
    return []


def _apply_children(target: ET.Element, rule: ET.Element) -> None:
    """Fold one amend rule's children into the base node it matched."""
    for child in rule:
        op = child.get(_OP)
        if op == "addnode":
            clone = _stripped(child)
            target.append(clone)
            continue
        existing = target.find(child.tag)
        if op == "remove":
            if existing is not None:
                target.remove(existing)
            continue
        if child.tag in _SELECTORS:
            continue  # it named the node; it is not an edit
        if len(child) and existing is not None:
            # a container (`<techniques>`): recurse so `addnode` lands inside
            # it rather than replacing the whole list
            _apply_children(existing, child)
            continue
        if existing is not None:
            target.remove(existing)
        target.append(_stripped(child))


def _stripped(node: ET.Element) -> ET.Element:
    """A copy with the amend bookkeeping attributes gone, so nothing
    downstream has to know this element arrived through a merge."""
    clone = ET.Element(node.tag, {k: v for k, v in node.attrib.items() if k not in (_OP, "pathfilter")})
    clone.text, clone.tail = node.text, node.tail
    for child in node:
        clone.append(_stripped(child))
    return clone


def apply_amend(base: ET.Element, amend: ET.Element, source: str, report: MergeReport) -> None:
    """`amend_*.xml` -> edits on the base tree.

    Both are `<chummer>` roots holding one list element per kind
    (`<qualities>`, `<martialarts>`); rules are matched inside the list of the
    same tag.
    """
    for amend_list in amend:
        base_list = base.find(amend_list.tag)
        if base_list is None:
            report.skip(source, f"<{amend_list.tag}> is not in the base data")
            continue
        for rule in amend_list:
            if rule.get(_OP) == "addnode":
                base_list.append(_stripped(rule))
                report.applied += 1
                continue
            targets = _targets(base_list, rule)
            if not targets:
                name = (rule.findtext("name") or rule.findtext("id") or rule.tag).strip()
                report.skip(source, f"no <{rule.tag}> matches {name!r}")
                continue
            for target in targets:
                _apply_children(target, rule)
                report.applied += 1


def apply_custom(base: ET.Element, custom: ET.Element, source: str, report: MergeReport) -> None:
    """`custom_*.xml` -> new entries appended to the matching list.

    A list the base does not have is created rather than skipped: a custom
    file may be the only source of, say, `<books>` in a data file that had
    none.
    """
    for custom_list in custom:
        base_list = base.find(custom_list.tag)
        if base_list is None:
            base_list = ET.SubElement(base, custom_list.tag)
        for entry in custom_list:
            base_list.append(_stripped(entry))
            report.applied += 1
        if not len(custom_list):
            report.skip(source, f"<{custom_list.tag}> is empty")


# --- turning uploaded files into an overlay ----------------------------- #


#: `custom_qualities.xml` / `amend_qualities.xml` -> `qualities.xml`. Chummer
#: names custom files after the base file they extend.
_PREFIXES = ("custom_", "amend_", "override_")


def base_file_of(filename: str) -> str | None:
    """The vendored data file a custom-data file applies to, or `None` if the
    name is not one of Chummer's."""
    for prefix in _PREFIXES:
        if filename.startswith(prefix):
            return filename[len(prefix) :]
    return None


def _directory_of(path: str) -> str:
    return path.split("/", 1)[0] if "/" in path else ""


def build_overlay(
    files: Mapping[str, bytes],
    enabled: Sequence[str],
) -> tuple[dict[str, ET.Element], MergeReport]:
    """Merge the enabled custom-data directories into copies of the base files.

    `files` is the uploaded tree keyed by `<directory>/<file>`; `enabled` is
    the settings file's `<customdatadirectoryname>` list, in the order it gave
    them — order decides who wins when two directories touch the same entry,
    which is why it is not sorted here.

    A directory the settings asked for but the upload does not contain is
    reported rather than skipped quietly: the character was built against it.
    """
    report = MergeReport()
    by_key: dict[str, str] = {}
    for path, raw in files.items():
        if path.endswith("manifest.xml"):
            key = manifest_key(raw)
            if key:
                by_key[key] = _directory_of(path)

    trees: dict[str, ET.Element] = {}

    def base_tree(name: str) -> ET.Element | None:
        if name not in trees:
            root = data_root(name)
            if root is None:
                return None
            # a copy: the overlay must not edit the tree another request reads
            trees[name] = ET.fromstring(ET.tostring(root, encoding="unicode"))
        return trees[name]

    by_directory = {_fold(_directory_of(p)): _directory_of(p) for p in files if "/" in p}
    for wanted in enabled:
        # tolerate a settings file naming the directory rather than the guid,
        # which is what a hand-edited one usually does
        directory = by_key.get(_fold(wanted)) or by_directory.get(_fold(wanted))
        if directory is None:
            report.skip(wanted, "the custom data for this entry was not supplied")
            continue
        for path in sorted(files):
            if _directory_of(path) != directory:
                continue
            filename = path.rsplit("/", 1)[-1]
            base_name = base_file_of(filename)
            if base_name is None:
                continue  # manifest.xml, or something Chummer would ignore too
            base = base_tree(base_name)
            if base is None:
                report.skip(path, f"{base_name} is not part of this app's data")
                continue
            text = files[path].decode("utf-8-sig", errors="replace")
            if "<chummer" not in text:
                # A placeholder: several published packs ship a licence header
                # with no root element. There is no rule in it to drop, so this
                # is not something to report.
                continue
            try:
                node = ET.fromstring(text)
            except ET.ParseError as exc:
                report.skip(path, f"not valid XML: {exc}")
                continue
            if filename.startswith("amend_"):
                apply_amend(base, node, path, report)
            else:
                apply_custom(base, node, path, report)
    return trees, report
