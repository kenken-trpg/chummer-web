# Mac で Chummer 本体を動かす（Wine）

書き出した `.chum5` を Chummer 本体で開いて保存し直す確認は、Windows 機が無くても
Mac の Wine でできます。2026-10-26 に `fixtures/critter-powers/` の 5 ファイルを Mac で
作り直し、Windows 版と同じ結果になることを確かめました（下の「確かめたこと」）。

## 用意するもの

| もの           | 版                | 入手先                                                                                                                         |
| -------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Wine           | 11.0_1（stable）  | [Gcenx/macOS_Wine_builds](https://github.com/Gcenx/macOS_Wine_builds/releases/tag/11.0_1) の `wine-stable-11.0_1-osx64.tar.xz` |
| winetricks     | 20260125          | `brew install winetricks`                                                                                                      |
| .NET Framework | 4.8               | winetricks が入れる                                                                                                            |
| Chummer        | 5.226.177 Nightly | [chummer5a のリリース](https://github.com/chummer5a/chummer5a/releases/tag/Nightly-v5.226.177) の `Chummer.Nightly.zip`        |

- Chummer はこのアプリが固定しているコミットから作られた版を使います。データとコードが
  同じなので、ずれが出たらこのアプリの側を疑えます。
- Homebrew の `wine-stable` cask は Gatekeeper を通らないため 2026-09-01 から無効です。
  同じファイルを GitHub から直接取り、cask が持っていた SHA-256
  `b50dc50ec7f41d58b115a6b685d4d1315ba3c797bd3aa0f49213f2703cb82388` で確かめます。
- Apple Silicon では Rosetta が要ります。空き容量は .NET 込みで 3 GB ほど使います。

## 入れる

ここでは `~/chummer-mac/` にまとめます。リポジトリの外に置いてください。

```sh
mkdir -p ~/chummer-mac/dl ~/chummer-mac/wine ~/chummer-mac/chummer ~/chummer-mac/rt
cd ~/chummer-mac/dl
curl -LO https://github.com/Gcenx/macOS_Wine_builds/releases/download/11.0_1/wine-stable-11.0_1-osx64.tar.xz
shasum -a 256 wine-stable-11.0_1-osx64.tar.xz   # 上の値と一致すること
tar -xJf wine-stable-11.0_1-osx64.tar.xz -C ~/chummer-mac/wine
gh release download Nightly-v5.226.177 -R chummer5a/chummer5a -p Chummer.Nightly.zip
unzip -q Chummer.Nightly.zip -d ~/chummer-mac/chummer
brew install winetricks
```

`curl` で取ったファイルには隔離属性が付かないので、`xattr` で外す手順は要りません。

### Wine の環境と .NET 4.8（1 回だけ）

`~/chummer-mac/setup.sh`:

```sh
#!/bin/zsh
set -eu
export PATH="$HOME/chummer-mac/wine/Wine Stable.app/Contents/Resources/wine/bin:$PATH"
export WINEPREFIX="$HOME/chummer-mac/prefix"
export WINEDEBUG=-all
wine --version
wineboot --init
winetricks -q dotnet48 corefonts
echo "setup done"
```

**winetricks はほぼ確実に途中で固まります。** 2026-10-26 には次の 2 か所で止まりました。

1. **.NET 4.0 の後の `wineserver -w`** — NGen の作業プロセス（`mscorsvw.exe`）の 1 つが
   CPU 99% で回り続け、終わりません。`ps -axo pid,etime,%cpu,command | grep mscorsvw`
   で長く動いているものを `kill` すると先へ進みます。
2. **.NET 4.8 のインストーラーの終わり** — インストーラーも NGen も CPU 0% のまま
   動きません。4.8 が入ったかはレジストリで分かります。

   ```sh
   grep -A12 'NDP\\\\v4\\\\Full\]' ~/chummer-mac/prefix/system.reg
   # "Release"=dword:00080eb1（= 528049、4.8）と "Version"="4.8.03761" があれば入っている
   ```

   入っていれば、インストーラー（`Setup.exe`・`ndp48-…exe`）と `msiexec.exe`・
   `mscorsvw.exe` を `kill` します。winetricks は失敗として終わり、`setup done` は出ません。
   corefonts も入りませんが、英語表示では文字化けしませんでした。

固まった後に `setup.sh` を流し直さないでください。winetricks の記録に dotnet48 が
残らないので、4.8 を入れ直そうとしてまた固まります。

## 起動する

`~/chummer-mac/run.sh`:

```sh
#!/bin/zsh
export PATH="$HOME/chummer-mac/wine/Wine Stable.app/Contents/Resources/wine/bin:$PATH"
export WINEPREFIX="$HOME/chummer-mac/prefix"
export WINEDEBUG=err+all
cd "$HOME/chummer-mac/chummer"
wine Chummer5.exe "$@" > "$HOME/chummer-mac/run.log" 2>&1
```

```sh
zsh ~/chummer-mac/run.sh 'Z:\Users\<ユーザー名>\chummer-mac\rt\RT-Banshee.chum5'
```

- Wine の中では `Z:\` が Mac の `/` です。ファイルの受け渡しに NAS は要りません。
- 引数に渡したファイルを開いた状態で立ち上がります。Chummer が起動中なら、新しく
  起動せずに動いている Chummer へ渡してすぐ終わります。
- **同じファイルは 2 つ目のタブで開きません。** 同じ書き出しから別の確認をするときは、
  `cp X.orig.chum5 X-src.chum5` のように新しい名前の写しを作って開きます。
- 書き出したままのファイルは `.orig` などの写しを残してください。Chummer は開いた
  ファイルを上書きすることがあります（Mac でも `RT-Banshee.chum5` が書き換わった）。
- `run.log` の `fixme:` の行は Wine の未実装の記録で、動作には関係ありません。

## 操作するときの注意

- **保存はメニューの File → Save As から。** ツールバーのボタンと取り違えて
  作成完了（Create Character）を押すと、規則違反が無いキャラクターは確認なしに
  キャリアに移ります（`created` が `True`、Starting Karma の支出が付く）。
  規則違反があると「This character is not valid and breaks the following rules」が出て
  止まります。往復の確認用の最小限のキャラクターは、このアプリでもカルマが足りないので、
  この画面が出るのは書き出しの不具合ではありません。
- 保存の画面では、ファイル名の欄に `Z:\…\rt\名前.chum5` を丸ごと入れると確実です。
- 画面の言語は Chummer の既定の英語です。
- **Claude Desktop の computer use では操作できません。** `wine Chummer5.exe` で起動した
  ウィンドウは macOS のアプリ（バンドル ID）に結び付かないので、スクリーンショットに
  写りません。画面の操作は人が行い、保存したファイルの比較を Claude Code に任せます。
- Wine と Chummer の起動は Claude Code の auto mode が止めます。Claude Code の中から
  動かすときは、プロンプトで `! zsh ~/chummer-mac/run.sh …` のように実行します。

## 確かめたこと（2026-10-26）

`fixtures/critter-powers/README.md` の手順を、その日の main で書き出したファイルで
繰り返しました。このアプリで読み直した結果（資質・任意パワー・アーマー）は 5 ファイルとも
Windows 版と同じでした。

| ファイル                                        | Mac の結果                                                                                                 |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `RT-WesternDrake-resave`                        | 書き出した改善効果 17 件がそのまま残る。Hardened Armor などのレーティングは 0 になる（Windows 版と同じ癖） |
| `RT-Banshee-resave`                             | 書き出した改善効果 20 件がそのまま残る。Chummer は値の無い改善効果に `val` 0 を足すだけ                    |
| `RT-WesternDrake-reapplied`                     | アーマーの改善効果が 2 つになる（Windows 版と同じ癖）                                                      |
| `RT-WesternDrake-removed`・`RT-Banshee-removed` | パワーも資質との結び付きも消える                                                                           |

Windows 版との違いは、メモの色が `#E3813C` ではなく `Chocolate` と書かれることだけでした。
キャラクター設定（Run Faster・Howling Shadows を有効にしたもの）を Mac では作っていないので、
`settingshashcode` も違います。
