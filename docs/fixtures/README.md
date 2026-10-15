# Chummer ライフモジュール実動作確認

## 修正版を開く手順

`chummer-life-module-skill-overflow-configured.zip` にはキャラクター、対応する設定XML、手順書が入っています。

1. ZIPを展開し、Chummerを終了する。
2. 展開した `settings/` のXMLを **Chummer本体の `settings` フォルダー** にコピーする。
3. Chummerを起動し、全体設定のLife Modulesを有効にする。これはChummer側では試験機能。
4. ZIP内の `character.chum5` を開く。単体の `chummer-life-module-skill-overflow-configured.chum5` も同内容。
5. 設定名が `Chummer Web Life Modules`、作成方式が `LifeModule` になっていることを確認する。
6. 元ファイルを上書きせず別名保存し、そのファイルをもう一度Chummerで開く。

設定XMLはLifeModule方式、750 Karma、能動技能上限7、知識技能上限9、SR5・RF・CFを指定します。
Chummerのカスタム設定はファイル名で検索されるため、設定XMLを改名しないでください。

## 確認する値

- 名前（alias）: `Chummer Life Module Compatibility`
- モジュール5件: Seattle、Orphan、Factory Child Worker、Graphic Designer、Government Agent
- Perception 7、Navigation 2、Spanish 1、UCAS 1
- アプリ側の消費カルマ245、超過移し替え2ランク
- モジュール由来の能力値・資質・連絡先

修正版のアプリ内往復で、Perception 7・Navigation 2・245 Karma・移し替え履歴の保持をテストしています。
Chummer本体で開いて再保存した後は、選択・移し替え履歴が失われます。今回の修正では、そのファイルを確定済みのキャリアスナップショットとして取り込み、保存済み技能値・能力値・資質を再計算で変えず、取り込み時点をキャリア成長の基準にします。元のモジュール名は参照用アーカイブとして保持しますが、履歴からの再計算はできません。
EXファイルでは `<created>False</created>` と記録されるため、読み込み時にキャリア状態へ移行します。アプリ内のキャリア成長は基準値から差分だけを価格計算します。Chummer本体で開き直して再保存する実地確認は未実施です。

## 最初の検証ファイルと実測結果

`chummer-life-module-skill-overflow.chum5` は最初の出力です。LifeModule方式にStandard設定IDを組み合わせていました。
`EX_chummer-life-module-skill-overflow.chum5` は、これをChummer 5.222.0で開いて別名保存したファイルです。
元の実測証拠として両方を保持します。

EXファイルでは作成方式がKarmaに変わり、設定IDも別のStandard設定へ変わりました。
有効ソースからCFが外れ、アプリ固有の `<lifemoduleskillstate>` もなくなっています。
ライフモジュール資質5件と技能Perception 7・Navigation 2はXMLに残っています。
修正前のアプリはこれを警告なしでKarmaキャラクターとして取り込み、通常作成上限6でPerceptionを切り詰めていました。
修正後は作成方式の文字列にかかわらずLifeModule型の資質を検出します。アプリ固有の選択履歴がないChummer再保存ファイルは確定値スナップショットとして取り込み、LifeModule作成方式なのにモジュール記録も選択履歴もない不完全なファイルは引き続き停止します。

## Chummer 5.222.0 のソース根拠

確認したタグは `5.222.0`、コミットは `28f99280c99defcd8e6481558cc9ff077030ab69` です。

- [CharacterSettings.cs](https://github.com/chummer5a/chummer5a/blob/5.222.0/Chummer/Backend/Character%20Settings/CharacterSettings.cs#L38): `CharacterBuildMethod` はKarma、Priority、SumtoTen、LifeModuleを定義。LifeModuleは正式な列挙値。
- [GlobalSettings.cs](https://github.com/chummer5a/chummer5a/blob/5.222.0/Chummer/Backend/Static/GlobalSettings.cs#L200): `LifeModuleEnabled` は初期値false。レジストリの `lifemodule` から読み込む。
- [EditCharacterSettings.cs](https://github.com/chummer5a/chummer5a/blob/5.222.0/Chummer/Forms/EditCharacterSettings.cs#L89): `GlobalSettings.LifeModuleEnabled` がtrueのときだけLifeModuleを作成方式の候補に追加。
- [SelectBuildMethod.cs](https://github.com/chummer5a/chummer5a/blob/5.222.0/Chummer/Forms/Character%20Creation%20Forms/SelectBuildMethod.cs#L47): スクリーンショットの一覧は読み込まれたキャラクター設定の一覧。
- [Character.cs](https://github.com/chummer5a/chummer5a/blob/5.222.0/Chummer/Backend/Characters/Character.cs#L3416): 保存済み作成方式を列挙値として解析し、設定ファイルの方式と異なる場合は設定の再選択を促す。
- [Character.csの保存処理](https://github.com/chummer5a/chummer5a/blob/5.222.0/Chummer/Backend/Characters/Character.cs#L2384): `<buildmethod>` に `Settings.BuildMethod` を保存。
- [CharacterSettings.csの設定キー](https://github.com/chummer5a/chummer5a/blob/5.222.0/Chummer/Backend/Character%20Settings/CharacterSettings.cs#L2020): カスタム設定はゼロGUIDとファイル名、組み込み設定はソースGUIDで識別。

「ChummerはLifeModule作成方式を未対応」という初期説明は誤りです。
作成方式自体は対応しており、今回直すべき点は対応する設定ファイルの供給と、履歴消失後の取り込み判定です。

## 続く開発: 履歴のないファイルの確定値取り込み

履歴がないファイルを通常のLifeModule入力として再計算すると、付与の二重計上や購入コストの誤算が起きます。
確定値取り込みは通常の作成入力と別の保存形式にし、次を揃えてから提供します。

- 保存済み技能・能力値・資質・残カルマ・所持金を固定し、経歴は参照用に保持。
- 元の選択・移し替え履歴を復元できないことを表示し、経歴の追加・削除による再計算を禁止。
- キャリア移行時は確定値を成長の基準にして、移行後の購入だけを価格計算。
- JSON・共有・再出力で固定状態を保持し、成長・取り消しで固定値を変えない。
- 今回のEXファイルと、正しくLifeModule設定で再保存した実測ファイルの両方で回帰検証。

確定値取り込みは実装済みです。Chummerの再保存によって失われた技能移し替えの理由や個別の選択記録は復元できないため、履歴を保持したアプリ側JSONまたは再保存前ファイルもバックアップしてください。
