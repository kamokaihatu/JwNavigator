# -*- coding: utf-8 -*-
"""
Jw_cad 外部変形: 全レイヤグループ×全レイヤ(16x16=256)の状態を取得する。

必要なバッチ制御行（JWW_SMPL.BAT の仕様に準拠）:
    REM #jww
    REM #h1     データ選択方式（これが無いと #g1 が効かない）
    REM #g1     必ず #h* の直後。全レイヤグループ選択
    REM #gn     レイヤグループ・レイヤの状態と名前を書き出す
    REM #e

図面は変更しない（Jw_cad へは he 行だけ返す）。

出力（このスクリプトと同じフォルダの layerdump\\ 配下）:
    raw_*.txt      jwc_temp.txt の内容
    layers_*.csv   256行の一覧
    matrix_*.csv   16x16 の一覧表（人が見る用）
    layers_*.json  差分を取る用
    commands_*.csv 行頭コマンドの出現数
"""
import os
import re
import sys
import csv
import json
import datetime
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "layerdump")
ENC = "cp932"  # jwc_temp.txt は Shift_JIS

TEMP_PATH = None  # 実際に読んだ jwc_temp.txt のパス（返信も必ずここへ書く）

# --- 行の解釈（lgn/lyn を先に判定すること）---------------------------------
RE_LGN = re.compile(r"^lgn(.*)$", re.I)
RE_LYN = re.compile(r"^lyn(.*)$", re.I)
RE_LG = re.compile(r"^lg([0-9a-fA-F])\s*(\S*)")
RE_LY = re.compile(r"^ly([0-9a-fA-F])\s*(\S*)")

HEX = "0123456789abcdef"

# JWW_SMPL.BAT の定義:
#   11: 編集可能、表示状態 / 01: 編集不可、表示状態 / 00: 編集不可、非表示状態
#   10の位が 2以上はプロテクト
ONES = {0: "非表示", 1: "表示"}
TENS = {
    0: "編集不可",
    1: "編集可能",
    2: "編集不可・プロテクト(状態変更可)",
    3: "編集可能・プロテクト(状態変更可)",
    6: "編集不可・プロテクト(状態変更不可)",
    7: "編集可能・プロテクト(状態変更不可)",
}
# Jw_cad の画面上の呼び名（書込レイヤはヘッダ側で別に示される）
SHORT = {"11": "編集可能", "01": "表示のみ", "00": "非表示"}


def find_temp():
    for p in (os.path.join(os.getcwd(), "jwc_temp.txt"),
              os.path.join(HERE, "jwc_temp.txt"),
              r"C:\jww\jwc_temp.txt"):
        if os.path.isfile(p):
            return p
    return None


def reply(msg):
    """he = メッセージ表示のみで作図しない。読んだのと同じパスへ書き戻す。"""
    p = TEMP_PATH or os.path.join(os.getcwd(), "jwc_temp.txt")
    try:
        with open(p, "w", encoding=ENC, errors="replace", newline="\r\n") as f:
            f.write("he " + msg + "\n")
    except Exception as e:
        print("reply write failed:", e)


