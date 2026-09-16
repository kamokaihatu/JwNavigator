"""👑 2026-09-16: kosakaPCで「レイヤ保存が一度も動かない」を丸1日かけて
追った件の再発防止テスト。

このファイルの各テストは、**実際に起きた不具合をそのまま再現したもの**。
jw_cadを起動しなくても検証できる部分(プロファイルの解析と書き換え)だけを
対象にしている。

最重要は test_profile_without_gcom_line_is_reported。真因は
「GCOM_1XXの行が無いプロファイルを、無言でスキップしていた」こと。
例外も出ず、ログにも何も残らなかったため、原因特定に丸1日かかった。
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import external_transform_setup as ets

TARGET_DIR = r"C:\test\external_transform"
# jw_cadが実際に使っているCtrl+英字(メニューのアクセラレータから実測した値)
RESERVED = set("ACFNOPSVXYZ")


def _profile(gcom100="", gcom110="", extra_lines=()):
    """GCOM行の中身を指定して、最小限のプロファイルを一時ファイルに作る。
    gcom100/gcom110 に None を渡すとその行自体を書かない(=行が無い環境)。"""
    lines = ["KEY_A =    5     1 "]
    if gcom100 is not None:
        lines.append(f"GCOM_100 ={gcom100}")
    if gcom110 is not None:
        lines.append(f"GCOM_110 ={gcom110}")
    lines.extend(extra_lines)
    fd, path = tempfile.mkstemp(suffix=".jwf")
    os.close(fd)
    with open(path, "wb") as f:
        f.write("\r\n".join(lines).encode("cp932"))
    return path


def _gcom_lines(path):
    with open(path, "rb") as f:
        raw = f.read().decode("cp932", errors="replace")
    return {
        line.split("=")[0].strip(): line.split("=", 1)[1]
        for line in raw.splitlines()
        if line.startswith("GCOM_1")
    }


class RegisterInProfileTests(unittest.TestCase):
    def setUp(self):
        self.logs = []
        self.paths = []

    def tearDown(self):
        for p in self.paths:
            for candidate in (p, p + ".bak_jwnavigator"):
                if os.path.exists(candidate):
                    os.remove(candidate)

    def _run(self, **kwargs):
        path = _profile(**kwargs)
        self.paths.append(path)
        result = ets._register_in_profile(
            path, TARGET_DIR, log=self.logs.append, reserved_letters=RESERVED
        )
        return path, result

    def test_empty_slots_use_the_default_keys(self):
        """空のプロファイルなら、従来どおり Ctrl+J / Ctrl+K に入る。"""
        path, result = self._run(gcom100="," * 10, gcom110="," * 10)
        self.assertEqual(result["keys"]["B_MARK"], "J")
        self.assertEqual(result["keys"]["A_SAVE"], "K")
        self.assertTrue(result["new_registration"])
        lines = _gcom_lines(path)
        self.assertIn("B_MARK", lines["GCOM_100"])
        self.assertIn("A_SAVE", lines["GCOM_110"])
        self.assertIn(TARGET_DIR, lines["GCOM_110"])

    def test_profile_without_gcom_line_is_reported(self):
        """👑 **kosakaPCの真因そのもの**。GCOM行が無いプロファイルを、
        黙って「正常な空データ」として素通りさせない。

        当時は例外もログも出ず、呼び出し元は成功と区別できなかった。
        ここでは(1)キーが決まらないこと(2)理由がログに残ることを固定する。"""
        path, result = self._run(gcom100=None, gcom110=None)
        self.assertIsNone(result["keys"]["B_MARK"])
        self.assertIsNone(result["keys"]["A_SAVE"])
        self.assertFalse(result["new_registration"])
        self.assertTrue(
            any("GCOM_100の行がありません" in m for m in self.logs),
            f"行が無いことがログに残っていない: {self.logs}",
        )

    def test_existing_registration_of_another_tool_is_never_overwritten(self):
        """他人が使っている割り当ては絶対に書き換えない。"""
        path, result = self._run(
            gcom100=",,,,,,,,,MYTOOL," + TARGET_DIR, gcom110="OTHER" + "," * 10
        )
        lines = _gcom_lines(path)
        self.assertIn("MYTOOL", lines["GCOM_100"])
        self.assertIn("OTHER", lines["GCOM_110"])

    def test_falls_back_to_a_free_key_avoiding_jw_cad_shortcuts(self):
        """既定のJ/Kが埋まっていたら空きへ回る。その際、jw_cadが使っている
        キー(Ctrl+A/C等)は奪わない。"""
        _, result = self._run(
            gcom100=",,,,,,,,,MYTOOL," + TARGET_DIR, gcom110="OTHER" + "," * 10
        )
        for name in ("B_MARK", "A_SAVE"):
            letter = result["keys"][name]
            self.assertIsNotNone(letter, f"{name}が登録されなかった")
            self.assertNotIn(letter, RESERVED, f"{name}がjw_cadの使用中キーを奪った")
            self.assertNotIn(letter, ("J", "K"), f"{name}が埋まっているキーを使った")

    def test_no_free_key_reports_conflict_instead_of_stealing_one(self):
        """空きが無ければ、予約キーを奪わずconflictとして知らせる。"""
        busy = ",".join(["X"] * 10) + ","
        _, result = self._run(gcom100=busy, gcom110=busy)
        self.assertIsNone(result["keys"]["A_SAVE"])
        self.assertTrue(result["conflicts"], "空きが無いのにconflictが報告されない")

    def test_registration_only_touches_gcom_lines(self):
        """書き換えるのはGCOM行だけ。他の行(KEY_A等)は1バイトも変えない。"""
        path, _ = self._run(gcom100="," * 10, gcom110="," * 10)
        with open(path, "rb") as f:
            after = f.read().decode("cp932")
        self.assertIn("KEY_A =    5     1 ", after)


class HasJwWinJwfTests(unittest.TestCase):
    """👑 GCOMはJw_win.jwfからしか読まれない(実機の対照実験で確定)。
    このファイルの有無の判定を間違えると、kosakaPCの状況を検知できない。"""

    def test_detects_presence_and_absence(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(ets.has_jw_win_jwf(d))
            open(os.path.join(d, "Jw_win.jwf"), "w").close()
            self.assertTrue(ets.has_jw_win_jwf(d))

    def test_missing_directory_is_false_not_an_error(self):
        self.assertFalse(ets.has_jw_win_jwf(r"C:\no\such\folder"))
        self.assertFalse(ets.has_jw_win_jwf(""))


class FallbackKeyOrderTests(unittest.TestCase):
    def test_covers_every_available_letter_exactly_once(self):
        """候補順はGCOM_100(A〜J)とGCOM_110(K〜T)の20文字を過不足なく含む。
        重複や抜けがあると、空きがあるのに登録できない環境が生まれる。"""
        order = ets._FALLBACK_LETTER_ORDER
        self.assertEqual(sorted(order), [chr(ord("A") + i) for i in range(20)])

    def test_prefers_the_right_side_of_the_keyboard(self):
        """kamoの指示「BDEは後回しに。キーボードの右のほうから使いましょう」。
        左手の狭い範囲(B/D/E)より、右寄りのL/K/I/Mが先に来ること。"""
        order = ets._FALLBACK_LETTER_ORDER
        for right, left in (("L", "B"), ("K", "D"), ("I", "E")):
            self.assertLess(
                order.index(right), order.index(left),
                f"{right}より{left}が先に来ている",
            )


if __name__ == "__main__":
    unittest.main()
