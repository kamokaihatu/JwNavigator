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

**やらないこと**: jw_cad自身の環境設定ファイル(`Jw_win.jwf`等)への
`GCOM_100`キー割り付け登録は、自動化しない。他アプリの設定ファイルを
無断で書き換えるリスクを避けるため、引き続き手動(`config/keybind_setup.md`
参照)。ただし登録するフォルダパスは、この自動展開先(`external_transform\`)
と必ず一致させる必要がある。

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
