"""Shadowrun Codex (シャドウラン・コデックス), the Japanese-original supplement.

Chummer does not know it: its books.xml has no such book. The rules it brings
are not new, though — pp.198-204 quote and translate items from untranslated
English supplements (Chrome Flesh, Data Trails, Run Faster, Hard Targets, Kill
Code, Better than Bad), all of which Chummer already carries. So the Codex is
a second place those items are printed: ticking it makes them buyable even
with their own English book off, and each row names its Codex page.

Rows are matched by Chummer id, not name — one CSV line can be several
Chummer entries (Tough as Nails comes in a Physical and a Stun version,
Easy Breakdown powered and unpowered).
"""

from __future__ import annotations

from typing import Any

CODE = "SRCX"
BOOK = {"code": CODE, "name": "Shadowrun Codex", "name_ja": "シャドウラン・コデックス"}

#: Chummer id -> (Codex page, Codex's Japanese name).
ITEMS: dict[str, tuple[str, str]] = {
    # 有利な資質 / 不利な資質
    "23bfa65d-9241-4183-b7ea-0e2935e42f29": ("198", "インプラント適合性（サイバーウェア）"),
    "dcecd7e5-8cf1-4f83-89fa-177e28cfba03": ("198", "インプラント適合性（バイオウェア）"),
    "08c4dfad-3661-48d9-a265-43cce84e20d8": ("198", "プロトタイプ・トランスヒューマン"),
    "b47319f5-372d-4e23-9fd9-a8e4aecd4c85": ("198", "サイバー・シンギュラリティの探求者"),
    "38deea18-76f0-49a3-95ba-50006e4e7f90": ("199", "リミッター解除"),
    "2e3e5050-c77b-4ad8-8f7a-eff1b94b64a0": ("199", "特異なデータ"),
    "d62880dd-3e28-4b0c-8c71-dc0e4b72397b": ("199", "オタクからテクノマンサー"),
    "554ca59c-22e6-46ef-9b05-250ec8abd728": ("199", "オーバークロッカー"),
    "fd78fa11-5ab6-40db-bdb8-9fd722b08054": ("199", "時間感覚"),
    "ce939b04-5fc6-49e9-a747-9c9d1254449e": ("199", "規制品"),
    "3deeaa50-96d3-4c21-8f09-b9c224af5de3": ("199", "頑丈（肉体）"),
    "798c8081-d7a8-4c11-8d6f-80fb12a48062": ("199", "頑丈（朦朧）"),
    "8bdd4868-191c-4c28-800b-526cb39f7786": ("200", "マトリックスと一体 I"),
    "3c83d73e-7aa7-4fe5-8f03-6e983648e2eb": ("200", "マトリックスと一体 II"),
    "b705a89c-219c-432c-ab47-98ff6c975b4a": ("200", "マトリックスと一体 III"),
    "ef40cac3-d81e-4c7f-b14d-46abfd2f9dff": ("200", "本能的ハッキング"),
    "31e3097d-68c4-4140-969d-91bd43612afd": ("200", "ハイレズ"),
    "1e3d8aff-c31c-41f9-8c62-e3332cac79fa": ("200", "賞金首"),
    # 武器の改造
    "5d819147-d262-48c2-bb0e-80e0049c67ed": ("200", "セラミック/プラスティール素材"),
    "5cc39a55-3973-4368-81ee-c7a5c0432323": ("200", "カメレオンコーティング（ピストル）"),
    "98c9ed33-2636-40bb-a455-334e8fb8e65f": ("200", "カメレオンコーティング（ライフル）"),
    "83902f51-5f87-444f-a3ff-a74ce865e1af": ("201", "簡易分解（非電動）"),
    "f27402fa-2845-4314-a97d-2747b3263e0d": ("201", "簡易分解（電動）"),
    "d5abeadd-fba4-47f9-ac35-bfbb31ce34be": ("201", "銃身延長"),
    "85b01b5c-c788-4b43-8190-9e0c18391436": ("201", "カスタム・グリップ"),
    "225d5411-953e-4537-9e97-40bced059bd3": ("201", "ソウドオフ/銃身短縮"),
    "88d0e08b-1ac2-442e-8f2f-dfaeb9cda9ab": ("201", "ストック除去"),
    "01bb2926-c25f-4eba-acfc-aa4b14019607": ("201", "ソウドオフ/銃身短縮とストック除去"),
    # コムリンク・ドングル
    "d66c8cfa-2d00-4f5f-ac7a-eed5f5f7dde7": ("200", "アタック・ドングル"),
    "6c51c77c-7fb7-4ac4-aece-b800047d6d7f": ("200", "ケーブル・タップ"),
    "f52b8d11-f1ba-4fa2-9a1b-07a533b21b05": ("200", "ステルス・ドングル"),
    "78c6b0ef-4ac5-4623-bf52-4f299e84d036": ("200", "スタン・ドングル"),
    "e2689c1f-4dd1-40b7-8771-1bb5926b5ebf": ("200", "レシーバー"),
    # 追加サイバーリム
    "4630313c-aca9-4aa3-8fce-ba064423b1c7": ("202", "部分サイバースカル"),
    "f7ff7a58-ac0e-49a9-8cbe-741df59a33e5": ("203", "スケート"),  # also a gear item named Skates
    "fe394e6c-c9b4-492e-91a3-65b5e63692ed": ("203", "サイバーリム・アクセサリー：スキマー"),
    "f6b19dab-872b-423a-8cd3-f5811ff3ba00": ("203", "サイバーリム・アクセサリー：ウォータージェット"),
    # 追加バイオウェア
    "afbf823f-3116-4967-93d2-0e334bb35d3a": ("203", "小脳強化"),
    "aece83ad-cec8-4117-adbd-3ec5e2049372": ("203", "知識注入"),
    # 追加エコー
    "18269d5a-2750-4636-8ae3-f9f268d44577": ("204", "FFF"),
    "e7dc7a5a-89dc-42e4-8332-8225bbff3c45": ("204", "マスマジックス"),
    "262dd3e2-5433-4b9a-b637-c5f5a3af5510": ("204", "MMRI"),
    "032d5d7f-41b9-47f5-8bd0-b7e2cf2c3adf": ("204", "クワイエット"),
    "0408da17-8327-4e8c-a64f-48431bba8e58": ("204", "共振接続"),
    "e6f66ec1-af07-4008-abbe-e4d31cc82358": ("204", "共振スクリーム"),
    "45ed755c-cf0e-4f57-95d2-2c01b4eda760": ("204", "スキンリンク"),
    "228b8261-deca-4723-b072-0a5135ddef3f": ("204", "スリープウォーカー"),
}

