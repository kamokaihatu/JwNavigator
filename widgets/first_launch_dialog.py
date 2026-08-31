# ===== ✂️ widgets/first_launch_dialog.py START ✂️ =====
"""
初回起動時（config/config.jsonがまだ存在しない時）に出す、パレットの
初期構成を選ばせるダイアログ。選んだプリセットのJSONをそのまま
config/config.jsonとしてコピーする。

👑 ×で閉じた場合や、万が一プリセットのコピーに失敗した場合も、
アプリの起動自体は止めない（空の状態から普通に使い始められる）。
"""
import os
import shutil
import tkinter as tk
from tkinter import ttk

from utils import palette_config

PRESETS = [
    ("empty", "空から始める", "ボタン0個。設定画面で自分の好きな構成を一から組み立てます。"),
    ("minimal", "ミニマムおすすめセット", "線・矩形・円弧・文字・寸法・範囲・複写・移動・伸縮・消去の10個だけ。"),
    ("jw_default", "jw初期セット", "jw_cad本体の標準ツールバーに近い構成（メインコマンド39個）。"),
    ("developer", "開発者おすすめセット", "開発者が実務で使っている構成をそのまま。"),
    ("full", "フルセット", "現時点で使える全74コマンドを詰め込みます。後で不要な分を削ってください。"),
]


def _presets_dir():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "data", "starter_presets")


class FirstLaunchDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("JwNavigatorへようこそ")
        self.geometry("440x420")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")
        self.attributes("-topmost", True)
        # 👑 このダイアログはroot.withdraw()直後、mainloop開始前に出す
        # ため、transient(master)にすると（masterがまだ一度も画面に
        # 出ていない=withdrawn状態のため）ウィンドウ自体が表示されない
        # ことを実測で確認した。ここではtransientにせず独立ウィンドウ
        # として出す（-topmostだけで最前面表示は確保できる）。
        self.chosen = "empty"

        tk.Label(
            self, text="はじめまして。パレットの初期構成を選んでください。\n"
                       "(あとから設定画面でいつでも変更できます)",
            font=("Meiryo UI", 10), justify="center", bg="#f0f0f0",
        ).pack(pady=(14, 10), padx=16)

        for key, label, desc in PRESETS:
            row = tk.Frame(self, bg="#ffffff", highlightthickness=1, highlightbackground="#cccccc")
            row.pack(fill="x", padx=16, pady=4)
            btn = tk.Button(
                row, text=label, font=("Meiryo UI", 10, "bold"), width=18, anchor="w",
                command=lambda k=key: self._choose(k), bg="#2b4c7e", fg="white", relief="raised",
            )
            btn.pack(side="left", padx=8, pady=8)
            tk.Label(
                row, text=desc, font=("Meiryo UI", 8), justify="left", wraplength=230,
                bg="#ffffff", anchor="w",
            ).pack(side="left", padx=(0, 8), pady=8, fill="x", expand=True)

        self.protocol("WM_DELETE_WINDOW", lambda: self._choose("empty"))
        self.grab_set()

    def _choose(self, key):
        self.chosen = key
        self.destroy()


def run_first_launch_setup_if_needed(root):
    # 👑 config/config.jsonが存在しない=初回起動とみなす。既に存在する
    # 場合（アップデートや再インストール等）は絶対に上書きしない。
    target_path = palette_config.config_path()
    if os.path.exists(target_path):
        return

    dlg = FirstLaunchDialog(root)
    root.wait_window(dlg)

    preset_path = os.path.join(_presets_dir(), f"{dlg.chosen}.json")
    if not os.path.exists(preset_path):
        return
    try:
        target_dir = os.path.dirname(target_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
        shutil.copy(preset_path, target_path)
    except Exception:
        pass
# ===== ✂️ widgets/first_launch_dialog.py END ✂️ =====
