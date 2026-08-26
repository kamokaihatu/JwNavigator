# JwNavigator Ver2.0 システム要件定義書・基本設計仕様書

本ドキュメントは、Python 3.13 および Windows 11 環境下において、CADフリーソフト「Jw_cad (10.03以降)」の操作を画期的に高速化する補助コマンドランチャーシステム「JwNavigator Ver2.0」の完全復旧・安定稼働を担保するための最終確定仕様書である。

---

## 1. システム動作要件（System Requirements）

*   **OS**: Windows 11 (64bit) 
*   **開発言語**: Python 3.13
*   **対象CAD**: Jw_cad 10.03
*   **主要Win32API依存関係**: `pywin32` (`win32gui`, `win32con`, `win32process`, `win32api`), `ctypes`

---

## 2. 物理配置・フォルダツリー（Folder Structure）

PyInstallerによるEXE単体パッケージ化の際、作業ディレクトリ依存によるファイル紛失（物理クラッシュ）を完全に防ぐため、実行プロセスの実引数（`sys.argv`）を起点とした絶対パスシールドを採用する。

```text
JwNavigator/
├── main.py                    # 司令塔・メインパイプライン（50ms周期）
├── JwNavigator_Log.txt        # 1ミリ秒精度 垂れ流しシステムログファイル
├── config/
│   └── config.csv             # 5列構成：配置,種類,名前,キー,アイコン
├── utils/
│   ├── __init__.py
│   ├── jww_watcher.py         # Jwwステータスバー生テキスト抽出
│   ├── state_patterns.py      # 型安全Enum & 状態正規表現データベース
│   ├── state_parser.py        # ステータスバー解析・状態ID翻訳
│   ├── event_engine.py        # 150ms（3ループ）静止判定イベントエンジン
│   └── send_key.py            # アタッチハック内蔵高速物理キー送信
└── widgets/
    ├── __init__.py
    ├── toolbar.py             # 小ウィンドウ型Toolbar（Toplevel）
    └── button.py              # 1.22仕様カスタムボタン・ラッパー（ScaledCanvas内蔵）
```

---

## 3. コアアーキテクチャ・設計仕様（Technical Specifications）

### ① 【取得層・解析層】4レイヤー・パイプライン
*   基本内部スキャン周期を **50ms** に一本化。
*   Jwwの一瞬の文字明滅（30msノイズ）に騙されないよう、同じ状態が3ループ継続したことを検知する「150ms静止判定イベントエンジン」を搭載。
*   `ctypes.create_unicode_buffer` 直撃による `memoryview` 型エラーを完全防止。

### ② 【送信層】最表面アタッチ・高速物理キー送信
*   Jwwを内部フリーズさせる `win32gui.SetFocus` は永久追放（引き算）。
*   現在前面ウィンドウとPython側のスレッドIDを `AttachThreadInput` で電気的にドッキングさせ、Windows11のフォーカス制限を完全突破。
*   最前面化の確保後、`win32com.client.Dispatch("WScript.Shell")` による高速打鍵を実行。
*   先頭 `%` を検知した際、Alt ➔ 30ms待機 ➔ e ➔ 60ms待機 ➔ 後続文字 の3段階時間差バラバラタイピングを完全再現（Altマクロ処理）。

### ③ 【UI層】48pxカスタムボタン＆多重マージン
*   **パッキング配置サイズ**: 横52 × 縦52 ピクセル（`pady=1` などの余白込み）。
*   **ボタン全体のサイズ**（`NavButton`）：48 × 48 ピクセル（`bg="#ffffff"`）。
*   **内蔵Canvas領域**（`tk.Canvas`）：44 × 44 ピクセル。
*   **マージン**: 上下左右に **2px** ずつ（`padx=2, pady=2`）。
*   **アイコン表示優先順位**: ① PNG画像 (`png_icons/`) ➔ ② Python Canvas等倍描画 (`icons/`) ➔ ③ 文字自動生成。
*   **ScaledCanvas**: 16pxで美しく設計された数式座標コードを改変せず、内部で自動2倍化して32px領域へセンター配置（`x=5, y=5`）するラッパー構造。
*   **ドラッグ誤反応防止（マウスガード）**: `<B1-Motion>` でドラッグ中フラグ（`_is_dragging=True`）を立て、リリース時の意図しないコマンド発動を完全シールド。
*   **画面端・マルチディスプレイ吸着**: `win32api.GetSystemMetrics` から全仮想画面の物理サイズを取得し、2画面をまたぐ境界であってもパレットが画面外へ消滅するのを完全防止。

### ④ 【設定層】5列拡張 config.csv 仕様
*   Excel保存（`utf-8-sig`）対応。先頭 `#` のコメント行や空行を無視するスキップガードを内蔵。
*   **フォーマット**: `配置位置, ボタンタイプ, コマンド名, 送信キー, アイコン名`
*   **特殊キー**: アンドゥ・リドゥ等の `{ESC}` 構文をWScript公式規則である `{ESCAPE}` へリアルタイム置換。

---

## 4. 進捗状況および残された課題（Current Status & Final Task）

