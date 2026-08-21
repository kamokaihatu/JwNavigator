# ===== ✂️ widgets/button.py START PART 1 ✂️ =====
import os
import re
import tkinter as tk


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 56
        y = self.widget.winfo_rooty() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.overrideredirect(True)
        tw.attributes("-topmost", True)
        tw.geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            bg="#ffffe1",
            fg="#000000",
            relief=tk.SOLID,
            bd=1,
            font=("Meiryo UI", 9),
        )
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


class ScaledCanvas:
    def __init__(self, canvas):
        self.canvas = canvas

    def _scale_args(self, args, kwargs):
        new_args = [v * 1.5 if isinstance(v, (int, float)) else v for v in args]
        if "width" in kwargs:
            kwargs["width"] = max(1.0, kwargs["width"] * 1.5)
        return new_args, kwargs

    def create_line(self, *args, **kwargs):
        a, k = self._scale_args(args, kwargs)
        return self.canvas.create_line(*a, **k)

    def create_oval(self, *args, **kwargs):
        a, k = self._scale_args(args, kwargs)
        return self.canvas.create_oval(*a, **k)

    def create_rectangle(self, *args, **kwargs):
        a, k = self._scale_args(args, kwargs)
        return self.canvas.create_rectangle(*a, **k)

    def create_polygon(self, *args, **kwargs):
        a, k = self._scale_args(args, kwargs)
        return self.canvas.create_polygon(*a, **k)

    def create_arc(self, *args, **kwargs):
        a, k = self._scale_args(args, kwargs)
        return self.canvas.create_arc(*a, **k)

    def create_text(self, *args, **kwargs):
        new_args = []
        for i, v in enumerate(args):
            if i < 2 and isinstance(v, (int, float)):
                new_args.append(v * 1.5)
            else:
                new_args.append(v)
        if "font" in kwargs and isinstance(kwargs["font"], tuple):
            f_list = list(kwargs["font"])
            if len(f_list) > 1 and isinstance(f_list[1], (int, float)):
                f_list[1] = int(f_list[1] * 1.5)
            kwargs["font"] = tuple(f_list)
        return self.canvas.create_text(*new_args, **kwargs)


# ===== ✂️ widgets/button.py END PART 1 ✂️ =====
# ===== ✂️ widgets/button.py START PART 2 ✂️ =====
class NavButton(tk.Frame):
    def __init__(self, master, name, icon_module, cmd_color, command, manager_ref=None):
        super().__init__(
            master, width=48, height=48, bg="#f0f0f0", relief="raised", bd=1
        )
        self.pack_propagate(False)
        self.name = name
        self.icon_module = icon_module
        self.cmd_color = cmd_color
        self.command = command
        self.manager_ref = manager_ref

        self.command_key = ""
        self.hwnd = 0
        self.icon_name = "fallback"
        self.selected = False
        self._is_dragging = False
        self._press_x = 0
        self._press_y = 0
        self.photo_img = None

        self.canvas = tk.Canvas(
            self,
            width=44,
            height=44,
            bg="#f0f0f0",
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(padx=1, pady=1)

        self.canvas.bind("<ButtonPress-1>", self.press)
        self.canvas.bind("<B1-Motion>", self.motion)
        self.canvas.bind("<ButtonRelease-1>", self.release)
        self.canvas.bind("<Enter>", self.enter)
        self.canvas.bind("<Leave>", self.leave)

        Tooltip(self, self.name)
        Tooltip(self.canvas, self.name)

    @staticmethod
    def _wrap_label(name):
        # 「1/4」のような分数表記が行の途中で切れて "1/" のように
        # みっともなくならないよう、まず分数をひとかたまりのトークンとして
        # 抜き出し、それ以外は1文字ずつのトークンにする。
        tokens = re.findall(r"\d+/\d+|.", name)
        n = len(tokens)
        if n <= 2:
            return name, 18

        rows = ["".join(tokens[i:i + 2]) for i in range(0, n, 2)]
        num_rows = len(rows)
        if num_rows == 2:
            f_size = 14
        elif num_rows == 3:
            f_size = 11
        else:
            f_size = 9
        return "\n".join(rows), f_size

    def load_and_draw(self):
        self.canvas.delete("all")

        png_path = f"png_icons/{self.icon_name}.png"
        if os.path.exists(png_path):
            try:
                self.photo_img = tk.PhotoImage(file=png_path)
                self.canvas.create_image(22, 22, image=self.photo_img)
                return
            except Exception:
                pass

        if self.icon_module:
            try:
                if hasattr(self.icon_module, "draw"):
                    scaled = ScaledCanvas(self.canvas)
                    self.icon_module.draw(scaled, x=4, y=4)
                    return
                elif hasattr(self.icon_module, "draw_icon"):
                    scaled = ScaledCanvas(self.canvas)
                    self.icon_module.draw_icon(scaled, x=4, y=4)
                    return
            except Exception:
                pass

        display_text, f_size = self._wrap_label(self.name)

        self.canvas.create_text(
            22,
            22,
            text=display_text,
            font=("Meiryo UI", f_size, "bold"),
            fill=self.cmd_color,
            justify="center",
        )

    DRAG_THRESHOLD_PX = 8

    def press(self, event):
        self._is_dragging = False
        self._press_x = event.x
        self._press_y = event.y
        return "break"

    def motion(self, event):
        dx = event.x - self._press_x
        dy = event.y - self._press_y
        if (dx * dx + dy * dy) ** 0.5 > self.DRAG_THRESHOLD_PX:
            self._is_dragging = True
        return "break"

    def release(self, event):
        if self._is_dragging:
            return "break"

        try:
            self.winfo_toplevel().attributes("-topmost", False)
        except Exception:
            pass

        if hasattr(self.master, "select_button"):
            self.master.select_button(self)
        else:
            self.set_selected()

        if getattr(self.manager_ref, "record_state_collection_event", None):
            raw_status_text = self.manager_ref.capture_statusbar_for_window(self.hwnd)
            self.manager_ref.record_state_collection_event(
                "CLICK",
                self.name,
                raw_status_text=raw_status_text,
            )

        if self.command:
            self.command()

        try:
            self.winfo_toplevel().attributes("-topmost", True)
        except Exception:
            pass
        return "break"

    def enter(self, event):
        if getattr(self.manager_ref, "record_state_collection_event", None):
            self.manager_ref.record_state_collection_event("HOVER", self.name)

    def leave(self, event):
        # ホバー時の着色は抑止し、実際のクリック/選択時のみ着色する
        pass

    def set_selected(self):
        self.selected = True
        self.configure(bg="#99ccff", relief="sunken")
        self.canvas.configure(bg="#99ccff")

    def clear_selected(self):
        self.selected = False
        self.configure(bg="#f0f0f0", relief="raised")
        self.canvas.configure(bg="#f0f0f0")


# ===== ✂️ widgets/button.py END PART 2 ✂️ =====
