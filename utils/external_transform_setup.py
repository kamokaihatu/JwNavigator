# ===== ✂️ utils/external_transform_setup.py START ✂️ =====
"""
外部変形ツール(B_MARK.BAT/A_SAVE.BAT/mark_point.exe/dump_layers.exe)を
JwNavigator.exeの隣に自動展開する。

👑 2026-09-11決定(DECISIONS.md参照): 「利用者がexe1個置くだけで動く状態」
を目標に、これらのファイルを手動でビルド・配置してもらう前提をやめた。
JwNavigator.exe自身にdatas(external_transform_bundle/)として埋め込み、
起動のたびに<exeのあるフォルダ>\\external_transform\\ へ展開し直す
(常にexeに同梱された最新版へ揃える)。

jw_cad側のGCOM_100キー割り付け登録だけは、jw_cad自身の設定ファイルを
直接書き換えるリスクを避けるため、引き続き手動(config/keybind_setup.md
参照)。展開先パスはexeの場所に追従するので、登録時は「今JwNavigator.exe
が置いてあるフォルダ + \\external_transform」を指定すればよい。

layerdump\\(実行時のログ・トレース)は展開対象に含めない
(利用者の使用履歴なので上書きで消さない)。
"""
import os
import shutil
import sys

EXTERNAL_TRANSFORM_DIRNAME = "external_transform"
_BUNDLE_ITEMS = ("B_MARK.BAT", "A_SAVE.BAT", "mark_point", "dump_layers")


def _resolve_base_dir():
    # 👑 main.py/utils/palette_config.py等と同じ小さなヘルパーの重複
    # (既存パターンに合わせた許容範囲、モジュール間の不要な結合を避ける)。
    try:
        script_path_str, *_ = sys.argv
        exe_dir = os.path.dirname(os.path.abspath(script_path_str))
        if os.path.isdir(exe_dir):
            return exe_dir
    except Exception:
        pass
    return os.getcwd()


def external_transform_dir():
    return os.path.join(_resolve_base_dir(), EXTERNAL_TRANSFORM_DIRNAME)


def _bundle_source_dir():
    if not getattr(sys, "frozen", False):
        return None
    base = getattr(sys, "_MEIPASS", _resolve_base_dir())
    return os.path.join(base, "external_transform_bundle")


def ensure_deployed(log=None):
    # 👑 開発環境(python main.py)では何もしない。B_MARK.BAT/A_SAVE.BATは
    # リポジトリ直下に既にあり、mark_point.exe/dump_layers.exeは開発中は
    # 存在しない(pythonスクリプトを直接使う想定)ため、展開対象が無い。
    if not getattr(sys, "frozen", False):
        return

    source_dir = _bundle_source_dir()
    if not source_dir or not os.path.isdir(source_dir):
        if log:
            log(f"⚠️ 外部変形ツールの同梱データが見つかりません: {source_dir}")
        return

    target_dir = external_transform_dir()
    try:
        os.makedirs(target_dir, exist_ok=True)
    except Exception as e:
        if log:
            log(f"⚠️ 外部変形ツールの展開先フォルダを作成できません: {e}")
        return

    failed = []
    for name in _BUNDLE_ITEMS:
        src = os.path.join(source_dir, name)
        dst = os.path.join(target_dir, name)
        try:
            if os.path.isdir(src):
                shutil.rmtree(dst, ignore_errors=True)
                shutil.copytree(src, dst)
            elif os.path.isfile(src):
                shutil.copy2(src, dst)
        except Exception as e:
            failed.append(name)
            if log:
                log(f"⚠️ 外部変形ツール展開失敗 ({name}): {e}")

    if log and len(failed) < len(_BUNDLE_ITEMS):
        log(f"🔧 外部変形ツールを展開しました: {target_dir}")
# ===== ✂️ utils/external_transform_setup.py END ✂️ =====