*   **現在のステータス**: **「片思い（片方向連動）」状態の完全復活完了。** パレットのボタンを押すことで、Jww側のコマンドが最表面でサクサクと確実に切り替わることが実証されている。
*   **残された最終タスク**: **「両思い（双方向連動）」の開通。** Jww側で直接「線」や「矩形」をクリックした際に、パレット側の対応するボタンも連動して自動で凹凸トグル点灯（選択状態の同期・Idle時の自動リセット）を走らせるための、`main.py` (PART 3) 内の逆引き判定スキャンのカチ込み。


# DEVELOPMENT_STATUS 20260806

## 1. プロジェクト概要

- JwNavigator は、Jw_cad の操作を補助するための Windows 向け Python アプリケーションである。
- 目的は、Jw_cad のツールバーが小さく操作しづらい点を補うため、コマンドパレットと状態収集機能を通じて操作を支援することにある。
- 現在の開発目的は、Jw_cad の状態遷移を検出し、対応するボタンの選択状態や送信動作を反映することにある。
- 仕様書では「Jw_cad 10.03 以降」を対象とし、Windows 11 / Python 3.13 / pywin32 / ctypes を利用した実装として整理されている。

## 2. 開発環境

- OS: Windows
- 実際の Python バージョン: 3.13.14
- .venv の Python バージョン: 3.13.14
- .venv の場所: [.venv](.venv)
- Jw_cad のバージョン:
  - リポジトリ内の文書では「Jw_cad 10.03 以降」と記載されている。
  - 実行環境上の具体的なバージョン情報は、この作業時点では確認できていない。
- 主要ライブラリ:
  - pywin32
  - tkinter
  - ctypes
  - win32com.client
- VS Code / Git / GitHub:
  - Git リポジトリあり
  - GitHub remote は https://github.com/kamokaihatu/JwNavigator.git
  - 現在の作業ブランチは fix/main-lint

## 3. 現在の Git 状態

- 現在のブランチ: fix/main-lint
- remote: origin -> https://github.com/kamokaihatu/JwNavigator.git
- 直近のコミット: 4ba3a71ecf35253881a8a12d6e451e2748e6e9db
- Git 履歴の確認では、初期コミットと main との merge が確認できる。
- 現在の working tree が clean かどうかについては、この作業では Git コマンド実行による直接確認は行っていない。
- GitHub へ push 済みか: この作業時点では確認できていない。
- 現在の状態から安全に戻れるコミット: 4ba3a71ecf35253881a8a12d6e451e2748e6e9db が現状のブランチ先頭コミットとして確認できる。

## 4. 現在のプロジェクト構成

- [main.py](main.py)
  - アプリの司令塔。JwNavigator の全体制御、フック、監視ループ、Tkinter UI、状態解析・送信をまとめて担当する。
- [utils/](utils)
  - [utils/jww_watcher.py](utils/jww_watcher.py): Jw_cad のステータスバー文字列を取得する。
  - [utils/state_parser.py](utils/state_parser.py): ステータスバー文字列を解析して状態 ID とルールを返す。
  - [utils/state_patterns.py](utils/state_patterns.py): 状態パターン定義。
  - [utils/parse_result.py](utils/parse_result.py): パース結果の構造体。
  - [utils/send_key.py](utils/send_key.py): Windows 上でキー送信を行う。
  - [utils/state_collection.py](utils/state_collection.py): 状態収集ログの記録処理。
  - [utils/event_engine.py](utils/event_engine.py): イベント判定用の補助モジュール。
- [widgets/](widgets)
  - [widgets/toolbar.py](widgets/toolbar.py): パレットの UI を構成するウィンドウ。
  - [widgets/button.py](widgets/button.py): ボタンの描画と挙動を担当する。
  - [widgets/debug_window.py](widgets/debug_window.py): デバッグ用ウィンドウ。
- [tests/](tests)
  - [tests/test_state_collection.py](tests/test_state_collection.py): 状態収集の行整形テスト。
  - [tests/record_status_transitions.py](tests/record_status_transitions.py): 状態遷移記録用の補助スクリプト。
- [config/](config)
  - [config/config.csv](config/config.csv): パレットボタン構成を定義する設定ファイル。
- [data/](data)
  - [data/commands_master.csv](data/commands_master.csv) と [data/commands_master.md](data/commands_master.md): Jw_cad のコマンド情報を整理したマスターデータ。
- [typings/](typings)
  - [typings/win32api.pyi](typings/win32api.pyi), [typings/win32con.pyi](typings/win32con.pyi), [typings/win32gui.pyi](typings/win32gui.pyi): pywin32 用の型情報。
- [_internal/]( _internal)
  - PyInstaller / Python ランタイム周りの内部資産や DLL を含むディレクトリ。

## 5. JwNavigator の現在の起動経路

- [main.py](main.py) の `if __name__ == "__main__":` で `JwNavigatorManager()` を生成している。
- `JwNavigatorManager.__init__()` で Tk のルートウィンドウを作成し、各種状態変数とフック制御オブジェクトを初期化する。
- `StateCollectionLogger` を生成し、`enable()` を呼び出して状態収集を有効化する。
- `JwNavigatorManager.start()` で `MouseHookController.start()` と `KeyboardHookController.start()` を呼び、次に `root.after(500, self.monitor_loop)` で監視ループを開始し、最後に `root.mainloop()` を実行する。
- `monitor_loop()` は 1 秒ごとに再スケジュールされ、Jw_cad ウィンドウの列挙、状態解析、ログ出力、UI 更新を行う。

## 6. 現在確認されている問題

### 確認済み事実

