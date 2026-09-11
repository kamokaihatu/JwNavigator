# ===== ✂️ widgets/first_launch_dialog.py START ✂️ =====
"""
初回起動時（config/config.jsonがまだ存在しない時）に出す、パレットの
初期構成を選ばせるダイアログ。選んだプリセットのJSONをそのまま
config/config.jsonとしてコピーする。

👑 ×で閉じた場合や、万が一プリセットのコピーに失敗した場合も、
アプリの起動自体は止めない（空の状態から普通に使い始められる）。
"""
import json
import os
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from utils import palette_config

PRESETS = [
    ("empty", "空から始める", "ボタン0個。設定画面で自分の好きな構成を一から組み立てます。"),
    ("minimal", "ミニマムセット", "線・矩形・円弧・文字・寸法・範囲・複写・移動・伸縮・消去の10個だけ。"),
    ("developer", "誰かのおすすめ", "ある人が実務で使っている構成をそのまま。"),
    ("full", "フルセット", "現時点で使える全74コマンドを詰め込みます。後で不要な分を削ってください。"),
]


def _presets_dir():
    # 👑 exe化すると__file__は仮想パス（実ファイルなし）になるため
    # 使えない（list_icon_modules()で踏んだのと同じ問題、2026-08-31）。
    # 凍結時はsys._MEIPASS配下（JwNavigator.specでdatasとしてバンドル
    # する想定）、開発時はリポジトリルート基準で解決する。
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", "")
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "data", "starter_presets")


class FirstLaunchDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("JwNavigatorへようこそ")
        self.geometry("440x480")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")
        self.attributes("-topmost", True)
        # 👑 このダイアログはroot.withdraw()直後、mainloop開始前に出す
        # ため、transient(master)にすると（masterがまだ一度も画面に
        # 出ていない=withdrawn状態のため）ウィンドウ自体が表示されない
        # ことを実測で確認した。ここではtransientにせず独立ウィンドウ
        # として出す（-topmostだけで最前面表示は確保できる）。
        self.chosen = None

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

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=16, pady=(10, 6))

        row = tk.Frame(self, bg="#ffffff", highlightthickness=1, highlightbackground="#cccccc")
        row.pack(fill="x", padx=16, pady=4)
        btn = tk.Button(
            row, text="📂 すでに設定済み", font=("Meiryo UI", 10, "bold"), width=18, anchor="w",
            command=self._browse_existing, bg="#5a5a5a", fg="white", relief="raised",
        )
        btn.pack(side="left", padx=8, pady=8)
        tk.Label(
            row, text="以前使っていたconfig.jsonを選ぶと、その設定をそのまま使い始めます。",
            font=("Meiryo UI", 8), justify="left", wraplength=230,
            bg="#ffffff", anchor="w",
        ).pack(side="left", padx=(0, 8), pady=8, fill="x", expand=True)

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.grab_set()

    def _choose(self, key):
        self.chosen = key
        self.destroy()

    def _browse_existing(self):
        # 👑 exeの移動/再インストールのたびに%APPDATA%移行(app_paths.py)や
        # exe隣接の旧config探索だけでは拾えない旧設定(別フォルダに置いた
        # 旧バージョンのconfig.json等)を、ユーザー自身に探してもらう救済策
        # (2026-09-11、kamo自身が「0から設定する羽目に」なった実体験から)。
        initial_dir = "C:\\jww" if os.path.isdir("C:\\jww") else os.path.expanduser("~")
        path = filedialog.askopenfilename(
            parent=self, title="以前のconfig.jsonを選択してください",
            initialdir=initial_dir,
            filetypes=[("config.json", "config.json"), ("JSONファイル", "*.json"), ("すべてのファイル", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            messagebox.showerror(
                "読み込み失敗",
                "このファイルは読み込めませんでした。\nJwNavigatorのconfig.jsonを選んでください。",
                parent=self,
            )
            return
        self.chosen = ("import", raw)
        self.destroy()


def _apply_choice(chosen, target_path):
    """chosenは文字列(プリセットキー)か、("import", 生JSON辞書)のタプル。
    実際にtarget_pathへ書き込めたらTrue。"""
    try:
        target_dir = os.path.dirname(target_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
        if isinstance(chosen, tuple) and chosen[0] == "import":
            # 👑 ブラウズで選ばれたファイルは他人の壊れたconfigかもしれない
            # ので、そのままコピーせずnormalize_config()を通してから書く
            # (normalize_config()はどんな形の入力でも必ず妥当な形を返す)。
            normalized = palette_config.normalize_config(chosen[1])
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(normalized, f, ensure_ascii=False, indent=2)
            return True
        preset_path = os.path.join(_presets_dir(), f"{chosen}.json")
        if not os.path.exists(preset_path):
            return False
        shutil.copy(preset_path, target_path)
        return True
    except Exception:
        return False


def run_first_launch_setup_if_needed(root):
    # 👑 config/config.jsonが存在しない=初回起動とみなす。既に存在する
    # 場合（アップデートや再インストール等）は絶対に上書きしない。
    target_path = palette_config.config_path()
    if os.path.exists(target_path):
        return

    dlg = FirstLaunchDialog(root)
    root.wait_window(dlg)
    # 👑 ×で閉じた(何も選ばなかった)場合は「空から始める」を選んだのと
    # 同じ扱いにする(初回起動は必ず何らかのconfig.jsonを作りたいため)。
    chosen = dlg.chosen or "empty"
    _apply_choice(chosen, target_path)


def run_preset_reset(root):
    """設定画面/トレイメニューから明示的に呼ぶ「初期構成を選び直す」。
    初回起動時と違って既存のconfig.jsonを上書きする破壊的操作なので、
    ダイアログを×で閉じた(何も選ばなかった)場合は何もしない
    (run_first_launch_setup_if_needed()のように「空」へ勝手に倒さない)。
    呼び出し元(main.py)が確認ダイアログを出す前提。
    戻り値: 実際にconfig.jsonを上書きしたらTrue、しなかったらFalse。"""
    dlg = FirstLaunchDialog(root)
    root.wait_window(dlg)
    if dlg.chosen is None:
        return False
    target_path = palette_config.config_path()
    return _apply_choice(dlg.chosen, target_path)
# ===== ✂️ widgets/first_launch_dialog.py END ✂️ =====
