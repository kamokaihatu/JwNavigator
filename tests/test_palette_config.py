"""👑 2026-09-16: 「パレットを1枚にできない」不具合の再発防止テスト。

`normalize_config()` が組み込みの"左"/"右"を**常に作り直していた**ため、
設定画面で削除しても次の読み込みで必ず復活していた(kamo報告:
「パレット1枚でいいときにパレット1と2は削除できない」)。

ここは設定ファイルの入り口で、**壊れた入力でも必ず妥当な形を返す**ことが
前提になっている箇所でもあるので、異常系もあわせて固定しておく。
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import palette_config


def _side_with_button():
    return {
        "orientation": "portrait",
        "button_size": 40,
        "groups": [{"buttons": [{"command_id": "C001", "name": "線"}]}],
    }


class NormalizeConfigTests(unittest.TestCase):
    def test_deleted_builtin_palette_stays_deleted(self):
        """👑 **この不具合そのもの**。"左"/"右"を消した設定を正規化しても
        復活しない。以前は無条件に作り直していた。"""
        config = {"sides": {"palette_3": _side_with_button()}}
        result = palette_config.normalize_config(config)
        self.assertEqual(list(result["sides"].keys()), ["palette_3"])

    def test_builtin_palettes_survive_being_emptied(self):
        """ただし「中身を全部消しただけ」では消えない。作り直しの途中で
        パレットごと消えると事故になるため、組み込みは空でも残す。"""
        config = {"sides": {"左": {"groups": []}, "右": _side_with_button()}}
        result = palette_config.normalize_config(config)
        self.assertIn("左", result["sides"])

    def test_extra_palette_with_no_buttons_is_dropped(self):
        """組み込み以外は、ボタンが0個になったら保存のたびに消える
        (専用UIなしで「パレット削除」を実現していた従来の仕組み)。"""
        config = {"sides": {"左": _side_with_button(), "palette_9": {"groups": []}}}
        result = palette_config.normalize_config(config)
        self.assertNotIn("palette_9", result["sides"])

    def test_never_returns_zero_palettes(self):
        """1枚も無いと操作する術が無くなるので、その時だけ既定を作る。"""
        result = palette_config.normalize_config({"sides": {}})
        self.assertEqual(len(result["sides"]), 1)

    def test_survives_broken_input(self):
        """👑 設定ファイルが壊れていてもクラッシュせず、妥当な形を返す
        (readmeで「壊れていたら黙って空へフォールバックする」と約束している)。"""
        for broken in ({}, {"sides": None}, {"sides": {"左": None}}, {"sides": []}):
            with self.subTest(broken=broken):
                result = palette_config.normalize_config(broken)
                self.assertIsInstance(result.get("sides"), dict)
                self.assertGreaterEqual(len(result["sides"]), 1)

    def test_all_side_keys_preserves_insertion_order(self):
        """パレットの並び順は挿入順。main.py側が「先頭のパレット」を
        使う箇所があるため、順序が崩れると表示位置が変わる。"""
        config = palette_config.normalize_config(
            {"sides": {"左": _side_with_button(), "右": _side_with_button(),
                       "palette_3": _side_with_button()}}
        )
        self.assertEqual(
            palette_config.all_side_keys(config), ["左", "右", "palette_3"]
        )


if __name__ == "__main__":
    unittest.main()
