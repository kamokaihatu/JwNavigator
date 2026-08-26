# ===== ✂️ widgets/settings_window.py START ✂️ =====
import colorsys
import re
import tkinter as tk
from tkinter import ttk, messagebox

from utils import palette_config, command_master

ICON_NONE_LABEL = "アイコンなし"
_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _is_valid_hex_color(value):
    return bool(_HEX_COLOR_RE.match(value or ""))


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


class CommandPickerDialog(tk.Toplevel):
    """コマンド追加ダイアログ。選択されたコマンド一覧をself.resultに残す。"""

    def __init__(self, master, existing_ids=None):
        super().__init__(master)
        self.result = []
        self._existing_ids = existing_ids or set()
        self._all_rows = command_master.list_available_commands()
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

        self.listbox.delete(0, tk.END)
        for row in self.filtered:
            suffix = " ※配置済" if row["command_id"] in self._existing_ids else ""
            text = f"{row['command_id']}  {row['toolbar_name']}  ({row['command_kind']}/{row['category']}){suffix}"
            self.listbox.insert(tk.END, text)

    def _on_ok(self, event=None):
        indices = self.listbox.curselection()
        self.result = [self.filtered[i] for i in indices]
        self.destroy()

    def _on_cancel(self):
        self.result = []
        self.destroy()


