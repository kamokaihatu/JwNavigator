# ===== ✂️ utils/command_master.py START ✂️ =====
import csv
import os
import sys

_cache = None


def _resolve_csv_path():
    try:
        script_path_str, *_ = sys.argv
        exe_dir = os.path.dirname(os.path.abspath(script_path_str))
        path = os.path.join(exe_dir, "data", "commands_master.csv")
        if os.path.exists(path):
            return path
    except Exception:
        pass
    # 👑 tools/usage_logger.pyのようにexe横にdata/を配置しない単体配布
    # （PyInstaller onefile）の場合、上のexe_dir基準では見つからない。
    # その場合はsys._MEIPASS配下に同梱したフォールバック用コピーを使う。
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        bundled_path = os.path.join(meipass, "data", "commands_master.csv")
        if os.path.exists(bundled_path):
            return bundled_path
    return os.path.join("data", "commands_master.csv")


def _load():
    global _cache
    if _cache is not None:
        return _cache

    _cache = {}
    path = _resolve_csv_path()
    if not os.path.exists(path):
        return _cache

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            command_id = row.get("command_id", "").strip()
            if command_id:
                _cache[command_id] = row
    return _cache


def get_by_command_id(command_id: str):
    return _load().get(command_id)


def get_id_command(command_id: str):
    row = get_by_command_id(command_id)
    if not row:
        return None
    value = row.get("idCommand", "").strip()
    return int(value) if value else None


def get_shortcut_key(command_id: str):
    row = get_by_command_id(command_id)
    if not row:
        return None
    value = row.get("shortcut_key", "").strip()
    return value or None


def list_available_commands():
    # idCommandとshortcut_keyが両方とも空の行は実行できないため除外する
    rows = []
    for command_id, row in _load().items():
        id_cmd = (row.get("idCommand") or "").strip()
        shortcut = (row.get("shortcut_key") or "").strip()
        if not id_cmd and not shortcut:
            continue
        toolbar_no = (row.get("toolbar_no") or "").strip()
        rows.append(
            {
                "command_id": command_id,
                "toolbar_name": (row.get("toolbar_name") or "").strip() or command_id,
                "category": (row.get("category") or "").strip() or "その他",
                "command_kind": (row.get("command_kind") or "").strip() or "その他",
                "shortcut_key": shortcut,
                "id_command": int(id_cmd) if id_cmd.isdigit() else None,
                "default_icon": (row.get("default_icon") or "").strip(),
                "toolbar_no": int(toolbar_no) if toolbar_no.isdigit() else None,
            }
        )
    # 👑 2026-09-14: 以前は(category, command_id)順だったが、カテゴリ
    # ごとにまとめて表示されるだけで「一覧全体としては番号順に見えない」
    # という指摘(ユーザー)があったため、jw_cad実機のツールバー配置
    # そのままの番号であるtoolbar_no順に変更した(commands_master.csvの
    # 収集時にこの列だけ実際のボタン位置を反映済み、doc参照)。同じ
    # toolbar_noを複数行が共有する場合(例: 図登録スロット1〜8=C058_1〜8)
    # はcommand_idで安定した順に並べる。toolbar_noが無い行は末尾に回す。
    rows.sort(key=lambda r: (r["toolbar_no"] is None, r["toolbar_no"], r["command_id"]))
    return rows


def list_categories():
    return sorted({r["category"] for r in list_available_commands()})


def list_command_kinds():
    # 👑 メイン/サブ/ファイル操作/ブロックの並び順を固定したいので、実データ
    # からの集合ソートではなく既知の順序を優先し、未知の値だけ末尾に追加する。
    known_order = ["メイン", "サブ", "ファイル操作", "ブロック"]
    present = {r["command_kind"] for r in list_available_commands()}
    ordered = [k for k in known_order if k in present]
    ordered += sorted(present - set(known_order))
    return ordered
# ===== ✂️ utils/command_master.py END ✂️ =====
