# ===== ✂️ widgets/toolbar.py START ✂️ =====
import os
import tkinter as tk
from widgets.button import NavButton, import_icon_module as _import_icon_module
from widgets.flyout_popup import FlyoutPopup
from utils import palette_config


class Toolbar(tk.Toplevel):
    def __init__(self, master, side_type, hwnd, execute_func=None, manager_ref=None):
        super().__init__(master)
        self.side_type = side_type
        self.target_hwnd = hwnd
        self.execute_func = execute_func
        self.manager_ref = manager_ref

        self.current_selected_button = None
        self.buttons = []
        self.is_pinned = False
        self.user_hidden = False
        self._open_flyout = None  # 👑 グループボタン(フライアウト)の開閉状態

        self.orientation = palette_config.ORIENTATION_PORTRAIT
        self.button_size = palette_config.DEFAULT_BUTTON_SIZE
        self.columns_container = None
        self.group_frames = []
        self.group_sizes = []

        self.title(f"JwNavigator - {self.side_type}")
        self.configure(bg="#f0f0f0")
        self.wm_overrideredirect(True)
        self.attributes("-topmost", True)

        self._drag_start_x = 0
        self._drag_start_y = 0
        self._is_dragging = False

        self.create_pin_button()
        self._bind_drag_move(self)
        self.columns_container = tk.Frame(self, bg="#f0f0f0")
        # fill/expandを付けると、ウィンドウ幅がボタン列の実サイズより
        # わずかに大きい場合に余白が右側だけに寄ってしまう（左詰めに見える
        # 原因）。fill/expandなしでpackすると、Tkinterのデフォルトの
        # center配置により左右対称に余白が入る。空白部分のドラッグは
        # self（Toplevel本体）側のバインドでカバーする。
        self.columns_container.pack(side="top", padx=3, pady=3)
        self._bind_drag_move(self.columns_container)
        self.load_and_build_buttons()

    def create_pin_button(self):
        self.pin_btn = tk.Button(
            self, text="👣 追従", font=("Meiryo UI", 8),
            bg="#ffcccc", relief="sunken", bd=1
        )
        self.pin_btn.pack(side="top", fill="x")
        # 👑 command=は使わない。tk.Buttonの標準クリック処理は
        # <ButtonPress-1>/<B1-Motion>/<ButtonRelease-1>を自分のクラス
        # バインドで消費してしまい、Toplevel側へは伝播しない（実測で確認、
        # ドラッグしても常にクリック扱いになっていた）。ボタン自身に
        # 直接バインドして、クリックとドラッグを自前で判定する。
        self._bind_drag_move(self.pin_btn, click_action=self.toggle_pin)

    def _bind_drag_move(self, widget, click_action=None):
        # ウィジェット相対座標（event.x/event.y）を使う。event.x_root/y_root
        # とwinfo_x()を組み合わせる方式は、wm_geometry()直後にwinfo_x()が
        # 不正確な値を返すことがあり、ドラッグ中に誤差が蓄積して暴れる
        # ことが分かったため採用しない。ウィジェット相対座標は毎回その
        # ウィジェットの「今の」画面位置を基準にTkが計算し直すため、
        # 1回の誤差が蓄積しない（β版で実際に動いていた方式）。
        DRAG_THRESHOLD_PX = 8

        def on_press(event):
            self._drag_start_x = event.x
            self._drag_start_y = event.y
            self._is_dragging = False

        def on_motion(event):
            dx = event.x - self._drag_start_x
            dy = event.y - self._drag_start_y
            if (dx * dx + dy * dy) ** 0.5 > DRAG_THRESHOLD_PX:
                self._is_dragging = True
                # 追従中の自動位置補正（sync_toolbar_position）が掴んだ直後の
                # わずかな隙に発火して引き戻すのを防ぐため、動かし始めた
                # 瞬間に自由モードへ切り替えておく。
                if not self.is_pinned:
                    self.is_pinned = True
                    self.pin_btn.configure(text="自由", bg="#e1e1e1", relief="raised")
                new_x = self.winfo_x() + dx
                new_y = self.winfo_y() + dy
                self.wm_geometry(f"+{new_x}+{new_y}")

        def on_release(event):
            if not self._is_dragging and click_action:
                click_action()

        widget.bind("<ButtonPress-1>", on_press)
        widget.bind("<B1-Motion>", on_motion)
        widget.bind("<ButtonRelease-1>", on_release)

    def group_count(self):
        return len(self.group_sizes)

    def max_group_length(self):
        return max(self.group_sizes) if self.group_sizes else 0

    def toggle_pin(self):
        # click_actionとして呼ばれるのはon_release()がドラッグでなかったと
        # 判定した時だけなので、ここでは単純にトグルするだけでよい。
        self.is_pinned = not self.is_pinned
        if self.is_pinned:
            self.pin_btn.configure(text="自由", bg="#e1e1e1", relief="raised")
        else:
            self.pin_btn.configure(text="👣 追従", bg="#ffcccc", relief="sunken")
            # 自由配置中に手動でドラッグ移動していると、main.py側が
            # 覚えている「前回適用した座標」（_last_geom）が実際の位置と
            # ズレたままになる。追従に戻す時はこれを捨てて、次のsync tickで
            # 必ず新しい座標を適用させる（そうしないと「変化なし」と
            # 誤判定されて、追従位置へ飛んでくれないことがある）。
            self._last_geom = None

    def load_and_build_buttons(self):
        for child in self.columns_container.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass
        self.buttons = []
        self.group_frames = []
        self.group_sizes = []
        self.current_selected_button = None

        try:
            config = palette_config.load_config()
            side_cfg = palette_config.side_config(config, self.side_type)
        except Exception as e:
            if self.manager_ref:
                self.manager_ref.write_system_log(f"❌ [{self.side_type}ツールバー] config.json読込失敗: {str(e)}")
            side_cfg = {"orientation": palette_config.ORIENTATION_PORTRAIT, "button_size": palette_config.DEFAULT_BUTTON_SIZE, "groups": []}

        self.orientation = side_cfg["orientation"]
        self.button_size = side_cfg["button_size"]

        if self.orientation == palette_config.ORIENTATION_LANDSCAPE:
            group_side, group_anchor, button_side = "top", "w", "left"
        else:
            group_side, group_anchor, button_side = "left", "n", "top"

        for group in side_cfg["groups"]:
            entries = group.get("buttons") or []
            if not entries:
                continue

            frame = tk.Frame(self.columns_container, bg="#f0f0f0")
            frame.pack(side=group_side, anchor=group_anchor)
            self.group_frames.append(frame)

            for entry in entries:
                icon_module = _import_icon_module(entry["icon"])
                kind = entry.get("kind", palette_config.BUTTON_KIND_SINGLE)

                if kind == palette_config.BUTTON_KIND_FLYOUT:
                    command = None  # 生成後、btn自身を参照するために下で差し替える
                elif kind == palette_config.BUTTON_KIND_MACRO:
                    command = lambda e=entry: self.execute_macro(e)
                elif kind == palette_config.BUTTON_KIND_AUTO_ATTR:
                    command = None  # 生成後、btn自身を参照するために下で差し替える
                elif kind == palette_config.BUTTON_KIND_LAYER_SNAPSHOT:
                    command = None  # 生成後、btn自身を参照するために下で差し替える
                else:
                    command = lambda k=entry["command_id"]: self.execute_command(k)

                display_name = entry["name"]
                if kind == palette_config.BUTTON_KIND_LAYER_SNAPSHOT:
                    # 👑 保存済みかどうかをボタンの表示名に一目でわかるよう付記する
                    # (専用の描画を新設する時間が無いため、名前ラベルで代用)。
                    snap_path = palette_config.layer_snapshot_path(entry.get("snapshot_id", ""))
                    display_name = entry["name"] + ("\n💾保存済" if os.path.isfile(snap_path) else "\n(未保存)")

                btn = NavButton(
                    master=frame, name=display_name, icon_module=icon_module, cmd_color=entry["color"],
                    command=command, manager_ref=self.manager_ref,
                    size=self.button_size,
                )
                if kind == palette_config.BUTTON_KIND_FLYOUT:
                    btn.command = lambda b=btn, e=entry: self.toggle_flyout(b, e)
                elif kind == palette_config.BUTTON_KIND_AUTO_ATTR:
                    btn.command = lambda b=btn, e=entry: self.execute_auto_attr(b, e)
                elif kind == palette_config.BUTTON_KIND_LAYER_SNAPSHOT:
                    btn.command = lambda b=btn, e=entry: self.execute_layer_snapshot(b, e)
                btn.command_key = entry["command_id"]
                btn.hwnd = self.target_hwnd
                btn.icon_name = entry["icon"]
                btn.entry = entry
                btn.load_and_draw()

                btn.pack(side=button_side)
                self.buttons.append(btn)

            self.group_sizes.append(len(entries))

        if self.manager_ref:
            self.manager_ref.write_system_log(f"🎨 [{self.side_type}ツールバー] config.json から正常に {len(self.buttons)} 個のボタンをパッキング整列しました。")

        print(f"{self.side_type}: {len(self.buttons)} 個")

    def execute_command(self, command_id):
        btn_name = ""
        icon_name = ""
        for btn in self.buttons:
            if getattr(btn, "command_key", "") == command_id:
                btn_name = getattr(btn, "name", "")
                icon_name = getattr(btn, "icon_name", "")
                break

        if self.manager_ref:
            self.manager_ref.write_system_log(
                f"[パレット操作] source=toolbar side={self.side_type} command_id={command_id} name={btn_name} icon={icon_name} hwnd={self.target_hwnd}"
            )
        if self.execute_func:
            self.execute_func(self.target_hwnd, command_id)

    def toggle_flyout(self, trigger_btn, entry):
        was_open_for_same = False
        if self._open_flyout is not None:
            was_open_for_same = self._open_flyout.trigger_btn is trigger_btn
            self._open_flyout.close()
            self._open_flyout = None
            if was_open_for_same:
                return  # 同じボタンをもう一度押した＝閉じるだけでよい

        def _clear():
            self._open_flyout = None

        on_pick = lambda sub_entry: self._on_flyout_pick(trigger_btn, sub_entry)
        on_pick_auto_attr = lambda sub_entry: self._on_flyout_pick_auto_attr(trigger_btn, sub_entry)
        self._open_flyout = FlyoutPopup(
            trigger_btn, entry, on_pick=on_pick, on_pick_auto_attr=on_pick_auto_attr, on_close=_clear,
        )

    def _on_flyout_pick(self, trigger_btn, sub_entry):
        # 👑 選んだ中身の見た目(アイコン/名前)を起動ボタン自身にも反映する
        # (「入れ物」から「面取り」に変わる)。command_keyも実コマンドの
        # ものへ差し替えることで、CHECKEDビット監視の対象になり、以後は
        # 普通のコマンドボタンと同じく選択中/非選択中が正しく凹み表示に
        # 反映されるようになる(ユーザー要望: 「面取りおしたら、入れ物から
        # 面取りに変わってさらに凹んでくれるとうれしい」)。
        command_id = sub_entry.get("command_id", "")
        trigger_btn.name = sub_entry.get("name") or trigger_btn.name
        trigger_btn.icon_name = sub_entry.get("icon", "")
        trigger_btn.icon_module = _import_icon_module(trigger_btn.icon_name)
        trigger_btn.command_key = command_id
        trigger_btn.update_tooltip_text(trigger_btn.name)
        trigger_btn.load_and_draw()
        self.execute_command(command_id)

    def _on_flyout_pick_auto_attr(self, trigger_btn, sub_entry):
        # 👑 箱の中身が補助線系(kind="auto_attr")の場合の選択。顔を借りる
        # のは_on_flyout_pickと同じだが、command_keyは使わない(auto_attr
        # は独自のハイライト管理のため)。既に別の中身を選んでいた場合に
        # 備えて念のためクリアしておく。
        trigger_btn.name = sub_entry.get("name") or trigger_btn.name
        trigger_btn.icon_name = sub_entry.get("icon", "")
        trigger_btn.icon_module = _import_icon_module(trigger_btn.icon_name)
        trigger_btn.command_key = ""
        trigger_btn.update_tooltip_text(trigger_btn.name)
        trigger_btn.load_and_draw()
        if self.manager_ref and hasattr(self.manager_ref, "start_auto_attr_sequence"):
            self.manager_ref.start_auto_attr_sequence(self.target_hwnd, sub_entry, trigger_btn)

    def execute_macro(self, entry):
        sub_buttons = entry.get("sub_buttons") or []
        command_ids = [b["command_id"] for b in sub_buttons if b.get("command_id")]
        if self.manager_ref and hasattr(self.manager_ref, "execute_macro_sequence"):
            self.manager_ref.execute_macro_sequence(self.target_hwnd, command_ids)

    def execute_auto_attr(self, trigger_btn, entry):
        # 👑 「補助線モードで書いてる間は補助線ボタンへこませといて」
        # (ユーザー要望)。当初はcommand_keyを直線コマンドに借りて既存の
        # CHECKEDビット監視に相乗りさせていたが、本物の「線」ボタンと
        # command_keyが競合し、locked_intent(名前ベースの先行点灯)が
        # 「線」の方を凹ませてしまう不具合が実機で発覚(2026-09-02)。
        # command_keyは""のまま変えず、このボタンの凹み表示は完全に
        # main.py側(start_auto_attr_sequence/_revert_auto_attr)が
        # 直接set_selected()/clear_selected()で管理する、独立した仕組みに
        # した方が確実。
        if self.manager_ref and hasattr(self.manager_ref, "start_auto_attr_sequence"):
            self.manager_ref.start_auto_attr_sequence(self.target_hwnd, entry, trigger_btn)

    def execute_layer_snapshot(self, trigger_btn, entry):
        # 👑 「電灯配線図」のようなレイヤ状態の保存/復元ボタン。押した時に
        # 専用JWLファイルが無ければ保存フロー、あれば復元フローへ分岐する
        # 判定自体はmain.py側(handle_layer_snapshot_click)で行う。
        if self.manager_ref and hasattr(self.manager_ref, "handle_layer_snapshot_click"):
            self.manager_ref.handle_layer_snapshot_click(self.target_hwnd, entry, trigger_btn)

    def select_button(self, target_btn):
        if self.current_selected_button and self.current_selected_button != target_btn:
            self.current_selected_button.clear_selected()
        self.current_selected_button = target_btn
        if self.current_selected_button:
            self.current_selected_button.set_selected()
# ===== ✂️ widgets/toolbar.py END ✂️ =====
