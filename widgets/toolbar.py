# ===== ✂️ widgets/toolbar.py START ✂️ =====
import tkinter as tk
import importlib
from widgets.button import NavButton
from utils import palette_config

_ICON_MODULE_CACHE = {}


def _import_icon_module(icon_name):
    if not icon_name:
        return None
    if icon_name in _ICON_MODULE_CACHE:
        return _ICON_MODULE_CACHE[icon_name]
    module = None
    try:
        module = importlib.import_module(f"icons.{icon_name}")
    except Exception as e:
        print(f"[WARN] icon module load failed: {icon_name} ({e})")
    _ICON_MODULE_CACHE[icon_name] = module
    return module


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
                btn = NavButton(
                    master=frame, name=entry["name"], icon_module=icon_module, cmd_color=entry["color"],
                    command=lambda k=entry["command_id"]: self.execute_command(k), manager_ref=self.manager_ref,
                    size=self.button_size,
                )
                btn.command_key = entry["command_id"]
                btn.hwnd = self.target_hwnd
                btn.icon_name = entry["icon"]
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

    def select_button(self, target_btn):
        if self.current_selected_button and self.current_selected_button != target_btn:
            self.current_selected_button.clear_selected()
        self.current_selected_button = target_btn
        if self.current_selected_button:
            self.current_selected_button.set_selected()
# ===== ✂️ widgets/toolbar.py END ✂️ =====