#: Entries found by name, since their ids are several (one per size).
NAMED: dict[str, tuple[str, str]] = {
    "Bulk Modification (Hand/Foot/Half-Skull)": ("203", "大容量化改造（手/足/ハーフスカル）"),
    "Bulk Modification (Lower Arm/Lower Leg/Skull)": ("203", "大容量化改造（前腕/下腿/スカル）"),
    "Bulk Modification (Full Arm/Full Leg)": ("203", "大容量化改造（腕/脚）"),
    "Bulk Modification (Torso/Liminal Chassis)": ("203", "大容量化改造（胴体/リミナル・シャーシ）"),
    "Bilateral Coordination Co-processor": ("203", "両側協応コプロセッサ"),
}


def _entry(row: dict[str, Any]) -> tuple[str, str] | None:
    return ITEMS.get(str(row.get("id") or "")) or NAMED.get(str(row.get("name") or ""))


def stamp(node: Any, names: dict[str, str] | None = None) -> dict[str, str]:
    """Mark every catalog row the Codex reprints with `also_in`.

    Returns English name -> the Codex's Japanese for the rows it marked, so
    the caller can fill in the translations those rows lack."""
    names = {} if names is None else names
    if isinstance(node, list):
        for child in node:
            stamp(child, names)
    elif isinstance(node, dict):
        if "source" in node and "id" in node:
            hit = _entry(node)
            if hit:
                node["also_in"] = [{"source": CODE, "page": hit[0]}]
                names[str(node.get("name") or "")] = hit[1]
        for key, child in node.items():
            if key not in ("translations", "translations_by_kind", "ui_strings"):
                stamp(child, names)
    return names


def fill_translations(translations: dict[str, str], names: dict[str, str]) -> dict[str, str]:
    """`translations` plus the Codex's names, for rows with no Japanese yet.

    Only those: an existing translation (the official one, or a
    ja_overrides entry) wins, and several of these English names — Skates,
    Quiet — are also some other item whose translation this would clobber."""
    out = dict(translations)
    for en, ja in names.items():
        if en and out.get(en, en) == en:
            out[en] = ja
    return out
