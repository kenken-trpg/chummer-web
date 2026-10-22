"""A matching desktop settings file for a life-module character.

Chummer 5.222.0 recognises LifeModule, but takes the effective build method
and enabled books from the selected settings file. Pointing at Standard
therefore prompts for another setting and can change the build method.
Custom settings use a zero source GUID and are looked up by file name.
"""

from __future__ import annotations

import hashlib
import io
import xml.etree.ElementTree as ET
import zipfile
from copy import deepcopy

from ..data_loader import catalog
from ..data_loader._xml import DATA_DIR, parse_vendored
from ..models import CharacterState, SettingsState
from ..settings_file import _ATTR_FIELDS, _BOOL_FIELDS, _INT_FIELDS, _KARMA_FIELDS


def life_module_settings(state: CharacterState) -> tuple[str, bytes]:
    """Return the exact settings key and XML to install in Chummer/settings."""
    root = _preset(state.settings.name)
    _set(root, "id", "00000000-0000-0000-0000-000000000000")
    _set(root, "name", "Chummer Web Life Modules")
    _set(root, "buildmethod", "LifeModule")
    _write_rules(root, state.settings)
    _write_lists(root, state.settings)
    ET.indent(root, space="  ")
    xml = ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"
    key = "chummer-web-life-module-" + hashlib.sha256(xml).hexdigest()[:16] + ".xml"
    return key, xml


def _preset(name: str) -> ET.Element:
    """A copy of the desktop preset the character's settings are named after, else Standard."""
    presets = parse_vendored(DATA_DIR / "settings.xml").findall("./settings/setting")
    preset = next((p for p in presets if p.findtext("name") == name), None)
    if preset is None:
        preset = next(p for p in presets if p.findtext("name") == "Standard")
    root = deepcopy(preset)
    root.tag = "settings"
    return root


def _set(parent: ET.Element, tag: str, value: object) -> None:
    node = parent.find(tag)
    if node is None:
        node = ET.SubElement(parent, tag)
    node.text = str(value)


def _write_rules(root: ET.Element, settings: SettingsState) -> None:
    """Every rule the character's settings change, over the preset's own values."""
    # LifeModule has a 750-karma pool and RF caps, independently of Standard.
    _set(root, "buildpoints", settings.karma_chargen_pool if settings.karma_chargen_pool is not None else 750)
    _set(root, "maxskillratingcreate", settings.chargen_skill_max if settings.chargen_skill_max is not None else 7)
    _set(
        root,
        "maxknowledgeskillratingcreate",
        settings.chargen_knowledge_skill_max if settings.chargen_knowledge_skill_max is not None else 9,
    )
    for tag, field in (_INT_FIELDS | _BOOL_FIELDS).items():
        if field in {"chargen_karma", "chargen_skill_max", "chargen_knowledge_skill_max"}:
            continue
        value = getattr(settings, field)
        if value is not None:
            _set(root, tag, value)
    costs = root.find("karmacost")
    if costs is None:
        costs = ET.SubElement(root, "karmacost")
    for tag, field in _KARMA_FIELDS.items():
        value = getattr(settings, field)
        if value is not None:
            _set(costs, tag, value)
    for tag, field in _ATTR_FIELDS.items():
        value = getattr(settings, field)
        if value is not None:
            _set(root, tag, "{" + value + "}")
    for field, tag in {
        "knowledge_points_expression": "knowledgepointsexpression",
        "exclude_limb_slot": "excludelimbslot",
        "priority_table": "prioritytable",
    }.items():
        value = getattr(settings, field)
        if value is not None:
            _set(root, tag, value)
    if settings.contact_free_mult is not None:
        _set(root, "contactpointsexpression", "{CHAUnaug} * " + str(settings.contact_free_mult))
    if settings.karma_to_nuyen is not None:
        _set(root, "nuyenperbpwftp", settings.karma_to_nuyen)
        _set(root, "chargenkarmatonuyenexpression", "{Karma} * " + str(settings.karma_to_nuyen) + " + {PriorityNuyen}")


def _write_lists(root: ET.Element, settings: SettingsState) -> None:
    """The books, custom data and banned grades, replacing the preset's lists."""
    for tag in ("books", "customdatadirectorynames", "bannedwaregrades"):
        old = root.find(tag)
        if old is not None:
            root.remove(old)
    books = ET.SubElement(root, "books")
    for code in sorted(settings.books or [book["code"] for book in catalog()["books"]]):
        ET.SubElement(books, "book").text = code
    directories = ET.SubElement(root, "customdatadirectorynames")
    for name in settings.customdata:
        directory = ET.SubElement(directories, "customdatadirectoryname")
        ET.SubElement(directory, "directoryname").text = name
        ET.SubElement(directory, "enabled").text = "True"
    grades = ET.SubElement(root, "bannedwaregrades")
    for grade in settings.banned_ware_grades:
        ET.SubElement(grades, "grade").text = grade


def life_module_bundle(state: CharacterState) -> bytes:
    """A character and the matching desktop settings, installed together."""
    from . import state_to_chum5

    key, settings = life_module_settings(state)
    instructions = (
        "Chummer 5.222.0 / Life Modules\n\n"
        "1. Chummerを終了し、settings/内のXMLをChummer本体のsettingsフォルダーへコピーしてください。\n"
        "2. Chummerを起動し、全体設定でLife Modulesを有効にしてください（試験機能です）。\n"
        "3. character.chum5を開いてください。作成方式はLifeModule、設定名はChummer Web Life Modulesです。\n"
        "4. Chummerで保存する場合は別名保存し、アプリのJSONバックアップも保管してください。\n"
        "Chummerの再保存ではアプリ固有の選択・超過移し替え履歴が消えるため、アプリへの再取り込みはできません。\n"
        "カスタムデータを使用している場合は、同じデータをChummerにもインストールしてください。\n\n"
        "Close Chummer, copy the XML under settings/ into Chummer's settings directory,\n"
        "then enable Life Modules in global options and open character.chum5.\n"
        "Use Save As and keep the web app's JSON backup. Desktop resaves lose the\n"
        "web app's module choices and overflow transfer history and cannot be re-imported.\n"
    )
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("character.chum5", state_to_chum5(state))
        archive.writestr("settings/" + key, settings)
        archive.writestr("README.txt", instructions)
    return stream.getvalue()