def decode(v):
    """状態値（文字列のまま保持）を (表示, 編集) のラベルに分解。"""
    if not v:
        return ("", "")
    try:
        n = int(v)
    except ValueError:
        return ("?", "?")
    return (ONES.get(n % 10, "?(%d)" % (n % 10)),
            TENS.get(n // 10, "?(%d)" % (n // 10)))


def parse(text):
    rows = []
    gstates = {}
    gnames = {}
    lnames = {}
    cur = None
    write_group = None
    write_layer = None

    for lineno, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s:
            continue

        m = RE_LGN.match(s)
        if m:
            if cur is not None:
                gnames[cur] = m.group(1).strip()
            continue

        m = RE_LYN.match(s)
        if m:
            if rows:
                lnames[(rows[-1]["group"], rows[-1]["layer"])] = m.group(1).strip()
            continue

        m = RE_LG.match(s)
        if m:
            g, v = m.group(1).lower(), m.group(2)
            if v == "":
                # 値なし = 書込レイヤグループの宣言（ヘッダ部）
                if write_group is None:
                    write_group = g
            else:
                cur = g
                gstates[g] = v
            continue

        m = RE_LY.match(s)
        if m:
            ly, v = m.group(1).lower(), m.group(2)
            if v == "":
                if write_layer is None:
                    write_layer = ly
                continue
            disp, edit = decode(v)
            rows.append({"line": lineno, "group": cur or "", "layer": ly,
                         "value": v, "disp": disp, "edit": edit, "src": s})
            continue

    return rows, gstates, gnames, lnames, write_group, write_layer


def head_token(s):
    for pat, name in ((RE_LGN, "lgn"), (RE_LYN, "lyn"), (RE_LG, "lg"), (RE_LY, "ly")):
        if pat.match(s):
            return name
    m = re.match(r"^([A-Za-z_#]+)", s)
    return m.group(1) if m else (s[:2] if s else "")


def main():
    global TEMP_PATH
    os.makedirs(OUTDIR, exist_ok=True)
    label = sys.argv[1] if len(sys.argv) > 1 else "X"
    stamp = "%s_%s" % (label, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))

    temp = find_temp()
    TEMP_PATH = temp
    if temp is None:
        print("jwc_temp.txt not found. cwd=", os.getcwd())
        reply("jwc_temp.txt が見つかりませんでした")
        return 1

    print("source:", temp)
    text = open(temp, "rb").read().decode(ENC, errors="replace")
    rows, gstates, gnames, lnames, wg, wl = parse(text)

    # raw（図面全体を選択すると巨大になるので大きい場合はレイヤ行だけ残す）
    raw_path = os.path.join(OUTDIR, "raw_%s.txt" % stamp)
    if len(text) > 2000000:
        keep = [l for l in text.splitlines()
                if any(p.match(l.strip()) for p in (RE_LGN, RE_LYN, RE_LG, RE_LY))
                or l.strip().startswith("h")]
        body = "[NOTE] 元データ %d 文字。ヘッダとレイヤ行のみ保存\n" % len(text) + "\n".join(keep)
    else:
        body = text
    with open(raw_path, "w", encoding="utf-8", newline="") as f:
        f.write(body)

    # 256行の一覧
    with open(os.path.join(OUTDIR, "layers_%s.csv" % stamp), "w",
              encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "layer", "value", "表示", "編集", "書込", "グループ名", "レイヤ名"])
        for r in rows:
            w.writerow([r["group"], r["layer"], r["value"], r["disp"], r["edit"],
                        "○" if (r["group"] == wg and r["layer"] == wl) else "",
                        gnames.get(r["group"], ""), lnames.get((r["group"], r["layer"]), "")])

    # 16x16 の一覧表（人が見る用）
    cell = {(r["group"], r["layer"]): r["value"] for r in rows}
    with open(os.path.join(OUTDIR, "matrix_%s.csv" % stamp), "w",
              encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["グループ\\レイヤ"] + list(HEX))
        for g in HEX:
            line = [g]
            for l in HEX:
                v = cell.get((g, l), "")
                s = SHORT.get(v, v)
                if g == wg and l == wl:
                    s = "書込(%s)" % s
                line.append(s)
            w.writerow(line)

    # コマンド出現数
    hist = collections.Counter(head_token(l.strip()) for l in text.splitlines() if l.strip())
    with open(os.path.join(OUTDIR, "commands_%s.csv" % stamp), "w",
              encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["command", "count"])
        for k, v in hist.most_common():
            w.writerow([k, v])

    # JSON（差分用）
    with open(os.path.join(OUTDIR, "layers_%s.json" % stamp), "w",
              encoding="utf-8", newline="") as f:
        json.dump({"source": temp, "stamp": stamp,
                   "write_group": wg, "write_layer": wl,
                   "group_states": gstates, "group_names": gnames,
                   "layers": rows, "command_histogram": dict(hist)},
                  f, ensure_ascii=False, indent=2)

    ngroup = len(set(r["group"] for r in rows if r["group"]))
    print("lines:", len(text.splitlines()), "groups:", ngroup, "layers:", len(rows),
          "write:", wg, wl)
    reply("[%s] group=%d layer=%d write=lg%s/ly%s" % (label, ngroup, len(rows), wg, wl))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        try:
            reply("layerdump でエラー。layerdump\\log_*.txt を確認してください")
        except Exception:
            pass
        sys.exit(1)
