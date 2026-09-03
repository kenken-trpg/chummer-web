# 日本語訳オーバーレイ (ja_overrides)

`backend/vendor/chummer/lang/` の翻訳ファイルは chummer5a 上流から
`scripts/fetch_chummer_data.py` で取得され、**Git 管理外**かつ再取得で上書きされる。

このディレクトリは、そのうえに重ねる**追記・修正の差分**を Git 管理下で保持する。
`app/data_loader.py` が vendored の翻訳を読み込んだ後、ここの内容で上書きマージする
(オーバーレイ側が優先)。

## ファイル

| ファイル | 対応する vendored | キー | 値 | 管理 |
|---|---|---|---|---|
| `data.json` | `ja-jp_data.xml` | データエンティティの英語名 (`<name>`) | 日本語訳 (`<translate>` 相当) | **生成物** |
| `ui.json`   | `ja-jp.xml`      | UI 文字列キー (`<string key>`)          | 日本語訳 (`<text>` 相当) | 手編集 |

### `data.json` は生成物

全エントリは curated モジュール
(`scripts/import_ja_from_refs.py` の `CURATED`、`scripts/ja_curated_spells.py`、
`scripts/ja_curated_entities.py`) ＋ `$JA_REF_DIR/` (既定 `~/Downloads/`) の
参考資料 (chumJA SR4) の完全一致から生成される。**訳を足す/直すときはこれらの
モジュールを編集**し、

```
backend/scripts/regen_ja.sh
```

で `data.json` と `docs/translation-*.md` を再生成する (`--no-reset` / `--no-test` あり)。
`data.json` を直接編集しても次の再生成で消える。`ui.json` は手編集で可。

## フォーマット

キー・値ともに文字列の JSON オブジェクト。UTF-8、末尾改行あり。

```json
{
  "Ares Predator V": "アレス・プレデターV",
  "Combat Sense": "戦闘感覚"
}
```

- 空文字列の値は無視される (未訳扱い)。
- vendored に存在しないキーを足してもよい (将来の上流更新に備えた先行訳)。
- キーの重複は JSON パーサの挙動 (最後の値) に従うため作らないこと。

## 出典と方針

`docs/plans/translation-plan.md` を参照。用語は 2021 年版シート用語集
(`xz.language.xslt` / 公式 5 版表記) を正とし、競合時は新しい資料を優先する。

## ライセンス

元データは chummer5a/chummer5a (GPL-3.0) の派生物。本オーバーレイも GPL-3.0。
