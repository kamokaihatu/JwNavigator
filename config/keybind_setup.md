# レイヤ保存機能のセットアップ (jw_cad外部変形の登録)

JwNavigator Ver3.62以降、**このセットアップは全自動です**。
JwNavigator.exeを起動するだけで、以下が自動的に行われます
(2026-09-11、DECISIONS.md参照)。

1. 外部変形ツール一式(`B_MARK.BAT`/`A_SAVE.BAT`/`mark_point.ps1`/
   `dump_layers.ps1`)を、exeと同じフォルダの`external_transform\`へ展開
   (`utils/external_transform_setup.py`の`ensure_deployed()`)。
2. jw_cadの環境設定ファイル(`*.jwf`/`*.JWF`、見つかった全プロファイル)の
   `GCOM_100`のCtrl+Jスロットに、上記フォルダを自動登録
   (`ensure_gcom100_registered()`)。**空きスロットへの新規登録、または
   以前JwNavigatorが登録した`B_MARK`の移設先追従だけを行い、他の用途で
   使われているスロットには一切触れません**(書き換え前に`.bak_jwnavigator`
   のバックアップも作成)。

利用者が行う作業は「JwNavigator.exeを起動する」だけです。手動でのビルド・
コピー・設定ファイル編集は不要です。

## 動作確認

1. jw_cadで適当な図面を開き、図形を1つ以上作図しておく
   (外部変形は「選択する図形が0個」だと起動しません)。
2. JwNavigatorのパレットで「レイヤ情報を保存」ボタンを押し、名前を入力する。
3. 10〜20秒程度で保存完了のログが出れば成功。

## うまくいかない時

JwNavigatorの起動ログ(`JwNavigator_Log.txt`)に、以下のような行が出て
いるか確認してください。

- `🔧 外部変形ツールを展開しました: ...` — ツール展開が成功
- `🔧 <ファイル名>のGCOM_100...登録しました/更新しました: ...` — jw_cad側の登録が成功
- `⚠️ <ファイル名>のGCOM_100(Ctrl+J)は別の外部変形(...)が既に使用中のため、
  自動登録をスキップしました` — **手動対応が必要**。`[Ctrl]+[J]`が既に
  別の外部変形で使われています。空いている別のキーに変更する場合は、
  jw_cadの環境設定ファイルの該当`GCOM_1XX`行を手で編集し、
  `utils/layer_snapshot.py`の`SAVE_KEY_VK`も合わせて変更してください。

`external_transform\`フォルダの中には`layerdump\`フォルダも自動生成され、
以下が残ります(トラブル時の切り分け用)。

- `layerdump\trace.txt` — `B_MARK.BAT`/`A_SAVE.BAT`自体が起動したかどうか
  (`[MARK] enter/exit`、`[SAVE] enter/exit`)
- `layerdump\log_MARK.txt` — `mark_point.ps1`の実行ログ
- `layerdump\log_A.txt` — `dump_layers.ps1`の実行ログ

`trace.txt`に何も書かれない場合は、GCOM_100登録が正しく効いていないか、
`[Ctrl]+[J]`が別の機能に奪われています。上記のJwNavigator起動ログの
警告を確認してください。

Windows 11のSmart App Controlが「オン」になっていると、署名の無い
`JwNavigator.exe`自体が無言でブロックされることがあります(2026-09-10、
実際に発生)。設定→プライバシーとセキュリティ→Windowsセキュリティ→
アプリとブラウザーの制御→Smart App Controlが「評価モード」ならオフに
できますが、「オン」で固定済みの場合はWindowsの再インストールが必要です。

法人向けのウイルス対策ソフト(ウイルスバスター Business等)が別途導入
されている場合、`mark_point.ps1`/`dump_layers.ps1`を呼び出す
`powershell.exe`自体がブロックされることも考えられます(2026-09-11、
実際に発生・対応済み。以前はPyInstallerでビルドした専用exeを使っていた
が、署名済みのpowershell.exe経由に変更してブロックを回避した経緯が
DECISIONS.mdにあります)。この場合はIT管理者にフォルダの除外設定を
依頼してください。

## 参考

詳しい設計・調査の経緯は`doc/HANDOFF_layer_control.md`、配布方針の決定は
`DECISIONS.md`を参照してください。
