# ===== ✂️ widgets/settings_window.py START ✂️ =====
import colorsys
import importlib
import os
import re
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

from utils import palette_config, command_master, menu_prefs, line_attr_dialog
from widgets.button import ScaledCanvas

ICON_NONE_LABEL = "アイコンなし"
_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _is_valid_hex_color(value):
    return bool(_HEX_COLOR_RE.match(value or ""))


def _get_jw_hwnd(manager_ref):
    # 👑 「見本で選ぶ…」(LineAttrSwatchDialog)用。線属性ダイアログは
    # jw_cad全体で共通の設定なので、複数ウィンドウが開いていてもどれか
    # 1つのhwndで足りる。
    if not manager_ref:
        return None
    try:
        hwnds = list(manager_ref.active_launchers.keys())
    except Exception:
        return None
    return hwnds[0] if hwnds else None


def draw_icon_thumbnail(canvas, icon_name, image_refs, size=40):
    # 👑 IconPickerDialogのサムネイル一覧とSidePanelのプレビューの両方から
    # 使う共通描画ロジック。widgets/button.pyのNavButton.load_and_draw()と
    # 同じ優先順位（png_icons/優先、無ければ.pyモジュール描画）で描く。
    # image_refsはPhotoImageの参照保持用リスト（呼び出し側が保持し続ける
    # こと。参照が切れるとTkinterが自動でガベージコレクトして表示が消える）。
    if not icon_name:
        canvas.create_text(size / 2, size / 2, text="✕", fill="#aaaaaa", font=("Meiryo UI", 12))
        return
    png_path = palette_config.png_icon_path(icon_name)
    try:
        if os.path.exists(png_path):
            img = tk.PhotoImage(file=png_path)
            image_refs.append(img)
            canvas.create_image(size / 2, size / 2, image=img)
            return
    except Exception:
        pass
    try:
        module = importlib.import_module(f"icons.{icon_name}")
        scaled = ScaledCanvas(canvas, 1.5 * size / 44.0)
        if hasattr(module, "draw"):
            module.draw(scaled, x=4, y=4)
        elif hasattr(module, "draw_icon"):
            module.draw_icon(scaled, x=4, y=4)
    except Exception:
        canvas.create_text(size / 2, size / 2, text="?", fill="#cc0000")


def _hex_to_rgb(value):
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def _rgb_to_hex(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"


class ColorPickerDialog(tk.Toplevel):
    """自前の色選択ダイアログ。tkinter標準のcolorchooser.askcolor()は
    Windows高DPI環境でダイアログのサイズが崩れ、OK/キャンセルボタンが
    ほとんど見えなくなる既知の不具合があり（実測で確認）、アプリ側からの
    確実な修正が困難なため、プリセットスウォッチ+HSVグラデーション
    ピッカー+カスタム16進入力の自前ウィンドウに置き換えた。選択結果は
    self.resultに#RRGGBBで残る（キャンセル時はNone）。PILは使わず、
    tk.PhotoImage.put()の行単位一括書き込みでグラデーションを生成する
    （依存追加を避けるため）。"""

    PRESETS = [
        "#ffffff", "#f0f0f0", "#d9d9d9", "#bfbfbf", "#808080", "#4d4d4d", "#262626", "#000000",
        "#ffb3b3", "#ffd9b3", "#fff2b3", "#c2f0c2", "#b3d9ff", "#d1b3ff", "#ffb3e6", "#b3fff0",
        "#ff4d4d", "#ff9933", "#ffe14d", "#4dbb4d", "#4d94ff", "#a366ff", "#ff4dc4", "#33e6c2",
    ]

    SV_W, SV_H = 160, 120
    HUE_W, HUE_H = 160, 18

    def __init__(self, master, initial_color=None):
        super().__init__(master)
        self.result = None
        self.title("色を選ぶ")
        self.configure(bg="#f0f0f0")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.transient(master)

        self._syncing = False
        start_color = initial_color if _is_valid_hex_color(initial_color) else palette_config.DEFAULT_COLOR
        r, g, b = _hex_to_rgb(start_color)
        self.hue, self.sat, self.val = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        self.hex_var = tk.StringVar(value=start_color)

        # ---- プリセット ----
        grid = tk.Frame(self, bg="#f0f0f0")
        grid.pack(padx=10, pady=(10, 4))
        cols = 8
        for i, color in enumerate(self.PRESETS):
            r_, c_ = divmod(i, cols)
            sw = tk.Label(grid, bg=color, width=3, height=1, relief="raised", bd=2, cursor="hand2")
            sw.grid(row=r_, column=c_, padx=2, pady=2)
            sw.bind("<Button-1>", lambda e, col=color: self._set_from_hex(col))

        # ---- HSVグラデーションピッカー ----
        hsv_frame = tk.Frame(self, bg="#f0f0f0")
        hsv_frame.pack(padx=10, pady=(4, 4))

        self.sv_image = tk.PhotoImage(width=self.SV_W, height=self.SV_H)
        self.sv_canvas = tk.Canvas(hsv_frame, width=self.SV_W, height=self.SV_H,
                                    highlightthickness=1, highlightbackground="#999999", cursor="crosshair")
        self.sv_canvas.pack(side="top")
        self.sv_canvas.create_image(0, 0, anchor="nw", image=self.sv_image, tags="bg")
        self.sv_cursor = self.sv_canvas.create_oval(0, 0, 8, 8, outline="#ffffff", width=2)
        self.sv_canvas.bind("<Button-1>", self._on_sv_click)
        self.sv_canvas.bind("<B1-Motion>", self._on_sv_click)

        self.hue_image = tk.PhotoImage(width=self.HUE_W, height=self.HUE_H)
        self._draw_hue_bar()
        self.hue_canvas = tk.Canvas(hsv_frame, width=self.HUE_W, height=self.HUE_H,
                                     highlightthickness=1, highlightbackground="#999999", cursor="sb_h_double_arrow")
        self.hue_canvas.pack(side="top", pady=(4, 0))
        self.hue_canvas.create_image(0, 0, anchor="nw", image=self.hue_image, tags="bg")
        self.hue_cursor = self.hue_canvas.create_line(0, 0, 0, self.HUE_H, fill="#ffffff", width=2)
        self.hue_canvas.bind("<Button-1>", self._on_hue_click)
        self.hue_canvas.bind("<B1-Motion>", self._on_hue_click)

        # ---- カスタム16進入力 + プレビュー ----
        custom = ttk.Frame(self)
        custom.pack(fill="x", padx=10, pady=(6, 8))
        ttk.Label(custom, text="カスタム(#RRGGBB):").pack(side="left")
        entry = ttk.Entry(custom, textvariable=self.hex_var, width=10)
        entry.pack(side="left", padx=6)
        self.preview = tk.Label(custom, width=3, relief="solid", bd=1)
        self.preview.pack(side="left", padx=4)
        self.hex_var.trace_add("write", self._on_hex_typed)

        footer = ttk.Frame(self)
        footer.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(footer, text="OK", command=self._on_ok, width=10).pack(side="right")
        ttk.Button(footer, text="キャンセル", command=self._on_cancel, width=10).pack(side="right", padx=(0, 6))

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self._draw_sv_square()
        self._update_cursors()
        self._sync_preview()
        entry.focus_set()
        self.grab_set()

    # ---- グラデーション描画 ----

    def _draw_hue_bar(self):
        row = []
        for x in range(self.HUE_W):
            r, g, b = colorsys.hsv_to_rgb(x / (self.HUE_W - 1), 1.0, 1.0)
            row.append(_rgb_to_hex(int(r * 255), int(g * 255), int(b * 255)))
        self.hue_image.put([row] * self.HUE_H)

    def _draw_sv_square(self):
        # 現在の色相(hue)固定で、X=彩度・Y=明度のグラデーションを生成する
        rows = []
        for y in range(self.SV_H):
            value = 1.0 - (y / (self.SV_H - 1))
            row = []
            for x in range(self.SV_W):
                sat = x / (self.SV_W - 1)
                r, g, b = colorsys.hsv_to_rgb(self.hue, sat, value)
                row.append(_rgb_to_hex(int(r * 255), int(g * 255), int(b * 255)))
            rows.append(row)
        self.sv_image.put(rows)

    def _update_cursors(self):
        x = self.sat * (self.SV_W - 1)
        y = (1.0 - self.val) * (self.SV_H - 1)
        self.sv_canvas.coords(self.sv_cursor, x - 4, y - 4, x + 4, y + 4)
        hx = self.hue * (self.HUE_W - 1)
        self.hue_canvas.coords(self.hue_cursor, hx, 0, hx, self.HUE_H)

    # ---- 入力ハンドラ ----

    def _on_sv_click(self, event):
        x = min(max(event.x, 0), self.SV_W - 1)
        y = min(max(event.y, 0), self.SV_H - 1)
        self.sat = x / (self.SV_W - 1)
        self.val = 1.0 - (y / (self.SV_H - 1))
        self._update_cursors()
        self._sync_from_hsv()

    def _on_hue_click(self, event):
        x = min(max(event.x, 0), self.HUE_W - 1)
        self.hue = x / (self.HUE_W - 1)
        self._draw_sv_square()
        self._update_cursors()
        self._sync_from_hsv()

    def _sync_from_hsv(self):
        self._syncing = True
        try:
            r, g, b = colorsys.hsv_to_rgb(self.hue, self.sat, self.val)
            hex_color = _rgb_to_hex(int(r * 255), int(g * 255), int(b * 255))
            self.hex_var.set(hex_color)
            self.preview.configure(bg=hex_color)
        finally:
            self._syncing = False

    def _sync_preview(self):
        self.preview.configure(bg=self.hex_var.get())

    def _set_from_hex(self, hex_color):
        # プリセットクリック時: HSVピッカー側の状態(色相バー・SV正方形の
        # カーソル位置)も合わせて更新する。
        self.hex_var.set(hex_color)

    def _on_hex_typed(self, *args):
        if self._syncing:
            return
        val = self.hex_var.get()
        if not _is_valid_hex_color(val):
            return
        self.preview.configure(bg=val)
        r, g, b = _hex_to_rgb(val)
        self.hue, self.sat, self.val = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        self._draw_sv_square()
        self._update_cursors()

    def _on_ok(self):
        val = self.hex_var.get()
        if not _is_valid_hex_color(val):
            messagebox.showwarning("入力エラー", "#RRGGBB形式で入力してください。", parent=self)
            return
        self.result = val
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()


class IconPickerDialog(tk.Toplevel):
    """アイコン選択ダイアログ。サムネイル一覧から選ぶ。プルダウンの
    テキスト一覧だと、png_icons/が増えてくると選びにくいという指摘を
    受けて、実際の見た目をグリッド表示するダイアログに置き換えた。
    選択結果はself.resultにアイコン名（NO_ICON=""含む）で残る
    （キャンセル時はNone、"アイコンなし"を選んだ場合はNOT None）。"""

    THUMB_SIZE = 40
    COLS = 6

    def __init__(self, master, current_icon=None):
        super().__init__(master)
        self.result = None
        self._selected = current_icon or palette_config.NO_ICON
        self._image_refs = []
        self.title("アイコンを選ぶ")
        self.geometry("420x520")
        self.configure(bg="#f0f0f0")
        self.attributes("-topmost", True)
        self.transient(master)

        search_bar = ttk.Frame(self)
        search_bar.pack(side="top", fill="x", padx=8, pady=6)
        ttk.Label(search_bar, text="検索:").pack(side="left")
        self.query_var = tk.StringVar()
        entry = ttk.Entry(search_bar, textvariable=self.query_var, width=20)
        entry.pack(side="left", padx=4, fill="x", expand=True)
        self.query_var.trace_add("write", lambda *a: self._rebuild_grid())

        # 👑 サンプルパック（png_icons/にsample_*で大量投入したアイコン群）を
        # 検索欄に文字を打たなくてもワンクリックで絞り込めるようにする
        # ショートカットボタン。「ざっくり入れると選ぶの難しい」という
        # 指摘を受けて追加。プレフィックスはサンプル投入時の命名規則
        # （sample_cmd_/emoji_/stylish_/cute_/cool_）に合わせてある。
        category_bar = ttk.Frame(self)
        category_bar.pack(side="top", fill="x", padx=8, pady=(0, 4))
        categories = [
            ("全部", ""),
            ("コマンド風", "sample_cmd_"),
            ("派手", "sample_emoji_"),
            ("落ち着いた", "sample_stylish_"),
            ("かわいい", "sample_cute_"),
            ("かっこいい", "sample_cool_"),
        ]
        for label, prefix in categories:
            ttk.Button(
                category_bar, text=label, width=8,
                command=lambda p=prefix: self.query_var.set(p),
            ).pack(side="left", padx=(0, 3))

        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True, padx=8)
        canvas = tk.Canvas(container, bg="#f0f0f0", highlightthickness=0)
        vscroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")
        self.grid_frame = tk.Frame(canvas, bg="#f0f0f0")
        grid_window = canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.grid_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(grid_window, width=e.width))
        self._mousewheel_bind_id = canvas.bind_all(
            "<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units")
        )
        self._mousewheel_canvas = canvas

        footer = ttk.Frame(self)
        footer.pack(side="top", fill="x", padx=8, pady=8)
        ttk.Button(footer, text="OK", command=self._on_ok, width=10).pack(side="right")
        ttk.Button(footer, text="キャンセル", command=self._on_cancel, width=10).pack(side="right", padx=(0, 6))

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self._cell_widgets = []
        self._rebuild_grid()
        entry.focus_set()
        self.grab_set()

    def _rebuild_grid(self):
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self._cell_widgets = []
        self._image_refs = []

        query = self.query_var.get().strip().lower()
        names = [n for n in palette_config.list_all_icon_names() if query in n.lower()]
        entries = [(palette_config.NO_ICON, ICON_NONE_LABEL)] + [(n, n) for n in names]

        for i, (icon_name, label) in enumerate(entries):
            r, c = divmod(i, self.COLS)
            is_sel = icon_name == self._selected
            cell = tk.Frame(self.grid_frame, bg="#f0f0f0", cursor="hand2",
                             highlightthickness=2, highlightbackground=("#4d94ff" if is_sel else "#f0f0f0"))
            cell.grid(row=r, column=c, padx=3, pady=3)
            thumb = tk.Canvas(cell, width=self.THUMB_SIZE, height=self.THUMB_SIZE,
                               bg="#ffffff", highlightthickness=1, highlightbackground="#cccccc")
            thumb.pack(padx=4, pady=(4, 0))
            self._draw_thumb(thumb, icon_name)
            short = label if len(label) <= 8 else label[:7] + "…"
            lbl = tk.Label(cell, text=short, bg="#f0f0f0", font=("Meiryo UI", 7))
            lbl.pack(pady=(0, 4))
            for w in (cell, thumb, lbl):
                w.bind("<Button-1>", lambda e, n=icon_name: self._select(n))
            self._cell_widgets.append((icon_name, cell))

    def _draw_thumb(self, canvas, icon_name):
        draw_icon_thumbnail(canvas, icon_name, self._image_refs, self.THUMB_SIZE)

    def _select(self, icon_name):
        self._selected = icon_name
        for name, cell in self._cell_widgets:
            cell.configure(highlightbackground=("#4d94ff" if name == icon_name else "#f0f0f0"))

    def _cleanup_mousewheel(self):
        try:
            self._mousewheel_canvas.unbind_all("<MouseWheel>")
        except Exception:
            pass

    def _on_ok(self):
        self.result = self._selected
        self._cleanup_mousewheel()
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self._cleanup_mousewheel()
        self.destroy()


