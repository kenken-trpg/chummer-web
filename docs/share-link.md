# 読み取り専用の共有リンク

キャラクターを **URL だけで** 他人に見せる仕組み。サーバーにも DB にも何も保存しない
ので、「アカウントなし・サーバー側にユーザー状態を持たない」という本プロジェクトの
非目標（`CONTRIBUTING.md`）を崩さずに共有できる。

```
https://<host>/share#c=<base64url(deflate-raw(JSON))>
```

## なぜフラグメントなのか

`#` 以降は **ブラウザがサーバーに送らない**。つまり

- バックエンド・リバースプロキシ・アクセスログのどこにもキャラクターは残らない
- Referer ヘッダにも乗らない
- 永続ボリュームもクリーンアップのバッチも不要

`?c=`（クエリ）にすると全部がログに残るので、必ずフラグメントを使うこと。

## 送る側

`lib/character/share.ts`

| 関数 | 役割 |
| --- | --- |
| `toSharePayload(ch)` | `derived` / `id` / `portrait` を落とす |
| `encodeShare(ch)` | `{v, s}` を JSON → `deflate-raw` → base64url |
| `buildShareUrl(ch, href)` | 同一オリジンの `/share#c=…` を組み立てる |

`derived` はバックエンドが再計算するので送らない（エンジンが更新されても古いリンクが
正しく開ける）。`id` は受け側で振り直す（ロースターの既存キャラと衝突させない）。
`portrait` は 3MB 画像 → base64 約 4MB で、圧縮も効かず URL に乗らないため除外。

圧縮は `CompressionStream("deflate-raw")` — ブラウザ標準で、依存パッケージは増えない。
非対応ブラウザでは `shareSupported()` が `false` を返し、明示的なエラーになる。

UI はツールバーの「共有リンク」ボタン（`useCharacterEditor.copyShareLink`）。
URL が `SHARE_URL_WARN`（8,000 文字）を超えたときはコピーした上で警告を出す
— チャットやメールで途中改行・切断されることがあるため。

## 受け取る側

`app/share/page.tsx`（静的ルート。サーバーは `/share` を返すだけ）

1. `readShareValue(location.hash)` → `decodeShare(value)`
2. ペイロードを `POST /api/characters/import` に投げて `derived` を得る
   （`api.preview` — **ローカルロースターには書かない**）
3. `CharacterSheet` を描画。エディタは一切出さない＝構造的に読み取り専用

「自分のロースターに取り込む」を押すと `api.import` で新しい `id` を発行して
IndexedDB に保存し、`lastCharacterId` を立てて `/` に遷移する。

## 受け取ったデータの扱い

共有リンクの中身は **第三者が作れる入力** なので、多段で絞っている。

| 層 | 防いでいるもの |
| --- | --- |
| `/^[A-Za-z0-9_-]+$/` | base64url 以外の文字 |
| `MAX_SHARE_BYTES`（4MB）で展開を打ち切り | 解凍爆弾（短い URL → 巨大 JSON） |
| エンベロープの型チェック（`{v, s}`、`s` はオブジェクト） | 配列・プリミティブ・null |
| `v !== SHARE_VERSION` を拒否 | 将来形式を古いページが誤読すること |
| `derived` / `id` を再度剥がす | 手書きリンクによる差し込み |
| バックエンドの Pydantic `CharacterState`（コレクション長上限つき） | 本命の検証 |

シートはテキストしか描画せず、`portrait` は共有されないので `data:` URL の
差し込み経路もない。

## 形式を変えるとき

`SHARE_VERSION` を上げる。古いリンクを生かすなら `decodeShare` にバージョン別の
変換を足す（`local-store.ts` の `migrate()` と同じ考え方）。上げないまま
ペイロードの意味を変えると、古いリンクが黙って壊れる。

## 対象外

- 編集可能な共有 / 同時編集（サーバー状態が必要。非目標）
- 短縮 URL（保存が必要になる。長さが問題ならファイル共有か `.chum5` 書き出しで）
- ポートレート（上記のとおりサイズで断念）
