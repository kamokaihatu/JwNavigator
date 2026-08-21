# ===== ✂️ widgets/settings_window.py START ✂️ =====
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox

from utils import palette_config, command_master

ICON_NONE_LABEL = "アイコンなし"


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
        self.cat_var = tk.StringVar(value="すべて")

        filter_bar = ttk.Frame(self)
        filter_bar.pack(side="top", fill="x", padx=8, pady=6)
        ttk.Label(filter_bar, text="検索:").pack(side="left")
        entry = ttk.Entry(filter_bar, textvariable=self.query_var, width=24)
        entry.pack(side="left", padx=(4, 12))
        ttk.Label(filter_bar, text="分類:").pack(side="left")
        categories = ["すべて"] + command_master.list_categories()
        combo = ttk.Combobox(filter_bar, textvariable=self.cat_var, values=categories, state="readonly", width=10)
        combo.pack(side="left", padx=4)

        self.query_var.trace_add("write", self._apply_filter)
        self.cat_var.trace_add("write", self._apply_filter)

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
        cat = self.cat_var.get()
        self.filtered = []
        for row in self._all_rows:
            if cat != "すべて" and row["category"] != cat:
                continue
            if query and query not in row["command_id"].lower() and query not in row["toolbar_name"].lower():
                continue
            self.filtered.append(row)

        self.listbox.delete(0, tk.END)
        for row in self.filtered:
            suffix = " ※配置済" if row["command_id"] in self._existing_ids else ""
            text = f"{row['command_id']}  {row['toolbar_name']}  ({row['category']}){suffix}"
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
        ttk.Button(color_frame, text="色を選ぶ…", command=self._on_pick_color).pack(side="left", padx=6)
        ttk.Button(color_frame, text="既定に戻す", command=self._on_reset_color).pack(side="left")

        self._set_detail_enabled(False)

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

    def _set_detail_enabled(self, enabled):
        state = "readonly" if enabled else "disabled"
        self.name_entry.configure(state=("normal" if enabled else "disabled"))
        self.icon_combo.configure(state=state)

    def _load_detail(self):
        self._loading_detail = True
        try:
            btn = self._selected_button()
            if btn is None:
                self.cmd_var.set("")
                self.name_var.set("")
                self.icon_var.set("")
                self.color_swatch.configure(bg=palette_config.DEFAULT_COLOR)
                self._set_detail_enabled(False)
                return
            row = command_master.get_by_command_id(btn["command_id"]) or {}
            category = (row.get("category") or "").strip()
            self.cmd_var.set(f"{btn['command_id']} ({category})" if category else btn["command_id"])
            self.name_var.set(btn["name"])
            self.icon_var.set(self.icon_label_map.get(btn["icon"], ICON_NONE_LABEL))
            self.color_swatch.configure(bg=btn["color"])
            self._set_detail_enabled(True)
        finally:
            self._loading_detail = False

    def _select(self, group_index, item_index):
        self.selected = (group_index, item_index)
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
        self.selected = (group_index, sel[0])
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
            lb = tk.Listbox(gf, exportselection=0, height=18, width=14,
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
        btn = self._selected_button()
        if btn is None:
            return
        result = colorchooser.askcolor(color=btn.get("color", palette_config.DEFAULT_COLOR),
                                        parent=self.winfo_toplevel())
        if result and result[1]:
            btn["color"] = result[1]
            self.color_swatch.configure(bg=result[1])

    def _on_reset_color(self):
        btn = self._selected_button()
        if btn is None:
            return
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
        self.geometry("800x640")
        self.minsize(720, 560)
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