class SidePanel(ttk.Frame):
    def __init__(self, master, side, side_cfg):
        super().__init__(master)
        self.side = side
        self.side_cfg = side_cfg
        self.selected = None
        self._selected_group = None
        self._selected_indices = []
        self.list_widgets = []
        self._loading_detail = False

        self.icon_choices = [ICON_NONE_LABEL] + palette_config.list_icon_modules()
        self.icon_value_map = {ICON_NONE_LABEL: palette_config.NO_ICON}
        self.icon_value_map.update({m: m for m in palette_config.list_icon_modules()})
        self.icon_label_map = {v: k for k, v in self.icon_value_map.items()}

        self.orient_var = tk.StringVar(value=side_cfg["orientation"])
        self.size_var = tk.IntVar(value=side_cfg["button_size"])
        self.cmd_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.icon_var = tk.StringVar()

        self._build_shape_bar()
        self._build_layout_area()
        self._build_detail_form()

        self.name_var.trace_add("write", self._on_name_changed)
        self.icon_var.trace_add("write", self._on_icon_changed)

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
        ttk.Label(lf, textvariable=self.cmd_var).grid(row=0, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(lf, text="表示名:").grid(row=1, column=0, sticky="e", padx=6, pady=4)
        self.name_entry = ttk.Entry(lf, textvariable=self.name_var, width=18)
        self.name_entry.grid(row=1, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(lf, text="アイコン:").grid(row=2, column=0, sticky="e", padx=6, pady=4)
        self.icon_combo = ttk.Combobox(lf, textvariable=self.icon_var, values=self.icon_choices,
                                        state="readonly", width=18)
        self.icon_combo.grid(row=2, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(lf, text="背景色:").grid(row=3, column=0, sticky="e", padx=6, pady=4)
        color_frame = ttk.Frame(lf)
        color_frame.grid(row=3, column=1, sticky="w", padx=6, pady=4)
        self.color_swatch = tk.Label(color_frame, width=4, relief="solid", bd=1, bg=palette_config.DEFAULT_COLOR)
        self.color_swatch.pack(side="left")
        self.pick_color_btn = ttk.Button(color_frame, text="色を選ぶ…", command=self._on_pick_color)
        self.pick_color_btn.pack(side="left", padx=6)
        self.reset_color_btn = ttk.Button(color_frame, text="既定に戻す", command=self._on_reset_color)
        self.reset_color_btn.pack(side="left")
        ttk.Label(lf, text="(リストでCtrl/Shiftクリックすると複数選択してまとめて色変更できます)",
                  foreground="#888888").grid(row=4, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 4))

        self._set_detail_enabled(False, False)

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
        # 👑 色のまとめ変更のため、複数選択(extended)の全ボタンを返す。
        # 名前/アイコン編集は単一選択時のみ意味があるので_selected_button()
        # (単一)は引き続き使う。
        if self._selected_group is None or not self._selected_indices:
            return []
        groups = self.side_cfg["groups"]
        if self._selected_group >= len(groups):
            return []
        buttons = groups[self._selected_group]["buttons"]
        return [buttons[i] for i in self._selected_indices if i < len(buttons)]

    def _set_detail_enabled(self, name_icon_enabled, color_enabled):
        state = "readonly" if name_icon_enabled else "disabled"
        self.name_entry.configure(state=("normal" if name_icon_enabled else "disabled"))
        self.icon_combo.configure(state=state)
        color_state = "normal" if color_enabled else "disabled"
        self.pick_color_btn.configure(state=color_state)
        self.reset_color_btn.configure(state=color_state)

    def _load_detail(self):
        self._loading_detail = True
        try:
            multi = self._selected_buttons()
            btn = self._selected_button()
            if btn is None and len(multi) <= 1:
                self.cmd_var.set("")
                self.name_var.set("")
                self.icon_var.set("")
                self.color_swatch.configure(bg=palette_config.DEFAULT_COLOR)
                self._set_detail_enabled(False, False)
                return
            if btn is not None:
                row = command_master.get_by_command_id(btn["command_id"]) or {}
                category = (row.get("category") or "").strip()
                self.cmd_var.set(f"{btn['command_id']} ({category})" if category else btn["command_id"])
                self.name_var.set(btn["name"])
                self.icon_var.set(self.icon_label_map.get(btn["icon"], ICON_NONE_LABEL))
                self.color_swatch.configure(bg=btn["color"])
                self._set_detail_enabled(True, True)
            else:
                # 複数選択中: 名前・アイコンは編集不可、色だけまとめて変更可能
                self.cmd_var.set(f"{len(multi)}個選択中")
                self.name_var.set("")
                self.icon_var.set("")
                self.color_swatch.configure(bg=multi[0]["color"])
                self._set_detail_enabled(False, True)
        finally:
            self._loading_detail = False

    def _select(self, group_index, item_index):
        self.selected = (group_index, item_index)
        self._selected_group = group_index
        self._selected_indices = [item_index]
        for i, lb in enumerate(self.list_widgets):
            lb.selection_clear(0, tk.END)
        if group_index < len(self.list_widgets):
            self.list_widgets[group_index].selection_set(item_index)
            self.list_widgets[group_index].activate(item_index)
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
            lb = tk.Listbox(gf, exportselection=0, height=18, width=14, selectmode="extended",
                             font=("Meiryo UI", 9), activestyle="none")
            scroll = ttk.Scrollbar(gf, orient="vertical", command=lb.yview)
            lb.configure(yscrollcommand=scroll.set)
            lb.pack(side="left", fill="both", expand=True)
            scroll.pack(side="right", fill="y")
            for btn in group["buttons"]:
                lb.insert(tk.END, btn["name"])
            lb.bind("<<ListboxSelect>>", lambda e, gi=i: self._on_select(gi))
            self.list_widgets.append(lb)

        if self.selected is not None:
            gi, ii = self.selected
            if gi < len(self.list_widgets) and ii < len(groups[gi]["buttons"]):
                self._select(gi, ii)
            else:
                self.selected = None
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

    def _on_icon_changed(self, *args):
        if self._loading_detail:
            return
        btn = self._selected_button()
        if btn is None:
            return
        btn["icon"] = self.icon_value_map.get(self.icon_var.get(), palette_config.NO_ICON)

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
        if self.selected is None:
            return
        gi, ii = self.selected
        buttons = self.side_cfg["groups"][gi]["buttons"]
        if ii <= 0:
            return
        buttons[ii - 1], buttons[ii] = buttons[ii], buttons[ii - 1]
        self.selected = (gi, ii - 1)
        self._rebuild_groups()

    def _move_down(self):
        if self.selected is None:
            return
        gi, ii = self.selected
        buttons = self.side_cfg["groups"][gi]["buttons"]
        if ii >= len(buttons) - 1:
            return
        buttons[ii + 1], buttons[ii] = buttons[ii], buttons[ii + 1]
        self.selected = (gi, ii + 1)
        self._rebuild_groups()

    def _move_prev_group(self):
        if self.selected is None:
            return
        gi, ii = self.selected
        if gi <= 0:
            return
        groups = self.side_cfg["groups"]
        btn = groups[gi]["buttons"].pop(ii)
        target = groups[gi - 1]["buttons"]
        new_index = min(ii, len(target))
        target.insert(new_index, btn)
        self.selected = (gi - 1, new_index)
        self._rebuild_groups()

    def _move_next_group(self):
        if self.selected is None:
            return
        gi, ii = self.selected
        groups = self.side_cfg["groups"]
        if gi >= len(groups) - 1:
            return
        btn = groups[gi]["buttons"].pop(ii)
        target = groups[gi + 1]["buttons"]
        new_index = min(ii, len(target))
        target.insert(new_index, btn)
        self.selected = (gi + 1, new_index)
        self._rebuild_groups()

    # ---- 追加・削除 ----

    def _existing_ids(self):
        ids = set()
        for group in self.side_cfg["groups"]:
            for btn in group["buttons"]:
                ids.add(btn["command_id"])
        return ids

    def _on_add(self):
        dlg = CommandPickerDialog(self.winfo_toplevel(), existing_ids=self._existing_ids())
        self.winfo_toplevel().wait_window(dlg)
        rows = dlg.result
        if not rows:
            return

        groups = self.side_cfg["groups"]
        if not groups:
            groups.append(palette_config.new_group())
        gi = self.selected[0] if self.selected is not None else 0
        gi = min(gi, len(groups) - 1)
        insert_at = self.selected[1] + 1 if self.selected is not None and self.selected[0] == gi else len(groups[gi]["buttons"])

        last_index = insert_at
        for row in rows:
            new_btn = palette_config.new_button(row["command_id"], row["toolbar_name"])
            groups[gi]["buttons"].insert(insert_at, new_btn)
            insert_at += 1
            last_index = insert_at - 1

        self.selected = (gi, last_index)
        self._rebuild_groups()

    def _on_remove(self):
        if self.selected is None:
            return
        gi, ii = self.selected
        groups = self.side_cfg["groups"]
        buttons = groups[gi]["buttons"]
        if ii >= len(buttons):
            return
        if not messagebox.askyesno("確認", f"「{buttons[ii]['name']}」を削除しますか?", parent=self.winfo_toplevel()):
            return
        buttons.pop(ii)
        self.selected = None
        self._rebuild_groups()

    def _on_add_group(self):
        self.side_cfg["groups"].append(palette_config.new_group())
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


class SettingsWindow(tk.Toplevel):
    def __init__(self, master, manager_ref=None):
        super().__init__(master)
        self.manager_ref = manager_ref
        self.title("⚙️ JwNavigator パレット設定")
        self.geometry("800x700")
        self.minsize(720, 620)
        self.configure(bg="#f0f0f0")
        self.attributes("-topmost", True)

        self.config_data = palette_config.clone_config(palette_config.load_config())
        self.panels = {}

        notebook = ttk.Notebook(self)
        notebook.pack(side="top", fill="both", expand=True, padx=8, pady=(8, 0))

        for side in palette_config.SIDES:
            side_cfg = palette_config.side_config(self.config_data, side)
            panel = SidePanel(notebook, side, side_cfg)
            notebook.add(panel, text=f"{side}パレット")
            self.panels[side] = panel

        footer = ttk.Frame(self)
        footer.pack(side="top", fill="x", padx=8, pady=10)
        ttk.Button(footer, text="保存", command=self._on_save, width=14).pack(side="right", ipady=4)
        ttk.Button(footer, text="キャンセル", command=self._on_cancel, width=14).pack(side="right", padx=(0, 8), ipady=4)

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _on_cancel(self):
        self.destroy()

    def _on_save(self):
        for panel in self.panels.values():
            panel.commit_scalars()

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
