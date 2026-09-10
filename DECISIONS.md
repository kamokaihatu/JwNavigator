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