class TextInputDialog(tk.Toplevel):
    """1行だけの名前入力用ダイアログ。tkinter標準のsimpledialog.askstring()は
    使わず、ColorPickerDialog/IconPickerDialogと同じ自前スタイルに揃える
    （このマシンの高DPI環境で標準ダイアログが崩れる既知の問題を避ける方針
    を踏襲）。結果はself.result(文字列、キャンセル時はNone)に残る。"""

    def __init__(self, master, title, label, initial="", note=None):
        super().__init__(master)
        self.result = None
        self.title(title)
        self.configure(bg="#f0f0f0")
        self.resizable(False, False)
        # 👑 タイトルバーがラベル文字列より狭いと表示が切れる
        # (ユーザー報告)。本文側の最小幅を確保してタイトルも収まりやすく
        # する(内容に応じてTkが自動で広げる分にはこの値を下回らない)。
        self.minsize(260, 1)
        self.attributes("-topmost", True)
        # 👑 masterが非表示(withdraw済み、常駐トレイアプリのroot等)だと、
        # transient()で結び付けた瞬間にこのダイアログも「非表示の親を
        # 持つtransientウィンドウ」としてTkに扱われ、後段のdeiconify()が
        # 「it is a transient window whose master is not deiconified」で
        # 例外になり、ダイアログごと固まって二度と表示されない不具合が
        # 実機で発生した(main.py: レイヤ保存ボタンの名前入力、2026-09-04)。
        # 親が実際に見えている時だけtransient化する。
        try:
            if master.winfo_viewable():
                self.transient(master)
        except Exception:
            pass

        self.name_var = tk.StringVar(value=initial)

        body = ttk.Frame(self)
        body.pack(padx=12, pady=12)
        ttk.Label(body, text=label).pack(side="left", padx=(0, 6))
        entry = ttk.Entry(body, textvariable=self.name_var, width=24)
        entry.pack(side="left")
        entry.bind("<Return>", lambda e: self._on_ok())

        if note:
            ttk.Label(self, text=note).pack(padx=12, pady=(0, 8), fill="x")

        footer = ttk.Frame(self)
        footer.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Button(footer, text="OK", command=self._on_ok, width=10).pack(side="right")
        ttk.Button(footer, text="キャンセル", command=self._on_cancel, width=10).pack(side="right", padx=(0, 6))

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        # 👑 masterが非表示(withdraw済み)のウィンドウだと、transient()の
        # 影響でこのダイアログ自体も非表示のまま生成され、grab_set()が
        # 「window not viewable」で失敗して以降のコードごと固まる不具合が
        # 実機で発生した(main.py側からself.root=トレイ用の隠しrootを
        # 親にして呼んだ時に発覚、2026-09-04)。表示状態を確定させてから
        # grab_set()する。
        self.deiconify()
        self.lift()
        self.update_idletasks()
        entry.focus_set()
        entry.select_range(0, tk.END)
        self.grab_set()

    def _on_ok(self):
        val = self.name_var.get().strip()
        if not val:
            messagebox.showwarning("入力エラー", "名前を入力してください。", parent=self)
            return
        self.result = val
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()