- Python 実行環境は 3.13 系であり、.venv も 3.13.14 である。
- 以前に `typing.py` が壊れており、Python の標準ライブラリ読み込み時に構文エラーが発生する事象が確認されていた。
- .venv は再作成済みである。
- pywin32 は再インストール済みである。
- `StateCollectionLogger` には `enable()` / `disable()` / `is_enabled()` の不整合があり、[main.py](main.py) の呼び出しと実装が一致していなかった。
- 起動時に `0xC000041D` / `-1073740771` が発生する事象が確認されている。
- MouseHook / KeyboardHook を有効にしたときに、起動直後の挙動が重くなり、しばらく後にプロセスが終了して PowerShell に戻る現象が確認されている。
- 両方の Hook を有効にした場合、CPU 負荷が高くなる挙動が確認されている。
- UI が表示されない理由として、`self.root.withdraw()` が実行されていることと、`self._auto_create_palettes = False` でパレットの動的生成条件が成立しないことがコード上確認できる。

### 推測・可能性

- フック周りの処理と監視ループの重なりが、起動後の高負荷や終了につながっている可能性がある。
- 低レベルフック処理、Windows API 呼び出し、状態収集ログの書き込み、Jw_cad ウィンドウ列挙が同時に発生しているため、原因の切り分けが必要である。

## 7. StateCollection 関連

- [utils/state_collection.py](utils/state_collection.py) では、`StateCollectionLogger` がログの有効/無効フラグをもつ。
- `record()` は `_enabled` が False の場合に何もしない。
- [main.py](main.py) の `JwNavigatorManager.__init__()` で `StateCollectionLogger` を生成し、`enable()` を呼び出している。
- [main.py](main.py) の `record_state_collection_event()` から `record()` が呼ばれる。
- [main.py](main.py) の `MouseHookController` と `KeyboardHookController` のイベント処理からも、状態収集ログの記録が発生する可能性がある。
- 依存関係として、[utils/state_collection.py](utils/state_collection.py) から [utils/state_parser.py](utils/state_parser.py) と [utils/jww_watcher.py](utils/jww_watcher.py) の結果を受ける構造になっている。

## 8. Hook 関連

- [main.py](main.py) の `JwNavigatorManager.__init__()` で `MouseHookController(self)` と `KeyboardHookController(self)` が生成される。
- [main.py](main.py) の `JwNavigatorManager.start()` で `self.mouse_hook_controller.start()` と `self.keyboard_hook_controller.start()` が呼ばれる。
- MouseHookController は `ctypes.windll.user32.SetWindowsHookExW()`、`GetMessageW()`、`TranslateMessage()`、`DispatchMessageW()`、`CallNextHookEx()` を利用している。
- KeyboardHookController も同様に `SetWindowsHookExW()` と `CallNextHookEx()` などを利用している。
- どちらも `ctypes.WINFUNCTYPE(...)` で callback を定義し、Windows からイベントを受け取ったときに `self.manager` 経由で状態取得・イベント記録・ステータス収集を行う。

## 9. 現在の変更点

- 本作業ではコード変更は行っていない。
- ただし、以下の点は確認済みである。
  - [utils/state_collection.py](utils/state_collection.py) に `enable()` / `disable()` / `is_enabled()` を追加する対応が必要であった。
  - [main.py](main.py) では、フック起動と監視ループの実行順が起動時の挙動に大きく影響している。
  - 既存の [main.py](main.py) と [utils/state_collection.py](utils/state_collection.py) の API には不整合がある。

## 10. 現在の作業状態

### 現在できていること

- プロジェクト構成、主要ファイル、Git 設定、起動経路、Hook / StateCollection 周りの実装を確認できている。
- 既知の異常について、コード上の実際の箇所と症状の対応を整理できている。

### 現在できていないこと

- 0xC000041D の直接的な原因をコード修正なしで断定できていない。
- フックと監視ループのどちらが主因かを、実行ログやデバッグ手段で明示的に切り分け切れていない。

### 未解決の問題

- 0xC000041D / -1073740771 の原因。
- 起動後の高負荷とプロセス終了の関係。
- UI が表示されない原因の切り分け。

### 次に調査すべきこと

- Hook を単独で起動した場合の再現性確認。
- `monitor_loop()` と `root.after()` の連鎖を止めた場合の挙動確認。
- 状態収集ログ書き込みを抑止した場合の挙動確認。
- `root.withdraw()` と `_auto_create_palettes=False` を含む UI 起動条件の再確認。

## 11. AI 作業時の注意事項

- 大規模な変更を一度に行わない。
- 1 ファイルまたは小さな変更単位で作業する。
- 変更前に対象ファイルを読む。
- 変更後は必ず起動テストをする。
- 動作確認後に Git コミットする。
- 既存機能を勝手に削除しない。
- 状態収集機能と JwNavigator 本体の役割を混同しない。
- 原因調査とコード修正を同時に行わない。
- 不明な部分は推測で修正せず、確認を求める。

---

# DEVELOPMENT_STATUS 20260821

このセクションは次回作業再開時に最初に読む用の最新サマリー。上の章（8月6日時点）は当時のデバッグ記録として残しているが、内容は大きく古くなっている（config.csvはこの時点でJSONへ移行済み）。

## 1. 現在の到達点（ざっくり）

