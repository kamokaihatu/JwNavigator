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

    def test_sxf_ids_have_sixteen_entries_each(self):
        self.assertEqual(len(lad.SXF_COLOR_CTRL_IDS), 16)
        self.assertEqual(len(lad.SXF_TYPE_CTRL_IDS), 16)

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


class _FakeWin32Gui:
    """必要なメッセージだけを記録する差し替え。"""

    def __init__(self, checked=1):
        self.sent = []
        self.posted = []
        self._checked = checked

    def SendMessage(self, hwnd, msg, wparam, lparam):
        self.sent.append((hwnd, msg))
        if msg == lad.BM_GETCHECK:
            return self._checked
        if msg == lad.BM_GETSTATE:
            return 0
        return 0

    def PostMessage(self, hwnd, msg, wparam, lparam):
        self.posted.append((hwnd, msg))
        return 0

    def GetWindowText(self, hwnd):
        return ""


class _Patched:
    """_open_dialog/_build_ctrl_map/win32guiを差し替えるコンテキスト。"""

    def __init__(self, ctrl_map, checked=1):
        self.ctrl_map = ctrl_map
        self.fake = _FakeWin32Gui(checked=checked)

    def __enter__(self):
        self._saved = (lad._open_dialog, lad._build_ctrl_map, lad.win32gui)
        lad._open_dialog = lambda hwnd: 4854510
        lad._build_ctrl_map = lambda dlg: dict(self.ctrl_map)
        lad.win32gui = self.fake
        return self.fake

    def __exit__(self, *exc):
        lad._open_dialog, lad._build_ctrl_map, lad.win32gui = self._saved
        return False


def _sxf_dialog_ctrl_map():
    """SXFモードのダイアログ(キャンセル無し、線色は2268〜、線種は2449〜)。"""
    m = {lad.SXF_CHECKBOX_ID: 2312_000, lad.OK_CTRL_ID: 1_000, lad.WIDTH_EDIT_ID: 2224_000}
    for cid in lad.SXF_COLOR_CTRL_IDS + lad.SXF_TYPE_CTRL_IDS:
        m[cid] = cid * 1000
    return m


class ApplyAttrTests(unittest.TestCase):
    def test_returns_false_when_the_requested_color_is_absent(self):
        """👑 **不具合(2)そのもの**。既定モードの補助線色(1409)はSXFモードの
        ダイアログに存在しない。以前はここを素通りしてOKを押し、何も変えて
        いないのにTrueを返していた。"""
        ctrl_map = _sxf_dialog_ctrl_map()
        with _Patched(ctrl_map, checked=1) as fake:
            # sxf=Noneでモードを触らせない = 既定IDとSXFダイアログのミスマッチ
            ok = lad.apply_attr(1, color_ctrl_id=1409, type_ctrl_id=2457, sxf=None)
        self.assertFalse(ok, "変更できていないのに成功を返した")
        clicked = [h for h, msg in fake.sent if msg == BM_CLICK]
        self.assertNotIn(ctrl_map[lad.OK_CTRL_ID], clicked, "失敗時にOKを押している")

    def test_failure_still_closes_the_dialog(self):
        """👑 **不具合(1)**。失敗して抜けるときもダイアログを閉じること。
        閉じ忘れるとモーダルのまま残り、jw_cadが操作不能になる。
        SXFモードにはキャンセルが無いのでWM_CLOSEで閉じる。"""
        ctrl_map = _sxf_dialog_ctrl_map()
        self.assertNotIn(lad.CANCEL_CTRL_ID, ctrl_map, "SXFモードにキャンセルは無い")
        with _Patched(ctrl_map, checked=1) as fake:
            lad.apply_attr(1, color_ctrl_id=1409, sxf=None)
        self.assertIn((4854510, WM_CLOSE), fake.posted, "ダイアログを閉じていない")

    def test_aborts_instead_of_pressing_a_colliding_id(self):
        """👑 SXFを外せなかった場合は、線種IDが重なっているため**何も押さずに**
        中止する。押すと黙って別の線種(SXFの9番=点線)に変わってしまう。"""
        ctrl_map = _sxf_dialog_ctrl_map()
        with _Patched(ctrl_map, checked=1) as fake:
            # checked=1固定なので、チェックを押してもOFFにならない環境を模擬
            ok = lad.apply_attr(1, color_ctrl_id=1409, type_ctrl_id=2457, sxf=False)
        self.assertFalse(ok)
        clicked = [h for h, msg in fake.sent if msg == BM_CLICK]
        self.assertNotIn(ctrl_map[2457], clicked, "重なっているIDを押してしまった")


class ReadSxfModeTests(unittest.TestCase):
    def test_absent_checkbox_is_none_not_false(self):
        """👑 None(SXFの概念が無い)とFalse(OFF)を混同しないこと。混同すると
        「OFFにした」つもりで何もしていない状態を成功と誤認する。"""
        with _Patched({}, checked=0):
            self.assertIsNone(lad.read_sxf_mode({}))

    def test_reads_checked_state(self):
        with _Patched({}, checked=1):
            self.assertTrue(lad.read_sxf_mode({lad.SXF_CHECKBOX_ID: 1}))
        with _Patched({}, checked=0):
            self.assertFalse(lad.read_sxf_mode({lad.SXF_CHECKBOX_ID: 1}))


if __name__ == "__main__":
    unittest.main()
