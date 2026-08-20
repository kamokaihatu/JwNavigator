# ===== ✂️ widgets/toolbar.py START ✂️ =====
import tkinter as tk
import os
import csv
import sys
import importlib
from widgets.button import NavButton

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

        self.max_rows = 20
        self.columns_container = None
        self.current_column = None
        self.current_column_row_count = 0

        self.title(f"JwNavigator - {self.side_type}")
        self.configure(bg="#f0f0f0")
        self.wm_overrideredirect(True)
        self.attributes("-topmost", True)

        self._drag_start_x = 0
        self._drag_start_y = 0
        self._is_dragging = False

        self.create_pin_button()
        self.columns_container = tk.Frame(self, bg="#f0f0f0")
        self.columns_container.pack(side="top", fill="both", expand=True)
        self._enable_drag_move()
        self.load_and_build_buttons()

    def create_pin_button(self):
        self.pin_btn = tk.Button(
            self, text="👣 追従", font=("Meiryo UI", 8),
            bg="#ffcccc", relief="sunken", bd=1, command=self.toggle_pin
        )
        self.pin_btn.pack(side="top", fill="x")

    def _enable_drag_move(self):
        # β版で実際に動いていた方式：ウィジェット相対座標（event.x/event.y）を
        # 使う。event.x_root/y_rootとwinfo_x()を組み合わせる方式は、
        # wm_geometry()直後にwinfo_x()が不正確な値を返すことがあり、
        # ドラッグ中に誤差が蓄積して暴れることが分かったため採用しない。
        # ウィジェット相対座標は毎回そのウィジェットの「今の」画面位置を
        # 基準にTkが計算し直すため、1回の誤差が蓄積しない。
        # Toplevel全体に直接バインドするので、NavButton側でbreakを
        # 返さないと、ボタン上のドラッグもここに伝播してしまう点に注意。
        DRAG_THRESHOLD_PX = 8

        def start_drag(event):
            self._drag_start_x = event.x
            self._drag_start_y = event.y
            self._is_dragging = False

        def drag_motion(event):
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

        self.bind("<Button-1>", start_drag)
        self.bind("<B1-Motion>", drag_motion)

    def _next_column_slot(self):
        if self.current_column is None or self.current_column_row_count >= self.max_rows:
            self.current_column = tk.Frame(self.columns_container, bg="#f0f0f0")
            # 上下左右に数pxの余白を残す。この余白はcolumns_container自身の
            # 背景なので、ボタンには重ならずドラッグでウィンドウを掴める。
            self.current_column.pack(side="left", anchor="n", padx=1, pady=1)
            self.current_column_row_count = 0
        self.current_column_row_count += 1
        return self.current_column

    def toggle_pin(self):
        # 追従ボタンのcommand=は、ドラッグ移動と同じ<Button-1>系イベントで
        # 発火するため、実際にドラッグした直後の指離しでも呼ばれてしまう。
        # ドラッグが起きていた場合はここで無視し、二重切り替えを防ぐ。
        if self._is_dragging:
            return
        self.is_pinned = not self.is_pinned
        if self.is_pinned:
            self.pin_btn.configure(text="自由", bg="#e1e1e1", relief="raised")
        else:
            self.pin_btn.configure(text="👣 追従", bg="#ffcccc", relief="sunken")

    def load_and_build_buttons(self):
        try:
            script_path_str, *dummy_args = sys.argv
            exe_dir = os.path.dirname(os.path.abspath(script_path_str))
            csv_path = os.path.join(exe_dir, "config", "config.csv")
        except Exception:
            csv_path = os.path.join("config", "config.csv")

        if not os.path.exists(csv_path):
            csv_path = os.path.join("config", "config.csv")
            
        if not os.path.exists(csv_path):
            if self.manager_ref:
                self.manager_ref.write_system_log("⚠️ [物理クラッシュ] config/config.csv が見つかりません。")
            return

        try:
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row:
                        continue
                    
                    first_col = "".join(row[0:1]).strip()
                    if first_col == "#MAX_ROWS" and len(row) >= 2:
                        try:
                            self.max_rows = int(row[1].strip())
                        except ValueError:
                            pass
                        continue
                    if first_col.startswith("#"):
                        continue

                    if len(row) < 5:
                        continue
                    
                    pos = "".join(row[0:1]).strip()
                    btn_type = "".join(row[1:2]).strip()
                    name = "".join(row[2:3]).strip()
                    command_id = "".join(row[3:4]).strip()
                    icon_name = "".join(row[4:5]).strip()

                    if pos != self.side_type:
                        continue

                    icon_module = None
                    try:
                        icon_module = importlib.import_module(f"icons.{icon_name}")
                    except Exception as e:
                        if self.manager_ref:
                            self.manager_ref.write_system_log(f"⚠️ [アイコン未検出] icons.{icon_name} 読込スキップ: {e}")

                    color = "#333333"
                    column = self._next_column_slot()
                    btn = NavButton(
                        master=column, name=name, icon_module=icon_module, cmd_color=color,
                        command=lambda k=command_id: self.execute_command(k), manager_ref=self.manager_ref
                    )

                    btn.command_key = command_id
                    btn.hwnd = self.target_hwnd
                    btn.icon_name = icon_name
                    btn.load_and_draw()
                    
                    btn.pack(side="top", pady=1, padx=2)
                    self.buttons.append(btn)
                    
            if self.manager_ref:
                self.manager_ref.write_system_log(f"🎨 [{self.side_type}ツールバー] config.csv から正常に {len(self.buttons)} 個のボタンをパッキング整列しました。")
                
        except Exception as e:
            if self.manager_ref:
                self.manager_ref.write_system_log(f"❌ [{self.side_type}ツールバー] CSV展開物理クラッシュ: {str(e)}")

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
