# 設計判断メモ

このファイルは、後から見て「なぜそうなっているか」が分かりにくい、
複数ファイルにまたがる構造的な決定だけを記録する。個々の実装の理由は
各ファイル内の👑コメントを参照。

## 2026-09-11: 外部変形ツールの自動展開(exe1個で動く配布)

**決定**: `mark_point.exe`/`dump_layers.exe`/`B_MARK.BAT`/`A_SAVE.BAT`を
`JwNavigator.exe`に同梱し、起動のたびに`<JwNavigator.exeのあるフォルダ>\
external_transform\`へ自動展開する。展開先はこの1か所に固定。

**経緯**: 同僚PCでの実地テストで、①外部変形の裏方スクリプトが単体の
`.py`のままで動作に別途Pythonインストールが必要だった(exe化は既に対応
済み)、②その単体exe化した`mark_point.exe`/`dump_layers.exe`をどこに置く
か・毎回手動でビルドし直すかが配布の負担になっていた、という2点が
分かった。「利用者がexe1個置くだけで動く状態」を目標に、配布物自体に
組み込むことにした。

**なぜこの場所か**: `config\`/`data\`/`icons\`/`png_icons\`など、
JwNavigator関連のフォルダは全て「exeのあるフォルダの直下」に置く既存の
慣習(`utils/palette_config.py`の`_resolve_base_dir()`等)に合わせた。

**やらないこと(当初の方針、下記の追記で変更)**: jw_cad自身の環境設定
ファイル(`Jw_win.jwf`等)への`GCOM_100`キー割り付け登録は、当初は自動化
しない方針だった。他アプリの設定ファイルを無断で書き換えるリスクを
避けるためだったが、ユーザーから「バージョンアップのたびに手で直すのは
面倒、Ctrl+Jは元々JwNavigatorが送っているんだから自動化してほしい」との
要望を受け、下記の追記の通り自動化した。

**実装箇所**:
- `utils/external_transform_setup.py` — 展開処理本体(`ensure_deployed()`)。
  凍結exe(`sys.frozen`)の時だけ動作し、開発環境(`python main.py`)では
  何もしない(展開元の同梱データが無いため)。
- `JwNavigator.spec` — `external_transform_bundle/`としてdatas同梱。
  `dist/mark_point`・`dist/dump_layers`を先にビルドしておく必要がある
  (ビルド順: `MarkPoint.spec` → `DumpLayers.spec` → `JwNavigator.spec`)。
- `utils/layer_snapshot.py`の`TRACE_LOG_PATH` — 以前は`C:\jww\JWW_EXT`に
  ハードコードしていたが、`external_transform_setup.external_transform_dir()`
  を参照する形に変更(展開先と自動的に一致する)。
- 展開は**起動のたびに毎回上書き**する(バージョン管理はしない、シンプル
  優先)。ただし`layerdump\`(実行時に生成されるログ・トレース)は展開対象
  に含めず、上書きで消さない。

## 2026-09-11(追記): GCOM_100自動登録も自動化した

**決定**: jw_cad側の`GCOM_100`(Ctrl+Jスロット)への登録も、JwNavigator
自身が起動時に自動で行うようにした(`utils/external_transform_setup.py`の
`ensure_gcom100_registered()`)。当初の「他アプリの設定ファイルは無断で
書き換えない」方針からの転換。

**安全のための制約**:
- 書き換えるのは**Ctrl+Jスロット(GCOM_100の10番目のフィールド)だけ**。
  空なら新規登録し、既に`B_MARK`(JwNavigator自身の登録)が入っていれば
  フォルダパスだけ更新する。**それ以外の名前が既に入っている場合は
  一切触らず、ログに警告を出すだけ**(他の外部変形との衝突を避ける)。
- ファイル全体をテキストとして読み書きし直すのではなく、**GCOM_100の
  1行だけをバイト列レベルで置換**する。実機のjwfに元々含まれていた
  文字コード非適合バイト(過去の手編集由来と見られる)を巻き添えで
  壊さないため(2026-09-11、実測で発覚・対応)。
- 書き換え前に`<ファイル名>.bak_jwnavigator`のバックアップを必ず作る
  (既にあれば上書きしない=最初の1回分だけ残す)。
- jw_cadのフォルダにある`*.jwf`/`*.JWF`**全部**が対象(`Sample.jwf`は
  jw_cad同梱のひな形であり実プロファイルではないため除外)。どのプロ
  ファイルが「今アクティブか」を外部から確実に判別する方法が無いため、
  見つかった全プロファイルに同じ登録をしておくことで取りこぼしを防ぐ
  アプローチを取った。
- `ensure_deployed()`と同じく凍結exe(`sys.frozen`)の時だけ動作する。
  開発環境(`python main.py`)では`external_transform_dir()`が実際には
  ツールを展開しない場所を指すため、ここで登録すると実在しないパスを
  jw_cad側に書いてしまう(実装中に気づいて安全策として追加)。

**実機検証**: 本物の`Jw_win.jwf`/`kamo.JWF`/`20260513shinji.JWF`/
`Sample.jwf`に対して実際に動作させ、GCOM_100の1行だけが変わり他は
バイト単位で一致すること、`Sample.jwf`が触られないことを確認した
(2026-09-11)。検証後、開発機の既存セットアップ(`C:\jww\JWW_EXT`)を
壊さないよう手動で元に戻した。

## 2026-09-11(追記): 設定ファイル一式を%APPDATA%へ移した

**決定**: `config.json`/`window_state.json`/`menu_prefs.json`/
`auto_attr_pending.json`/`layer_snapshots\`を、パッケージ版に限り
`exeの隣のconfig\`から`%APPDATA%\JwNavigator\config\`へ移した
(`utils/app_paths.py`)。

**経緯**: 「exeを入れ替え/移動してもパレット設定が消えないようにしたい」
という要望。exe隣接保存だと、zipを新しいフォルダへ展開し直したり、
exeだけ差し替えたりするたびに設定が「無くなった」ように見えてしまう。

**開発環境は対象外**: `python main.py`実行時は今まで通りリポジトリ直下の
`config\`のまま(`utils/app_paths.py`の`user_config_dir()`が
`sys.frozen`で分岐)。`config/config.json`をgitでコミットして共有する
既存の運用(「今のパレット配置でコミットプッシュで」等)を崩さないため。

**移さないもの**: `data\`(starter_presets/commands_master.csv/
app_icon.ico)・`icons\`・`png_icons\`はexeに同梱される読み取り専用
リソースで利用者の設定ではないため対象外。`external_transform\`
(外部変形ツール一式)も、常に「今動いているexeに同梱された最新版」で
あるべきなので意図的にexeの隣に残す(こちらもDECISIONS.md参照)。

**移行**: 初回起動時だけ、以前のexe隣接`config\`にある上記5項目を
新しい場所へ自動コピーする(`migrate_legacy_config_if_needed()`)。
新しい場所に既にファイルがあれば上書きしない(1回きりの移行、以後は
新しい場所が正)。**呼び出し順序が重要**: `main.py`の`__init__`の中で
`window_state.load_state()`や初回起動判定(`run_first_launch_setup_if_needed`)
より前に呼ぶ必要がある。でないと「移行前の空のAppDataを読んでしまい、
今回のセッションだけ設定が消えたように見える/初回起動画面が誤って
また出る」事故になる(実装中に気づいて`__init__`の先頭、
`self.log_file_path`設定の直後まで呼び出し位置を動かした)。

**実機検証**: 実際に凍結exeへ`config.json`を配置した状態で起動し、
`%APPDATA%\JwNavigator\config\config.json`へ内容が完全一致でコピーされ、
かつそのままパレットのボタン配置(19/23/1個)が正しく読み込まれることを
確認した(2026-09-11)。検証後、テスト用の`%APPDATA%\JwNavigator\`は
削除して片付けた。

## 2026-09-11(追記): 外部変形ツールをexeからPowerShellスクリプトへ移行

**決定**: `mark_point.exe`/`dump_layers.exe`(PyInstaller単体ビルド)を廃止し、
`mark_point.ps1`/`dump_layers.ps1`(PowerShellスクリプト)へ全面移行した。
`MarkPoint.spec`/`DumpLayers.spec`は削除、`JwNavigator.spec`のビルド前提
だった「先にdist/mark_point・dist/dump_layers をビルドしておく」手順も
不要になった。

**経緯**: 法人向けウイルス対策ソフト(ウイルスバスター Business)が導入
された利用者PCで、未署名の自前exe(`mark_point.exe`)がブロックされ、
レイヤ保存機能が動かない事例が発生した。切り分けのため、まず
`python.exe`を追加インストールして`python mark_point.py`形式を試したが、
python.exeも同様にブロックされた。ここから、**「未署名だから」ではなく
「cmd.exeからスクリプト系の実行ファイル(インタプリタ)を子プロセスとして
起動すること自体」が警戒されている**と判断し、Windows標準搭載で追加
インストール不要な`powershell.exe`経由を試したところ、ブロックされずに
実機で正常動作した(2026-09-11、コワーカーの実PCで確認)。

**ロジックの正しさの検証方法**: `dump_layers.ps1`は`dump_layers.py`の
`write_jwl()`相当のみを移植したもの(CSV/matrix/JSON等のデバッグ出力は
実際の保存/復元機能では使われないため省略)。過去に実機で取得した
`layerdump/raw_*.txt`(実データ)57件全てに対し、Python版が生成する
`LAYER_RESTORE.JWL`とPowerShell版が生成するものを突き合わせ、全件で
バイト単位で一致することを確認してから採用した。

**副次的な利点**: exeのビルド・バンドルが不要になり、配布サイズが
縮小した。PowerShellはWindows標準搭載のため、追加インストール不要な点も
「利用者がexe1個置くだけで動く状態」の方針([[2026-09-11の外部変形ツール
自動展開の決定]]参照)に合致する。

**変わらないこと**: 開発環境(`python main.py`)は今まで通り
`mark_point.py`/`dump_layers.py`を直接使う。`ensure_deployed()`の
凍結exe限定ゲートも変更なし。

## 2026-09-14: レイヤ保存の高速版(Ctrl+K→A_SAVE直結)を追加

**決定**: 通常の「レイヤ保存」ボタンとは別に、「レイヤ保存(高速・要選択)」
ボタン(kind="layer_snapshot", role="save", fast=True)を新設した。
`utils/layer_snapshot.py`の`trigger_save_fast()`が実装本体。

**経緯**: 実測で、レイヤ保存が遅い(10〜20秒)原因は「jw_cad側が外部変形を
1回起動するたびに約6〜7秒の固定コストを払う」ことにあり、通常版はこれを
**2回**払っている(①Ctrl+J→B_MARK起動、②B_MARKからA_SAVEへの連鎖)と
判明した(2026-09-14、実測。過去の記録にあった「連鎖は1.7秒で速い」は
再現せず、古い記録の誤りだったとみられる)。GCOM_110のCtrl+Kスロットに
A_SAVEを直結登録すれば、B_MARKの点作図(=選択できる目印を用意するための
1回)を丸ごと省略でき、外部変形の呼び出しを1回で済ませられる。実機検証
(2026-09-14)で合計約15秒→約8.6秒(4割強短縮)を確認した。

**なぜ別ボタンにしたか**: 高速版は「利用者が事前に図面上で何か1つ以上を
選択しておく」という前提が必要(通常版はB_MARKが目印点を自動作図する
ため、この前提が不要で常に成功する)。この前提の有無で失敗率・UXが
変わるため、既存の「押すだけで確実」なボタンの挙動を変えず、選べる形の
別ボタンとして追加した(ユーザー決定)。

**技術詳細**:
- `GCOM_110`のCtrl+Kスロット(0番目のフィールド、A=1番目...J=10番目が
  GCOM_100、K=1番目...T=10番目がGCOM_110、実機確認済み)に`A_SAVE`を
  直結登録する。安全のための制約(空きスロットのみ書き換え、バックアップ
  作成等)はGCOM_100と全く同じ(`ensure_gcom100_registered()`内で両方を
  一度に処理するよう拡張した)。
- Ctrl+K送信後、jw_cad本体(パレットではなく本体側)の条件設定バー上に
  ある「選択確定」ボタン(ctrl_id=1120、実機確認済み)をBM_CLICKする
  ことで、選択済みのデータを使って直接A_SAVEを起動する。このBM_CLICK
  はjw_cad内部でA_SAVE完了まで**同期的にブロックする**(Ctrl+J経由の
  連鎖とは違い非同期ではない)ため、戻ってきた時点でほぼ完了している。
- 事前に何も選択していない場合、Ctrl+Kを送っても条件設定バーに
  「選択確定」ボタン自体が表示されないため、`_find_confirm_selection_button()`
  がNoneを返して安全に失敗する(Ctrl+K送信自体は無害)。

**実機検証の副産物**: `trigger_restore()`の「開く」ダイアログ検出
タイムアウトが2.0秒だと、保存直後(特に高速版のBM_CLICK直後)にまれに
間に合わないことが判明し、4.0秒に延長した。
