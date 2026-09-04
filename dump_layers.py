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



def to_jwl(v):
    """#gn の状態値 -> レイヤ設定ファイル(.JWL)の値。

    #gn 側: 1の位 1=表示/0=非表示、10の位 0=編集不可,1=編集可能,
            2,3=プロテクト(変更可),6,7=プロテクト(変更不可)
    JWL 側: 1の位 0=非表示,1=表示のみ,2=編集可能
            10の位 0=通常,1=プロテクト(変更可),2=プロテクト(変更不可)
    """
    try:
        n = int(v)
    except (TypeError, ValueError):
        return 2
    ones, tens = n % 10, n // 10
    if ones == 0:
        state = 0                      # 非表示
    elif tens in (1, 3, 7):
        state = 2                      # 編集可能
    else:
        state = 1                      # 表示のみ
    prot = 1 if tens in (2, 3) else (2 if tens in (6, 7) else 0)
    return prot * 10 + state


def write_jwl(path, rows, gstates, wg, wl, stamp):
    """現在のレイヤ状態を復元できる .JWL を書き出す。

    復元手順: Jw_cad の [設定]→[環境設定ファイル]→[読込み] で
              ファイルの種類を *.JWL にして、このファイルを選ぶ。
    """
    cell = {(r["group"], r["layer"]): r["value"] for r in rows}
    lines = [
        "# Jw_cad レイヤ設定ファイル (自動生成 %s)" % stamp,
        "# [設定]→[環境設定ファイル]→[読込み] で *.JWL を選んで読み込むと",
        "# 全レイヤグループ・全レイヤの状態がこの内容に戻ります。",
        "#",
        "PRTCT_CH =  1",
    ]
    for g in HEX:
        vals = []
        # 先頭はレイヤグループ自身の状態
        vals.append(100 if g == wg else to_jwl(gstates.get(g, "11")))
        for l in HEX:
            if g == wg and l == wl:
                vals.append(100)
            else:
                vals.append(to_jwl(cell.get((g, l), "11")))
        lines.append("LAYCND_%s =%s" % (g.upper(), ",".join("%3d" % v for v in vals)))
    with open(path, "w", encoding=ENC, errors="replace", newline="\r\n") as f:
        f.write("\n".join(lines) + "\n")


def write_outputs(stamp, text, rows, gstates, gnames, lnames, wg, wl, make_jwl=True):
    """解析結果をファイル一式に書き出す。戻り値は (グループ数, レイヤ数, JWLを書いたか)。"""
    os.makedirs(OUTDIR, exist_ok=True)
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
        json.dump({"source": TEMP_PATH, "stamp": stamp,
                   "write_group": wg, "write_layer": wl,
                   "group_states": gstates, "group_names": gnames,
                   "layers": rows, "command_histogram": dict(hist)},
                  f, ensure_ascii=False, indent=2)

    ngroup = len(set(r["group"] for r in rows if r["group"]))

    # 復元用の .JWL
    # 【重要】256レイヤ揃っていないと、取れなかったグループを既定値で埋めてしまい、
    #        復元時にそれらのレイヤ状態を破壊する。揃ったときだけ書く。
    jwl_ok = make_jwl and (ngroup == 16 and len(rows) == 256)
    if jwl_ok:
        write_jwl(os.path.join(OUTDIR, "restore_%s.jwl" % stamp),
                  rows, gstates, wg, wl, stamp)
        jwl_fixed = os.path.join(os.path.dirname(TEMP_PATH), "LAYER_RESTORE.JWL")
        try:
            write_jwl(jwl_fixed, rows, gstates, wg, wl, stamp)
            print("jwl:", jwl_fixed)
        except Exception as e:
            print("jwl(fixed) failed:", e)
    else:
        print("jwl: SKIP (group=%d layer=%d 不完全なため復元ファイルは作らない)"
              % (ngroup, len(rows)))

    print("lines:", len(text.splitlines()), "groups:", ngroup, "layers:", len(rows),
          "write:", wg, wl)
    return ngroup, len(rows), jwl_ok


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

    ngroup, nlayer, jwl_ok = write_outputs(stamp, text, rows, gstates, gnames, lnames, wg, wl)

    reply("[%s] group=%d layer=%d write=lg%s/ly%s  %s"
          % (label, ngroup, nlayer, wg, wl,
             "JWL保存OK" if jwl_ok else "JWL未作成(256レイヤ揃わず)"))
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
