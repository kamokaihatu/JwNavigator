# ===== ✂️ widgets/toolbar.py START ✂️ =====
import tkinter as tk
import os
import csv
import sys
import importlib
from widgets.button import NavButton

class Toolbar(tk.Toplevel):
    def __init__(self, master, side_type, hwnd, send_key_func=None, manager_ref=None):
        super().__init__(master)
        self.side_type = side_type
        self.target_hwnd = hwnd
        self.send_key_to_hwnd = send_key_func
        self.manager_ref = manager_ref
        
        self.current_selected_button = None
        self.buttons = []
        self.is_pinned = False
        self.user_hidden = False

        self.title(f"JwNavigator - {self.side_type}")
        self.configure(bg="#f0f0f0")
        self.wm_overrideredirect(True)
        self.attributes("-topmost", True)

        self.create_pin_button()
        self.load_and_build_buttons()

    def create_pin_button(self):
        self.pin_btn = tk.Button(
            self, text="👣 追従", font=("Meiryo UI", 8), 
            bg="#ffcccc", relief="sunken", bd=1, command=self.toggle_pin
        )
        self.pin_btn.pack(side="top", fill="x")

    def toggle_pin(self):
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
                    if first_col.startswith("#"):
                        continue
                        
                    if len(row) < 5:
                        continue
                    
                    pos = "".join(row[0:1]).strip()
                    btn_type = "".join(row[1:2]).strip()
                    name = "".join(row[2:3]).strip()
                    key = "".join(row[3:4]).strip()
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
                    btn = NavButton(
                        master=self, name=name, icon_module=icon_module, cmd_color=color,
                        command=lambda k=key: self.execute_command(k), manager_ref=self.manager_ref
                    )
                    
                    btn.command_key = key
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

    def execute_command(self, key_str):
        btn_name = ""
        icon_name = ""
        for btn in self.buttons:
            if getattr(btn, "command_key", "") == key_str:
                btn_name = getattr(btn, "name", "")
                icon_name = getattr(btn, "icon_name", "")
                break

        if self.manager_ref:
            self.manager_ref.write_system_log(
                f"[パレット操作] source=toolbar side={self.side_type} key={key_str} name={btn_name} icon={icon_name} hwnd={self.target_hwnd}"
            )
        if self.send_key_to_hwnd:
            self.send_key_to_hwnd(self.target_hwnd, key_str, mode="A")

    def select_button(self, target_btn):
        if self.current_selected_button and self.current_selected_button != target_btn:
            self.current_selected_button.clear_selected()
        self.current_selected_button = target_btn
        if self.current_selected_button:
            self.current_selected_button.set_selected()
# ===== ✂️ widgets/toolbar.py END ✂️ =====
