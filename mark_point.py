# -*- coding: utf-8 -*-
"""
Jw_cad 外部変形: 書込レイヤに点(MARK_X, MARK_Y)を1個作図する。

「全選択」の代わりに小さい範囲選択(0,0)~(2,2)で256レイヤを取りたい
(doc/HANDOFF_layer_control.md 14章参照)ための目印用。書込レイヤは
定義上必ず編集可能なので、この点は確実に選択できる。

必要なバッチ制御行(B_MARK.bat):
    REM #jww
    REM #h0     データ選択不要(この用途では選択自体を行わない)
    REM #e

図形データの読込み書式(JWW_SMPL.BAT 421-422行目「点データ」)は
「pt %lg %lg」。書込みデータ(書出し方向)と同じ書式が読込み(返信)方向でも
使える、と仕様書に明記されている(578-579行目)。

さらに、返信に「h/********.BAT」(仕様書527-530行目)を含めると、この
外部変形の終了後に別の外部変形へ自動的に移行できる。これを使い、点を
作図した直後にA_SAVE.BATへ自動で連鎖させる(ユーザー操作は1回のホット
キーで済む)。B_MARK自体は選択不要(#h0)なので必ず起動する。

👑 2026-09-08: この連鎖を使うと、1回の操作で点作図→A_SAVE一式がまるごと
2周してしまう不具合が実機で確認されている(原因未特定。連鎖を使わず
Ctrl+Jを直接A_SAVEに割り付けた場合は1回しか実行されないことを確認済み
なので、連鎖の仕組み自体が原因と判定)。代替として「B_MARK/A_SAVEを
別々のホットキーに分けてJwNavigator側で順番に送る」方式も試したが、
2つ目のホットキー(Ctrl+K)がGCOM_1XXの想定通りには割り付かず(jw_cadの
キー割り付けの優先順位が仕様書の記述と食い違う可能性がある、要調査)、
断念した。**2周する不具合は許容し、連鎖ありの現状の方式を採用する**
（doc/HANDOFF_layer_control.md 21章参照）。
"""
import os
import time

ENC = "cp932"  # jwc_temp.txt は Shift_JIS
CHAIN_TO = "A_SAVE.BAT"

# 👑 2026-09-09: (1,1)だと図面によっては表示範囲の中央付近に来てしまい
# 目立つ(kamo報告「1,1ってど真ん中なんだ」)ため、一度(100000,100000)
# まで離してみたが、**保存のたびに外部変形が「再選択」の状態になり、
# ファイル選択ダイアログで手動操作が必要になる不具合が発生した**
# (kamo実機確認、原因はおそらく遠い座標へのパン/再描画が固定待ち時間に
# 間に合わないこと)。信頼性を優先し(1,1)に戻す。utils/layer_snapshot.py
# の範囲選択もこの値に合わせて動かす必要がある。
MARK_X = 1
MARK_Y = 1

_T0 = time.perf_counter()
_LAP = _T0


def lap(name):
    """区間の所要時間をログに出す(dump_layers.pyのlap()と同じ形式)。"""
    global _LAP
    now = time.perf_counter()
    print("[time] %-12s %6.3f s  (累計 %6.3f s)" % (name, now - _LAP, now - _T0))
    _LAP = now


def find_temp():
    here = os.path.dirname(os.path.abspath(__file__))
    for p in (os.path.join(os.getcwd(), "jwc_temp.txt"),
              os.path.join(here, "jwc_temp.txt"),
              r"C:\jww\jwc_temp.txt"):
        if os.path.isfile(p):
            return p
    return None


def main():
    temp = find_temp()
    lap("起動と探索")
    if temp is None:
        print("jwc_temp.txt not found. cwd=", os.getcwd())
        return 1
    print("target:", temp)
    with open(temp, "w", encoding=ENC, errors="replace", newline="\r\n") as f:
        f.write("pt %g %g\n" % (MARK_X, MARK_Y))
        f.write("h/%s\n" % CHAIN_TO)
    lap("返信書込み")
    print("[MARK] pt %g %g を書込レイヤへ返信し、%s へ連鎖しました" % (MARK_X, MARK_Y, CHAIN_TO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
