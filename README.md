# Chummer Web

非公式の Shadowrun 5th Edition キャラクター作成 Web アプリです。Catalyst Game Labs / The Topps Company とは無関係です。

ゲームデータと翻訳は [chummer5a/chummer5a](https://github.com/chummer5a/chummer5a)（GPL-3.0）の `Chummer/data` と `Chummer/lang` を使います。このプロジェクトも GPL-3.0 です。

第1段階: Priority、メタタイプ、属性、スキル、Quality、派生値、JSON 保存/読込。

## 起動

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/fetch_chummer_data.py
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

別ターミナル:

```bash
cd frontend
npm install
npm run dev
```

ブラウザで http://localhost:3000 を開きます。

## テスト

```bash
cd backend
source .venv/bin/activate
python -m pytest
```
