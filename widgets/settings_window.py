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
# 👑 2026-09-16: ダイアログ群はwidgets/dialogs.pyへ切り出した(依存は
# SidePanel→ダイアログの一方向だけなので循環importにならない)。
from widgets.side_panel_edit import SidePanelEditMixin
from widgets.dialogs import (
    ICON_NONE_LABEL, draw_icon_thumbnail, _get_jw_hwnd, _is_valid_hex_color,
    ColorPickerDialog, IconPickerDialog, TextInputDialog, LineAttrSwatchDialog,
    CommandPickerDialog, GroupContentsDialog,
)























# 👑 2026-09-16: 一覧の編集操作(追加/削除/並べ替え/グループ化)は
# widgets/side_panel_edit.py へ切り出した(動作は変えていない)。
class SidePanel(SidePanelEditMixin, ttk.Frame):
    def __init__(self, master, side, side_cfg, manager_ref=None, swatch_cache=None, config_data=None):
        super().__init__(master)
        self.side = side
        self.side_cfg = side_cfg
        self.manager_ref = manager_ref
        self.swatch_cache = swatch_cache if swatch_cache is not None else {"data": None}
        # 👑 ドッキング位置(edges/positions)はside_cfg(このパレット単体の
        # 辞書)ではなくconfig全体の直下にあるため、参照を別途持つ
        # (「ボタン詳細」の右に置いてほしいという要望で、この場所=
        # SidePanel内から書き換えられるようにする必要があった、2026-09-10)。
        self.config_data = config_data
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
        # 👑 2026-09-14修正: _build_detail_form()(固定高さの「ボタン詳細」)
        # を、fill="both", expand=Trueの_build_layout_area()(「ボタン
        # 配置」一覧)より**先に**呼ぶ(SettingsWindow等と同じ不具合・同じ
        # 理由)。ただし見た目の上下は変えたくない(一覧が上、詳細が下の
        # まま)ため、_build_detail_form()側のwrapperをside="bottom"で
        # packするよう変更してある(呼び出し順を変えても、下端に固定表示
        # されたまま)。
        self._build_detail_form()
        self._build_layout_area()
        self._update_dock_selector()

        self.name_var.trace_add("write", self._on_name_changed)

        self._rebuild_groups()

    def _update_dock_selector(self):
        if self.config_data is None:
            return
        edge = self.config_data.get("edges", {}).get(self.side)
        position = self.config_data.get("positions", {}).get(self.side)
        self.dock_picker.set_selected(edge, position)
        self.dock_status_label.configure(text=_dock_label_for(edge, position))

    def _on_dock_pick(self, edge, position):
        if self.config_data is None:
            return
        palette_config.set_dock_position(self.config_data, self.side, edge, position)
        self.dock_status_label.configure(text=_dock_label_for(edge, position))

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

        # 👑 2026-09-14修正: ops(▲▼◀▶追加削除＋行/列－行/列)は、
        # fill="both", expand=Trueのgroups_hostより**先に**side="right"で
        # packする(SettingsWindow等と同じ不具合・同じ理由。今回は横方向
        # で発生: 行数が増えてgroups_hostの内容が横に伸びると、後から
        # packされていたopsの取り分が無くなり、右側のボタンが全て見えなく
        # なっていた、実機確認)。
        ops = ttk.Frame(lf)
        ops.pack(side="right", fill="y", padx=(0, 6), pady=4)

        self.groups_host = tk.Frame(lf, bg="#f0f0f0")
        self.groups_host.pack(side="left", fill="both", expand=True, padx=4, pady=4)

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
        # 👑 ドッキング位置ピッカーを「ボタン詳細」の枠の外、隣に置く
        # (ユーザー指摘: 枠の中に入っているのは変)。wrapperで横に並べ、
        # lf(ボタン詳細)とdock_frame(ドッキング位置)を別々のLabelFrame
        # として同格に扱う。
        wrapper = ttk.Frame(self)
        wrapper.pack(side="bottom", fill="x", padx=8, pady=(0, 8))

        lf = ttk.LabelFrame(wrapper, text="ボタン詳細")
        lf.pack(side="left", fill="both", expand=True)

        # 👑 2026-09-14: 「モード」(kind="auto_attr")の線色/線種/線幅/
        # レイヤ設定は、以前はlf内にgrid()/grid_remove()で出し入れして
        # いたが、選択中のボタン種別によって「ボタン詳細」全体の高さが
        # 変わってしまい、そのたびに「ボタン配置」エリア(特に右のops列
        # =▲▼◀▶等のボタン)が窮屈になって潰れる不具合が実機で繰り返し
        # 発生した(ユーザー指摘)。「ボタン詳細」「モード設定」「ドッキング
        # 位置」を常に横並びの3枠にして高さを固定し、対象外の時はモード
        # 設定側を丸ごとdisabled表示にする方式へ変更した(ユーザー提案)。
        mode_lf = ttk.LabelFrame(wrapper, text="モード設定")
        # 👑 fill="y"にすると、隣のlf(「ボタン詳細」、5行分で背が高い)に
        # 合わせて縦に引き伸ばされ、中身は8行程度しか無いのに下に大きな
        # 空白ができてしまう(ユーザー指摘: 「空白いっぱいあるよ」)。
        # fillなし+anchor="n"で、自分の内容ぶんの高さだけ使い、上詰めで
        # 表示する。
        mode_lf.pack(side="left", anchor="n", padx=(8, 0))
        self.mode_lf = mode_lf

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

        # 👑 「ドッキング位置の表示はボタン詳細の右に」(ユーザー要望、
        # 2026-09-10)。ただし「ボタン詳細」の枠の中に入っているのは変、
        # との指摘で、lfの中ではなくwrapper直下の別枠(LabelFrame)として
        # 隣に並べる形にした。ドッキング位置はパレット(タブ)ごとの設定
        # なので、他のパレット単位設定(向き・ボタンサイズ等)と同じく
        # このタブの中に置く。
        dock_frame = ttk.LabelFrame(wrapper, text="ドッキング位置")
        dock_frame.pack(side="left", fill="y", padx=(8, 0))
        self.dock_picker = DockPositionPicker(dock_frame, on_select=self._on_dock_pick)
        self.dock_picker.pack(side="top", padx=6, pady=(6, 2))
        self.dock_status_label = ttk.Label(dock_frame, text="")
        self.dock_status_label.pack(side="top")

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

        # 👑 「補助線」「配線」等(kind="auto_attr")用の線色・線種・線幅・
        # 水平垂直・レイヤグループ・レイヤ・コマンド・見本で選ぶ。
        # 👑 2026-09-14: 親をlfからmode_lf(常時表示・固定幅の別枠)へ変更。
        # 「横長い、空白が多い」→ 全部1行1項目に分解、の後で「今度は
        # ボタン詳細(説明文を消して4行に短縮済み)より縦に長すぎて
        # バランスが悪い、全体の余白が最小になるように」という指摘
        # (ユーザー、2026-09-14)を受け、2項目/行に組み直して5行程度に
        # 収め、隣のlf(4行)と高さがおおむね釣り合うようにした。
        # 👑 2026-09-24: jw_cadの線属性ダイアログと同じ場所(一番上)・同じ
        # 文言でSXFの切替を置く。ONにすると線色/線種の選択肢が16色/15種の
        # SXF側へ入れ替わる。**SXFには補助線色・補助線種が無い**ので、
        # 補助線モードボタンを作るときはOFFのままにする。
        self.auto_attr_sxf_var = tk.BooleanVar()
        self.auto_attr_sxf_check = ttk.Checkbutton(
            mode_lf, text="SXF対応拡張線色・線種", variable=self.auto_attr_sxf_var,
            command=self._on_auto_attr_sxf_toggled,
        )
        self.auto_attr_sxf_check.grid(row=0, column=0, columnspan=4, sticky="w", padx=(6, 6), pady=(3, 1))

        ttk.Label(mode_lf, text="線色:").grid(row=1, column=0, sticky="e", padx=(6, 2), pady=3)
        self.auto_attr_color_var = tk.StringVar()
        self.auto_attr_color_combo = ttk.Combobox(
            mode_lf, textvariable=self.auto_attr_color_var, values=palette_config.LINE_COLOR_LABELS,
            state="readonly", width=7,
        )
        self.auto_attr_color_combo.grid(row=1, column=1, sticky="w", padx=(0, 6), pady=3)
        self.auto_attr_color_combo.bind("<<ComboboxSelected>>", self._on_auto_attr_changed)

        ttk.Label(mode_lf, text="線種:").grid(row=1, column=2, sticky="e", padx=(6, 2), pady=3)
        self.auto_attr_type_var = tk.StringVar()
        self.auto_attr_type_combo = ttk.Combobox(
            mode_lf, textvariable=self.auto_attr_type_var, values=palette_config.LINE_TYPE_LABELS,
            state="readonly", width=7,
        )
        self.auto_attr_type_combo.grid(row=1, column=3, sticky="w", padx=(0, 6), pady=3)
        self.auto_attr_type_combo.bind("<<ComboboxSelected>>", self._on_auto_attr_changed)

        ttk.Label(mode_lf, text="線幅:").grid(row=2, column=0, sticky="e", padx=(6, 2), pady=3)
        self.auto_attr_width_var = tk.StringVar()
        self.auto_attr_width_entry = ttk.Entry(mode_lf, textvariable=self.auto_attr_width_var, width=7)
        self.auto_attr_width_entry.grid(row=2, column=1, sticky="w", padx=(0, 6), pady=3)
        self.auto_attr_width_var.trace_add("write", self._on_auto_attr_width_changed)

        self.auto_attr_hv_var = tk.BooleanVar()
        self.auto_attr_hv_check = ttk.Checkbutton(
            mode_lf, text="水平･垂直もON", variable=self.auto_attr_hv_var,
            command=self._on_auto_attr_changed,
        )
        self.auto_attr_hv_check.grid(row=2, column=2, columnspan=2, sticky="w", padx=(6, 6), pady=3)

        ttk.Label(mode_lf, text="レイヤG:").grid(row=3, column=0, sticky="e", padx=(6, 2), pady=3)
        self.auto_attr_layer_group_var = tk.StringVar()
        self.auto_attr_layer_group_combo = ttk.Combobox(
            mode_lf, textvariable=self.auto_attr_layer_group_var,
            values=palette_config.LAYER_NUMBER_LABELS, state="readonly", width=7,
        )
        self.auto_attr_layer_group_combo.grid(row=3, column=1, sticky="w", padx=(0, 6), pady=3)
        self.auto_attr_layer_group_combo.bind("<<ComboboxSelected>>", self._on_auto_attr_changed)

        ttk.Label(mode_lf, text="レイヤ:").grid(row=3, column=2, sticky="e", padx=(6, 2), pady=3)
        self.auto_attr_layer_number_var = tk.StringVar()
        self.auto_attr_layer_number_combo = ttk.Combobox(
            mode_lf, textvariable=self.auto_attr_layer_number_var,
            values=palette_config.LAYER_NUMBER_LABELS, state="readonly", width=7,
        )
        self.auto_attr_layer_number_combo.grid(row=3, column=3, sticky="w", padx=(0, 6), pady=3)
        self.auto_attr_layer_number_combo.bind("<<ComboboxSelected>>", self._on_auto_attr_changed)

        # 👑 切替先コマンド(既定は直線)。「他のコマンド選択することできる？
        # 連続線とか」というユーザー要望への対応。対象を「メイン」種別
        # (線・矩形・連続線等)だけに絞る。ファイル操作/一発系コマンドは
        # CHECKED状態を持たず、「離脱したら自動で戻す」の検知ができない
        # ため選ばせない(ユーザー指摘:「コマンド全部いれたら問題おき
        # ないかな。クラッシュしそうじゃない？」→ クラッシュはしないが、
        # 選ぶと線属性が戻らなくなる実害があるため制限した)。
        ttk.Label(mode_lf, text="コマンド:").grid(row=4, column=0, sticky="e", padx=(6, 2), pady=3)
        self._target_command_options = [
            (row["command_id"], f"{row['command_id']} {row['toolbar_name']}")
            for row in command_master.list_available_commands()
            if row["command_id"] in palette_config.AUTO_ATTR_DRAW_TARGET_COMMAND_IDS
        ]
        self.auto_attr_target_var = tk.StringVar()
        self.auto_attr_target_combo = ttk.Combobox(
            mode_lf, textvariable=self.auto_attr_target_var,
            values=[label for _cid, label in self._target_command_options], state="readonly", width=20,
        )
        self.auto_attr_target_combo.grid(row=4, column=1, columnspan=3, sticky="w", padx=(0, 6), pady=3)
        self.auto_attr_target_combo.bind("<<ComboboxSelected>>", self._on_auto_attr_changed)

        self.pick_swatches_btn = ttk.Button(mode_lf, text="見本で選ぶ…", command=self._on_pick_swatches)
        self.pick_swatches_btn.grid(row=5, column=0, columnspan=4, sticky="ew", padx=6, pady=(3, 6))

        # 👑 「電灯配線図を復元」等(kind="layer_snapshot", role="restore")用:
        # 復元時に書込レイヤをどう扱うかのチェックボックス(ユーザー要望:
        # 「入力レイヤをどうするかはチェックボックスで決めてもらったら
        # いいかと」、2026-09-07)。既定はON(=復元後、押す直前にいた
        # 書込レイヤへ自動で戻す。OFFにすると保存時点の書込レイヤへ
        # 素直に切り替わる、元々の.JWLの挙動)。
        layer_restore_frame = ttk.Frame(lf)
        self.layer_restore_frame = layer_restore_frame
        self.layer_restore_keep_var = tk.BooleanVar(value=True)
        self.layer_restore_keep_check = ttk.Checkbutton(
            layer_restore_frame, text="復元後も今の書込レイヤを維持する",
            variable=self.layer_restore_keep_var, command=self._on_layer_restore_changed,
        )
        self.layer_restore_keep_check.pack(side="left")

        # 👑 保存ボタン(role="save")用: 新しく作る復元ボタンの既定値
        # (ユーザー指摘:「レイヤ保存したらこのボタンの設定には来ないと
        # おもうんだ」→ 復元ボタン個別のチェックボックスは残しつつ、
        # 保存ボタン側に既定値を持たせる、2026-09-07)。
        layer_save_frame = ttk.Frame(lf)
        self.layer_save_frame = layer_save_frame
        self.layer_save_default_var = tk.BooleanVar(value=True)
        self.layer_save_default_check = ttk.Checkbutton(
            layer_save_frame, text="新しく作る復元ボタンも既定でONにする(復元後に今の書込レイヤを維持)",
            variable=self.layer_save_default_var, command=self._on_layer_save_default_changed,
        )
        self.layer_save_default_check.pack(side="left")

        self._set_detail_enabled(False, False)
        self._set_detail_extra_section(None)

    def _set_detail_extra_section(self, section):
        # 👑 group_frame(箱用)/layer_restore_frame/layer_save_frameは
        # 排他なので、選ばれた方だけ実際にgrid()して表示し、他方は
        # grid_remove()で完全に外す。
        # 👑 2026-09-14: auto_attr_frame/auto_attr_frame2(モード設定)は
        # ここでの出し入れ対象から外した。以前はこれも含めてgrid_remove()
        # していたが、選択中のボタン種別によって「ボタン詳細」全体の
        # 高さが変わり、「ボタン配置」エリアのops列(▲▼◀▶等)が窮屈に
        # なって潰れる不具合が繰り返し発生したため、常時表示・固定幅の
        # 別枠(mode_lf、_build_detail_form()参照)へ移した。この関数からは
        # _set_mode_enabled()を呼んで有効/無効の切り替えだけ行う。
        # section: None(何も出さない)/"group"/"auto_attr"/"layer_restore"/"layer_save"
        self.group_frame.grid_remove()
        self.layer_restore_frame.grid_remove()
        self.layer_save_frame.grid_remove()
        self.extra_row_label.grid_remove()
        self._set_mode_enabled(section == "auto_attr")
        # 👑 2026-09-14: auto_attr(モード)は中身をmode_lf側へ完全に移した
        # ため、lf側には「中身:」等に相当する行もdetail_separatorも不要
        # (以前はdetail_separatorだけ残していたが、下に何も無いのに
        # 区切り線だけ残るのは不自然、とのユーザー指摘で削除)。
        if section is None or section == "auto_attr":
            self.detail_separator.grid_remove()
            return
        self.detail_separator.grid()
        self.extra_row_label.grid()
        if section == "group":
            self.extra_row_label.configure(text="中身:")
            self.group_frame.grid(row=self._detail_extra_row, column=1, sticky="w", padx=6, pady=4)
        elif section == "layer_restore":
            self.extra_row_label.configure(text="復元設定:")
            self.layer_restore_frame.grid(row=self._detail_extra_row, column=1, sticky="w", padx=6, pady=4)
        elif section == "layer_save":
            self.extra_row_label.configure(text="保存設定:")
            self.layer_save_frame.grid(row=self._detail_extra_row, column=1, sticky="w", padx=6, pady=4)

    def _set_mode_enabled(self, enabled):
        state = "readonly" if enabled else "disabled"
        entry_state = "normal" if enabled else "disabled"
        self.auto_attr_sxf_check.configure(state=entry_state)
        self.auto_attr_color_combo.configure(state=state)
        self.auto_attr_type_combo.configure(state=state)
        self.auto_attr_width_entry.configure(state=entry_state)
        self.auto_attr_hv_check.configure(state=entry_state)
        self.pick_swatches_btn.configure(state=entry_state)
        self.auto_attr_layer_group_combo.configure(state=state)
        self.auto_attr_layer_number_combo.configure(state=state)
        self.auto_attr_target_combo.configure(state=state)
        if not enabled:
            self.auto_attr_sxf_var.set(False)
            self.auto_attr_color_var.set("")
            self.auto_attr_type_var.set("")
            self.auto_attr_width_var.set("")
            self.auto_attr_hv_var.set(False)
            self.auto_attr_layer_group_var.set("")
            self.auto_attr_layer_number_var.set("")
            self.auto_attr_target_var.set("")

    def _on_auto_attr_changed(self, event=None):
        if self._loading_detail:
            return
        btn = self._selected_button()
        if btn is None or btn.get("kind") != palette_config.BUTTON_KIND_AUTO_ATTR:
            return
        # 👑 2026-09-24: ラベルとIDは必ずline_attr_choices()から対で取る。
        # 既定(9色/9線種)とSXF(16色/15線種)で**個数が違う**ため、片方だけ
        # 別の一覧を使うと添字がずれて別の線種になる。
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
        """SXFのチェックを切り替えたら、線色/線種の選択肢ごと入れ替える。
        👑 番号は一覧をまたいで意味が変わるので、切替時は持ち越さずに
        その一覧の先頭(既定=補助線色/補助線種、SXF=1番)へ寄せる。
        黙って別の色・線種になるより、選び直してもらう方が安全。"""
        if self._loading_detail:
            return
        btn = self._selected_button()
        if btn is None or btn.get("kind") != palette_config.BUTTON_KIND_AUTO_ATTR:
            return
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
        btn = self._selected_button()
        if btn is None or btn.get("kind") != palette_config.BUTTON_KIND_AUTO_ATTR:
            return
        btn["line_width"] = self.auto_attr_width_var.get()

    def _on_layer_restore_changed(self):
        if self._loading_detail:
            return
        btn = self._selected_button()
        if (
            btn is None
            or btn.get("kind") != palette_config.BUTTON_KIND_LAYER_SNAPSHOT
            or btn.get("role") != palette_config.LAYER_SNAPSHOT_ROLE_RESTORE
        ):
            return
        btn["keep_write_layer"] = self.layer_restore_keep_var.get()

    def _on_layer_save_default_changed(self):
        if self._loading_detail:
            return
        btn = self._selected_button()
        if (
            btn is None
            or btn.get("kind") != palette_config.BUTTON_KIND_LAYER_SNAPSHOT
            or btn.get("role") != palette_config.LAYER_SNAPSHOT_ROLE_SAVE
        ):
            return
        btn["default_keep_write_layer"] = self.layer_save_default_var.get()

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
            swatch_cache=self.swatch_cache, sxf=bool(btn.get("line_attr_sxf")),
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
                is_layer_restore = (
                    kind == palette_config.BUTTON_KIND_LAYER_SNAPSHOT
                    and btn.get("role") == palette_config.LAYER_SNAPSHOT_ROLE_RESTORE
                )
                is_layer_save = (
                    kind == palette_config.BUTTON_KIND_LAYER_SNAPSHOT
                    and btn.get("role") == palette_config.LAYER_SNAPSHOT_ROLE_SAVE
                )
                if is_layer_restore:
                    self.cmd_var.set(f"(レイヤ復元・{btn.get('snapshot_name', '')})")
                    self.layer_restore_keep_var.set(bool(btn.get("keep_write_layer", True)))
                elif is_layer_save:
                    self.cmd_var.set("(レイヤ保存)")
                    self.layer_save_default_var.set(bool(btn.get("default_keep_write_layer", True)))
                elif is_group:
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
                    # 👑 2026-09-24: どちらの一覧の番号かはline_attr_sxfで
                    # 決まる。一覧を取り違えると添字がずれて別の線種が
                    # 表示される(番号が重なっているため例外にもならない)。
                    sxf = bool(btn.get("line_attr_sxf"))
                    color_ids, color_labels, type_ids, type_labels =                         palette_config.line_attr_choices(sxf)
                    self.auto_attr_sxf_var.set(sxf)
                    self.auto_attr_color_combo.configure(values=color_labels)
                    self.auto_attr_type_combo.configure(values=type_labels)
                    color_idx = color_ids.index(btn["line_color"])
                    type_idx = type_ids.index(btn["line_type"])
                    self.auto_attr_color_var.set(color_labels[color_idx])
                    self.auto_attr_type_var.set(type_labels[type_idx])
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
                if is_layer_restore:
                    section = "layer_restore"
                elif is_layer_save:
                    section = "layer_save"
                elif is_group:
                    section = "group"
                elif is_auto_attr:
                    section = "auto_attr"
                else:
                    section = None
                self._set_detail_extra_section(section)
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
        if (
            btn.get("kind") == palette_config.BUTTON_KIND_LAYER_SNAPSHOT
            and btn.get("role") == palette_config.LAYER_SNAPSHOT_ROLE_RESTORE
        ):
            # 👑 表示名(name)とsnapshot_name(保存ボタンが同名かどうかを
            # 照合する時に使う正式名)が別々に持てる設計だったが、表示名
            # だけ変えるとsnapshot_nameが古いまま取り残され、後で同じ
            # 元の名前で保存すると別ボタンだと思っていたこの復元ボタンを
            # 上書きしてしまう混乱を生む。「名前の変更を簡単にしたい」
            # (2026-09-08)を踏まえ、表示名の変更にsnapshot_nameを常に
            # 追従させ、両者が乖離しないようにする。
            btn["snapshot_name"] = btn["name"]
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