- 「両想い（双方向連動）」は完成済み。パレット→jw_cad、jw_cad→パレットの両方向で選択状態が同期する。
- コマンド送信は`idCommand`（WM_COMMAND直送）が主経路、`shortcut_key`はフォールバック。ショートカットキーのカスタマイズに依存しないので安定。
- ユーザーの実際のjw_cadツールバー配置を再現したカスタムパレットレイアウトが動いている（左17個1列、右22個を12個+10個の2列）。
- パレットのボタン構成をGUIで編集できる「設定画面」が完成（パレットを右クリック→「⚙️ パレットを編集」）。config.csvは廃止し、config/config.jsonに移行済み。

## 2. ブランチ状況

- 作業ブランチ: `feature/palette-settings-editor`（`feature/custom-toolbar-layout`から分岐）
- 直近コミット: `6f8b6fb`（このセッションの最終コミット、pushmi済み）
- `main`へはまだマージしていない（未マージのfeatureブランチが複数ある: `feature/idcommand-execution`, `feature/custom-toolbar-layout`, `feature/palette-settings-editor`）。マージのタイミングはまだ相談していない。

## 3. 現在のファイル構成（主要なもの）

```text
JwNavigator/
├── main.py                       # 司令塔。監視ループ・状態同期・パレット生成/破棄・設定画面の呼び出し
├── config/
│   └── config.json                # パレットのボタン構成（旧config.csvは廃止・削除済み）
├── data/
│   └── commands_master.csv        # 全85コマンドのマスターデータ（idCommand/shortcut_key/toolbar_no等）
├── utils/
│   ├── palette_config.py          # config.jsonの読み書き・正規化（新規）
│   ├── palette_layout.py          # パレットのドッキング座標計算（純粋関数、win32非依存）
│   ├── command_master.py          # commands_master.csvの読み込み・検索
│   ├── send_command.py            # WM_COMMAND送信（idCommand経路）
│   ├── send_key.py                # ショートカットキー送信（フォールバック経路）
│   ├── jww_watcher.py / state_parser.py / state_patterns.py / state_collection.py / event_engine.py
├── widgets/
│   ├── toolbar.py                 # パレット本体（Toplevel）。config.jsonからグループ/ボタンを構築
│   ├── button.py                  # ボタン描画（アイコン/文字フォールバック、サイズ・背景色対応）
│   ├── settings_window.py         # グラフィカル設定エディタ（新規）
│   └── debug_window.py
└── icons/                          # 25種のアイコン描画モジュール（黒固定・色パラメータなし）
```

## 4. 今回のセッションでやったこと

1. `main.py`の重複ドラッグ実装（`enable_drag_move`）を削除し、`widgets/toolbar.py`側の実装に一本化。
2. `sync_toolbar_position`の座標計算を`utils/palette_layout.py`の純粋関数に切り出し。
3. **グラフィカル設定エディタを新規実装**（要望: ボタンの入れ替え・追加削除・アイコン選択・配置・形状・サイズ・色）
   - `config/config.csv` → `config/config.json`へ移行（列を「グループ」の明示的なリストとして表現、`#MAX_ROWS`/`#BREAK`のようなディレクティブ力技を廃止）。
   - `widgets/settings_window.py`: 左右タブ、グループ単位のListbox表示、▲▼で並べ替え、◀▶でグループ間移動、追加（コマンドピッカー）/削除、＋列/－列、向き（縦長/横長）、ボタンサイズ、色（既定に戻すボタンあり）。
   - 保存すると`reload_all_palettes()`が即座に全パレットを再構築（アプリ再起動不要）。
4. ボタンの色は**背景色**として実装（アイコン付きボタンにも効くように。文字色だと25種のアイコンモジュールを全部書き換える必要があり、今回は見送った）。背景の明るさから文字の黒/白を自動選択。選択（押下）時はその背景色を暗くした版を使う。ボタンの立体感（raised/sunken）はjw_cad純正に寄せてそのまま維持。
5. 4文字ラベルの2行折り返し表示（属性取得→「属性」「取得」等）、分数「1/4」が行またぎで切れない処理。
6. **バグ修正**: `locked_intent`（パレットのボタン凹み保持ロック）が一度セットされると永久に解除されないバグを修正。タイムスタンプ付きにして1.5秒で自動失効するようにした。修正前は「パレット外のjw_cad操作に凹みが追従しない」「Idleに戻っても凹みが戻らない」症状があった。
7. VS Code再起動時にCMDウィンドウが出る問題は、こちらが`python.exe`ではなく`pythonw.exe`で起動すれば出ない（アプリ側の仕様ではない）。

## 5. 未解決・積み残し（優先度未定、次回相談したいこと）

