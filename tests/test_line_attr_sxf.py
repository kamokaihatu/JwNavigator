"""👑 2026-09-24: 外部から受け取った図面が「SXF対応拡張線色・線種」に
なっていると、補助線モードボタンでjw_cadが操作不能になった件の再発防止。

実機(tools/dump_line_attr_dialog.py)で確定した事実:
  既定モード: コントロール44個、線色1401〜1409、線種2449〜2457、キャンセルあり
  SXFモード : コントロール75個、線色2268〜2283、線種2449〜2464、キャンセル無し

不具合は2つあった。
 (1) SXFモードにはキャンセルが無いため、読み取りだけのつもりで開いた
     ダイアログが閉じられず、モーダルのまま残った(これが「とまっちゃった」)。
 (2) apply_attr()が、指定のコントロールが1つも見つからなくてもOKを押して
     Trueを返していた。さらに線種はIDが重なるため、既定の「補助線種=2457」
     を押すつもりでSXFの「9番=点線」を押してしまう経路があった。
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import line_attr_dialog as lad

BM_CLICK = 0x00F5
WM_CLOSE = 0x0010


class CtrlIdFactsTests(unittest.TestCase):
    """IDの並びは実機の観測結果。ここが崩れると判別ロジックの前提が壊れる。"""

    def test_sxf_has_sixteen_colors_but_fifteen_types(self):
        """👑 2026-09-24 実測。色16/線種15で**数が違う**。2464は存在せず、
        2465は「ユーザー定義線種(UDLT)」なので線種一覧に入れてはいけない
        (入れると、UDLTが選ばれている時に線種として誤って拾う)。"""
        self.assertEqual(len(lad.SXF_COLOR_CTRL_IDS), 16)
        self.assertEqual(len(lad.SXF_TYPE_CTRL_IDS), 15)
        self.assertNotIn(2464, lad.SXF_TYPE_CTRL_IDS)
        self.assertNotIn(2465, lad.SXF_TYPE_CTRL_IDS, "UDLTを線種として扱っている")

    def test_line_type_ids_collide_so_ids_cannot_identify_the_mode(self):
        """👑 **この事実がバグの根っこ**。既定の線種IDはSXFの線種IDに
        丸ごと含まれるので、「1401が無ければSXF」のようなID有無による
        判別をしてはいけない。必ずチェックボックスの状態で判別する。"""
        self.assertTrue(set(lad.TYPE_CTRL_IDS) <= set(lad.SXF_TYPE_CTRL_IDS))
        self.assertIn(2457, lad.TYPE_CTRL_IDS, "既定の補助線種")
        self.assertIn(2457, lad.SXF_TYPE_CTRL_IDS, "SXFの9番(点線)")

    def test_line_color_ids_do_not_overlap(self):
        """線色は重ならない。だから線色だけはNoneで気づけた(線種は気づけない)。"""
        self.assertFalse(set(lad.COLOR_CTRL_IDS) & set(lad.SXF_COLOR_CTRL_IDS))


class _FakeJwDialog:
    """実機の線属性ダイアログの再現。

    👑 **一番大事な再現点**: SXFのチェックを押すと、jw_cadは中身を
    入れ替えるのではなく**ダイアログを丸ごと作り直す**(hwndが変わり、
    古いhwndは無効になる)。2026-09-24の1回目の修正はここを読み違えて
    いて、古いhwndを列挙して「コントロール0個」になり、新しく開いた
    ダイアログを閉じられずに残していた。
    """

    SXF_HWND = 4854510
    PLAIN_HWND = 7770001

    def __init__(self, sxf=True, rebuild_on_toggle=True):
        self.sxf = sxf
        self.rebuild_on_toggle = rebuild_on_toggle
        self.clicked = []
        self.posted = []
        self.dead = set()

    @property
    def hwnd(self):
        return self.SXF_HWND if self.sxf else self.PLAIN_HWND

    def ctrl_map_for(self, hwnd):
        """無効になったhwndを列挙すると空になる(実機と同じ)。"""
        if hwnd in self.dead or hwnd != self.hwnd:
            return {}
        m = {lad.OK_CTRL_ID: hwnd * 10 + 1, lad.WIDTH_EDIT_ID: hwnd * 10 + 2}
        if self.sxf:
            m[lad.SXF_CHECKBOX_ID] = hwnd * 10 + 3
            for cid in lad.SXF_COLOR_CTRL_IDS + lad.SXF_TYPE_CTRL_IDS:
                m[cid] = hwnd * 100 + cid
        else:
            # 既定モードにもチェックボックスは在る(外れた状態で表示される)
            m[lad.SXF_CHECKBOX_ID] = hwnd * 10 + 3
            m[lad.CANCEL_CTRL_ID] = hwnd * 10 + 4
            for cid in lad.COLOR_CTRL_IDS + lad.TYPE_CTRL_IDS:
                m[cid] = hwnd * 100 + cid
        return m

    def click(self, ctrl_hwnd):
        self.clicked.append(ctrl_hwnd)
        if ctrl_hwnd == self.hwnd * 10 + 3:  # SXFチェックボックス
            if self.rebuild_on_toggle:
                self.dead.add(self.hwnd)
            self.sxf = not self.sxf


class _FakeWin32Gui:
    def __init__(self, dialog):
        self.d = dialog

    def SendMessage(self, hwnd, msg, wparam, lparam):
        if msg == lad.BM_GETCHECK:
            return 1 if self.d.sxf else 0
        if msg == lad.BM_GETSTATE:
            return 0
        if msg == lad.BM_CLICK:
            self.d.click(hwnd)
        return 0

    def PostMessage(self, hwnd, msg, wparam, lparam):
        if hwnd in self.d.dead:
            raise Exception((1400, "PostMessage", "ウィンドウ ハンドルが無効です。"))
        self.d.posted.append((hwnd, msg))
        return 0

    def GetWindowText(self, hwnd):
        return ""

    def SetWindowPos(self, *a, **k):
        return 0


class _Patched:
    def __init__(self, dialog):
        self.d = dialog
        self.fake = _FakeWin32Gui(dialog)

    def __enter__(self):
        self._saved = (
            lad._open_dialog, lad._build_ctrl_map, lad._find_dialog_hwnd, lad.win32gui,
        )
        lad._open_dialog = lambda hwnd: self.d.hwnd
        lad._build_ctrl_map = lambda dlg: self.d.ctrl_map_for(dlg)
        lad._find_dialog_hwnd = lambda timeout=0.6: self.d.hwnd
        lad.win32gui = self.fake
        return self.d

    def __exit__(self, *exc):
        (lad._open_dialog, lad._build_ctrl_map,
         lad._find_dialog_hwnd, lad.win32gui) = self._saved
        return False


class ApplyAttrTests(unittest.TestCase):
    def test_switches_out_of_sxf_and_applies_the_default_ids(self):
        """👑 意図した動作の本筋。SXF図面でも、モードを落としてから
        既定モードのID(補助線色1409/補助線種2457)を押してOKまで行く。"""
        d = _FakeJwDialog(sxf=True)
        with _Patched(d):
            ok = lad.apply_attr(1, color_ctrl_id=1409, type_ctrl_id=2457, sxf=False)
        self.assertTrue(ok)
        self.assertFalse(d.sxf, "SXFが外れていない")
        plain = d.PLAIN_HWND
        self.assertIn(plain * 100 + 1409, d.clicked, "補助線色を押していない")
        self.assertIn(plain * 100 + 2457, d.clicked, "補助線種を押していない")
        self.assertIn(plain * 10 + 1, d.clicked, "OKを押していない")

    def test_uses_the_new_dialog_handle_after_the_toggle(self):
        """👑 **2026-09-24の1回目の修正が踏んだ落とし穴**。チェックを押すと
        ダイアログが作り直されるので、古いhwndを使い続けてはいけない。"""
        d = _FakeJwDialog(sxf=True)
        with _Patched(d):
            lad.apply_attr(1, color_ctrl_id=1409, sxf=False)
        self.assertIn(d.SXF_HWND, d.dead, "古いダイアログが無効になっていない")
        stale = [h for h in d.clicked if h // 100 == d.SXF_HWND and h != d.SXF_HWND * 10 + 3]
        self.assertFalse(stale, f"無効になった古いhwndのコントロールを押している: {stale}")

    def test_returns_false_when_the_requested_color_is_absent(self):
        """👑 SXFのまま既定IDを押そうとしたら、何もせずFalse。以前は
        素通りしてOKを押し、何も変えていないのにTrueを返していた。"""
        d = _FakeJwDialog(sxf=True)
        with _Patched(d):
            ok = lad.apply_attr(1, color_ctrl_id=1409, type_ctrl_id=2457, sxf=None)
        self.assertFalse(ok, "変更できていないのに成功を返した")
        self.assertNotIn(d.SXF_HWND * 10 + 1, d.clicked, "失敗時にOKを押している")

    def test_aborts_instead_of_pressing_a_colliding_id(self):
        """👑 SXFを外せない環境では**何も押さずに**中止する。押すと
        既定の補助線種(2457)のつもりでSXFの9番(点線)に変えてしまう。"""
        d = _FakeJwDialog(sxf=True, rebuild_on_toggle=True)
        d.click = lambda ctrl_hwnd: d.clicked.append(ctrl_hwnd)  # 押しても変わらない環境
        with _Patched(d):
            ok = lad.apply_attr(1, color_ctrl_id=1409, type_ctrl_id=2457, sxf=False)
        self.assertFalse(ok)
        self.assertNotIn(d.SXF_HWND * 100 + 2457, d.clicked, "重なっているIDを押した")

    def test_failure_still_closes_the_dialog(self):
        """👑 失敗して抜けるときもダイアログを閉じること。閉じ忘れると
        モーダルのまま残り、jw_cadが操作不能になる(報告された症状)。"""
        d = _FakeJwDialog(sxf=True)
        with _Patched(d):
            lad.apply_attr(1, color_ctrl_id=1409, sxf=None)
        closed = [h for h, msg in d.posted if msg == WM_CLOSE]
        self.assertTrue(closed, "ダイアログを閉じていない")


class ReadCurrentAttrTests(unittest.TestCase):
    def test_reports_the_sxf_state_along_with_the_ids(self):
        """👑 ctrl_idは"sxf"とセットでしか意味を持たない。復元時に
        モードを合わせられるよう、必ず一緒に返すこと。"""
        d = _FakeJwDialog(sxf=True)
        with _Patched(d):
            got = lad.read_current_attr(1)
        self.assertTrue(got["sxf"])
        self.assertTrue(d.sxf, "読み取りだけなのにモードを変えている")

    def test_closes_even_without_a_cancel_button(self):
        """👑 SXFモードにはキャンセルが無い。WM_CLOSEで閉じること。"""
        d = _FakeJwDialog(sxf=True)
        self.assertNotIn(lad.CANCEL_CTRL_ID, d.ctrl_map_for(d.hwnd))
        with _Patched(d):
            lad.read_current_attr(1)
        self.assertIn((d.SXF_HWND, WM_CLOSE), d.posted, "WM_CLOSEで閉じていない")


class ReadSxfModeTests(unittest.TestCase):
    def test_absent_checkbox_is_none_not_false(self):
        """👑 None(SXFの概念が無い)とFalse(OFF)を混同しないこと。"""
        d = _FakeJwDialog(sxf=True)
        with _Patched(d):
            self.assertIsNone(lad.read_sxf_mode({}))

    def test_reads_checked_state(self):
        d = _FakeJwDialog(sxf=True)
        with _Patched(d):
            self.assertTrue(lad.read_sxf_mode({lad.SXF_CHECKBOX_ID: 1}))
            d.sxf = False
            self.assertFalse(lad.read_sxf_mode({lad.SXF_CHECKBOX_ID: 1}))


if __name__ == "__main__":
    unittest.main()
