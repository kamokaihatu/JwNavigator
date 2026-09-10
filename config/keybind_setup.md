# レイヤ保存機能の初回セットアップ (jw_cad外部変形の登録)

JwNavigatorの「レイヤ情報を保存」ボタンは、JwNavigator.exe単体では完結しません。
jw_cad側に外部変形(バッチファイル)を登録しておく必要があります。**新しいPCに
JwNavigatorを入れるたびに、この手順を1回だけ行ってください。**

これを忘れると「復元ボタンは出現するのに、押しても中身が保存されていない」
「レイヤの状態がうまく切り替わらない」という無言の失敗になります
(2026-09-10、同僚PCで実際に発生・原因特定)。

## 1. 必要なファイルを配置する

以下のファイルを、jw_cadとは別の**専用フォルダ**(例: `C:\jww\JWW_EXT\`)へ
まとめて置きます。JwNavigator.exe本体のフォルダとは別で構いません。

```
C:\jww\JWW_EXT\
├── B_MARK.BAT
├── A_SAVE.BAT
├── mark_point\        ← mark_point.exeとその依存ファイル一式(フォルダごと)
│   ├── mark_point.exe
│   └── _internal\...
└── dump_layers\        ← dump_layers.exeとその依存ファイル一式(フォルダごと)
    ├── dump_layers.exe
    └── _internal\...
```

`B_MARK.BAT`/`A_SAVE.BAT`はこのリポジトリのルート直下にあるものをそのまま
コピーしてください。`mark_point.exe`/`dump_layers.exe`は以下でビルドします
(👑 **重要**: `python mark_point.py`のようにPythonスクリプトを直接呼ぶ方式は
やめました。配布先PCにPythonが入っていないと無言で失敗するためです、
2026-09-10)。

```
.venv\Scripts\pyinstaller.exe MarkPoint.spec --noconfirm
.venv\Scripts\pyinstaller.exe DumpLayers.spec --noconfirm
```

`dist\mark_point\`と`dist\dump_layers\`ができるので、それぞれフォルダごと
上記の配置先へコピーします(onedir形式。onefileは初回展開が遅い上に
Windows Application Control policyでブロックされることがあるため不使用)。

## 2. jw_cadの環境設定ファイルにキー割り付けを追記する

jw_cadの環境設定ファイル(`Jw_win.jwf`、または使用中のプロファイル`.jwf`)に
以下の1行を追記します。10文字ごとに`GCOM_100`〜`GCOM_190`があり、10番目の
文字がキー(`J`=Ctrl+J)、11番目がフォルダパスです。

```
GCOM_100 =A_SAVE,,,,,,,,,,C:\jww\JWW_EXT
```

- 1番目のファイル名(`A_SAVE`)は実際にはB_MARK.BATから連鎖起動されるため、
  jw_cadから見た「登録名」程度の意味です。拡張子は書きません。
- `C:\jww\JWW_EXT`の部分は手順1で置いたフォルダのパスと必ず一致させてください
  (`utils\layer_snapshot.py`の`TRACE_LOG_PATH`もこの値に合わせてあります)。
- `[Ctrl]+[J]`に既存の割り付けが無いことを確認してください。あれば別の
  空いている文字に変更し、`utils\layer_snapshot.py`の`SAVE_KEY_VK`も
  合わせて変更する必要があります。
- この設定はjw_cad上のプロファイル切替では引き継がれないことがあるので、
  常用するプロファイルの`.jwf`に書いてください。

## 3. バッチファイルの先頭コメントを確認する

`B_MARK.BAT`/`A_SAVE.BAT`の先頭に`REM #jww`という行が無いと、jw_cadの
外部変形一覧に一切出てきません(ファイルは存在するのに選べない、という
形で気づきにくいハマりどころです)。リポジトリのものにはすでに入って
いますが、コピー時に壊れていないか一応確認してください。

## 4. 動作確認

1. jw_cadで適当な図面を開き、図形を1つ以上作図しておく
   (外部変形は「選択する図形が0個」だと起動しません)。
2. JwNavigatorのパレットで「レイヤ情報を保存」ボタンを押し、名前を入力する。
3. 10〜20秒程度で保存完了のログが出れば成功。

### うまくいかない時に見るログ

配置先フォルダ(例: `C:\jww\JWW_EXT\`)の中に`layerdump\`フォルダが
自動生成され、以下が残ります。

- `layerdump\trace.txt` — `B_MARK.BAT`/`A_SAVE.BAT`自体が起動したかどうか
  (`[MARK] enter/exit`、`[SAVE] enter/exit`)
- `layerdump\log_MARK.txt` — `mark_point.exe`の実行ログ
- `layerdump\log_A.txt` — `dump_layers.exe`の実行ログ

`trace.txt`に何も書かれない場合は、手順2(GCOM_100登録)が正しく効いて
いないか、`[Ctrl]+[J]`が別の機能に奪われています。`trace.txt`に`enter`は
あるが`log_*.txt`が空/存在しない場合は、exeの配置場所(パス)が
`GCOM_100`の11番目の指定と食い違っている可能性が高いです。

## 参考

詳しい設計・調査の経緯は`doc/HANDOFF_layer_control.md`を参照してください。