- ~~jw_cadの実際にグレーアウトしている（無効な）コマンドを、パレット側で判別せずに送信できてしまう問題~~ → **2026-08-25対応済み**。`utils/send_command.py`に`is_command_enabled`/`get_command_states`（TB_GETSTATE経由）を追加し、1秒ごとの監視ループ（`main.py`の`_update_button_enabled_states`）で全ボタンの有効/無効を判定してグレーアウト・クリック無効化するようにした（`widgets/button.py`の`set_enabled`）。ハマった点: pywin32のSendMessageがTB_GETSTATEの「見つからない」を符号なし`4294967295`で返す／jw_cadは同じidCommandを持つ非表示ツールバー（ユーザーツールバーの別ページ等）を複数保持しており、`IsWindowVisible`で表示中のものだけに絞る必要があった。
- **ステータスバー文字列による状態判定は完璧ではない**（複数コマンドが同じ汎用文言を共有し、状態が一意に決まらないケースがある）。これは前々から分かっている既知の限界で、優先度判断待ちのまま。
- **将来構想**: 設定エディタを今のリスト+フォーム形式から、ドラッグ&ドロップで見た目通りに配置できるUIへ発展させたい（ユーザー要望、今回は着手せず）。
- **アイコンの色対応**: 今は背景色のみ変更可能。アイコン自体（25個のPythonモジュール）に色を効かせるには各ファイルの書き換えが必要で未着手。
- **未整理のファイル**: `png_icons/sakuzu.png`（未使用、7/9付け、コードから未参照）、`data/kamo作業画面.png`（テスト用、「消さないでおいて」とのことで放置中）、`cowork/`ディレクトリ（ChatGPT関連の作業用？ユーザー自身のファイルなので未着手）。
- **マージ計画未定**: `main`ブランチへいつどうマージするか、複数のfeatureブランチをどう整理するかは未相談。
- **VS Codeクラッシュ対策**（`disable-hardware-acceleration`）が実際に効いているかは、まだ長期間の様子見ができていない（8月20日時点の話）。

## 6. 起動方法メモ

- 通常起動: `.venv\Scripts\pythonw.exe main.py`（`python.exe`だとCMDウィンドウが出る）
- ログ: `JwNavigator_Log.txt`（システムログ）、`JwNavigator_StateCollection_Log.txt`（状態収集ログ）
- 現在アクティブなプロセスは親子構成で2つ立ち上がる（`main.py`が自分自身を子プロセスとして持つ構造、既存仕様）。

---

# DEVELOPMENT_STATUS 20260825

ブランチ: `feature/palette-settings-editor`（`main`未マージ）。8月21日の続きで、設定エディタの実地テストと、両想い（jw_cad→パレット方向）の状態同期まわりのバグ修正に丸一日費やした。

## 1. 今日解決したもの

- **`locked_intent`永久固定バグ**: 一度パレットのボタンを押すと凹みが永久に固定され、以降jw_cad側の実操作に反応しなくなっていた。タイムスタンプ付きで1.5秒失効するよう修正（`main.py`）。これにより初めて「jw_cad直接操作→パレット反映」の経路がまともに動くようになり、以下の問題が次々表面化して見つかった。
- **グレーアウトコマンドの誤送信**: jw_cad側で無効になっているコマンドがパレットからは押せてしまう問題。`utils/send_command.py`の`get_command_states`（`TB_GETSTATE`）で1秒ごとに全ボタンの有効/無効を判定し、`widgets/button.py`の`set_enabled`でグレーアウト・クリック無効化するようにした。
- **円弧ボタンが直接操作に無反応**: `jp_match_map`の`"CIRCLE": "円"`が実際のボタン名`"円弧"`と不一致だった単純なタイポ的バグ。修正済み。
- **マウスオンだけでパレットが誤反応する問題**: `utils/state_patterns.py`に`STATES_WITH_WAIT_RULE`/`is_hover_trustworthy_rule()`を追加し、「実際にコマンドを開始しないと出ない入力待ち文言」を持つコマンドは、その文言が出るまで反映を待つようにした（ツールチップだけでは反映しない）。
- **文言衝突（コーナー↔面取り、座標↔式計算、線↔矩形）**: `utils/state_parser.py`に`AMBIGUOUS_GROUPS`を追加し、衝突文言に当たった時は直前に確定していた方の状態を維持するようにした。
- **線↔矩形だけ直りが悪かった問題**: ポーリング（1秒間隔+クリック検知時の即時読み直し）だと、ツール切替え直後の短命なツールチップ文言を取りこぼしやすく、線と矩形を行ったり来たり誤判定することがあった。`SetWinEventHook`（`OBJECT_NAMECHANGE`）でjw_cadのステータスバー更新を**通知ベースで即座に**検知する`utils/win_event_watcher.py`を新規実装し解決。過去にクラッシュした低レベル入力フック（`WH_MOUSE_LL`/`WH_KEYBOARD_LL`）とは別のAPIで、対象プロセスへのコード注入を伴わない（実機で25秒テストし、統計バー更新205件を正しく検知、クラッシュなしを確認済み）。
- **VS Codeクラッシュ対策の効果確認**: `disable-hardware-acceleration`設定後、クラッシュが再発しなくなったことをユーザーが確認。解決とみなしてよい。

## 2. 今日わかった設計上の知見

- `NavButton.release()`は自分自身で即座に凹み表示するため、`main.py`側で「送信をスキップする」判断をしても、パレットの見た目は一瞬反応してしまう（グレーアウトで事前に押せなくする方が正しい対策）。
- 統計バーの「ツールチップ文言」と「入力待ち文言」は同じ`state_id`に解決されるため、区別するには`rule_name`（`_WAIT`で終わるかどうか）を見る必要がある。
- `SetWinEventHook`（`WINEVENT_OUTOFCONTEXT`）は低レベル入力フックと違い、対象プロセスへのコード注入がなく、コールバックは呼び出し元スレッドのメッセージキューに配送される。今回のような「別プロセスのUI変化を検知したい」用途では、ポーリングより低負荷かつフックより安全な第3の選択肢として有効だった。

