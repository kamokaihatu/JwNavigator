# ===== ✂️ utils/app_paths.py START ✂️ =====
"""
利用者のパレット設定・レイヤ保存データ等の永続化先を一元管理する。

👑 2026-09-11決定(DECISIONS.md参照): 「exeを入れ替え/移動してもパレット
設定が消えないように」という要望を受け、設定ファイル群(config.json/
window_state.json/menu_prefs.json/auto_attr_pending.json/
layer_snapshots/)の保存先を、パッケージ版(凍結exe)に限り
exeの隣(_resolve_base_dir()配下)から%APPDATA%\\JwNavigator\\configへ
移した。

開発環境(python main.py)は対象外で、従来通りリポジトリ直下のconfig\\の
ままにする(config/config.json をgitでコミットして共有する既存の運用を
崩さないため)。

移さないもの: data/(starter_presets/commands_master.csv/app_icon.ico)・
icons/・png_icons/はexeに同梱される読み取り専用リソースであり利用者の
設定ではないため対象外。external_transform/(外部変形ツール一式、
utils/external_transform_setup.py)も、常に「今動いているexeに同梱された
最新版」であるべきなので意図的にexeの隣へ残す。

既存ユーザーが以前のバージョンで使っていたexe隣接のconfig/フォルダの
中身は、初回起動時だけ自動でここへコピーする
(migrate_legacy_config_if_needed())。新しい場所に既にファイルがあれば
上書きしない(移行は1回きり)。
"""
import os
import shutil
import sys

APP_DIRNAME = "JwNavigator"
_MIGRATE_ITEMS = (
    "config.json",
    "window_state.json",
    "menu_prefs.json",
    "auto_attr_pending.json",
    "layer_snapshots",
)


def _resolve_base_dir():
    # 👑 他のutils/*.pyと同じ小さなヘルパーの重複(既存パターンに合わせた
    # 許容範囲、モジュール間の不要な結合を避ける)。
    try:
        script_path_str, *_ = sys.argv
        exe_dir = os.path.dirname(os.path.abspath(script_path_str))
        if os.path.isdir(exe_dir):
            return exe_dir
    except Exception:
        pass
    return os.getcwd()


def _legacy_config_dir():
    return os.path.join(_resolve_base_dir(), "config")


def user_config_dir():
    # 👑 開発環境では今まで通りリポジトリ直下のconfig\を使う(gitでの
    # 共有運用を維持するため)。パッケージ版(凍結exe)だけAppDataへ。
    if not getattr(sys, "frozen", False):
        return _legacy_config_dir()
    appdata = os.environ.get("APPDATA")
    if not appdata:
        # 👑 APPDATA未設定という異常系(通常のWindows実行では起こらない)
        # だけ、従来通りexe隣接へフォールバックする。
        return _legacy_config_dir()
    return os.path.join(appdata, APP_DIRNAME, "config")


def migrate_legacy_config_if_needed(log=None):
    if not getattr(sys, "frozen", False):
        return

    legacy_dir = _legacy_config_dir()
    new_dir = user_config_dir()
    if os.path.normcase(os.path.abspath(legacy_dir)) == os.path.normcase(os.path.abspath(new_dir)):
        return  # APPDATA未設定でフォールバック先が同じになったケース等
    if not os.path.isdir(legacy_dir):
        return

    try:
        os.makedirs(new_dir, exist_ok=True)
    except Exception as e:
        if log:
            log(f"⚠️ 設定の移行先フォルダを作成できません: {e}")
        return

    moved = []
    for name in _MIGRATE_ITEMS:
        src = os.path.join(legacy_dir, name)
        dst = os.path.join(new_dir, name)
        if os.path.exists(dst):
            continue  # 新しい場所に既にあるなら移行済み、上書きしない
        if not os.path.exists(src):
            continue
        try:
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            moved.append(name)
        except Exception as e:
            if log:
                log(f"⚠️ 設定の移行に失敗しました ({name}): {e}")

    if moved and log:
        log(f"🔧 以前の設定を新しい保存先へ引き継ぎました: {', '.join(moved)} → {new_dir}")
# ===== ✂️ utils/app_paths.py END ✂️ =====
