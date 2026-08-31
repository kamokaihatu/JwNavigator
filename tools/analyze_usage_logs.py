# ===== ✂️ tools/analyze_usage_logs.py START ✂️ =====
"""
tools/usage_logger.py（配布版: JwNavigator_UsageLogger.exe）が書き出す
JwNavigator_UsageLog.txt を1つ以上まとめて集計する開発者向けツール。

同僚から集めた複数人分・複数回分のログをまとめて、コマンド別の
使用回数ランキング（実行中の左右クリック・Escape・直後の戻る回数の
内訳込み）や合計クリック数などを1本のレポートにする。

使い方:
    .venv\\Scripts\\python.exe tools\\analyze_usage_logs.py [パスまたはフォルダ...]

    引数なしの場合はカレントフォルダ直下の *UsageLog*.txt を対象にする。
    フォルダを渡すと、その中の *UsageLog*.txt を再帰的に探す
    （複数人から集めたログを1つのフォルダに集めて渡す想定）。
    ファイル名がそのまま「誰の分か」の識別に使われる（例:
    田中さんのログを "田中_JwNavigator_UsageLog.txt" のように
    リネームしておくと、レポートの内訳に名前が出る）。

結果はコンソールに表示すると同時に、JwNavigator_UsageAnalysis.txt
としても保存する。
"""
import datetime
import glob
import os
import re
import sys
from collections import defaultdict

SESSION_HEADER = "=== JwNavigator 簡易利用状況ログ ==="
# 👑 「コマンド別使用回数」の行は [左N 右N EscN 戻るN] という実行中の
# 内訳が付く（旧バージョンのログには付かないので後半を丸ごと省略可能に
# しておく）。「単発コマンド使用回数」の行は内訳なしの単純な形。
_LINE_RE = re.compile(
    r"^\s*([A-Za-z0-9]+)\s+(.+?):\s*(\d+)回"
    r"(?:\s*\[左(\d+)\s*右(\d+)\s*Esc(\d+)\s*戻る(\d+)\])?\s*$"
)


def _parse_int(line):
    m = re.search(r"(\d+)", line)
    return int(m.group(1)) if m else 0


def _parse_dt(s):
    try:
        return datetime.datetime.fromisoformat(s.strip())
    except Exception:
        return None


def _parse_block(block, source_name):
    lines = [l.rstrip() for l in block.strip("\n").splitlines()]
    if not lines:
        return None
    session = {
        "source": source_name,
        "started_at": None,
        "ended_at": None,
        "left_clicks": 0,
        "right_clicks": 0,
        "key_presses": 0,
        "escape_presses": 0,
        "commands": defaultdict(int),
        "momentary": defaultdict(int),
        "during_left": defaultdict(int),
        "during_right": defaultdict(int),
        "during_escape": defaultdict(int),
        "undo_after": defaultdict(int),
    }
    mode = None
    for line in lines:
        if line.startswith("開始:"):
            session["started_at"] = _parse_dt(line.split(":", 1)[1])
        elif line.startswith("終了:"):
            session["ended_at"] = _parse_dt(line.split(":", 1)[1])
        elif line.startswith("左クリック回数:"):
            session["left_clicks"] = _parse_int(line)
        elif line.startswith("右クリック回数:"):
            session["right_clicks"] = _parse_int(line)
        elif line.startswith("キー入力回数:"):
            session["key_presses"] = _parse_int(line)
        elif line.startswith("Escapeキー押下回数:"):
            session["escape_presses"] = _parse_int(line)
        elif line.startswith("コマンド別使用回数"):
            mode = "commands"
        elif line.startswith("単発コマンド使用回数") or line.startswith("推定値"):
            mode = "momentary"
        elif "使用されたコマンドはありませんでした" in line:
            continue
        elif mode in ("commands", "momentary"):
            m = _LINE_RE.match(line)
            if m:
                cid, name, cnt = m.group(1), m.group(2), int(m.group(3))
                key = (cid, name)
                target = session["commands"] if mode == "commands" else session["momentary"]
                target[key] += cnt
                if mode == "commands" and m.group(4) is not None:
                    session["during_left"][key] += int(m.group(4))
                    session["during_right"][key] += int(m.group(5))
                    session["during_escape"][key] += int(m.group(6))
                    session["undo_after"][key] += int(m.group(7))
    if session["started_at"] is None and not session["commands"]:
        return None
    return session


def parse_log_file(path):
    source_name = os.path.splitext(os.path.basename(path))[0]
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f"⚠️ 読み込み失敗: {path} ({e})")
        return []
    blocks = text.split(SESSION_HEADER)
    sessions = []
    for block in blocks[1:]:
        session = _parse_block(block, source_name)
        if session:
            sessions.append(session)
    return sessions


def _collect_target_files(paths):
    if not paths:
        paths = ["."]
    files = []
    for p in paths:
        if os.path.isdir(p):
            files.extend(glob.glob(os.path.join(p, "**", "*UsageLog*.txt"), recursive=True))
        elif os.path.isfile(p):
            files.append(p)
    # 👑 usage_logger.py自身の自動保存ファイル（進行中.txt）は未確定の
    # 途中経過であり、確定ログ（.txt本体）と二重集計になり得るため除外する。
    return sorted(set(f for f in files if "進行中" not in os.path.basename(f)))