## 3. 新しく出た要望（次回以降）

- **グループボタン**: パレット編集機能の一部として、jw_cadには存在しない「グループ」を自作し、その中に複数のコマンドをまとめて格納できるようにしたい（フォルダ的なボタン）。今の設定エディタの「グループ（列/行）」とは別概念で、1つのボタン枠の中にサブメニュー的に複数コマンドを入れるイメージ。未設計・未着手。

## 4. 残っている・保留のもの

- ~~複写・移動・面取りは今もツールチップ頼み（WAIT文言がそもそも存在しないコマンド）なので、理論上はまだホバーに弱い可能性がある~~ → **2026-08-26に検証・対応**。詳細は下のDEVELOPMENT_STATUS 20260826を参照。
- `main`ブランチへのマージ計画（3つのfeatureブランチをどう整理するか）は未相談。
- `png_icons/sakuzu.png`（未使用）は放置中。`data/kamo作業画面.png`は「消さないで」の指示どおり保持。`cowork/`はコミット・push済み（ユーザーが後で手動マージ予定）。
- アイコン自体の色対応（今は背景色のみ）は未着手。
- 設定エディタのドラッグ&ドロップ化は将来構想のまま。

---

# DEVELOPMENT_STATUS 20260826

ブランチ: `feature/palette-settings-editor`（`main`未マージ）。8月25日の続きで、「複写・移動・面取りがまだホバーに弱いのでは」の検証から始めたところ、右パレット全体の反映が最初から機能していなかったこと等、さらに大きな不具合が連鎖的に見つかった一日。

## 1. 今日解決したもの

- **時間ベース安定判定への切り替え**: `utils/event_engine.py`の`JwwEventEngine`が「連続◯回」で安定判定していたが、WinEvent導入後は呼び出し頻度が不定になり、0.26秒のホバーでも誤反映するようになっていた。「同じ状態が何秒続いたか」という経過時間ベースに変更（`required_duration_sec`）。
- **ステータスバー文言クリーンアップの過剰削除バグ**: 「（例：線）」のような注釈だけを消すはずの正規表現が、`(L)`/`(R)`のような文言本体に含まれる括弧まで全部削っていた。消去・ハッチ・AUTO・距離点・図形登録のWAIT文言がこのせいで永久に検知不能になっていた。「例」を含む括弧だけに絞って修正。
- **DIST（距離指定点）の誤登録パターン削除**: 上記の修正で判明。距離指定点のWAIT文言だと思っていたものが、実は線・矩形と共通の汎用「点を指示」文言の切れ端で、括弧削除バグにより偶然「距離指定点固有」に見えていただけだった。距離指定点は現在未設定ボタンのため実害を避けて削除。
- **複写・移動と範囲選択の文言衝突**: 複写・移動はどちらも対象選択フェーズで範囲選択と全く同じ文言を経由する仕様と判明。線↔矩形と同じ`AMBIGUOUS_GROUPS`方式で解決。
- **円弧と多角形の文言衝突**: 多角形も中心点から描き始める仕様のため、円弧の「中心点を指示してください」と文言が完全一致。同様に解決。
- **左右パレットの選択状態が独立していた問題**: 円弧（左）→多角形（右）のように左右をまたぐ切り替えで、片方の凹みが消えず両方光って見えていた。一致した側以外の選択を明示的にクリアするよう修正。
- **右パレット全体が最初から未対応だった**: `jp_match_map`（状態→ボタン名の対応表）に右パレット22個分の対応が最初から一つも登録されていなかった（発見時点まで気づかれていなかった長年の抜け）。`utils/state_patterns.py`のSTATE_DATABASEと突き合わせて、対応可能な範囲を全て追加（`main.py`のモジュールレベル定数`JP_MATCH_MAP`に整理）。「戻る」「進む」も、無関係な`FILE_OPEN`/`FILE_SAVE`状態にひもづく場当たり的対応から、正しい`MODORU`/`SUSUMU`に訂正。
- **文言衝突判定がグローバル単一トラッカーだった問題**: `_last_state_id`という単一の変数で「直前の状態」を覚えていたため、テスト中に無関係な別コマンド（測定・ハッチ等）を一瞬でも経由すると記憶が上書きされ、コーナー↔面取りの判定がふらついた。衝突グループ単位（`_last_group_member`、キー=グループのfrozenset）で別々に記憶するよう変更し解決。
- **サブ・ワンショットコマンドを凹み対象から除外**: ユーザー要望により、`commands_master.csv`の`command_kind`列が「メイン」のコマンドだけを凹み判定の対象にするようにした（`main.py`）。戻る・進む・上書・印刷・保存・コピー・中心点・円周1/4点・属性取得・2点長は今後凹まない。
- **接円だけホバーで誤反応するバグ**: `SETSUEN_WAIT_3RD`という名前が「WAIT」で終わっていない（「3RD」で終わる）ため、WAIT系ルール判定の単純な終端チェックに引っかからず、接円だけホバー扱いされていた。`NON_HOVER_ONLY_RULE_NAMES`に明示追加して修正。

## 2. 既知の制約リスト（jw_cad側の仕様上、これ以上は直しようがないもの）