class LineAttrSwatchDialog(tk.Toplevel):
    """線色・線種を、jw_cad本体の線属性ダイアログと同じ見本(実際の色・
    実際の線種パターン)から選ぶダイアログ。従来はラベル名(「線色3」等)
    だけのコンボボックスだったが、「線種決めるのに、jwのシステムは
    使えないよねー」という指摘を受けて、線属性ダイアログを開いて
    (変更せず)GetPixelで実際の色・線種パターンを読み取り、それを見本
    として再現する(doc/シート管理_設計メモ.md参照)。
    選択結果はself.result_color/self.result_typeにctrl_idで残る
    (キャンセル時はNone)。"""

    SWATCH_W, SWATCH_H = 60, 28

    def __init__(self, master, hwnd, current_color=None, current_type=None, swatch_cache=None):
        super().__init__(master)
        self.result_color = None
        self.result_type = None
        self._selected_color = current_color
        self._selected_type = current_type
        self._color_cells = {}
        self._type_cells = {}
        self._color_swatches = {}
        self._type_canvases = {}
        self._hwnd = hwnd
        # 👑 まとめ合意の確定仕様:
        # 1) 開いたら読み込みはせず、色・線種グリッドの完成形レイアウトを
        #    そのまま出す(まだ未読み込みなのでマス目は空白)。
        # 2) 「📥 線色・線種の読み込み」を押した時だけjw_cad本体の線属性
        #    ダイアログを呼びに行き、実際の色・線種を読み取る。
        # 3) 直近の読み込み結果はセッション内キャッシュ(swatch_cache、
        #    SettingsWindow→SidePanel/GroupContentsDialog経由の共有dict)
        #    に残し、次に開いた時はそこから即表示する(自動でjw_cadには
        #    触れない、あくまで前回ユーザーが自分で読み込んだ結果の再利用)。
        #    色に違和感があれば改めて読み込みボタンを押せばよい。
        self._cache = swatch_cache if swatch_cache is not None else {"data": None}
        cached = self._cache.get("data")
        self._swatches = cached
        self._attempted = cached is not None

        self.title("線色・線種を見本から選ぶ")
        self.configure(bg="#f0f0f0")
        self.transient(master)
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self._body = None
        self._build_body()
        self._center_on_screen()

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.grab_set()

    def _center_on_screen(self):
        # 👑 「すべてが左上になってるから」「画面の真ん中でやって」への
        # 対応。既定だとToplevelが画面左上に出るため、毎回(内容によって
        # サイズが変わるstateごとに)実サイズを測ってから中央寄せし直す。
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.geometry(f"+{x}+{y}")

    def _load_and_build(self):
        # 👑 【重大】自分自身をtopmostにしたままjw_cad本体の線属性ダイアログ
        # を開くと、本物のダイアログが自分の裏に隠れてしまい、GetPixelで
        # 自分自身の白い背景を読み取ってしまう(実機で発覚: 全部白/実線に
        # なる不具合)。以前はwithdraw()で自分を完全に消していたが、
        # 「ボタン押したら画面きえちゃうの？残しておけない？」への対応で、
        # 消す(withdraw)のではなくtopmostを一旦外すだけにする。本物の
        # jw_cadダイアログ側は_open_dialog内で明示的にHWND_TOPMOSTへ
        # 上げているので、こちらがtopmostを譲れば自然に向こうが前面に来て
        # 正しく読み取れる。自分の窓自体は画面に残ったまま(裏に一瞬回る
        # だけ)。
        self.attributes("-topmost", False)
        t0 = time.time()
        # 👑 「読めたもの1個ずつ更新していけたら臨場感あるけどできそう？」
        # への対応。1項目読めるごとにon_color/on_typeコールバックで既存の
        # (今は空白の)マスをその場で塗り替えていく。既に画面には blank な
        # グリッドが出来上がっているので、全部読み終わった後で改めて
        # _build_body()し直す必要はない(成功時)。
        swatches = line_attr_dialog.capture_swatches(
            self._hwnd, on_color=self._update_color_swatch, on_type=self._update_type_swatch,
        )
        elapsed = time.time() - t0
        print(f"[LineAttrSwatchDialog] 読み取り: 成功={swatches is not None} 所要={elapsed:.2f}秒")
        self.attributes("-topmost", True)
        self._swatches = swatches
        self._attempted = True
        if swatches is not None:
            self._cache["data"] = swatches
        else:
            self._build_body()
            self._center_on_screen()

    def _build_body(self):
        if self._body is not None:
            self._body.destroy()
        self._color_cells = {}
        self._type_cells = {}
        self._color_swatches = {}
        self._type_canvases = {}
        body = ttk.Frame(self)
        body.pack(side="top", fill="both", expand=True)
        self._body = body
        swatches = self._swatches

        if self._attempted and swatches is None:
            ttk.Label(
                body, text="jw_cadから線属性を読み取れませんでした。\nウィンドウが開いているか確認してください。",
                justify="center", padding=16,
            ).pack()
        else:
            # 👑 未読み込み(swatches is None かつ self._attempted も False)の
            # 場合は、色・パターンをNoneのまま渡して空白マスとして描画する
            # (キャッシュ済み/読み込み済みなら実データをそのまま使う)。
            color_items = swatches["colors"] if swatches else [(cid, None) for cid in line_attr_dialog.COLOR_CTRL_IDS]
            type_items = swatches["types"] if swatches else [(cid, None) for cid in line_attr_dialog.TYPE_CTRL_IDS]

            ttk.Label(body, text="線色", font=("Meiryo UI", 9, "bold")).pack(side="top", anchor="w", padx=10, pady=(10, 2))
            color_frame = ttk.Frame(body)
            color_frame.pack(side="top", padx=10)
            for i, (cid, hex_color) in enumerate(color_items):
                label = line_attr_dialog.COLOR_LABELS[i]
                cell = self._build_color_cell(color_frame, cid, hex_color, label)
                cell.grid(row=0, column=i, padx=2, pady=2)

            ttk.Label(body, text="線種", font=("Meiryo UI", 9, "bold")).pack(side="top", anchor="w", padx=10, pady=(10, 2))
            type_frame = ttk.Frame(body)
            type_frame.pack(side="top", padx=10)
            for i, (cid, pattern) in enumerate(type_items):
                label = line_attr_dialog.TYPE_LABELS[i]
                cell = self._build_type_cell(type_frame, cid, pattern, label)
                cell.grid(row=i // 3, column=i % 3, padx=3, pady=3)

        # 👑 「線色・線種の更新じゃなくて読み込みにして。OKの上に少し
        # 大きめボタンで作ろう」への対応。初回読み込み・基本設定変更後の
        # 再読み込みを兼ねる、同じボタン一つだけ(常にOKのすぐ上に置く)。
        load_row = ttk.Frame(body)
        load_row.pack(side="top", fill="x", padx=10, pady=(6, 0))
        ttk.Button(
            load_row, text="📥 線色・線種の読み込み", command=self._load_and_build,
        ).pack(fill="x", ipady=6)
        ttk.Label(
            body, text="(10秒程度かかります。線属性ウィンドウが開きますが、触らないでください。)",
            font=("Meiryo UI", 8), foreground="#000000",
        ).pack(side="top", pady=(2, 2))

        footer = ttk.Frame(body)
        footer.pack(side="top", fill="x", padx=10, pady=(4, 10))
        ttk.Button(footer, text="OK", command=self._on_ok, width=10).pack(side="right")
        ttk.Button(footer, text="キャンセル", command=self._on_cancel, width=10).pack(side="right", padx=(0, 6))

        self._refresh_selection()

    def _build_color_cell(self, parent, ctrl_id, hex_color, label):
        # 👑 hex_color=None は「まだ読み込んでいない」空白マス(キャッシュ
        # 済み/読み込み済みの実データと区別するため、周囲の背景色と同じ
        # ままにして塗りつぶさない。線色2=白との混同も避けられる)。
        swatch_bg = hex_color if hex_color is not None else "#f0f0f0"
        cell = tk.Frame(parent, bg="#f0f0f0", cursor="hand2", highlightthickness=2, highlightbackground="#f0f0f0")
        swatch = tk.Frame(cell, width=self.SWATCH_W, height=self.SWATCH_H, bg=swatch_bg, relief="solid", bd=1)
        swatch.pack_propagate(False)
        swatch.pack(padx=3, pady=(3, 0))
        tk.Label(cell, text=label, bg="#f0f0f0", font=("Meiryo UI", 7)).pack(pady=(0, 3))
        for w in (cell, swatch):
            w.bind("<Button-1>", lambda e, c=ctrl_id: self._pick_color(c))
        self._color_cells[ctrl_id] = cell
        self._color_swatches[ctrl_id] = swatch
        return cell

    def _build_type_cell(self, parent, ctrl_id, pattern, label):
        cell = tk.Frame(parent, bg="#f0f0f0", cursor="hand2", highlightthickness=2, highlightbackground="#f0f0f0")
        canvas = tk.Canvas(cell, width=self.SWATCH_W + 20, height=16, bg="#ffffff",
                            highlightthickness=1, highlightbackground="#cccccc")
        canvas.pack(padx=3, pady=(3, 0))
        # 👑 pattern=None は「まだ読み込んでいない」空白マス。読み取り済み
        # だが個別に失敗した場合(全Falseパターン)の実線フォールバックとは
        # 区別し、こちらは何も描かず本当に空白のままにする。
        if pattern is not None:
            self._draw_pattern(canvas, pattern)
        tk.Label(cell, text=label, bg="#f0f0f0", font=("Meiryo UI", 7)).pack(pady=(0, 3))
        for w in (cell, canvas):
            w.bind("<Button-1>", lambda e, c=ctrl_id: self._pick_type(c))
        self._type_cells[ctrl_id] = cell
        self._type_canvases[ctrl_id] = canvas
        return cell

    def _update_color_swatch(self, ctrl_id, hex_color):
        # 👑 「読めたもの1個ずつ更新していけたら臨場感あるけど」への対応。
        # capture_swatchesから1項目読めるたびに呼ばれ、そのマスだけ即座に
        # 塗り替える(呼び出し元と同じメインスレッドなので、Tkinter操作は
        # そのまま安全に行える)。
        swatch = self._color_swatches.get(ctrl_id)
        if swatch is not None:
            swatch.configure(bg=hex_color)
            self.update_idletasks()

    def _update_type_swatch(self, ctrl_id, pattern):
        canvas = self._type_canvases.get(ctrl_id)
        if canvas is not None:
            canvas.delete("all")
            self._draw_pattern(canvas, pattern)
            self.update_idletasks()

    def _draw_pattern(self, canvas, pattern):
        w = self.SWATCH_W + 20
        y = 8
        n = len(pattern) or 1
        if not any(pattern):
            # 👑 実機で稀に見本パターンの読み取りに失敗する(補助線種等)。
            # 空白のまま誤解させないよう、素直な実線で代用する。
            canvas.create_line(4, y, w - 4, y, fill="#333333", width=1)
            return
        run_start = None
        for i, drawn in enumerate(pattern):
            x = 4 + (w - 8) * i / n
            if drawn and run_start is None:
                run_start = x
            elif not drawn and run_start is not None:
                canvas.create_line(run_start, y, x, y, fill="#333333", width=2)
                run_start = None
        if run_start is not None:
            canvas.create_line(run_start, y, w - 4, y, fill="#333333", width=2)

    def _pick_color(self, ctrl_id):
        self._selected_color = ctrl_id
        self._refresh_selection()

    def _pick_type(self, ctrl_id):
        self._selected_type = ctrl_id
        self._refresh_selection()

    def _refresh_selection(self):
        for cid, cell in self._color_cells.items():
            cell.configure(highlightbackground=("#4d94ff" if cid == self._selected_color else "#f0f0f0"))
        for cid, cell in self._type_cells.items():
            cell.configure(highlightbackground=("#4d94ff" if cid == self._selected_type else "#f0f0f0"))

    def _on_ok(self):
        self.result_color = self._selected_color
        self.result_type = self._selected_type
        self.destroy()

    def _on_cancel(self):
        self.result_color = None
        self.result_type = None
        self.destroy()


class CommandPickerDialog(tk.Toplevel):
    """コマンド追加ダイアログ。選択されたコマンド一覧をself.resultに残す。
    👑 「箱を作る」「線属性ボタンを作る」を専用の確認ダイアログに分離
    したところ、「コマンドをたくさん追加したいのに毎回別メニューが挟まる
    のが邪魔」という指摘があったため、special_kindsで指定した特殊行を
    このリストの先頭に混ぜて出す方式にした(常時表示、検索/種別/分類の
    絞り込みの影響を受けない)。選ばれた特殊行はself.result_specialsに
    種類("box"/"auto_attr")のリストとして残る(self.resultは今まで通り
    実コマンド行のみ)。"""

    SPECIAL_LABELS = {
        "box": "➕ グループボタン",
        "auto_attr": "➕ モードボタン",
        "layer_snapshot": "➕ レイヤ保存",
    }

    def __init__(self, master, existing_ids=None, special_kinds=()):
        super().__init__(master)
        self.result = []
        self.result_specials = []
        self._existing_ids = existing_ids or set()
        self._all_rows = command_master.list_available_commands()
        self._special_kinds = list(special_kinds)
        self._visible_specials = []
        self.filtered = []

        self.title("コマンドを追加")
        self.geometry("560x520")
        self.configure(bg="#f0f0f0")
        self.attributes("-topmost", True)
        self.transient(master)

        self.query_var = tk.StringVar()

        search_bar = ttk.Frame(self)
        search_bar.pack(side="top", fill="x", padx=8, pady=(6, 2))
        ttk.Label(search_bar, text="検索:").pack(side="left")
        entry = ttk.Entry(search_bar, textvariable=self.query_var, width=30)
        entry.pack(side="left", padx=(4, 0), fill="x", expand=True)
        self.query_var.trace_add("write", self._apply_filter)

        # 👑 プルダウン(単一選択)より、複数の種別/分類を同時にON/OFFできる
        # チェックボックスの方が絞り込みとして使いやすいという要望のため、
        # StringVar1本のComboboxではなく値ごとにBooleanVarを持たせる方式にした。
        kind_bar = ttk.Frame(self)
        kind_bar.pack(side="top", fill="x", padx=8, pady=2)
        ttk.Label(kind_bar, text="種別:").pack(side="left", padx=(0, 4))
        self.kind_vars = {}
        for kind in command_master.list_command_kinds():
            var = tk.BooleanVar(value=True)
            self.kind_vars[kind] = var
            ttk.Checkbutton(kind_bar, text=kind, variable=var, command=self._apply_filter).pack(side="left", padx=4)
        # 👑 「箱を作る」「線属性ボタンを作る」の特殊行も、種別フィルタの
        # 一員としてON/OFFできるようにする(ユーザー要望)。special_kindsを
        # 渡していない呼び出し元(GroupContentsDialog等で使わない場合)は
        # このチェックボックス自体を出さない。
        self.show_specials_var = tk.BooleanVar(value=True)
        if self._special_kinds:
            ttk.Checkbutton(
                kind_bar, text="特殊", variable=self.show_specials_var, command=self._apply_filter,
            ).pack(side="left", padx=4)

        cat_bar = ttk.Frame(self)
        cat_bar.pack(side="top", fill="x", padx=8, pady=(2, 6))
        ttk.Label(cat_bar, text="分類:").pack(side="left", padx=(0, 4))
        self.cat_vars = {}
        for cat in command_master.list_categories():
            var = tk.BooleanVar(value=True)
            self.cat_vars[cat] = var
            ttk.Checkbutton(cat_bar, text=cat, variable=var, command=self._apply_filter).pack(side="left", padx=4)

        list_frame = ttk.Frame(self)
        list_frame.pack(side="top", fill="both", expand=True, padx=8)
        self.listbox = tk.Listbox(list_frame, selectmode="extended", exportselection=0, font=("Meiryo UI", 9))
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.listbox.bind("<Double-Button-1>", self._on_ok)

        footer = ttk.Frame(self)
        footer.pack(side="top", fill="x", padx=8, pady=8)
        ttk.Button(footer, text="追加", command=self._on_ok, width=10).pack(side="right")
        ttk.Button(footer, text="キャンセル", command=self._on_cancel, width=10).pack(side="right", padx=(0, 6))

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self._apply_filter()

        entry.focus_set()
        self.grab_set()

    def _apply_filter(self, *args):
        query = self.query_var.get().strip().lower()
        self.filtered = []
        for row in self._all_rows:
            kind_var = self.kind_vars.get(row["command_kind"])
            if kind_var is not None and not kind_var.get():
                continue
            cat_var = self.cat_vars.get(row["category"])
            if cat_var is not None and not cat_var.get():
                continue
            if query and query not in row["command_id"].lower() and query not in row["toolbar_name"].lower():
                continue
            self.filtered.append(row)

        self._visible_specials = self._special_kinds if self.show_specials_var.get() else []
        self.listbox.delete(0, tk.END)
        for key in self._visible_specials:
            # 👑 下に並ぶ一般コマンド行(◯◯ (種別/分類))と見た目を揃え、
            # 実コマンドと区別しやすいよう「(特殊)」を付ける
            # (ユーザー提案、2026-09-04)。
            self.listbox.insert(tk.END, f"{self.SPECIAL_LABELS[key]} (特殊)")
        for row in self.filtered:
            suffix = " ※配置済" if row["command_id"] in self._existing_ids else ""
            text = f"{row['command_id']}  {row['toolbar_name']}  ({row['command_kind']}/{row['category']}){suffix}"
            self.listbox.insert(tk.END, text)

    def _on_ok(self, event=None):
        indices = self.listbox.curselection()
        n_special = len(self._visible_specials)
        self.result_specials = [self._visible_specials[i] for i in indices if i < n_special]
        self.result = [self.filtered[i - n_special] for i in indices if i >= n_special]
        self.destroy()

    def _on_cancel(self):
        self.result = []
        self.result_specials = []
        self.destroy()


class GroupContentsDialog(tk.Toplevel):
    """フライアウト/マクロの「箱」の中身編集。追加・削除・並べ替えに加え、
    中身1つ1つに個別のアイコン/色を付けられる(ユーザー要望:「中身の
    アイコンはどうやって選ぶの？」)。SidePanel本体の一覧+詳細の仕組みを
    そのまま流用せず、箱の中身専用の小さいダイアログとして独立させて
    ある(sub_buttonsはトップレベルのgroups[].buttonsとは別物で、既存の
    選択/並べ替えロジックがそのままでは使えないため)。
    OKを押すとself.resultに編集後のリストが残る(キャンセル時はNone)。"""

    def __init__(self, master, sub_buttons, manager_ref=None, swatch_cache=None):
        super().__init__(master)
        self.result = None
        self.manager_ref = manager_ref
        self.swatch_cache = swatch_cache if swatch_cache is not None else {"data": None}
        self._buttons = [dict(b) for b in sub_buttons]
        self._loading_detail = False
        self._icon_preview_refs = []

        self.title("中身を編集")
        self.geometry("520x680")
        self.configure(bg="#f0f0f0")
        self.attributes("-topmost", True)
        self.transient(master)

        self.name_var = tk.StringVar()

        body = ttk.Frame(self)
        body.pack(side="top", fill="both", expand=True, padx=8, pady=8)

        list_frame = ttk.Frame(body)
        list_frame.pack(side="left", fill="both", expand=True)
        self.listbox = tk.Listbox(list_frame, selectmode="extended", exportselection=0, font=("Meiryo UI", 9))
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._load_detail())

        ops = ttk.Frame(body)
        ops.pack(side="right", fill="y", padx=(6, 0))
        ttk.Button(ops, text="▲", width=8, command=self._move_up).pack(pady=2)
        ttk.Button(ops, text="▼", width=8, command=self._move_down).pack(pady=2)
        ttk.Separator(ops, orient="horizontal").pack(fill="x", pady=6)
        ttk.Button(ops, text="追加…", width=8, command=self._on_add).pack(pady=2)
        ttk.Button(ops, text="削除", width=8, command=self._on_remove).pack(pady=2)

        # 👑 「ボタン詳細は外の画面(SidePanel)と同じようにして」という
        # 要望のため、アイコン/色の変更をops列の小さいボタンから、
        # SidePanel本体と同じ構成(コマンド/表示名/アイコン/背景色)の
        # 専用欄に置き換えた。
        detail = ttk.LabelFrame(self, text="ボタン詳細")
        detail.pack(side="top", fill="x", padx=8, pady=(0, 4))

        ttk.Label(detail, text="コマンド:").grid(row=0, column=0, sticky="e", padx=6, pady=4)
        self.cmd_var = tk.StringVar()
        ttk.Label(detail, textvariable=self.cmd_var, wraplength=280, justify="left").grid(
            row=0, column=1, sticky="w", padx=6, pady=4
        )

        ttk.Label(detail, text="表示名:").grid(row=1, column=0, sticky="e", padx=6, pady=4)
        self.name_entry = ttk.Entry(detail, textvariable=self.name_var, width=18)
        self.name_entry.grid(row=1, column=1, sticky="w", padx=6, pady=4)
        self.name_var.trace_add("write", self._on_name_changed)

        ttk.Label(detail, text="アイコン:").grid(row=2, column=0, sticky="e", padx=6, pady=4)
        icon_frame = ttk.Frame(detail)
        icon_frame.grid(row=2, column=1, sticky="w", padx=6, pady=4)
        self.icon_preview = tk.Canvas(icon_frame, width=28, height=28, bg="#ffffff",
                                       highlightthickness=1, highlightbackground="#cccccc")
        self.icon_preview.pack(side="left")
        self.icon_name_label = ttk.Label(icon_frame, text="", width=12)
        self.icon_name_label.pack(side="left", padx=(4, 6))
        self.pick_icon_btn = ttk.Button(icon_frame, text="アイコンを選ぶ…", command=self._on_pick_icon)
        self.pick_icon_btn.pack(side="left")

        ttk.Label(detail, text="背景色:").grid(row=3, column=0, sticky="e", padx=6, pady=4)
        color_frame = ttk.Frame(detail)
        color_frame.grid(row=3, column=1, sticky="w", padx=6, pady=4)
        self.color_swatch = tk.Label(color_frame, width=4, relief="solid", bd=1, bg=palette_config.DEFAULT_COLOR)
        self.color_swatch.pack(side="left")
        self.pick_color_btn = ttk.Button(color_frame, text="色を選ぶ…", command=self._on_pick_color)
        self.pick_color_btn.pack(side="left", padx=6)
        self.reset_color_btn = ttk.Button(color_frame, text="既定に戻す", command=self._on_reset_color)
        self.reset_color_btn.pack(side="left")

        # 👑 「線属性ボタンってどこで設定するんだっけ」「中の話だね」への
        # 対応。箱の中身が補助線系(kind="auto_attr")の場合だけ、外の画面
        # (SidePanel)と同じ線色/線種/線幅/水平垂直/レイヤ/対象コマンドの
        # 設定欄を出す(単一選択時のみ、複数選択では出さない)。
        self.detail_separator = ttk.Separator(detail, orient="horizontal")
        self.detail_separator.grid(row=4, column=0, columnspan=2, sticky="ew", padx=6, pady=(2, 4))

        auto_attr_frame = ttk.Frame(detail)
        self.auto_attr_frame = auto_attr_frame
        ttk.Label(auto_attr_frame, text="線色:").pack(side="left")
        self.auto_attr_color_var = tk.StringVar()
        self.auto_attr_color_combo = ttk.Combobox(
            auto_attr_frame, textvariable=self.auto_attr_color_var, values=palette_config.LINE_COLOR_LABELS,
            state="readonly", width=7,
        )
        self.auto_attr_color_combo.pack(side="left", padx=(2, 8))
        self.auto_attr_color_combo.bind("<<ComboboxSelected>>", self._on_auto_attr_changed)

        ttk.Label(auto_attr_frame, text="線種:").pack(side="left")
        self.auto_attr_type_var = tk.StringVar()
        self.auto_attr_type_combo = ttk.Combobox(
            auto_attr_frame, textvariable=self.auto_attr_type_var, values=palette_config.LINE_TYPE_LABELS,
            state="readonly", width=7,
        )
        self.auto_attr_type_combo.pack(side="left", padx=(2, 8))
        self.auto_attr_type_combo.bind("<<ComboboxSelected>>", self._on_auto_attr_changed)

        ttk.Label(auto_attr_frame, text="線幅:").pack(side="left")
        self.auto_attr_width_var = tk.StringVar()
        self.auto_attr_width_entry = ttk.Entry(auto_attr_frame, textvariable=self.auto_attr_width_var, width=5)
        self.auto_attr_width_entry.pack(side="left", padx=(2, 8))
        self.auto_attr_width_var.trace_add("write", self._on_auto_attr_width_changed)

        self.auto_attr_hv_var = tk.BooleanVar()
        self.auto_attr_hv_check = ttk.Checkbutton(
            auto_attr_frame, text="水平･垂直もON", variable=self.auto_attr_hv_var, command=self._on_auto_attr_changed,
        )
        self.auto_attr_hv_check.pack(side="left", padx=(0, 8))

        # 👑 「見本で選ぶ…」等の設定用ボタンは行末(右側)へ(ユーザー要望:
        # 「右に設定ボタンをいろいろ持ってきたらいいんじゃない？」)。読み込み
        # は画面を開いた後にボタンを押した時だけ走るようになったため、
        # 「(5秒待つ)」の事前注記は不要になった(削除)。
        ttk.Button(auto_attr_frame, text="見本で選ぶ…", command=self._on_pick_swatches).pack(side="left", padx=(0, 8))

        auto_attr_frame2 = ttk.Frame(detail)
        self.auto_attr_frame2 = auto_attr_frame2
        ttk.Label(auto_attr_frame2, text="レイヤG:").pack(side="left")
        self.auto_attr_layer_group_var = tk.StringVar()
        self.auto_attr_layer_group_combo = ttk.Combobox(
            auto_attr_frame2, textvariable=self.auto_attr_layer_group_var,
            values=palette_config.LAYER_NUMBER_LABELS, state="readonly", width=7,
        )
        self.auto_attr_layer_group_combo.pack(side="left", padx=(2, 8))
        self.auto_attr_layer_group_combo.bind("<<ComboboxSelected>>", self._on_auto_attr_changed)

        ttk.Label(auto_attr_frame2, text="レイヤ:").pack(side="left")
        self.auto_attr_layer_number_var = tk.StringVar()
        self.auto_attr_layer_number_combo = ttk.Combobox(
            auto_attr_frame2, textvariable=self.auto_attr_layer_number_var,
            values=palette_config.LAYER_NUMBER_LABELS, state="readonly", width=7,
        )
        self.auto_attr_layer_number_combo.pack(side="left", padx=(2, 8))
        self.auto_attr_layer_number_combo.bind("<<ComboboxSelected>>", self._on_auto_attr_changed)

        ttk.Label(auto_attr_frame2, text="対象:").pack(side="left")
        # 👑 対象を「メイン」種別(線・矩形・連続線等)だけに絞る。
        # ファイル操作/一発系コマンドはCHECKED状態を持たず、「離脱したら
        # 自動で戻す」の検知ができないため選ばせない(ユーザー指摘:
        # 「コマンド全部いれたら問題おきないかな。クラッシュしそうじゃ
        # ない？」→ クラッシュはしないが、選ぶと線属性が戻らなくなる
        # 実害があるため制限した)。
        self._target_command_options = [
            (row["command_id"], f"{row['command_id']} {row['toolbar_name']}")
            for row in command_master.list_available_commands()
            if row["command_id"] in palette_config.AUTO_ATTR_DRAW_TARGET_COMMAND_IDS
        ]
        self.auto_attr_target_var = tk.StringVar()
        self.auto_attr_target_combo = ttk.Combobox(
            auto_attr_frame2, textvariable=self.auto_attr_target_var,
            values=[label for _cid, label in self._target_command_options], state="readonly", width=12,
        )
        self.auto_attr_target_combo.pack(side="left", padx=(2, 0))
        self.auto_attr_target_combo.bind("<<ComboboxSelected>>", self._on_auto_attr_changed)

        ttk.Label(self, text="(複数選択してまとめてアイコン・色を変更できます)",
                  foreground="#888888").pack(side="top", anchor="w", padx=8)

        footer = ttk.Frame(self)
        footer.pack(side="top", fill="x", padx=8, pady=8)
        ttk.Button(footer, text="OK", command=self._on_ok, width=10).pack(side="right")
        ttk.Button(footer, text="キャンセル", command=self._on_cancel, width=10).pack(side="right", padx=(0, 6))

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self._rebuild_list()
        self._set_detail_enabled(False, False)
        self._load_detail()
        self.grab_set()

    def _rebuild_list(self, reselect=None):
        self.listbox.delete(0, tk.END)
        for b in self._buttons:
            icon_label = b["icon"] or ICON_NONE_LABEL
            self.listbox.insert(tk.END, f"{b['name']}  [{icon_label}]")
        for i in (reselect or []):
            if 0 <= i < len(self._buttons):
                self.listbox.selection_set(i)
        self._load_detail()

    def _selected_indices(self):
        return list(self.listbox.curselection())

    def _set_detail_enabled(self, name_enabled, batch_enabled):
        self.name_entry.configure(state=("normal" if name_enabled else "disabled"))
        batch_state = "normal" if batch_enabled else "disabled"
        self.pick_icon_btn.configure(state=batch_state)
        self.pick_color_btn.configure(state=batch_state)
        self.reset_color_btn.configure(state=batch_state)

    def _update_icon_preview(self, icon_name):
        self.icon_preview.delete("all")
        self._icon_preview_refs = []
        if icon_name:
            draw_icon_thumbnail(self.icon_preview, icon_name, self._icon_preview_refs, size=28)
        self.icon_name_label.configure(text=icon_name if icon_name else ICON_NONE_LABEL)

    def _set_auto_attr_section_visible(self, visible):
        if visible:
            self.detail_separator.grid()
            self.auto_attr_frame.grid(row=5, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 2))
            self.auto_attr_frame2.grid(row=6, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 4))
        else:
            self.detail_separator.grid_remove()
            self.auto_attr_frame.grid_remove()
            self.auto_attr_frame2.grid_remove()

    def _load_detail(self):
        self._loading_detail = True
        try:
            indices = self._selected_indices()
            if not indices:
                self.cmd_var.set("")
                self.name_var.set("")
                self._update_icon_preview("")
                self.color_swatch.configure(bg=palette_config.DEFAULT_COLOR)
                self._set_detail_enabled(False, False)
                self._set_auto_attr_section_visible(False)
                return
            first = self._buttons[indices[0]]
            is_auto_attr = len(indices) == 1 and first.get("kind") == palette_config.BUTTON_KIND_AUTO_ATTR
            if len(indices) == 1:
                if is_auto_attr:
                    target_cid = first.get("target_command") or palette_config.DEFAULT_AUTO_ATTR_TARGET_COMMAND
                    target_label = next((lbl for cid, lbl in self._target_command_options if cid == target_cid), target_cid)
                    self.cmd_var.set(f"(モード・{target_label})")
                    color_idx = palette_config.LINE_COLOR_CTRL_IDS.index(first["line_color"])
                    type_idx = palette_config.LINE_TYPE_CTRL_IDS.index(first["line_type"])
                    self.auto_attr_color_var.set(palette_config.LINE_COLOR_LABELS[color_idx])
                    self.auto_attr_type_var.set(palette_config.LINE_TYPE_LABELS[type_idx])
                    self.auto_attr_width_var.set(first.get("line_width") or "")
                    self.auto_attr_hv_var.set(bool(first.get("horizontal_vertical")))

                    def _layer_value_to_label(value):
                        return palette_config.LAYER_NUMBER_LABELS[0] if value is None else palette_config.LAYER_NUMBER_LABELS[value + 1]

                    self.auto_attr_layer_group_var.set(_layer_value_to_label(first.get("layer_group")))
                    self.auto_attr_layer_number_var.set(_layer_value_to_label(first.get("layer_number")))
                    self.auto_attr_target_var.set(target_label)
                else:
                    row = command_master.get_by_command_id(first["command_id"]) or {}
                    category = (row.get("category") or "").strip()
                    self.cmd_var.set(f"{first['command_id']} ({category})" if category else first["command_id"])
                self.name_var.set(first["name"])
                self._set_detail_enabled(True, True)
            else:
                self.cmd_var.set(f"{len(indices)}個選択中")
                self.name_var.set("")
                self._set_detail_enabled(False, True)
            self._update_icon_preview(first.get("icon", ""))
            self.color_swatch.configure(bg=first.get("color") or palette_config.DEFAULT_COLOR)
            self._set_auto_attr_section_visible(is_auto_attr)
        finally:
            self._loading_detail = False

    def _on_auto_attr_changed(self, event=None):
        if self._loading_detail:
            return
        indices = self._selected_indices()
        if len(indices) != 1 or self._buttons[indices[0]].get("kind") != palette_config.BUTTON_KIND_AUTO_ATTR:
            return
        btn = self._buttons[indices[0]]
        try:
            color_idx = palette_config.LINE_COLOR_LABELS.index(self.auto_attr_color_var.get())
            btn["line_color"] = palette_config.LINE_COLOR_CTRL_IDS[color_idx]
        except ValueError:
            pass
        try:
            type_idx = palette_config.LINE_TYPE_LABELS.index(self.auto_attr_type_var.get())
            btn["line_type"] = palette_config.LINE_TYPE_CTRL_IDS[type_idx]
        except ValueError:
            pass
        btn["horizontal_vertical"] = self.auto_attr_hv_var.get()

        def _label_to_layer_value(label):
            try:
                idx = palette_config.LAYER_NUMBER_LABELS.index(label)
            except ValueError:
                return None
            return None if idx == 0 else idx - 1

        btn["layer_group"] = _label_to_layer_value(self.auto_attr_layer_group_var.get())
        btn["layer_number"] = _label_to_layer_value(self.auto_attr_layer_number_var.get())

        selected_label = self.auto_attr_target_var.get()
        for cid, label in self._target_command_options:
            if label == selected_label:
                btn["target_command"] = cid
                break

    def _on_auto_attr_width_changed(self, *args):
        if self._loading_detail:
            return
        indices = self._selected_indices()
        if len(indices) != 1 or self._buttons[indices[0]].get("kind") != palette_config.BUTTON_KIND_AUTO_ATTR:
            return
        self._buttons[indices[0]]["line_width"] = self.auto_attr_width_var.get()

    def _on_pick_swatches(self):
        indices = self._selected_indices()
        if len(indices) != 1 or self._buttons[indices[0]].get("kind") != palette_config.BUTTON_KIND_AUTO_ATTR:
            return
        hwnd = _get_jw_hwnd(self.manager_ref)
        if not hwnd:
            messagebox.showwarning("見本を読み取れません", "jw_cadのウィンドウが見つかりません。", parent=self)
            return
        btn = self._buttons[indices[0]]
        dlg = LineAttrSwatchDialog(
            self, hwnd, current_color=btn.get("line_color"), current_type=btn.get("line_type"),
            swatch_cache=self.swatch_cache,
        )
        self.wait_window(dlg)
        if dlg.result_color is not None:
            btn["line_color"] = dlg.result_color
        if dlg.result_type is not None:
            btn["line_type"] = dlg.result_type
        self._load_detail()

    def _on_name_changed(self, *args):
        if self._loading_detail:
            return
        indices = self._selected_indices()
        if len(indices) != 1:
            return
        self._buttons[indices[0]]["name"] = self.name_var.get()
        sel = list(self.listbox.curselection())
        self._rebuild_list(reselect=sel)

    def _on_reset_color(self):
        indices = self._selected_indices()
        if not indices:
            return
        for i in indices:
            self._buttons[i]["color"] = palette_config.DEFAULT_COLOR
        self.color_swatch.configure(bg=palette_config.DEFAULT_COLOR)

    def _on_add(self):
        # 👑 「グループボタンの中には線属性ボタン作れますか？」への対応。
        # 箱(box)は入れ子禁止だがauto_attrは中身自体が入れ物を持たない
        # ので許可する(palette_config._normalize_button側でも許可済み)。
        existing_ids = {b["command_id"] for b in self._buttons}
        dlg = CommandPickerDialog(self, existing_ids=existing_ids, special_kinds=("auto_attr",))
        self.wait_window(dlg)
        rows = dlg.result
        specials = dlg.result_specials
        if not rows and not specials:
            return
        known_icons = set(palette_config.list_all_icon_names())
        for row in rows:
            if row["command_id"] in existing_ids:
                continue
            default_color = (
                palette_config.SUB_COMMAND_DEFAULT_COLOR
                if row.get("command_kind") == "サブ"
                else palette_config.DEFAULT_COLOR
            )
            default_icon = row.get("default_icon") or palette_config.NO_ICON
            if default_icon not in known_icons:
                default_icon = palette_config.NO_ICON
            self._buttons.append(palette_config.new_button(
                row["command_id"], row["toolbar_name"], icon=default_icon, color=default_color
            ))
            existing_ids.add(row["command_id"])
        for key in specials:
            if key != "auto_attr":
                continue
            name_dlg = TextInputDialog(self, title="モードボタンを追加", label="名前:", initial="補助線")
            self.wait_window(name_dlg)
            if name_dlg.result:
                self._buttons.append(palette_config.new_auto_attr_button(name_dlg.result, horizontal_vertical=True))
        self._rebuild_list()

    def _on_remove(self):
        indices = self._selected_indices()
        if not indices:
            return
        for i in reversed(indices):
            self._buttons.pop(i)
        self._rebuild_list()

    def _move_up(self):
        indices = sorted(self._selected_indices())
        if not indices or indices[0] <= 0:
            return
        for i in indices:
            self._buttons[i - 1], self._buttons[i] = self._buttons[i], self._buttons[i - 1]
        self._rebuild_list(reselect=[i - 1 for i in indices])

    def _move_down(self):
        indices = sorted(self._selected_indices(), reverse=True)
        if not indices or indices[0] >= len(self._buttons) - 1:
            return
        for i in indices:
            self._buttons[i + 1], self._buttons[i] = self._buttons[i], self._buttons[i + 1]
        self._rebuild_list(reselect=[i + 1 for i in indices])

    def _on_pick_icon(self):
        indices = self._selected_indices()
        if not indices:
            return
        dlg = IconPickerDialog(self, current_icon=self._buttons[indices[0]].get("icon"))
        self.wait_window(dlg)
        if dlg.result is not None:
            for i in indices:
                self._buttons[i]["icon"] = dlg.result
            self._rebuild_list(reselect=indices)

    def _on_pick_color(self):
        indices = self._selected_indices()
        if not indices:
            return
        dlg = ColorPickerDialog(self, initial_color=self._buttons[indices[0]].get("color"))
        self.wait_window(dlg)
        if dlg.result:
            for i in indices:
                self._buttons[i]["color"] = dlg.result
            self._rebuild_list(reselect=indices)

    def _on_ok(self):
        self.result = self._buttons
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()


