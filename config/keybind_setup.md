# レイヤ保存機能の初回セットアップ (jw_cad外部変形の登録)

JwNavigator Ver3.62以降、外部変形ツール(`B_MARK.BAT`/`A_SAVE.BAT`/
`mark_point.exe`/`dump_layers.exe`)は**JwNavigator.exeに同梱されており、
起動のたびに自動でexeの隣の`external_transform\`フォルダへ展開されます**。
手動でのビルド・コピーは不要になりました(2026-09-11、DECISIONS.md参照)。

ただし、jw_cad側に**このフォルダの場所をキー割り付けとして1回だけ登録**
しておく必要があります。これは他アプリ(jw_cad)の設定ファイルを
JwNavigatorが無断で書き換えるのを避けるため、あえて自動化していません。
**新しいPCにJwNavigatorを入れるたびに、この手順を1回だけ行ってください。**

これを忘れると「復元ボタンは出現するのに、押しても中身が保存されていない」
「レイヤの状態がうまく切り替わらない」という無言の失敗になります
(2026-09-10、同僚PCで実際に発生・原因特定)。

## 1. JwNavigatorを一度起動して展開先を確認する

JwNavigator.exeを一度起動すると、そのexeと同じフォルダに`external_transform\`
フォルダが自動で作られます。

```
<JwNavigator.exeのあるフォルダ>\external_transform\
├── B_MARK.BAT
├── A_SAVE.BAT
├── mark_point\
└── dump_layers\
```

このフォルダの**フルパス**を、次の手順2で使います。

## 2. jw_cadの環境設定ファイルにキー割り付けを追記する

jw_cadの環境設定ファイル(`Jw_win.jwf`、または使用中のプロファイル`.jwf`)に
以下の1行を追記します。10文字ごとに`GCOM_100`〜`GCOM_190`があり、10番目の
文字がキー(`J`=Ctrl+J)、11番目がフォルダパスです。

```
GCOM_100 =A_SAVE,,,,,,,,,,<手順1で確認したexternal_transformフォルダのフルパス>
```

例: JwNavigator.exeを`C:\jww\JwNavigator\`に置いた場合

```
GCOM_100 =A_SAVE,,,,,,,,,,C:\jww\JwNavigator\external_transform
```

- 1番目のファイル名(`A_SAVE`)は実際にはB_MARK.BATから連鎖起動されるため、
  jw_cadから見た「登録名」程度の意味です。拡張子は書きません。
- フォルダパスは手順1で確認した`external_transform`の場所と必ず一致させて
  ください(`utils\layer_snapshot.py`の`TRACE_LOG_PATH`は自動でこの場所を
  参照するので、そちらは意識しなくて大丈夫です)。
- `[Ctrl]+[J]`に既存の割り付けが無いことを確認してください。あれば別の
  空いている文字に変更し、`utils\layer_snapshot.py`の`SAVE_KEY_VK`も
  合わせて変更する必要があります。
- この設定はjw_cad上のプロファイル切替では引き継がれないことがあるので、
  常用するプロファイルの`.jwf`に書いてください。

👑 **JwNavigatorを別のフォルダへ移動・再インストールした場合**は、
`external_transform`の場所も一緒に移動するので、この手順2をやり直して
GCOM_100のパスを新しい場所に書き換えてください。

## 3. 動作確認

1. jw_cadで適当な図面を開き、図形を1つ以上作図しておく
   (外部変形は「選択する図形が0個」だと起動しません)。
2. JwNavigatorのパレットで「レイヤ情報を保存」ボタンを押し、名前を入力する。
3. 10〜20秒程度で保存完了のログが出れば成功。

### うまくいかない時に見るログ

`external_transform\`フォルダの中に`layerdump\`フォルダが自動生成され、
以下が残ります。

- `layerdump\trace.txt` — `B_MARK.BAT`/`A_SAVE.BAT`自体が起動したかどうか
  (`[MARK] enter/exit`、`[SAVE] enter/exit`)
- `layerdump\log_MARK.txt` — `mark_point.exe`の実行ログ
- `layerdump\log_A.txt` — `dump_layers.exe`の実行ログ

`trace.txt`に何も書かれない場合は、手順2(GCOM_100登録)が正しく効いて
いないか、`[Ctrl]+[J]`が別の機能に奪われています。`trace.txt`に`enter`は
あるが`log_*.txt`が空/存在しない場合は、`external_transform`フォルダの
場所が`GCOM_100`の11番目の指定と食い違っている可能性が高いです。

Windows 11のSmart App Controlが「オン」になっていると、署名の無い
`JwNavigator.exe`/`mark_point.exe`/`dump_layers.exe`自体が無言でブロック
されることがあります(2026-09-10、実際に発生)。設定→プライバシーと
セキュリティ→Windowsセキュリティ→アプリとブラウザーの制御→
Smart App Controlが「評価モード」ならオフにできますが、「オン」で
固定済みの場合はWindowsの再インストールが必要です。

## 参考

詳しい設計・調査の経緯は`doc/HANDOFF_layer_control.md`、配布方針の決定は
`DECISIONS.md`を参照してください。