- **接円**: 1・2番目の指示文言が中心線と完全に同一のため区別不可能。3番目の指示まで進めないと反映されない（1回クリックしただけでは反応しない）。
- **ソリッド**: 対応する状態文言がそもそも未収集で、現状は直接操作からの反映に対応していない。

## 3. 検証方法の教訓

- ログの`[状態解析]`と`[ボタン反映]`を突き合わせることで、「今何が起きているか」をかなり正確に再現・特定できた。体感で「おかしい」と思った時も、ログを見ると実は正しく動いていた（コーナー/面取りの一部の指摘）こともあり、体感とログの両方を確認する価値がある。
- 同種の文言衝突（線↔矩形、コーナー↔面取り、座標↔式計算、複写/移動↔範囲、円弧↔多角形）が次々見つかったことから、jw_cadは「対象選択」や「基準点指示」のような汎用UI文言を多くのコマンドで使い回している可能性が高い。今後も未発見の衝突が出てくる前提で臨むのがよい。

## 4. 続き（同日、ユーザーによる全コマンド再収集後）

ユーザーが実機で全コマンドをクリックして回った結果、上記の対応だけでは足りない実データがさらに見つかった。

- **未登録文言の自動推定（`INFERRED_WAIT`）への一般化**: 個別コマンドごとにWAIT文言を手作業で収集・登録するアプローチはキリがないと判断し、方式転換。「直前に確認できた固有ツールチップ」を`_last_tooltip_state`として覚えておき、その後に未登録文言（`STATE_UNKNOWN`相当）へ変化したら「そのコマンドが実際に入力待ちフェーズへ進んだ」とみなして推定するように変更（`utils/state_parser.py`）。マウス移動中の一瞬だけの文言をノイズとして弾くため、同じ未登録文言が2回連続で観測できてから確定する（`_pending_unknown`）。
- **`_last_tooltip_state`の更新漏れ**: ツールチップ一致時だけ更新していたため、複写・移動が自分のツールチップを離れて「範囲選択の始点を…」（衝突文言）に進んだ時点で更新が止まり、その後の未登録文言（複写先の点を指示、等）が古い無関係コマンドに誤帰属した。マッチするたび常に更新するよう修正。
- **データ欠落の発見・修正**: ソリッドが文言未登録で常に「直前にホバーしたコマンド」に誤推定されていた（登録）。パラメトリックのツールチップ文言が全角/半角カタカナ混在で実際のjw_cad出力と一致していなかった（半角に統一）。2.5Dの固有ツールチップが未登録だった（登録）。分割の実際のWAIT文言（「分割始点指示」）が未登録だった（登録）。
- **ツールチップ判別とクリック確定の分離が不完全だった問題**: ソリッド・曲線・連続線・整理等、WAIT文言を経由せずツールチップのみで完結するコマンドは、キャンバスへ移動しない限り確定しない設計になっていたが、ユーザー指摘「ツールチップ判別してその確定をクリックで行うんじゃないの？」により、既存の`GetAsyncKeyState`ベースのクリック検知（`_check_click_for_immediate_refresh`）と組み合わせ、クリック直後ならツールチップ一致だけで即確定する`click_confirmed`パラメータを追加（`main.py`）。
- **線・矩形・曲線・ソリッド・連続線・範囲・複写・移動・円弧・多角形の衝突グループ統合**: click_confirmed導入直後の再検証で、ソリッド・曲線・連続線の「本当の」WAIT文言が、線・矩形と全く同じ汎用「始点を指示してください」であることが判明（クリック押下中はソリッドが凹むが、離すと矩形表示になり、キャンバスへ移動してもそのまま）。さらに複写・移動もクリック離した瞬間だけ同じ汎用文言を一瞬経由してからRANGE系文言に落ち着くことも判明。1つの状態が複数の衝突文言に関わるため、既存の複数グループを1つの大きなグループに統合（`AMBIGUOUS_GROUPS`、`utils/state_parser.py`）。

## 5. パレット最前面問題（jw_cad非アクティブ時にVSCodeより弱い）

- 症状: jw_cadが非アクティブな時、パレットの`-topmost`はFalseになるはずが、他アプリより手前に残ってしまう。実機の`win32gui.EnumWindows`/`GetWindowLong(-20)`で確認したところ`WS_EX_TOPMOST`は確かにFalseだったが、Z順ではまだ最上位のままだった。`-topmost`をFalseにするのは「最前面グループから外れる」だけで、Z順上の位置（＝外れた直後の一番上）は変わらない、というWindowsの仕様が原因。
- 対処: `-topmost`をFalseにする遷移のタイミングで、明示的に`win32gui.SetWindowPos(hwnd, win32con.HWND_BOTTOM, ...)`を呼び、Z順の最背面へ送るよう修正（`main.py`の`sync_toolbar_position`）。
- 検証結果: Chrome等の一般アプリでは解決。**VSCodeだけ**は依然としてパレットより後ろに来ないことがある（VSCode固有の何らかのウィンドウ挙動と推測、原因未特定）。ユーザー判断により「VSCodeだけの例外なら許容範囲」としてこのままの実装で確定（2026-08-26）。

## 6. パレット最前面問題・真因判明（同日、さらに続き）

