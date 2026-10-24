"""Hand translations for spells / rituals / enchantments still on English
fallback (Phase 2b, see docs/plans/translation-plan.md).

Scope: only entries that are a common English word with an unambiguous JP form,
or a compositional parallel to a spell already translated upstream (the Ward /
Circle / "Increase [X]" / "Extended" families). Obscure supplement-specific
coinages (most blood-magic, necro, geomancy, feng-shui and infected rituals)
are deliberately left on English fallback rather than guessed at.

House style, matching the ~193 entries already translated upstream:
  * spells:      "漢語訳/カタカナ音写"  e.g. 酸噴射/アシッド・ストリーム
  * rituals:     漢語のみ               e.g. 治癒円 / 結界 / 遠隔探知
  * bracketed placeholders kept on both sides:
      [Element]→[元素]/[エレメント], [Critter]→[クリッター]
  * "Extended" variant: 広域〜/エクステンデッド・〜

Empty since 2026-10-24: every spell here belonged only to a supplement with
no Japanese edition, so by the supplement-terms-stay-English policy they all
went back to English (docs/translation-import-report.md listed them). The
table stays so a spell a Japanese book prints has somewhere to go.

Consumed by import_ja_from_refs.py; every key is verified against catalog()
by tests/test_translation_overrides.py (orphan check).
"""

from __future__ import annotations

SPELLS: dict[str, str] = {}
