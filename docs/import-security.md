# インポートの入力制限

確認日: 2026-11-06。バックエンドのアップロード経路と既存テストを確認し、
LZMA のデコーダーメモリ上限を追加した。以下は個別の入力制限であり、
プロセス全体の最大メモリや同時リクエスト全体の CPU 使用量を保証するものではない。

| 境界 | 既定の制限 | 実装 |
| --- | --- | --- |
| HTTP リクエスト本文 | 12 MiB。Content-Length と実際の受信量を確認し、超過時は 413 | `backend/app/api/middleware.py` |
| JSON のキャラクター状態 | モデルの共通ガードでリスト・辞書を各 2,000 件、整数を ±10¹² に制限。フィールド固有の制限もある | `backend/app/models/_common.py` |
| アップロード XML | 要素数 250,000、深さ 64。エンティティ・外部参照を拒否 | `backend/app/data_loader/_xml.py` |
| `.chum5lz` の展開結果 | 32 MiB。`CHUM5_MAX_DECOMPRESSED_BYTES` で変更可 | `backend/app/chummer_import/container.py` |
| LZMA / XZ デコーダー | **128 MiB**。出力サイズとは別に `memlimit` で制限 | 同上 |
| XLSX | ZIP エントリ 512 件、各読込パート 32 MiB、読込パート合計 64 MiB。申告サイズと実読込量を確認 | `backend/app/xlsx_import/_sheet.py` |
| 設定 XML | 1 MiB、共通の XML 制限も適用 | `backend/app/settings_file.py` |
| カスタムデータ | 500 ファイル、選択ディレクトリ 500 件・名前各 256 文字、ファイル内容合計 16 MiB。HTTP 本文の制限も先に適用 | `backend/app/models/character.py`、`backend/app/api/import_routes.py` |
| Google Sheets からの取得 | 取得量・期限・リダイレクト回数・取得先を制限。取得後は通常の XLSX 読込制限も適用 | `backend/app/sheets_url.py` |

## 今回補った境界

従来の `.chum5lz` は、展開結果を上限以下に抑えていても、LZMA のヘッダーが
要求する辞書領域を制限していなかった。LZMA と XZ の両経路にデコーダーの
メモリ上限を設定し、超過時は既存の読込失敗通知で HTTP 400 を返す。
通常の LZMA 圧縮設定（preset 0〜9）の辞書に余裕を持たせた上限である。
128 MiB はデコーダー用で、出力 XML や解析済みツリーのメモリを含まない。

回帰テストでは小さな圧縮入力と小さなメモリ予算を用い、LZMA / XZ ともに
予算超過を拒否し、同じ入力を十分な予算では読み込めることを確認する。
実際に巨大な辞書を確保するテストにはしていない。

## 確認用テスト

- `backend/tests/test_chummer_import.py`: 通常の XML・LZMA・XZ、展開量上限、デコーダー上限、API の拒否応答。
- `backend/tests/test_xlsx_import.py`: エントリ数、パート展開量、読込合計量と通常のシート読込。
- `backend/tests/test_import_fuzz.py`: 不正入力、圧縮形式、XML の要素数・深さなど。
- `backend/tests/test_api.py`: 本文・チャンク受信量、JSON のコレクション、カスタムデータ合計量。
- `backend/tests/test_customdata.py`、`backend/tests/test_settings.py`: カスタムデータ件数と設定 XML の制限。

設定値を緩めるときは、転送量だけでなく展開・解析後と同時実行時の負荷も確認する。
デプロイ環境の受信制限は [デプロイ手順](deploy.md) を参照。