# 👑 「くっつく場所を指定できるように」(2026-09-10)。4辺(左/右/上/下)×
# 3位置(端/真ん中/端)=12か所+「自動」(明示指定なし、utils/palette_layout.py
# の_edge_for/_position_forの既定フォールバックに任せる)。(label, edge,
# position)のタプルで持ち、edge=Noneが「自動」を表す。
DOCK_POSITION_OPTIONS = [
    ("自動", None, None),
    ("左辺・上端", "left", "start"),
    ("左辺・真ん中", "left", "center"),
    ("左辺・下端", "left", "end"),
    ("右辺・上端", "right", "start"),
    ("右辺・真ん中", "right", "center"),
    ("右辺・下端", "right", "end"),
    ("上辺・左端", "top", "start"),
    ("上辺・真ん中", "top", "center"),
    ("上辺・右端", "top", "end"),
    ("下辺・左端", "bottom", "start"),
    ("下辺・真ん中", "bottom", "center"),
    ("下辺・右端", "bottom", "end"),
]


def _dock_label_for(edge, position):
    for label, e, p in DOCK_POSITION_OPTIONS:
        if e == edge and p == position:
            return label
    return DOCK_POSITION_OPTIONS[0][0]


class DockPositionPicker(tk.Frame):
    # 👑 「もう少し見やすく」への対応(ユーザー要望、2026-09-10)。ドロップ
    # ダウンのテキスト12択より、jw_cadウィンドウを模した四角の周囲に
    # チップ(丸)を配置して直接クリックで選ぶ方が直感的、という指摘。
    # 中央の丸は「自動」を表す。
    CANVAS_W = 170
    CANVAS_H = 100
    MARGIN = 26
    CHIP_R = 6
    FRACS = (0.18, 0.5, 0.82)  # 端・真ん中・端

    def __init__(self, master, on_select):
        super().__init__(master)
        self.on_select = on_select
        self._selected = (None, None)
        self._chip_items = {}
        self.canvas = tk.Canvas(
            self, width=self.CANVAS_W, height=self.CANVAS_H,
            bg="#ffffff", highlightthickness=1, highlightbackground="#999999",
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_click)
        self._draw()

    def _rect_bounds(self):
        m = self.MARGIN
        return m, m, self.CANVAS_W - m, self.CANVAS_H - m

    def _draw(self):
        self.canvas.delete("all")
        self._chip_items = {}
        x1, y1, x2, y2 = self._rect_bounds()
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="#666666", width=2, fill="#eef3fb")
        self.canvas.create_text(
            (x1 + x2) / 2, (y1 + y2) / 2 - 2, text="jw_cad", fill="#8899aa", font=("Meiryo UI", 7),
        )

        for frac, pos in zip(self.FRACS, ("start", "center", "end")):
            self._add_chip(x1 + (x2 - x1) * frac, y1, "top", pos)
            self._add_chip(x1 + (x2 - x1) * frac, y2, "bottom", pos)
            self._add_chip(x1, y1 + (y2 - y1) * frac, "left", pos)
            self._add_chip(x2, y1 + (y2 - y1) * frac, "right", pos)

        # 中央=「自動」。矩形の内側に収まる位置に小さめの丸を置く。
        self._add_chip((x1 + x2) / 2, (y1 + y2) / 2 + 12, None, None)

    def _add_chip(self, cx, cy, edge, pos):
        r = self.CHIP_R
        selected = self._selected == (edge, pos)
        is_auto = edge is None
        if selected:
            fill, outline = "#3f7ad1", "#2a5aa0"
        elif is_auto:
            fill, outline = "#dddddd", "#888888"
        else:
            fill, outline = "#ffffff", "#666666"
        item = self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=fill, outline=outline, width=2)
        self._chip_items[item] = (edge, pos)

    def _on_click(self, event):
        item = self.canvas.find_closest(event.x, event.y)
        if not item:
            return
        key = self._chip_items.get(item[0])
        if key is None:
            return
        self._selected = key
        self._draw()
        self.on_select(*key)

    def set_selected(self, edge, position):
        self._selected = (edge, position)
        self._draw()