class SidePanel(ttk.Frame):
    def __init__(self, master, side, side_cfg, manager_ref=None, swatch_cache=None):
        super().__init__(master)
        self.side = side
        self.side_cfg = side_cfg
        self.manager_ref = manager_ref
        self.swatch_cache = swatch_cache if swatch_cache is not None else {"data": None}
        self.selected = None
        self._selected_group = None
        self._selected_indices = []
        self.list_widgets = []
        self._loading_detail = False
        self._icon_preview_refs = []

        self.orient_var = tk.StringVar(value=side_cfg["orientation"])
        self.size_var = tk.IntVar(value=side_cfg["button_size"])
        self.cmd_var = tk.StringVar()
        self.name_var = tk.StringVar()

        self._build_shape_bar()
        self._build_layout_area()
        self._build_detail_form()

        self.name_var.trace_add("write", self._on_name_changed)

        self._rebuild_groups()

    def _group_noun(self):
        return "行" if self.orient_var.get() == palette_config.ORIENTATION_LANDSCAPE else "列"

    def _build_shape_bar(self):
        bar = ttk.LabelFrame(self, text="パレット形状")
        bar.pack(side="top", fill="x", padx=8, pady=6)

        ttk.Label(bar, text="向き:").pack(side="left", padx=6, pady=4)
        ttk.Radiobutton(bar, text="縦長", variable=self.orient_var,
                         value=palette_config.ORIENTATION_PORTRAIT, command=self._on_orientation).pack(side="left", padx=6, pady=4)
        ttk.Radiobutton(bar, text="横長", variable=self.orient_var,
                         value=palette_config.ORIENTATION_LANDSCAPE, command=self._on_orientation).pack(side="left", padx=6, pady=4)

        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=10)

        ttk.Label(bar, text="ボタンサイズ:").pack(side="left", padx=6, pady=4)
        ttk.Spinbox(bar, from_=palette_config.MIN_BUTTON_SIZE, to=palette_config.MAX_BUTTON_SIZE,
                    increment=4, width=5, textvariable=self.size_var, command=self._on_size,
                    state="readonly").pack(side="left", padx=6, pady=4)
        ttk.Label(bar, text="px").pack(side="left")

    def _build_layout_area(self):
        lf = ttk.LabelFrame(self, text="ボタン配置")
        lf.pack(side="top", fill="both", expand=True, padx=8, pady=6)

        self.groups_host = tk.Frame(lf, bg="#f0f0f0")
        self.groups_host.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        ops = ttk.Frame(lf)
        ops.pack(side="right", fill="y", padx=(0, 6), pady=4)

        ttk.Button(ops, text="▲", width=6, command=self._move_up).pack(pady=2)
        ttk.Button(ops, text="▼", width=6, command=self._move_down).pack(pady=2)
        ttk.Button(ops, text="◀", width=6, command=self._move_prev_group).pack(pady=2)
        ttk.Button(ops, text="▶", width=6, command=self._move_next_group).pack(pady=2)
        ttk.Separator(ops, orient="horizontal").pack(fill="x", pady=6)
        # 👑 「追加」「箱追加」「線属性追加」の3ボタンを1つに集約(ユーザー
        # 要望: 「箱と線属性を追加の中に入れたら？」)。操作列の縦の長さが
        # 設定ウィンドウ全体の高さの下限になっていた(ボタン配置エリアが
        # これより縮められない主因)ため、統合してその分を削れるように
        # した。
        ttk.Button(ops, text="追加", width=6, command=self._on_add).pack(pady=2)
        ttk.Button(ops, text="削除", width=6, command=self._on_remove).pack(pady=2)
        ttk.Separator(ops, orient="horizontal").pack(fill="x", pady=6)
        self.add_group_btn = ttk.Button(ops, text="＋列", width=6, command=self._on_add_group)
        self.add_group_btn.pack(pady=2)
        self.remove_group_btn = ttk.Button(ops, text="－列", width=6, command=self._on_remove_group)
        self.remove_group_btn.pack(pady=2)

    def _build_detail_form(self):
        lf = ttk.LabelFrame(self, text="ボタン詳細")
        lf.pack(side="top", fill="x", padx=8, pady=(0, 8))

        ttk.Label(lf, text="コマンド:").grid(row=0, column=0, sticky="e", padx=6, pady=4)
        ttk.Label(lf, textvariable=self.cmd_var, wraplength=460, justify="left").grid(row=0, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(lf, text="表示名:").grid(row=1, column=0, sticky="e", padx=6, pady=4)
        self.name_entry = ttk.Entry(lf, textvariable=self.name_var, width=18)
        self.name_entry.grid(row=1, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(lf, text="アイコン:").grid(row=2, column=0, sticky="e", padx=6, pady=4)
        icon_frame = ttk.Frame(lf)
        icon_frame.grid(row=2, column=1, sticky="w", padx=6, pady=4)
        self.icon_preview = tk.Canvas(icon_frame, width=28, height=28, bg="#ffffff",
                                       highlightthickness=1, highlightbackground="#cccccc")
        self.icon_preview.pack(side="left")
        self.icon_name_label = ttk.Label(icon_frame, text="", width=12)
        self.icon_name_label.pack(side="left", padx=(4, 6))
        self.pick_icon_btn = ttk.Button(icon_frame, text="アイコンを選ぶ…", command=self._on_pick_icon)
        self.pick_icon_btn.pack(side="left")

        ttk.Label(lf, text="背景色:").grid(row=3, column=0, sticky="e", padx=6, pady=4)
        color_frame = ttk.Frame(lf)
        color_frame.grid(row=3, column=1, sticky="w", padx=6, pady=4)
        self.color_swatch = tk.Label(color_frame, width=4, relief="solid", bd=1, bg=palette_config.DEFAULT_COLOR)
        self.color_swatch.pack(side="left")
        self.pick_color_btn = ttk.Button(color_frame, text="色を選ぶ…", command=self._on_pick_color)
        self.pick_color_btn.pack(side="left", padx=6)
        self.reset_color_btn = ttk.Button(color_frame, text="既定に戻す", command=self._on_reset_color)
        self.reset_color_btn.pack(side="left")
        ttk.Label(lf, text="(リストでCtrl/Shiftクリックすると複数選択してまとめて色・アイコン変更できます)",
                  foreground="#888888").grid(row=4, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 4))

        # 👑 フライアウト/マクロの「箱」ボタン用の操作と、補助線系
        # (kind="auto_attr")ボタン用の線属性/レイヤ設定は、同じボタンで
        # 両方使われることは無い(排他)。以前は両方を常時grid配置して
        # disabled状態で表示していたため、選んでいない方の分もずっと
        # 縦スペースを占有し続け、設定ウィンドウが必要以上に縦長になって
        # 保存/キャンセルが枠外に押し出される不具合を繰り返していた
        # (ユーザー指摘)。selectedなkindに応じてgrid()/grid_remove()で
        # 実際に出し入れし、同じ行位置(row=6)を使い回す。
        self._detail_extra_row = 6
        self.detail_separator = ttk.Separator(lf, orient="horizontal")
        self.detail_separator.grid(row=5, column=0, columnspan=2, sticky="ew", padx=6, pady=(2, 4))

        # 👑 「線属性ボタンだけボタン詳細が中央ぞろえになってる」への対応。
        # 以前はcolumnspan=2で1枠を丸ごと使っていたため、他の行(ラベルが
        # column0・中身がcolumn1)と揃わず中央寄りに見えていた。他の行と
        # 同じくcolumn0にラベル、column1に中身、という形に統一する
        # (箱用/補助線系用でラベルの出し分けが要るので共有のLabelを使う)。
        self.extra_row_label = ttk.Label(lf, text="")
        self.extra_row_label.grid(row=6, column=0, sticky="ne", padx=6, pady=4)

        group_frame = ttk.Frame(lf)
        self.edit_group_btn = ttk.Button(group_frame, text="中身を編集…", command=self._on_edit_group)
        self.edit_group_btn.pack(side="left")
        self.ungroup_btn = ttk.Button(group_frame, text="グループ解除", command=self._on_ungroup)
        self.ungroup_btn.pack(side="left", padx=(6, 0))
        self.group_frame = group_frame

        # 👑 「補助線」「配線」等(kind="auto_attr")用: 線色・線種・線幅・
        # 水平垂直・レイヤグループ・レイヤを、幅に余裕があるので1行に
        # まとめる(ユーザー要望: 「並べれるところは並べて」)。
        auto_attr_frame = ttk.Frame(lf)
        self.auto_attr_frame = auto_attr_frame
        ttk.Label(auto_attr_frame, text="線色:").pack(side="left")
        self.auto_attr_color_var = tk.StringVar()
        self.auto_attr_color_combo = ttk.Combobox(
            auto_attr_frame, textvariable=self.auto_attr_color_var, values=palette_config.LINE_COLOR_LABELS,
            state="readonly", width=7,
        )
        self.auto_attr_color_combo.pack(side="left", padx=(2, 8))
        self.auto_attr_color_combo.bind("<<ComboboxSelected>>", self._on_auto_attr_changed)

        ttk.Label(auto_attr_frame, text="線種:").pack(side="left")
        self.auto_attr_type_var = tk.StringVar()
        self.auto_attr_type_combo = ttk.Combobox(
            auto_attr_frame, textvariable=self.auto_attr_type_var, values=palette_config.LINE_TYPE_LABELS,
            state="readonly", width=7,
        )
        self.auto_attr_type_combo.pack(side="left", padx=(2, 8))
        self.auto_attr_type_combo.bind("<<ComboboxSelected>>", self._on_auto_attr_changed)

        ttk.Label(auto_attr_frame, text="線幅:").pack(side="left")
        self.auto_attr_width_var = tk.StringVar()
        self.auto_attr_width_entry = ttk.Entry(auto_attr_frame, textvariable=self.auto_attr_width_var, width=5)
        self.auto_attr_width_entry.pack(side="left", padx=(2, 8))
        self.auto_attr_width_var.trace_add("write", self._on_auto_attr_width_changed)

        self.auto_attr_hv_var = tk.BooleanVar()
        self.auto_attr_hv_check = ttk.Checkbutton(
            auto_attr_frame, text="水平･垂直もON", variable=self.auto_attr_hv_var,
            command=self._on_auto_attr_changed,
        )
        self.auto_attr_hv_check.pack(side="left", padx=(0, 8))

        # 👑 「見本で選ぶ…」等の設定用ボタンは行末(右側)へ(ユーザー要望:
        # 「右に設定ボタンをいろいろ持ってきたらいいんじゃない？」)。読み込み
        # は画面を開いた後にボタンを押した時だけ走るようになったため、
        # 「(5秒待つ)」の事前注記は不要になった(削除)。
        ttk.Button(auto_attr_frame, text="見本で選ぶ…", command=self._on_pick_swatches).pack(side="left", padx=(0, 8))

        # 👑 幅overflow対策で2行目に分ける(実機でレイヤ系の設定と保存/
        # キャンセルが右に切れる不具合が出た)。GroupContentsDialogの
        # auto_attr_frame/auto_attr_frame2と同じ構成に揃える。
        auto_attr_frame2 = ttk.Frame(lf)
        self.auto_attr_frame2 = auto_attr_frame2
        ttk.Label(auto_attr_frame2, text="レイヤG:").pack(side="left")
        self.auto_attr_layer_group_var = tk.StringVar()
        self.auto_attr_layer_group_combo = ttk.Combobox(
            auto_attr_frame2, textvariable=self.auto_attr_layer_group_var,
            values=palette_config.LAYER_NUMBER_LABELS, state="readonly", width=7,
        )
        self.auto_attr_layer_group_combo.pack(side="left", padx=(2, 8))
        self.auto_attr_layer_group_combo.bind("<<ComboboxSelected>>", self._on_auto_attr_changed)

        ttk.Label(auto_attr_frame2, text="レイヤ:").pack(side="left")
        self.auto_attr_layer_number_var = tk.StringVar()
        self.auto_attr_layer_number_combo = ttk.Combobox(
            auto_attr_frame2, textvariable=self.auto_attr_layer_number_var,
            values=palette_config.LAYER_NUMBER_LABELS, state="readonly", width=7,
        )
        self.auto_attr_layer_number_combo.pack(side="left", padx=(2, 8))
        self.auto_attr_layer_number_combo.bind("<<ComboboxSelected>>", self._on_auto_attr_changed)

        # 👑 切替先コマンド(既定は直線)。「他のコマンド選択することできる？
        # 連続線とか」というユーザー要望への対応。
        ttk.Label(auto_attr_frame2, text="対象:").pack(side="left")
        # 👑 対象を「メイン」種別(線・矩形・連続線等)だけに絞る。
        # ファイル操作/一発系コマンドはCHECKED状態を持たず、「離脱したら
        # 自動で戻す」の検知ができないため選ばせない(ユーザー指摘:
        # 「コマンド全部いれたら問題おきないかな。クラッシュしそうじゃ
        # ない？」→ クラッシュはしないが、選ぶと線属性が戻らなくなる
        # 実害があるため制限した)。
        self._target_command_options = [
            (row["command_id"], f"{row['command_id']} {row['toolbar_name']}")
            for row in command_master.list_available_commands()
            if row["command_id"] in palette_config.AUTO_ATTR_DRAW_TARGET_COMMAND_IDS
        ]
        self.auto_attr_target_var = tk.StringVar()
        self.auto_attr_target_combo = ttk.Combobox(
            auto_attr_frame2, textvariable=self.auto_attr_target_var,
            values=[label for _cid, label in self._target_command_options], state="readonly", width=12,
        )
        self.auto_attr_target_combo.pack(side="left", padx=(2, 0))
        self.auto_attr_target_combo.bind("<<ComboboxSelected>>", self._on_auto_attr_changed)

        self._set_detail_enabled(False, False)
        self._set_detail_extra_section(None)

    def _set_detail_extra_section(self, section):
        # 👑 group_frame(箱用)とauto_attr_frame(補助線系用)は排他なので、
        # 選ばれた方だけ実際にgrid()して表示し、他方はgrid_remove()で
        # 完全に外す(disabled表示のまま常時場所だけ取っていた以前の
        # 実装だと、使わない方の分まで縦に伸び続けていた)。
        # 👑 他の行(ラベルがcolumn0・中身がcolumn1)と揃える(以前は
        # columnspan=2で1枠を丸ごと使っていて中央寄りに見えていた)。
        # section: None(何も出さない)/"group"/"auto_attr"
        self.group_frame.grid_remove()
        self.auto_attr_frame.grid_remove()
        self.auto_attr_frame2.grid_remove()
        self.extra_row_label.grid_remove()
        if section is None:
            self.detail_separator.grid_remove()
            return
        self.detail_separator.grid()
        self.extra_row_label.grid()
        if section == "group":
            self.extra_row_label.configure(text="中身:")
            self.group_frame.grid(row=self._detail_extra_row, column=1, sticky="w", padx=6, pady=4)
        elif section == "auto_attr":
            self.extra_row_label.configure(text="モード:")
            self.auto_attr_frame.grid(row=self._detail_extra_row, column=1, sticky="w", padx=6, pady=(4, 0))
            self.auto_attr_frame2.grid(row=self._detail_extra_row + 1, column=1, sticky="w", padx=6, pady=(0, 4))

    def _on_auto_attr_changed(self, event=None):
        if self._loading_detail:
            return
        btn = self._selected_button()
        if btn is None or btn.get("kind") != palette_config.BUTTON_KIND_AUTO_ATTR:
            return
        try:
            color_idx = palette_config.LINE_COLOR_LABELS.index(self.auto_attr_color_var.get())
            btn["line_color"] = palette_config.LINE_COLOR_CTRL_IDS[color_idx]
        except ValueError:
            pass
        try:
            type_idx = palette_config.LINE_TYPE_LABELS.index(self.auto_attr_type_var.get())
            btn["line_type"] = palette_config.LINE_TYPE_CTRL_IDS[type_idx]
        except ValueError:
            pass
        btn["horizontal_vertical"] = self.auto_attr_hv_var.get()

        def _label_to_layer_value(label):
            try:
                idx = palette_config.LAYER_NUMBER_LABELS.index(label)
            except ValueError:
                return None
            return None if idx == 0 else idx - 1

        btn["layer_group"] = _label_to_layer_value(self.auto_attr_layer_group_var.get())
        btn["layer_number"] = _label_to_layer_value(self.auto_attr_layer_number_var.get())

        selected_label = self.auto_attr_target_var.get()
        for cid, label in self._target_command_options:
            if label == selected_label:
                btn["target_command"] = cid
                break

    def _on_auto_attr_width_changed(self, *args):
        if self._loading_detail:
            return
        btn = self._selected_button()
        if btn is None or btn.get("kind") != palette_config.BUTTON_KIND_AUTO_ATTR:
            return
        btn["line_width"] = self.auto_attr_width_var.get()

    def _on_pick_swatches(self):
        btn = self._selected_button()
        if btn is None or btn.get("kind") != palette_config.BUTTON_KIND_AUTO_ATTR:
            return
        hwnd = _get_jw_hwnd(self.manager_ref)
        if not hwnd:
            messagebox.showwarning("見本を読み取れません", "jw_cadのウィンドウが見つかりません。", parent=self.winfo_toplevel())
            return
        dlg = LineAttrSwatchDialog(
            self.winfo_toplevel(), hwnd, current_color=btn.get("line_color"), current_type=btn.get("line_type"),
            swatch_cache=self.swatch_cache,
        )
        self.winfo_toplevel().wait_window(dlg)
        if dlg.result_color is not None:
            btn["line_color"] = dlg.result_color
        if dlg.result_type is not None:
            btn["line_type"] = dlg.result_type
        self._load_detail()

    # ---- 選択・表示 ----

    def _selected_button(self):
        if self.selected is None:
            return None
        gi, ii = self.selected
        groups = self.side_cfg["groups"]
        if gi >= len(groups):
            return None
        buttons = groups[gi]["buttons"]
        if ii >= len(buttons):
            return None
        return buttons[ii]

    def _selected_buttons(self):
        # 👑 色・アイコンのまとめ変更のため、複数選択(extended)の全ボタンを
        # 返す。名前編集だけは単一選択時のみ意味があるので_selected_button()
        # (単一)を引き続き使う。
        if self._selected_group is None or not self._selected_indices:
            return []
        groups = self.side_cfg["groups"]
        if self._selected_group >= len(groups):
            return []
        buttons = groups[self._selected_group]["buttons"]
        return [buttons[i] for i in self._selected_indices if i < len(buttons)]

    def _set_detail_enabled(self, name_enabled, batch_enabled):
        self.name_entry.configure(state=("normal" if name_enabled else "disabled"))
        batch_state = "normal" if batch_enabled else "disabled"
        self.pick_icon_btn.configure(state=batch_state)
        self.pick_color_btn.configure(state=batch_state)
        self.reset_color_btn.configure(state=batch_state)

    def _update_icon_preview(self, icon_name):
        self.icon_preview.delete("all")
        self._icon_preview_refs = []
        if icon_name:
            draw_icon_thumbnail(self.icon_preview, icon_name, self._icon_preview_refs, size=28)
        self.icon_name_label.configure(text=icon_name if icon_name else ICON_NONE_LABEL)

    def _load_detail(self):
        self._loading_detail = True
        try:
            multi = self._selected_buttons()
            btn = self._selected_button()
            if btn is None and len(multi) <= 1:
                self.cmd_var.set("")
                self.name_var.set("")
                self._update_icon_preview("")
                self.color_swatch.configure(bg=palette_config.DEFAULT_COLOR)
                self._set_detail_enabled(False, False)
                self._set_detail_extra_section(None)
                return
            if btn is not None:
                kind = btn.get("kind")
                is_group = kind in (palette_config.BUTTON_KIND_FLYOUT, palette_config.BUTTON_KIND_MACRO)
                is_auto_attr = kind == palette_config.BUTTON_KIND_AUTO_ATTR
                if is_group:
                    # 👑 「中身5個」という個数だけでは何が入っているか分からない
                    # という指摘のため、コマンド欄に中身の名前も並べて表示する
                    # (専用の行を別途足すと縦に伸びて設定ウィンドウ下端の
                    # 保存ボタンが枠外に押し出されてしまったため、既存の
                    # 「コマンド:」行に折り返し表示でまとめる形にした)。
                    kind_label = "フライアウト" if kind == palette_config.BUTTON_KIND_FLYOUT else "マクロ"
                    sub_buttons = btn.get("sub_buttons") or []
                    contents = "、".join(sb["name"] for sb in sub_buttons) if sub_buttons else "(まだ何もありません)"
                    self.cmd_var.set(f"({kind_label}) {contents}")
                elif is_auto_attr:
                    target_cid = btn.get("target_command") or palette_config.DEFAULT_AUTO_ATTR_TARGET_COMMAND
                    target_label = next((lbl for cid, lbl in self._target_command_options if cid == target_cid), target_cid)
                    self.cmd_var.set(f"(モード・{target_label})")
                    self.auto_attr_target_var.set(target_label)
                    color_idx = palette_config.LINE_COLOR_CTRL_IDS.index(btn["line_color"])
                    type_idx = palette_config.LINE_TYPE_CTRL_IDS.index(btn["line_type"])
                    self.auto_attr_color_var.set(palette_config.LINE_COLOR_LABELS[color_idx])
                    self.auto_attr_type_var.set(palette_config.LINE_TYPE_LABELS[type_idx])
                    self.auto_attr_width_var.set(btn.get("line_width") or "")
                    self.auto_attr_hv_var.set(bool(btn.get("horizontal_vertical")))

                    def _layer_value_to_label(value):
                        return palette_config.LAYER_NUMBER_LABELS[0] if value is None else palette_config.LAYER_NUMBER_LABELS[value + 1]

                    self.auto_attr_layer_group_var.set(_layer_value_to_label(btn.get("layer_group")))
                    self.auto_attr_layer_number_var.set(_layer_value_to_label(btn.get("layer_number")))
                else:
                    row = command_master.get_by_command_id(btn["command_id"]) or {}
                    category = (row.get("category") or "").strip()
                    self.cmd_var.set(f"{btn['command_id']} ({category})" if category else btn["command_id"])
                self.name_var.set(btn["name"])
                self._update_icon_preview(btn["icon"])
                self.color_swatch.configure(bg=btn["color"])
                self._set_detail_enabled(True, True)
                self._set_detail_extra_section("group" if is_group else ("auto_attr" if is_auto_attr else None))
            else:
                # 複数選択中: 名前は編集不可、色・アイコンはまとめて変更可能
                self.cmd_var.set(f"{len(multi)}個選択中")
                self.name_var.set("")
                self._update_icon_preview(multi[0]["icon"])
                self.color_swatch.configure(bg=multi[0]["color"])
                self._set_detail_enabled(False, True)
                self._set_detail_extra_section(None)
        finally:
            self._loading_detail = False

    def _select(self, group_index, item_index):
        self._select_multi(group_index, [item_index])

    def _select_multi(self, group_index, item_indices):
        item_indices = sorted(item_indices)
        self.selected = (group_index, item_indices[0]) if len(item_indices) == 1 else None
        self._selected_group = group_index
        self._selected_indices = item_indices
        for i, lb in enumerate(self.list_widgets):
            lb.selection_clear(0, tk.END)
        if group_index < len(self.list_widgets):
            lb = self.list_widgets[group_index]
            for ii in item_indices:
                lb.selection_set(ii)
            lb.activate(item_indices[-1])
        self._load_detail()

    def _on_select(self, group_index):
        lb = self.list_widgets[group_index]
        sel = lb.curselection()
        if not sel:
            return
        for i, other in enumerate(self.list_widgets):
            if i != group_index:
                other.selection_clear(0, tk.END)
        self._selected_group = group_index
        self._selected_indices = list(sel)
        self.selected = (group_index, sel[0]) if len(sel) == 1 else None
        self._load_detail()

    # ---- グループ・リスト再構築 ----

    def _rebuild_groups(self):
        for child in self.groups_host.winfo_children():
            child.destroy()
        self.list_widgets = []

        noun = self._group_noun()
        self.add_group_btn.configure(text=f"＋{noun}")
        self.remove_group_btn.configure(text=f"－{noun}")

        groups = self.side_cfg["groups"]
        for i, group in enumerate(groups):
            gf = ttk.LabelFrame(self.groups_host, text=f"{noun} {i + 1}")
            gf.pack(side="left", fill="both", expand=True, padx=3)
            lb = tk.Listbox(gf, exportselection=0, height=11, width=14, selectmode="extended",
                             font=("Meiryo UI", 9), activestyle="none")
            scroll = ttk.Scrollbar(gf, orient="vertical", command=lb.yview)
            lb.configure(yscrollcommand=scroll.set)
            lb.pack(side="left", fill="both", expand=True)
            scroll.pack(side="right", fill="y")
            for btn in group["buttons"]:
                lb.insert(tk.END, btn["name"])
            lb.bind("<<ListboxSelect>>", lambda e, gi=i: self._on_select(gi))
            self.list_widgets.append(lb)

        if self._selected_group is not None and self._selected_indices:
            gi = self._selected_group
            valid = [ii for ii in self._selected_indices if gi < len(self.list_widgets) and ii < len(groups[gi]["buttons"])]
            if valid:
                self._select_multi(gi, valid)
            else:
                self.selected = None
                self._selected_group = None
                self._selected_indices = []
                self._load_detail()
        else:
            self._load_detail()

    def _refresh_current_group_labels(self):
        # 名前だけ変わった時に、選択を保ったままリストの表示だけ更新する
        if self.selected is None:
            return
        gi, ii = self.selected
        if gi >= len(self.list_widgets):
            return
        lb = self.list_widgets[gi]
        name = self.side_cfg["groups"][gi]["buttons"][ii]["name"]
        lb.delete(ii)
        lb.insert(ii, name)
        lb.selection_set(ii)

    # ---- 詳細フォームのハンドラ ----

    def _on_name_changed(self, *args):
        if self._loading_detail:
            return
        btn = self._selected_button()
        if btn is None:
            return
        btn["name"] = self.name_var.get()
        self._refresh_current_group_labels()

    def _on_pick_icon(self):
        buttons = self._selected_buttons()
        if not buttons:
            return
        dlg = IconPickerDialog(self.winfo_toplevel(), current_icon=buttons[0].get("icon"))
        self.winfo_toplevel().wait_window(dlg)
        if dlg.result is not None:
            for btn in buttons:
                btn["icon"] = dlg.result
            self._update_icon_preview(dlg.result)

    def _on_pick_color(self):
        buttons = self._selected_buttons()
        if not buttons:
            return
        dlg = ColorPickerDialog(self.winfo_toplevel(), initial_color=buttons[0].get("color"))
        self.winfo_toplevel().wait_window(dlg)
        if dlg.result:
            for btn in buttons:
                btn["color"] = dlg.result
            self.color_swatch.configure(bg=dlg.result)

    def _on_reset_color(self):
        buttons = self._selected_buttons()
        if not buttons:
            return
        for btn in buttons:
            btn["color"] = palette_config.DEFAULT_COLOR
        self.color_swatch.configure(bg=palette_config.DEFAULT_COLOR)

    def _on_orientation(self):
        self.side_cfg["orientation"] = self.orient_var.get()
        self._rebuild_groups()

    def _on_size(self):
        try:
            self.side_cfg["button_size"] = int(self.size_var.get())
        except (TypeError, ValueError):
            pass

    # ---- 並べ替え ----

    def _move_up(self):
        # 👑 複数選択時は、選ばれた全ボタンをまとめて1つ上へ移動する
        # （昇順に処理すると、隣接した選択でも正しく塊のまま繰り上がる）。
        if self._selected_group is None or not self._selected_indices:
            return
        gi = self._selected_group
        buttons = self.side_cfg["groups"][gi]["buttons"]
        indices = sorted(self._selected_indices)
        if indices[0] <= 0:
            return
        for ii in indices:
            buttons[ii - 1], buttons[ii] = buttons[ii], buttons[ii - 1]
        self._selected_indices = [ii - 1 for ii in indices]
        self._rebuild_groups()

    def _move_down(self):
        if self._selected_group is None or not self._selected_indices:
            return
        gi = self._selected_group
        buttons = self.side_cfg["groups"][gi]["buttons"]
        indices = sorted(self._selected_indices, reverse=True)
        if indices[0] >= len(buttons) - 1:
            return
        for ii in indices:
            buttons[ii + 1], buttons[ii] = buttons[ii], buttons[ii + 1]
        self._selected_indices = [ii + 1 for ii in indices]
        self._rebuild_groups()

    def _move_prev_group(self):
        if self._selected_group is None or not self._selected_indices:
            return
        gi = self._selected_group
        if gi <= 0:
            return
        groups = self.side_cfg["groups"]
        indices = sorted(self._selected_indices)
        moved = [groups[gi]["buttons"][ii] for ii in indices]
        for ii in reversed(indices):
            groups[gi]["buttons"].pop(ii)
        target = groups[gi - 1]["buttons"]
        insert_at = len(target)
        target[insert_at:insert_at] = moved
        self._selected_group = gi - 1
        self._selected_indices = list(range(insert_at, insert_at + len(moved)))
        self._rebuild_groups()

    def _move_next_group(self):
        if self._selected_group is None or not self._selected_indices:
            return
        gi = self._selected_group
        groups = self.side_cfg["groups"]
        if gi >= len(groups) - 1:
            return
        indices = sorted(self._selected_indices)
        moved = [groups[gi]["buttons"][ii] for ii in indices]
        for ii in reversed(indices):
            groups[gi]["buttons"].pop(ii)
        target = groups[gi + 1]["buttons"]
        insert_at = len(target)
        target[insert_at:insert_at] = moved
        self._selected_group = gi + 1
        self._selected_indices = list(range(insert_at, insert_at + len(moved)))
        self._rebuild_groups()

    # ---- 追加・削除 ----

    def _existing_ids(self):
        ids = set()
        for group in self.side_cfg["groups"]:
            for btn in group["buttons"]:
                ids.add(btn["command_id"])
        return ids

    def _on_add(self):
        # 👑 「箱を作る」「線属性ボタンを作る」を別メニューに分けたら、
        # コマンドをたくさん追加したい時に毎回そのメニューが挟まって
        # 邪魔という指摘があったため、同じCommandPickerDialogのリストに
        # special_kindsとして混ぜて出す方式にした(常に直接コマンド一覧が
        # 開く、特殊行も同じ多重選択でまとめて拾える)。
        dlg = CommandPickerDialog(
            self.winfo_toplevel(), existing_ids=self._existing_ids(),
            special_kinds=("box", "auto_attr", "layer_snapshot"),
        )
        self.winfo_toplevel().wait_window(dlg)
        rows = dlg.result
        specials = dlg.result_specials
        if not rows and not specials:
            return

        if rows:
            groups = self.side_cfg["groups"]
            if not groups:
                groups.append(palette_config.new_group())
            gi = self.selected[0] if self.selected is not None else 0
            gi = min(gi, len(groups) - 1)
            insert_at = self.selected[1] + 1 if self.selected is not None and self.selected[0] == gi else len(groups[gi]["buttons"])

            last_index = insert_at
            known_icons = set(palette_config.list_all_icon_names())
            for row in rows:
                default_color = (
                    palette_config.SUB_COMMAND_DEFAULT_COLOR
                    if row.get("command_kind") == "サブ"
                    else palette_config.DEFAULT_COLOR
                )
                default_icon = row.get("default_icon") or palette_config.NO_ICON
                if default_icon not in known_icons:
                    default_icon = palette_config.NO_ICON
                new_btn = palette_config.new_button(
                    row["command_id"], row["toolbar_name"], icon=default_icon, color=default_color
                )
                groups[gi]["buttons"].insert(insert_at, new_btn)
                insert_at += 1
                last_index = insert_at - 1

            # 👑 self.selectedだけ更新しても_rebuild_groups()が古い
            # self._selected_group/_selected_indicesを元に選択を復元して
            # 上書きしてしまう不具合があったため、3つとも合わせて更新する
            # (ユーザー報告: 「すべてが前の状態に戻ってるよ」)。
            # 👑 複数個まとめて選択状態にすると_select_multi()が
            # self.selectedをNoneにしてしまう(単一タプルで表せないため)。
            # このあと特殊行(箱/線属性ボタン)の追加がself.selectedに
            # 依存するので、最後の1個だけを単一選択にしておく。
            self.selected = (gi, last_index)
            self._selected_group = gi
            self._selected_indices = [last_index]
            self._rebuild_groups()

        # 👑 実コマンドの追加を終えてから、特殊行(箱/線属性ボタン)を順に
        # 作る(名前入力を挟むため、まとめての多重選択とは別処理になる)。
        for key in specials:
            if key == "box":
                self._on_add_box()
            elif key == "auto_attr":
                self._on_add_auto_attr()
            elif key == "layer_snapshot":
                self._on_add_layer_snapshot()

    def _on_remove(self):
        if self._selected_group is None or not self._selected_indices:
            return
        gi = self._selected_group
        buttons = self.side_cfg["groups"][gi]["buttons"]
        indices = sorted(i for i in self._selected_indices if i < len(buttons))
        if not indices:
            return
        if len(indices) == 1:
            msg = f"「{buttons[indices[0]]['name']}」を削除しますか?"
        else:
            names = "、".join(buttons[i]["name"] for i in indices)
            msg = f"{len(indices)}個({names})を削除しますか?"
        if not messagebox.askyesno("確認", msg, parent=self.winfo_toplevel()):
            return
        for i in reversed(indices):
            buttons.pop(i)
        self.selected = None
        self._selected_group = None
        self._selected_indices = []
        self._rebuild_groups()

    def _on_add_box(self):
        # 👑 「先に空のフライアウト箱を作って、あとから中身を詰める」
        # フロー。マクロ型は後回しなので、ここでは種別を聞かずフライアウト
        # 固定にする(ユーザー決定: 2026-08-31/2026-09-01)。
        dlg = TextInputDialog(self.winfo_toplevel(), title="グループボタンを追加", label="名前:", initial="新しいグループ")
        self.winfo_toplevel().wait_window(dlg)
        name = dlg.result
        if not name:
            return

        groups = self.side_cfg["groups"]
        if not groups:
            groups.append(palette_config.new_group())
        gi = self.selected[0] if self.selected is not None else 0
        gi = min(gi, len(groups) - 1)
        insert_at = self.selected[1] + 1 if self.selected is not None and self.selected[0] == gi else len(groups[gi]["buttons"])

        new_btn = palette_config.new_group_button(name, palette_config.BUTTON_KIND_FLYOUT, [])
        groups[gi]["buttons"].insert(insert_at, new_btn)
        # 👑 self.selectedだけ更新しても、_rebuild_groups()は
        # self._selected_group/_selected_indices(以前の選択)を元に選択を
        # 復元してしまい、せっかく指したはずの新規ボタンが元の選択に
        # 上書きされて消えてしまう不具合があった(ユーザー報告:「新しい
        # グループつくっても設定画面開かないよ」「すべてが前の状態に
        # 戻ってるよ」)。3つとも合わせて更新する。
        self.selected = (gi, insert_at)
        self._selected_group = gi
        self._selected_indices = [insert_at]
        self._rebuild_groups()
        # 👑 「中身を編集…」ボタンの位置が分かりにくいという指摘のため、
        # 箱を作った流れのまま、名前を決めたら続けて中身編集を開く。
        self._on_edit_group()

    def _on_add_auto_attr(self):
        # 👑 「補助線」「配線」等(kind="auto_attr")の追加。既定値は補助線色/
        # 補助線種(jw_cad標準プリセット)にしておき、配線等で使う場合は
        # 追加後に詳細パネルの線色・線種から選び直してもらう想定
        # (doc/補助線ボタン_要件書.md参照: 標準プリセットが無いので
        # ユーザーが決める方針)。
        dlg = TextInputDialog(self.winfo_toplevel(), title="モードボタンを追加", label="名前:", initial="補助線")
        self.winfo_toplevel().wait_window(dlg)
        name = dlg.result
        if not name:
            return

        groups = self.side_cfg["groups"]
        if not groups:
            groups.append(palette_config.new_group())
        gi = self.selected[0] if self.selected is not None else 0
        gi = min(gi, len(groups) - 1)
        insert_at = self.selected[1] + 1 if self.selected is not None and self.selected[0] == gi else len(groups[gi]["buttons"])

        new_btn = palette_config.new_auto_attr_button(name, horizontal_vertical=True)
        groups[gi]["buttons"].insert(insert_at, new_btn)
        self.selected = (gi, insert_at)
        self._selected_group = gi
        self._selected_indices = [insert_at]
        self._rebuild_groups()

    def _on_add_layer_snapshot(self):
        # 👑 「電灯配線図」のようなレイヤ状態の保存/復元ボタン(kind=
        # "layer_snapshot")の追加。2026-09-04の設計変更: 保存ボタンは
        # 名前を持たない汎用の1個のみをここで作る(「保存ボタんは1個で
        # 復元ボタンをたくさん」「保存の度に名前を付けたい」という
        # ユーザー要望)。名前を聞くのも、名前ごとに復元ボタンを新設
        # するのも、押した瞬間(main.py: _start_layer_snapshot_save)に
        # 動的に行う。
        new_btn = palette_config.new_layer_snapshot_button(
            "ﾚｲﾔ\n保存", palette_config.LAYER_SNAPSHOT_ROLE_SAVE,
        )
        groups = self.side_cfg["groups"]
        if not groups:
            groups.append(palette_config.new_group())
        gi = self.selected[0] if self.selected is not None else 0
        gi = min(gi, len(groups) - 1)
        insert_at = self.selected[1] + 1 if self.selected is not None and self.selected[0] == gi else len(groups[gi]["buttons"])
        groups[gi]["buttons"].insert(insert_at, new_btn)
        self.selected = (gi, insert_at)
        self._selected_group = gi
        self._selected_indices = [insert_at]
        self._rebuild_groups()

    def _on_edit_group(self):
        btn = self._selected_button()
        if btn is None or btn.get("kind") not in (palette_config.BUTTON_KIND_FLYOUT, palette_config.BUTTON_KIND_MACRO):
            return
        dlg = GroupContentsDialog(
            self.winfo_toplevel(), btn.get("sub_buttons") or [], manager_ref=self.manager_ref,
            swatch_cache=self.swatch_cache,
        )
        self.winfo_toplevel().wait_window(dlg)
        if dlg.result is not None:
            btn["sub_buttons"] = dlg.result
            self._load_detail()

    def _on_ungroup(self):
        btn = self._selected_button()
        if btn is None or btn.get("kind") not in (palette_config.BUTTON_KIND_FLYOUT, palette_config.BUTTON_KIND_MACRO):
            return
        gi, ii = self.selected
        sub_buttons = btn.get("sub_buttons") or []
        if sub_buttons and not messagebox.askyesno(
            "確認",
            f"「{btn['name']}」を解除して、中の{len(sub_buttons)}個を個別ボタンに戻しますか?",
            parent=self.winfo_toplevel(),
        ):
            return
        buttons = self.side_cfg["groups"][gi]["buttons"]
        buttons[ii:ii + 1] = [dict(sb) for sb in sub_buttons]
        self.selected = None
        self._selected_group = None
        self._selected_indices = []
        self._rebuild_groups()

    def _on_add_group(self):
        # 👑 新しい列を作った直後、選択状態(self.selected等)を更新して
        # いなかったため、そのままボタンを追加すると古い(前から選択中の)
        # 列に入ってしまっていた(ユーザー報告:「新しい列にボタンを直接
        # 配置できない」)。新しい列を選択済み状態にする。
        groups = self.side_cfg["groups"]
        groups.append(palette_config.new_group())
        new_gi = len(groups) - 1
        self.selected = (new_gi, -1)
        self._selected_group = new_gi
        self._selected_indices = []
        self._rebuild_groups()

    def _on_remove_group(self):
        groups = self.side_cfg["groups"]
        if len(groups) <= 1:
            messagebox.showwarning("削除できません", f"{self._group_noun()}は最低1つ必要です。", parent=self.winfo_toplevel())
            return
        gi = self.selected[0] if self.selected is not None else len(groups) - 1
        target = groups[gi]
        if target["buttons"]:
            if not messagebox.askyesno(
                "確認",
                f"{self._group_noun()} {gi + 1} には{len(target['buttons'])}個のボタンがあります。まとめて削除しますか?",
                parent=self.winfo_toplevel(),
            ):
                return
        groups.pop(gi)
        self.selected = None
        self._rebuild_groups()

    def commit_scalars(self):
        self.side_cfg["orientation"] = self.orient_var.get()
        self._on_size()


class RightClickMenuPanel(ttk.Frame):
    """パレット右クリックメニューの項目ごとのON/OFF設定タブ。
    「⚙️ 編集」だけは常に表示なのでここには出さない(消せない)。"""

    def __init__(self, master):
        super().__init__(master)
        prefs = menu_prefs.load_prefs()
        self.vars = {key: tk.BooleanVar(value=prefs.get(key, True)) for key in menu_prefs.ITEM_KEYS}

        ttk.Label(
            self, text="右クリックメニューに表示する項目を選んでください。\n"
                       "(「⚙️ 編集」は常に表示されます)",
            justify="left",
        ).pack(side="top", anchor="w", padx=12, pady=(12, 8))

        for key in menu_prefs.ITEM_KEYS:
            ttk.Checkbutton(
                self, text=menu_prefs.ITEM_LABELS[key], variable=self.vars[key],
            ).pack(side="top", anchor="w", padx=16, pady=3)

    def save(self):
        menu_prefs.save_prefs({key: var.get() for key, var in self.vars.items()})


class SettingsWindow(tk.Toplevel):
    def __init__(self, master, manager_ref=None, initial_side="左"):
        super().__init__(master)
        self.manager_ref = manager_ref
        self.title("⚙️ JwNavigator パレット設定")
        # 👑 group_frame(箱用)とauto_attr_frame(補助線系用)を排他的に
        # grid()/grid_remove()する方式に変更し、選んでいない方の分の
        # 無駄な縦スペースが無くなった(以前は両方を常時disabled表示で
        # 確保していたため、ボタンを選ぶたびに設定ウィンドウが必要以上に
        # 縦長になり、保存/キャンセルが枠外に押し出される不具合を繰り返
        # していた)。auto_attr側も1行に集約したため、以前の800x700より
        # 低くできる。
        self.geometry("800x680")
        self.minsize(720, 620)
        self.configure(bg="#f0f0f0")
        self.attributes("-topmost", True)

        self.config_data = palette_config.clone_config(palette_config.load_config())
        self.panels = {}
        # 👑 「見本で選ぶ…」の直近の読み込み結果のキャッシュ。以前は
        # このSettingsWindow自身が{"data": None}を毎回新規に持っていた
        # ため、設定画面を閉じて開き直すとキャッシュが消えていた(「2回目
        # に線属性設定するとき、見本から選ぶがキャッシュされてないよ」)。
        # manager_ref(main.pyのアプリ本体、app全体で1つだけ生きている)
        # 側のキャッシュをそのまま参照することで、設定画面を開き直しても
        # 前回の読み込み結果を使い回せるようにする。
        self.swatch_cache = getattr(self.manager_ref, "swatch_cache", None)
        if self.swatch_cache is None:
            self.swatch_cache = {"data": None}

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(side="top", fill="both", expand=True, padx=8, pady=(8, 0))

        # 👑 「N枚パレット見越してパレット名だけ変えとこうか」への対応。
        # 内部の"左"/"右"(config構造・ドッキング側の判定にそのまま使う
        # 実データ)は変えず、この設定画面のタブ表示名だけ「パレット1」
        # 「パレット2」に変える(将来N枚に増えても番号がそのまま使える)。
        tab_labels = {side: f"パレット{i + 1}" for i, side in enumerate(palette_config.SIDES)}

        for side in palette_config.SIDES:
            side_cfg = palette_config.side_config(self.config_data, side)
            panel = SidePanel(self.notebook, side, side_cfg, manager_ref=self.manager_ref, swatch_cache=self.swatch_cache)
            self.notebook.add(panel, text=tab_labels[side])
            self.panels[side] = panel

        self.menu_panel = RightClickMenuPanel(self.notebook)
        self.notebook.add(self.menu_panel, text="右クリック")

        footer = ttk.Frame(self)
        footer.pack(side="top", fill="x", padx=8, pady=10)
        ttk.Button(footer, text="保存", command=self._on_save, width=14).pack(side="right", ipady=4)
        ttk.Button(footer, text="キャンセル", command=self._on_cancel, width=14).pack(side="right", padx=(0, 8), ipady=4)

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.select_tab(initial_side)

    def select_tab(self, side):
        # 👑 右パレットの右クリックから開いた時は右パレットのタブから
        # 始まってほしい、というユーザー要望に対応（既存ウィンドウを
        # 再利用する場合も同様に切り替える）。
        panel = self.panels.get(side)
        if panel is not None:
            self.notebook.select(panel)

    def _on_cancel(self):
        self.destroy()

    def _on_save(self):
        for panel in self.panels.values():
            panel.commit_scalars()
        self.menu_panel.save()

        new_config = palette_config.normalize_config(self.config_data)

        total = sum(palette_config.count_buttons(new_config["sides"][s]) for s in palette_config.SIDES)
        if total == 0:
            messagebox.showwarning("保存できません", "ボタンが1つも登録されていません。", parent=self)
            return

        try:
            palette_config.save_config(new_config)
        except OSError as e:
            messagebox.showerror("保存エラー", f"config.json の保存に失敗しました。\n{e}", parent=self)
            return

        if self.manager_ref is not None:
            try:
                self.manager_ref.reload_all_palettes()
            except Exception as e:
                print(f"[WARN] reload_all_palettes failed: {e}")

        self.destroy()
# ===== ✂️ widgets/settings_window.py END ✂️ =====
