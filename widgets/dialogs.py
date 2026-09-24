# ===== ✂️ widgets/dialogs.py START ✂️ =====
"""
設定画面から開く各種ダイアログと、その描画ヘルパー。

👑 2026-09-16: widgets/settings_window.py(2,889行)から切り出した。
依存関係を調べたところ、6つのダイアログは**どれもSidePanel/SettingsWindow
を参照しておらず**(=葉)、参照は`SidePanel → ダイアログ`の一方向だけだった
ため、循環importにならずそのまま移せる。GroupContentsDialogだけは他の
ダイアログを開くが、それらも全部この中にある。

**動作は一切変えていない**。クラス本体は1文字も変えず、行範囲ごと移した。
"""
import colorsys
import importlib
import os
import re
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

from utils import palette_config, command_master, line_attr_dialog
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

    # 👑 2026-09-09: cowork製の追加アイコン(v2/汎用156個)を取り込んだ結果、
    # 検索文字を打たないと選びづらいほど数が増えた。「コマンド追加ダイアログ
    # みたいにチェックボックスで分類したい」という要望を受け、単発ボタン
    # (検索文字を差し替えるだけ)だったカテゴリ絞り込みを、
    # CommandPickerDialogの種別/分類チェックボックスと同じ方式
    # (複数同時ON/OFF、BooleanVarを値ごとに持つ)に置き換えた。
    # プレフィックスはファイル名の命名規則そのもの。
    CATEGORY_PREFIXES = [
        ("コマンド風", "sample_cmd_"),
        ("派手", "sample_emoji_"),
        ("落ち着いた", "sample_stylish_"),
        ("かわいい", "sample_cute_"),
        ("かっこいい", "sample_cool_"),
        ("UI", "ui_"),
        ("天気", "weather_"),
        ("機器", "device_"),
        ("物", "object_"),
        ("文房具", "stationery_"),
        ("動物", "animal_"),
        ("食べ物", "food_"),
        ("乗り物", "vehicle_"),
        ("自然", "nature_"),
    ]

    # 👑 2026-09-09: コマンド専用アイコンのうち、今回cowork製で追加された
    # 一式(既存の代替は"<元名>_v2"、ギャップ埋めは新規名)を「V2」として
    # 明示的に分類する。プレフィックスでは判別できない(元の名前をそのまま
    # 引き継ぐ新規分もあるため)ので、名前の集合で直接判定する。それ以外の
    # コマンド専用アイコン(元からあったもの)は「V1」として一括りにする。
    V2_ICON_NAMES = frozenset({
        "auto_v2", "basic_settings_v2", "bl_break_v2", "bl_edit_v2", "bl_make_v2",
        "center_point_v2", "center_v2", "chamfer_v2", "circle_v2", "cleanup_v2",
        "clip_copy_v2", "coordinate", "copy_v2", "corner_v2", "curve_v2", "cut_v2",
        "delete_v2", "dim_diagram", "dim_diagram_solve", "dimension_v2",
        "distance_point", "divide_line_v2", "external_transform", "file_new_v2",
        "file_open_v2", "file_overwrite_v2", "file_save_v2", "formula_calc",
        "get_attribute_v2", "hatch_v2", "image_edit_v2", "interval", "line_2_v2",
        "line_angle", "line_attribute", "line_length", "line_v2", "measure_v2",
        "move_v2", "origin_v2", "parametric", "paste_v2", "point_on_line",
        "point_v2", "polygon_v2", "polyline_v2", "print_out_v2",
        "quarter_circle_point_v2", "range_v2", "rect_v2", "redo_v2",
        "selection_diagram", "shadow_diagram_v2", "shape_register", "shape_v2",
        "sky_diagram_v2", "solid_v2", "speed_v2", "spreadsheet_v2", "stretch_v2",
        "tag_jump_v2", "text_v2", "two_point_angle", "two_point_five_d",
        "two_point_length", "undo_v2", "vertical_angle", "x_axis_angle",
    })
    OTHER_CATEGORY_LABEL = "V1"
    V2_CATEGORY_LABEL = "V2"

    def __init__(self, master, current_icon=None):
        super().__init__(master)
        self.result = None
        self._selected = current_icon or palette_config.NO_ICON
        self._image_refs = []
        self.title("アイコンを選ぶ")
        self.geometry("460x560")
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

        # 👑 分類チェックボックス(複数同時ON/OFF可能)。折り返しできるよう
        # 複数行のFrameに詰める(カテゴリ数が多いため単一行だと入り切らない)。
        # 数が増えて1個ずつ触るのが面倒という指摘があったため、全部ON/OFF
        # ボタンも添えてある。
        category_area = ttk.Frame(self)
        category_area.pack(side="top", fill="x", padx=8, pady=(0, 4))

        all_bar = ttk.Frame(category_area)
        all_bar.pack(side="top", fill="x", pady=(0, 2))
        ttk.Button(all_bar, text="全部ON", width=8, command=lambda: self._set_all_categories(True)).pack(side="left", padx=(0, 3))
        ttk.Button(all_bar, text="全部OFF", width=8, command=lambda: self._set_all_categories(False)).pack(side="left")

        # 👑 選択肢が一気に増えたため、開いた直後は見慣れた「V1」(元から
        # あったコマンド用アイコン)だけに絞っておく(ユーザー要望、
        # 2026-09-09)。他は必要な時だけチェックを入れて広げる想定。
        self.category_vars = {}
        row = None
        per_row = 5
        for i, (label, prefix) in enumerate(self.CATEGORY_PREFIXES):
            if i % per_row == 0:
                row = ttk.Frame(category_area)
                row.pack(side="top", fill="x")
            var = tk.BooleanVar(value=False)
            self.category_vars[prefix] = var
            ttk.Checkbutton(row, text=label, variable=var, command=self._rebuild_grid).pack(side="left", padx=3)
        self.v2_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, text=self.V2_CATEGORY_LABEL, variable=self.v2_var, command=self._rebuild_grid).pack(side="left", padx=3)
        self.other_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(row, text=self.OTHER_CATEGORY_LABEL, variable=self.other_var, command=self._rebuild_grid).pack(side="left", padx=3)

        # 👑 2026-09-14修正: footer(OK/キャンセル)は、fill="both",
        # expand=Trueのcontainerより**先に**side="bottom"でpackする
        # (SettingsWindowと同じ不具合・同じ理由。widgets/settings_window.py
        # のSettingsWindow.__init__のコメント参照)。
        footer = ttk.Frame(self)
        footer.pack(side="bottom", fill="x", padx=8, pady=8)
        ttk.Button(footer, text="OK", command=self._on_ok, width=10).pack(side="right")
        ttk.Button(footer, text="キャンセル", command=self._on_cancel, width=10).pack(side="right", padx=(0, 6))

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

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self._cell_widgets = []
        self._rebuild_grid()
        entry.focus_set()
        self.grab_set()

    def _set_all_categories(self, value):
        for var in self.category_vars.values():
            var.set(value)
        self.v2_var.set(value)
        self.other_var.set(value)
        self._rebuild_grid()

    def _category_visible(self, icon_name):
        for prefix, var in self.category_vars.items():
            if icon_name.startswith(prefix):
                return var.get()
        if icon_name in self.V2_ICON_NAMES:
            return self.v2_var.get()
        return self.other_var.get()

    def _rebuild_grid(self):
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self._cell_widgets = []
        self._image_refs = []

        query = self.query_var.get().strip().lower()
        names = [
            n for n in palette_config.list_all_icon_names()
            if query in n.lower() and self._category_visible(n)
        ]
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
            ttk.Label(self, text=note, anchor="center", justify="center").pack(padx=12, pady=(0, 8), fill="x")

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

    def __init__(self, master, hwnd, current_color=None, current_type=None, swatch_cache=None, sxf=False):
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
        # 👑 2026-09-24: 既定モードとSXFモードでは見本そのものが別物なので、
        # キャッシュもモード別に分ける(同じキーに入れると、片方を見た後に
        # もう片方を開いたとき前のモードの見本が出てしまう)。
        self._sxf = bool(sxf)
        self._cache_key = "data_sxf" if self._sxf else "data"
        self._cache = swatch_cache if swatch_cache is not None else {"data": None}
        cached = self._cache.get(self._cache_key)
        self._swatches = cached
        self._attempted = cached is not None

        self.title("線色・線種を見本から選ぶ")
        self.configure(bg="#f0f0f0")
        # 👑 2026-09-15訂正: このダイアログだけtransient()→topmostの順に
        # なっていた(他の全ダイアログ=ColorPickerDialog/IconPickerDialog/
        # CommandPickerDialog/GroupContentsDialogはtopmost→transientの順)。
        # Windows上、transient()確立時にラッパーHWNDが更新される挙動があり、
        # その後でtopmostを付けるとSettingsWindow(同じく-topmost)の裏に
        # 回ることがあった(実機報告)。他の全ダイアログと同じ順序に揃えた。
        self.attributes("-topmost", True)
        self.transient(master)
        self.resizable(False, False)

        self._body = None
        self._build_body()
        self._center_on_screen()

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.grab_set()
        # 👑 2026-09-14に追加したself.lift(master)は逆効果だった
        # (2026-09-15訂正): main.py内の実測コメント(パレットのZ順制御
        # 箇所)の通り、このシステムではSetWindowPos(hWndInsertAfter=X)が
        # 「Xの直後＝Xより背面」に置く動きになる。tkinterのlift(aboveThis)は
        # Windows側でこれと同じ仕組みのため、lift(master)は「masterの
        # 背面へ」自分を送っていた可能性が高い(=当時の修正が効かなかった
        # 理由)。引数無しのlift()(スタッキング順の最前面へ)に変更する。
        self.lift()
        self.focus_force()

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

    def _on_dialog_found(self, rect):
        # 👑 2026-09-15: GetPixelは画面の絶対座標を読むだけなので、自分の
        # 窓が線属性ダイアログ(rect)と重ならなければ、自分はtopmostの
        # ままで良い(読み取り中ずっと裏に隠れる必要が無い)。「せっかく
        # 1個ずつ更新しているのに、自分の窓が裏に回って見えないのは面白
        # くない」というユーザー指摘への対応。線属性ダイアログの右→左→
        # 下→上の順で、画面に収まる空きを探して自分をどける。どこにも
        # 収まらない極端な画面サイズの場合だけ、フォールバックの
        # topmost一旦解除(_load_and_build()のtry/finally)に任せる。
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        ox0, oy0, ox1, oy1 = rect
        candidates = [
            (ox1 + 10, oy0),
            (ox0 - 10 - w, oy0),
            (ox0, oy1 + 10),
            (ox0, oy0 - 10 - h),
        ]
        for x, y in candidates:
            if 0 <= x and x + w <= sw and 0 <= y and y + h <= sh:
                self.geometry(f"+{x}+{y}")
                return
        # 👑 どの向きにも収まらなかった(極端に小さい画面等)。この場合だけ
        # 従来通りtopmostを一旦外して道を譲る(重なったまま自分がtopmost
        # だと自分の背景を誤読するため)。
        self.attributes("-topmost", False)

    def _load_and_build(self):
        # 👑 【重大】自分自身をtopmostにしたままjw_cad本体の線属性ダイアログ
        # を開くと、本物のダイアログが自分の裏に隠れてしまい、GetPixelで
        # 自分自身の白い背景を読み取ってしまう(実機で発覚: 全部白/実線に
        # なる不具合)。以前はwithdraw()で自分を完全に消していたが、
        # 「ボタン押したら画面きえちゃうの？残しておけない？」への対応で、
        # 消す(withdraw)のではなくtopmostを一旦外すだけにしていた。
        # 👑 2026-09-15: さらに、_on_dialog_found()で線属性ダイアログと
        # 重ならない位置へ自分をどけられた場合は、topmostを外す必要
        # そのものが無くなった(重ならなければ何も隠れないため)。どけ
        # られなかった場合(_moved_for_capture=False)だけ、従来通り
        # topmostを一旦外して道を譲るフォールバックを使う。
        self.load_swatches_btn.configure(state="disabled", text="読み込み中…")
        self.load_swatches_note_var.set("(jw_cadの線属性ウィンドウが自動操作されています。触らずにお待ちください…)")
        try:
            t0 = time.time()
            # 👑 「読めたもの1個ずつ更新していけたら臨場感あるけどできそう？」
            # への対応。1項目読めるごとにon_color/on_typeコールバックで既存の
            # (今は空白の)マスをその場で塗り替えていく。既に画面には blank な
            # グリッドが出来上がっているので、全部読み終わった後で改めて
            # _build_body()し直す必要はない(成功時)。
            swatches = line_attr_dialog.capture_swatches(
                self._hwnd, on_color=self._update_color_swatch, on_type=self._update_type_swatch,
                on_dialog_found=self._on_dialog_found, sxf=self._sxf,
            )
            elapsed = time.time() - t0
            print(f"[LineAttrSwatchDialog] 読み取り: 成功={swatches is not None} 所要={elapsed:.2f}秒")
        finally:
            # 👑 2026-09-15訂正: 順序が逆(_center_on_screen()→topmost)だと、
            # Tk自身は.geometry()で正しい中央位置に動かしたと認識している
            # のに、直後のattributes("-topmost", True)でWindows側の実際の
            # ウィンドウ位置だけが動かす前の位置に巻き戻る不具合を実機の
            # デバッグログで確認した(self.geometry()の戻り値は正しい値なのに
            # win32のGetWindowRectでは元の位置のまま)。topmostを先に確定
            # させてから位置を決める順序に直した。
            self.attributes("-topmost", True)
            self._center_on_screen()
            # 👑 失敗時は_build_body()がボタン/注記ごと作り直すので不要だが、
            # 成功時はここで明示的に戻さないとボタンが「読み込み中…」の
            # まま固定されてしまう。
            self.load_swatches_btn.configure(state="normal", text="📥 線色・線種の読み込み")
            self.load_swatches_note_var.set("(10〜20秒程度かかります。線属性ウィンドウが開きますが、触らないでください。)")
        self._swatches = swatches
        self._attempted = True
        if swatches is not None:
            self._cache[self._cache_key] = swatches
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
            color_ids = (line_attr_dialog.SXF_COLOR_CTRL_IDS if self._sxf
                         else line_attr_dialog.COLOR_CTRL_IDS)
            type_ids = (line_attr_dialog.SXF_TYPE_CTRL_IDS if self._sxf
                        else line_attr_dialog.TYPE_CTRL_IDS)
            color_labels = (line_attr_dialog.SXF_COLOR_LABELS if self._sxf
                            else line_attr_dialog.COLOR_LABELS)
            type_labels = (line_attr_dialog.SXF_TYPE_LABELS if self._sxf
                           else line_attr_dialog.TYPE_LABELS)
            color_items = swatches["colors"] if swatches else [(cid, None) for cid in color_ids]
            type_items = swatches["types"] if swatches else [(cid, None) for cid in type_ids]

            ttk.Label(body, text="線色", font=("Meiryo UI", 9, "bold")).pack(side="top", anchor="w", padx=10, pady=(10, 2))
            color_frame = ttk.Frame(body)
            color_frame.pack(side="top", padx=10)
            for i, (cid, hex_color) in enumerate(color_items):
                label = color_labels[i]
                cell = self._build_color_cell(color_frame, cid, hex_color, label)
                cell.grid(row=0, column=i, padx=2, pady=2)

            ttk.Label(body, text="線種", font=("Meiryo UI", 9, "bold")).pack(side="top", anchor="w", padx=10, pady=(10, 2))
            type_frame = ttk.Frame(body)
            type_frame.pack(side="top", padx=10)
            for i, (cid, pattern) in enumerate(type_items):
                label = type_labels[i]
                cell = self._build_type_cell(type_frame, cid, pattern, label)
                cell.grid(row=i // 3, column=i % 3, padx=3, pady=3)

        # 👑 「線色・線種の更新じゃなくて読み込みにして。OKの上に少し
        # 大きめボタンで作ろう」への対応。初回読み込み・基本設定変更後の
        # 再読み込みを兼ねる、同じボタン一つだけ(常にOKのすぐ上に置く)。
        load_row = ttk.Frame(body)
        load_row.pack(side="top", fill="x", padx=10, pady=(6, 0))
        self.load_swatches_btn = ttk.Button(
            load_row, text="📥 線色・線種の読み込み", command=self._load_and_build,
        )
        self.load_swatches_btn.pack(fill="x", ipady=6)
        # 👑 2026-09-15: 実測で10秒を超えることがあり(このダイアログ自身が
        # 読み取り中は一時的にtopmostを譲ってjw_cad本体の裏に回るため
        # =_load_and_build()参照、GetPixelで自分の背景を誤読するのを防ぐ
        # ための正しい挙動)、「10秒程度」の表記だと待ちきれず「戻って
        # こない(壊れた)」と誤解されやすかった(実機でユーザーが誤解)。
        # 表記を実測値に合わせ、かつ二重押下/連打による多重実行を防ぐため
        # 読み込み中はボタン自体を無効化して分かりやすくする。
        self.load_swatches_note_var = tk.StringVar(
            value="(10〜20秒程度かかります。線属性ウィンドウが開きますが、触らないでください。)"
        )
        ttk.Label(
            body, textvariable=self.load_swatches_note_var,
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
        "layer_snapshot": "🧪 レイヤ保存(通常版・テスト用)",
        "layer_snapshot_fast": "🧪 レイヤ保存(要選択・テスト用)",
        "layer_snapshot_fast_auto": "➕ レイヤ保存(全自動)",
    }

    def __init__(self, master, existing_ids=None, special_kinds=(), test_kinds=()):
        super().__init__(master)
        self.result = []
        self.result_specials = []
        self._existing_ids = existing_ids or set()
        self._all_rows = command_master.list_available_commands()
        self._special_kinds = list(special_kinds)
        # 👑 2026-09-14: レイヤ保存は「全自動」だけを通常メニューに残し、
        # 通常版(低速だが確実)と要選択版は「普通は選ばない」テストモード
        # 的な位置づけに変更(ユーザー決定)。test_kindsに渡した種別は、
        # 「特殊」チェックだけでは出さず、追加の「テスト版も表示」
        # チェックを入れた時だけ一覧に混ぜる(削除はせず、選べる状態で
        # 隠しておく)。
        self._test_kinds = list(test_kinds)
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
        # 👑 2026-09-14: test_kinds(普段は隠しておきたい種別)は、既定OFFの
        # 別チェックボックスを追加した時だけ一覧に混ぜる。
        self.show_test_var = tk.BooleanVar(value=False)
        if self._test_kinds:
            ttk.Checkbutton(
                kind_bar, text="テスト版も表示", variable=self.show_test_var, command=self._apply_filter,
            ).pack(side="left", padx=4)

        cat_bar = ttk.Frame(self)
        cat_bar.pack(side="top", fill="x", padx=8, pady=(2, 6))
        ttk.Label(cat_bar, text="分類:").pack(side="left", padx=(0, 4))
        self.cat_vars = {}
        for cat in command_master.list_categories():
            var = tk.BooleanVar(value=True)
            self.cat_vars[cat] = var
            ttk.Checkbutton(cat_bar, text=cat, variable=var, command=self._apply_filter).pack(side="left", padx=4)

        # 👑 2026-09-14修正: footer(追加/キャンセル)は、fill="both",
        # expand=Trueのlist_frameより**先に**side="bottom"でpackする
        # (SettingsWindowと同じ不具合・同じ理由)。
        footer = ttk.Frame(self)
        footer.pack(side="bottom", fill="x", padx=8, pady=8)
        ttk.Button(footer, text="追加", command=self._on_ok, width=10).pack(side="right")
        ttk.Button(footer, text="キャンセル", command=self._on_cancel, width=10).pack(side="right", padx=(0, 6))

        list_frame = ttk.Frame(self)
        list_frame.pack(side="top", fill="both", expand=True, padx=8)
        self.listbox = tk.Listbox(list_frame, selectmode="extended", exportselection=0, font=("Meiryo UI", 9))
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.listbox.bind("<Double-Button-1>", self._on_ok)

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

        self._visible_specials = []
        if self.show_specials_var.get():
            self._visible_specials += self._special_kinds
            if self.show_test_var.get():
                self._visible_specials += self._test_kinds
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

        # 👑 2026-09-14修正: footer(OK/キャンセル)は、fill="both",
        # expand=Trueのbodyより**先に**side="bottom"でpackする
        # (SettingsWindowと同じ不具合・同じ理由。以前はbodyの後、detail等
        # を挟んだ末尾でpackしていたため、bodyが領域を使い切ってしまい
        # footerが下端で潰れる不具合があった)。
        footer = ttk.Frame(self)
        footer.pack(side="bottom", fill="x", padx=8, pady=8)
        ttk.Button(footer, text="OK", command=self._on_ok, width=10).pack(side="right")
        ttk.Button(footer, text="キャンセル", command=self._on_cancel, width=10).pack(side="right", padx=(0, 6))

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
        # 👑 2026-09-24: SidePanel側(widgets/settings_window.py)と同じ設定を
        # 箱の中身にも出す。ONにすると線色/線種が16色/15種のSXF側へ
        # 入れ替わる。**SXFには補助線色・補助線種が無い**点に注意。
        self.auto_attr_sxf_var = tk.BooleanVar()
        self.auto_attr_sxf_check = ttk.Checkbutton(
            auto_attr_frame, text="SXF", variable=self.auto_attr_sxf_var,
            command=self._on_auto_attr_sxf_toggled,
        )
        self.auto_attr_sxf_check.pack(side="left", padx=(0, 8))
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

        ttk.Label(auto_attr_frame2, text="コマンド:").pack(side="left")
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
                    # 👑 どちらの一覧の番号かはline_attr_sxfで決まる。
                    # 取り違えると添字がずれて別の線種が表示される
                    # (番号が重なっているので例外にもならない)。
                    sxf = bool(first.get("line_attr_sxf"))
                    color_ids, color_labels, type_ids, type_labels =                         palette_config.line_attr_choices(sxf)
                    self.auto_attr_sxf_var.set(sxf)
                    self.auto_attr_color_combo.configure(values=color_labels)
                    self.auto_attr_type_combo.configure(values=type_labels)
                    color_idx = color_ids.index(first["line_color"])
                    type_idx = type_ids.index(first["line_type"])
                    self.auto_attr_color_var.set(color_labels[color_idx])
                    self.auto_attr_type_var.set(type_labels[type_idx])
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
        # 👑 ラベルとIDは必ずline_attr_choices()から対で取る(個数が違う)。
        sxf = bool(self.auto_attr_sxf_var.get())
        color_ids, color_labels, type_ids, type_labels = palette_config.line_attr_choices(sxf)
        btn["line_attr_sxf"] = sxf
        try:
            color_idx = color_labels.index(self.auto_attr_color_var.get())
            btn["line_color"] = color_ids[color_idx]
        except ValueError:
            pass
        try:
            type_idx = type_labels.index(self.auto_attr_type_var.get())
            btn["line_type"] = type_ids[type_idx]
        except ValueError:
            pass
        btn["horizontal_vertical"] = self.auto_attr_hv_var.get()

    def _on_auto_attr_sxf_toggled(self):
        """SXFの切替で選択肢ごと入れ替える。👑 番号は一覧をまたいで意味が
        変わるので持ち越さず、その一覧の既定へ寄せて選び直してもらう。"""
        if self._loading_detail:
            return
        indices = self._selected_indices()
        if len(indices) != 1 or self._buttons[indices[0]].get("kind") != palette_config.BUTTON_KIND_AUTO_ATTR:
            return
        btn = self._buttons[indices[0]]
        sxf = bool(self.auto_attr_sxf_var.get())
        color_ids, color_labels, type_ids, type_labels = palette_config.line_attr_choices(sxf)
        btn["line_attr_sxf"] = sxf
        btn["line_color"] = (palette_config.SXF_DEFAULT_LINE_COLOR_CTRL_ID if sxf
                             else palette_config.DEFAULT_LINE_COLOR_CTRL_ID)
        btn["line_type"] = (palette_config.SXF_DEFAULT_LINE_TYPE_CTRL_ID if sxf
                            else palette_config.DEFAULT_LINE_TYPE_CTRL_ID)
        self.auto_attr_color_combo.configure(values=color_labels)
        self.auto_attr_type_combo.configure(values=type_labels)
        self.auto_attr_color_var.set(color_labels[color_ids.index(btn["line_color"])])
        self.auto_attr_type_var.set(type_labels[type_ids.index(btn["line_type"])])

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
            swatch_cache=self.swatch_cache, sxf=bool(btn.get("line_attr_sxf")),
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
# ===== ✂️ widgets/dialogs.py END ✂️ =====