def aggregate(all_sessions):
    total = {
        "left_clicks": 0, "right_clicks": 0, "key_presses": 0, "escape_presses": 0,
        "commands": defaultdict(int),
        "momentary": defaultdict(int),
        "during_left": defaultdict(int),
        "during_right": defaultdict(int),
        "during_escape": defaultdict(int),
        "undo_after": defaultdict(int),
        "duration_sec": 0.0,
        "earliest": None, "latest": None,
        "sources": defaultdict(lambda: {"sessions": 0, "duration_sec": 0.0}),
    }
    for s in all_sessions:
        total["left_clicks"] += s["left_clicks"]
        total["right_clicks"] += s["right_clicks"]
        total["key_presses"] += s["key_presses"]
        total["escape_presses"] += s["escape_presses"]
        for k, v in s["commands"].items():
            total["commands"][k] += v
        for k, v in s["momentary"].items():
            total["momentary"][k] += v
        for k, v in s["during_left"].items():
            total["during_left"][k] += v
        for k, v in s["during_right"].items():
            total["during_right"][k] += v
        for k, v in s["during_escape"].items():
            total["during_escape"][k] += v
        for k, v in s["undo_after"].items():
            total["undo_after"][k] += v

        duration = 0.0
        if s["started_at"] and s["ended_at"]:
            duration = max(0.0, (s["ended_at"] - s["started_at"]).total_seconds())
            total["duration_sec"] += duration
        for dt in (s["started_at"], s["ended_at"]):
            if dt:
                if total["earliest"] is None or dt < total["earliest"]:
                    total["earliest"] = dt
                if total["latest"] is None or dt > total["latest"]:
                    total["latest"] = dt

        src = total["sources"][s["source"]]
        src["sessions"] += 1
        src["duration_sec"] += duration
    return total


def _format_duration(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}時間{m}分"
    if m:
        return f"{m}分{s}秒"
    return f"{s}秒"


def build_report(all_sessions, target_files):
    total = aggregate(all_sessions)
    lines = []
    lines.append("=== JwNavigator 利用状況ログ 集計レポート ===")
    lines.append(f"集計対象ファイル数: {len(target_files)}")
    for f in target_files:
        lines.append(f"  - {f}")
    lines.append(f"セッション数（記録された起動〜終了の回数）: {len(all_sessions)}")
    if total["earliest"] and total["latest"]:
        lines.append(
            f"期間: {total['earliest'].isoformat(timespec='seconds')} 〜 "
            f"{total['latest'].isoformat(timespec='seconds')}"
        )
    lines.append(f"合計計測時間: {_format_duration(total['duration_sec'])}")
    lines.append("")
    lines.append(f"左クリック合計: {total['left_clicks']}")
    lines.append(f"右クリック合計: {total['right_clicks']}")
    lines.append(f"キー入力合計: {total['key_presses']}")
    lines.append(f"Escapeキー押下合計: {total['escape_presses']}")
    lines.append("")

    lines.append("--- コマンド別使用回数ランキング ---")
    lines.append("  （選択回数 / 実行中の左クリック・右クリック・Escape・その直後に戻るが押された回数）")
    command_total = sum(total["commands"].values())
    ranked = sorted(total["commands"].items(), key=lambda kv: -kv[1])
    if ranked:
        for (cid, name), cnt in ranked:
            pct = (cnt / command_total * 100) if command_total else 0
            dl = total["during_left"].get((cid, name), 0)
            dr = total["during_right"].get((cid, name), 0)
            de = total["during_escape"].get((cid, name), 0)
            du = total["undo_after"].get((cid, name), 0)
            lines.append(
                f"  {cnt:>5}回 ({pct:4.1f}%)  {cid} {name}"
                f"  [左{dl} 右{dr} Esc{de} 戻る{du}]"
            )
    else:
        lines.append("  (コマンド使用の記録がありませんでした)")

    if total["momentary"]:
        lines.append("")
        lines.append("--- 単発コマンド使用回数（戻る等、直接クリックのみ検出） ---")
        for (cid, name), cnt in sorted(total["momentary"].items(), key=lambda kv: -kv[1]):
            lines.append(f"  {cnt:>5}回  {cid} {name}")

    if len(total["sources"]) > 1:
        lines.append("")
        lines.append("--- ファイル別内訳 ---")
        for source, info in sorted(total["sources"].items()):
            lines.append(
                f"  {source}: セッション{info['sessions']}回 / "
                f"計測時間{_format_duration(info['duration_sec'])}"
            )

    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    target_files = _collect_target_files(args)
    if not target_files:
        print("集計対象の JwNavigator_UsageLog.txt が見つかりませんでした。")
        print("使い方: python tools\\analyze_usage_logs.py [パスまたはフォルダ...]")
        return

    all_sessions = []
    for path in target_files:
        all_sessions.extend(parse_log_file(path))

    report = build_report(all_sessions, target_files)
    print(report)

    out_path = "JwNavigator_UsageAnalysis.txt"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"\nレポートを保存しました: {os.path.abspath(out_path)}")
    except Exception as e:
        print(f"\nレポートの保存に失敗しました: {e}")


if __name__ == "__main__":
    main()
# ===== ✂️ tools/analyze_usage_logs.py END ✂️ =====