class SettingsWindow(tk.Toplevel):
    def __init__(self, master, manager_ref=None, initial_side="左"):
        super().__init__(master)
        self.manager_ref = manager_ref
        self.title("⚙️ JwNavigator パレット設定")
        # 👑 group_frame(箱用)とauto_attr_frame(補助線系用)を排他的に
        # grid()/grid_remove()する方式に変更し、選んでいない方の分の
        # 無駄な縦スペースが無くなった(以前は両方を常時disabled表示で
        # 確保していたため、ボタンを選ぶたびに設定ウィンドウが必要以上に
        # 縦長になっていた)。auto_attr側も1行に集約したため、以前の
        # 800x700より低くできる。
        # 👑 2026-09-14追記: 上記とは別に、footer(保存/キャンセル)を
        # notebookより後にside="top"でpackしていたため、notebookの
        # expand=Trueが残り領域を全部使ってしまい、footerが下端で潰れて
        # 半分しか見えない不具合があった(kosaka/kamo両方で実機確認)。
        # footerをside="bottom"でnotebookより先にpackする形へ修正済み
        # (下記のfooter/notebook.pack()参照)。
        # 👑 2026-09-14さらに追記: 上記を直したら、今度は「ボタン配置」
        # エリア内のops列(▲▼◀▶追加削除＋行－行)側が窮屈になり、
        # 「－行」ボタンが見えなくなる不具合が新たに出た(実機確認)。
        # 固定の800x680という数字には元々根拠が無く、内容が増えるたびに
        # 手で数字を調整しては別の場所が窮屈になる、といういたちごっこに
        # なっていた。そこで固定値をやめ、__init__の末尾(全タブ構築後)で
        # 実際に必要な幅・高さ(winfo_reqwidth/reqheight)を測って
        # ジオメトリを決める方式に変更した(_finalize_geometry()参照)。
        # これ以降、内容が増減してもウィンドウ側が自動で追従する。
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

        palette_bar = ttk.Frame(self)
        palette_bar.pack(side="top", fill="x", padx=8, pady=(8, 0))
        ttk.Button(palette_bar, text="＋ パレットを追加", command=self._on_add_palette).pack(side="left")
        self.remove_palette_btn = ttk.Button(
            palette_bar, text="🗑 このパレットを削除", command=self._on_remove_palette,
        )
        self.remove_palette_btn.pack(side="left", padx=(6, 0))

        # 👑 同じ辺(左/右)に複数パレットが割り当たった時、そのままだと
        # 全部同じ位置に重なって描画される(utils/palette_layout.pyの
        # compute_palette_geometry参照)。既定でONにして自動的に縦へ
        # 積み上げ、OFFにすれば従来通り重ねたままにできる(あえて同じ
        # 場所に置いて片方だけ自由配置で退避させたい場合向け)。
        self.prevent_overlap_var = tk.BooleanVar(
            value=bool(self.config_data.get("prevent_overlap", True))
        )
        ttk.Checkbutton(
            palette_bar, text="パレットの重なりを防止する", variable=self.prevent_overlap_var,
        ).pack(side="left", padx=(12, 0))

        # 👑 2026-09-14修正: footer(保存/キャンセル)は、fill="both",
        # expand=Trueのnotebookより**先に**side="bottom"でpackする必要が
        # ある。tkinterのpackは、後から積む部品ほど「先に積まれた
        # expand=True部品が使い切った残りの領域」しかもらえないため、
        # 以前のように notebook を先に積むと footer の取り分がほぼ無くなり、
        # ウィンドウ下端で保存/キャンセルボタンが潰れて半分しか見えなく
        # なる不具合があった(kosaka/kamo両方の環境で実機確認、2026-09-14。
        # コメントにあった「以前800x700→縦スペース節約で対応」は別事象への
        # 対策で、この根本原因の修正ではなかった)。先にfooterの領域を
        # side="bottom"で確保しておけば、notebookはそれ以外の領域を
        # fill="both"で埋めるだけになり、ウィンドウの高さに関わらず
        # footerが必ず見える。
        footer = ttk.Frame(self)
        footer.pack(side="bottom", fill="x", padx=8, pady=10)
        ttk.Button(footer, text="保存", command=self._on_save, width=14).pack(side="right", ipady=4)
        ttk.Button(footer, text="キャンセル", command=self._on_cancel, width=14).pack(side="right", padx=(0, 8), ipady=4)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(side="top", fill="both", expand=True, padx=8, pady=(8, 0))
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self._update_remove_palette_btn())
        self.menu_panel = None

        # 👑 「N枚パレット見越してパレット名だけ変えとこうか」への対応。
        # 内部の"左"/"右"(config構造・ドッキング側の判定にそのまま使う
        # 実データ)は変えず、この設定画面のタブ表示名だけ「パレット1」
        # 「パレット2」に変える(将来N枚に増えても番号がそのまま使える)。
        for side in palette_config.all_side_keys(self.config_data):
            self._add_side_tab(side)

        self.menu_panel = RightClickMenuPanel(self.notebook)
        self.notebook.add(self.menu_panel, text="右クリック")

        self._update_remove_palette_btn()

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.select_tab(initial_side)
        self._finalize_geometry()

    def _finalize_geometry(self):
        # 👑 2026-09-14: 固定の"800x680"をやめ、全タブ構築後に実際に必要な
        # 幅・高さを測ってジオメトリを決める(上のコメント参照)。
        # ttk.Notebookは「現在表示中のタブ」だけでなく管理下の全ページの
        # 中で最大の要求サイズを自身の要求サイズとして報告する(ttk標準
        # 挙動)ため、select_tab()の後でもここで全タブ分の必要サイズを
        # 取得できる。minsizeもここで同じ値にすることで、後からウィンドウ
        # を縮められて同じ不具合が再発しない(縮小の下限=内容が欠けない
        # 最小サイズ、という一致を保つ)。
        # 👑 追記: update_idletasks()を1回呼んだ直後のwinfo_reqheight()は、
        # 深くネストしたttk構成(Notebook→SidePanel→LabelFrame→Frame)だと
        # まだ確定前の値を返すことがあり、実際には「－行」ボタンが
        # わずかに潰れる不具合が実機で発生した。geometry()適用後にもう
        # 一度update_idletasks()して再計測し、大きい方を採用する
        # (1回では足りない場合があるための保険)。
        self.update_idletasks()
        width = max(800, self.winfo_reqwidth())
        height = max(680, self.winfo_reqheight())
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        width = max(width, self.winfo_reqwidth())
        height = max(height, self.winfo_reqheight())
        self.geometry(f"{width}x{height}")
        self.minsize(width, height)

    def _add_side_tab(self, side):
        side_cfg = palette_config.side_config(self.config_data, side)
        panel = SidePanel(
            self.notebook, side, side_cfg, manager_ref=self.manager_ref,
            swatch_cache=self.swatch_cache, config_data=self.config_data,
        )
        # 👑 ttk.Notebook.insert()は「まだどのタブでもない新規child」を
        # 数値位置で渡すと"Slave index out of bounds"になる（実測で発覚。
        # 数値位置は既存タブの並べ替え専用らしい）。新規追加は必ず"end"を
        # 使い、「右クリック」タブより前に置きたい時だけ、追加した直後に
        # 末尾から1つ手前へ動かす。
        self.notebook.insert("end", panel, text=f"パレット{len(self.panels) + 1}")
        if self.menu_panel is not None:
            self.notebook.insert(self.notebook.index("end") - 2, panel)
        self.panels[side] = panel
        return panel

    def _renumber_tabs(self):
        for i, panel in enumerate(self.panels.values()):
            self.notebook.tab(panel, text=f"パレット{i + 1}")

    def _current_side(self):
        current_tab = self.notebook.select()
        for side, panel in self.panels.items():
            if str(panel) == current_tab:
                return side
        return None

    def _update_remove_palette_btn(self):
        # 👑 2026-09-16: 以前は組み込みの"左"/"右"を削除不可にしていたため、
        # 「パレットは1枚でいい」という人が2枚目を消せなかった
        # (kamo報告)。最後の1枚だけ残せば、どれでも削除してよい。
        current = self._current_side()
        removable = current is not None and len(self.panels) > 1
        self.remove_palette_btn.configure(state="normal" if removable else "disabled")

    def _on_add_palette(self):
        side = palette_config.add_palette(self.config_data)
        panel = self._add_side_tab(side)
        self.notebook.select(panel)
        self._update_remove_palette_btn()

    def _on_remove_palette(self):
        # 👑 最後の1枚は削除させない(_update_remove_palette_btnでボタン
        # 自体を無効化しているが、念のため二重に防御)。
        current = self._current_side()
        if current is None or len(self.panels) <= 1:
            return
        if not messagebox.askyesno(
            "パレットを削除", "このパレットを削除しますか?(中のボタンも全て削除されます)", parent=self,
        ):
            return
        panel = self.panels.pop(current)
        self.notebook.forget(panel)
        panel.destroy()
        del self.config_data["sides"][current]
        self.config_data.get("edges", {}).pop(current, None)
        self.config_data.get("positions", {}).pop(current, None)
        self._renumber_tabs()
        self._update_remove_palette_btn()

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

        self.config_data["prevent_overlap"] = self.prevent_overlap_var.get()
        new_config = palette_config.normalize_config(self.config_data)

        total = sum(palette_config.count_buttons(cfg) for cfg in new_config["sides"].values())
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