上記5の対処後も「文字ツールバーより前に出てしまう」「最大化すると左パレットだけ消える」という新しい不具合が発覚し、調査の結果、**`tl.winfo_id()`/`tr.winfo_id()`が本当のトップレベルウィンドウではなく、その内側の子ウィンドウのhwndを返していた**（実測で`GetParent()!=0`を確認）ことが根本原因と判明。今日一日のZ順修正の試行錯誤（HWND_BOTTOM、topmost切り替え、`hWndInsertAfter`の挙動誤認）は、すべてこの子ウィンドウの兄弟内Z順をいじっていただけで、jw_cad等の他アプリとの前後関係には実質影響していなかった。

`GetParent(tl.winfo_id())`で辿れる本当のトップレベルhwndをキャッシュし、それを対象に「jw_cad本体の直前（１つ前面）に毎tick貼り付け続ける」方式（`hWndInsertAfter`は「指定ウィンドウの直後＝背面側」に置く動きだと実測で確定したため、jw_cad本体の直前にいる別のウィンドウを探してその後ろに割り込む）に統一。文字ツールバー問題・最大化時の消失問題ともに解決し、ユーザー確認済み。VSCodeとの前後関係についても、この方式に統一した結果「文字ツールバーより前面にいるが、これはこのままでいい」とユーザー了承。

## 7. 終了時の配置を記憶する機能

自由配置（ピン留め）中のパレット位置を、終了時に`config/window_state.json`へ保存し、次回起動時に復元する機能を追加（`utils/window_state.py`新設）。右クリックメニューに「📌 終了時の配置を記憶する」のON/OFFトグルを追加。保存位置が画面外（モニター構成変更等）の場合は復元をスキップし通常の追従モードにフォールバックする安全策を、ユーザーの「手の届かない場所に固定される事故が怖い」という懸念を受けて実装。

## 8. コマンド種別の再設計（メイン/サブ/ファイル操作/ブロック）

コマンド追加ダイアログの絞り込みを改善する過程で、旧来の`command_kind`（メイン/サブ/ワンショット）がユーザーの実感と合わないことが判明。ユーザーとの対話・実機検証（一時的な監視スクリプトでウィンドウの開閉を記録し、実際にクリックして確認）を経て、`data/commands_master.csv`の`command_kind`を全74コマンド分再分類:
- **サブ(15)**: jw_cad画面上でボタン文字色が紺/青のもの（線属性・属性取得等の設定系、および戻る・進む）
- **ブロック(5)**: Blk化・Blk解・Blk編・Blk属・Blk終を独立枠に
- **ファイル操作(15)**: クリックするとウィンドウが開く/ファイル選択が挟まるコマンド（新規・開く・上書・保存・印刷・建築3点セット・線記変・外変・図形・画像編集・切取・コピー・貼付）。建築3点セット（建平/建断/建立）が実は「ファイル選択」ダイアログを開くことは、一時的な監視スクリプトでの実測により発覚。
- **メイン(39)**: 残り全部

コマンド追加ダイアログ（`widgets/settings_window.py`のCommandPickerDialog）の絞り込みは、単一選択のプルダウンではなく「種別」「分類」それぞれ複数選択可能なチェックボックス方式に変更（ユーザー要望）。

なお、この再分類によりBlk化/解/編がハイライト判定（`command_kind=="メイン"`のみ対象）から外れる副作用があったが、ユーザー確認の上「やめてよい」と了承済み。

## 9. 【大発見】TBSTATE_CHECKEDビットによるハイライト判定への転換

上記8の作業中、ユーザーから「ブロック編集や画像編集は作業時間があるから凹み判定を残したい、jw本体はどうしているんだろう」という疑問が出たことをきっかけに、jw_cad自身のツールバーボタンの状態を`TB_GETSTATE`で調べたところ、**`TBSTATE_CHECKED`ビットが、今アクティブなコマンドを常に正確に示している**ことが実機検証で判明（線を作図中はCHECKED、矩形はCHECKEDでない、を確認 — この2つはまさに2026-08-25/26と丸1日以上かけてステータスバー文言の衝突解決に苦労してきた組み合わせ）。

新ブランチ`experiment/checked-bit-highlight`を切り、ハイライト判定の主軸を「ステータスバー文言解析（state_parser.py・AMBIGUOUS_GROUPS・INFERRED_WAIT・JP_MATCH_MAP等）」から「`get_command_checked_states()`によるCHECKEDビット直接読み取り」に転換（`main.py`の`_update_checked_highlight`）。旧システムはコードとして温存し、**ツールバーボタンが今表示中でないページにあるためTB_GETSTATEで判定不能なコマンド（例: ソリッド）のみ**、旧ステータスバー方式へフォールバックする設計。線/矩形/円弧/複写/移動等、これまで衝突解決に苦労していた組み合わせも含め、実機で正しく反映されることをユーザー確認済み。

処理負荷は「フォールバック用に旧システムの解析も毎tick動かしたままなので、むしろ増えている」ことをユーザーと確認したが、実用上問題なしとして現状維持で確定。将来的にはCHECKEDビットで判定できた場合はステータスバー読み取り自体をスキップする最適化も可能（未実施）。

**今後の検討**: このCHECKEDビット方式が安定して動作するなら、state_parser.py・AMBIGUOUS_GROUPS・INFERRED_WAIT・click_confirmed等、この2日間かけて作り込んだ複雑な文言解析システムの大部分が実質不要になる可能性がある。`experiment/checked-bit-highlight`ブランチでの検証を継続し、問題なければ`feature/palette-settings-editor`へマージするかどうかを判断する。