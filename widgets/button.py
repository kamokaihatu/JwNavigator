# ===== ✂️ widgets/button.py START PART 1 ✂️ =====
import os
import re
import tkinter as tk

from utils.palette_config import png_icon_path


class Tooltip:
    def __init__(self, widget, text, offset_x=56):
        self.widget = widget
        self.text = text
        self.offset_x = offset_x
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + self.offset_x
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

        # 👑 右パレットが画面右端にドッキングしている時、offset_x分右へ
        # ずらす位置のままだとツールチップが画面外にはみ出す。実際の描画
        # 幅が確定してから（update_idletasks後）画面幅と比較し、はみ出す
        # 場合はボタンの左側に表示するよう反転する。
        tw.update_idletasks()
        tip_width = tw.winfo_width()
        screen_width = tw.winfo_screenwidth()
        if x + tip_width > screen_width:
            x = max(0, self.widget.winfo_rootx() - tip_width - 4)
            tw.geometry(f"+{x}+{y}")

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


class ScaledCanvas:
    def __init__(self, canvas, scale=1.5):
        self.canvas = canvas
        self.scale = scale

    def _scale_args(self, args, kwargs):
        new_args = [v * self.scale if isinstance(v, (int, float)) else v for v in args]
        if "width" in kwargs:
            kwargs["width"] = max(1.0, kwargs["width"] * self.scale)
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
                new_args.append(v * self.scale)
            else:
                new_args.append(v)
        if "font" in kwargs and isinstance(kwargs["font"], tuple):
            f_list = list(kwargs["font"])
            if len(f_list) > 1 and isinstance(f_list[1], (int, float)):
                f_list[1] = max(1, int(f_list[1] * self.scale))
            kwargs["font"] = tuple(f_list)
        return self.canvas.create_text(*new_args, **kwargs)


# ===== ✂️ widgets/button.py END PART 1 ✂️ =====
# ===== ✂️ widgets/button.py START PART 2 ✂️ =====
def _darken_color(hex_color, factor=0.7):
    # 選択中の凹み表現に使う、そのボタン自身の色を暗くしたバリエーション
    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
    except (ValueError, IndexError):
        return "#99ccff"
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


def _contrast_text_color(bg_hex):
    # 背景色の明るさから、読みやすい方の文字色（黒/白）を選ぶ
    try:
        r = int(bg_hex[1:3], 16)
        g = int(bg_hex[3:5], 16)
        b = int(bg_hex[5:7], 16)
    except (ValueError, IndexError):
        return "#000000"
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    return "#000000" if luminance > 0.6 else "#ffffff"


class NavButton(tk.Frame):
    def __init__(self, master, name, icon_module, cmd_color, command, manager_ref=None, size=48):
        self.size = max(24, int(size))
        self.bg_color = cmd_color or "#f0f0f0"
        super().__init__(
            master, width=self.size, height=self.size, bg=self.bg_color, relief="raised", bd=1
        )
        self.pack_propagate(False)
        self.name = name
        self.icon_module = icon_module
        self.cmd_color = cmd_color
        self.command = command
        self.manager_ref = manager_ref

        # 44px(size=48時)を基準にしたキャンバスサイズとスケール。
        # size=48のとき従来と完全に同じ値になる（canvas_size=44, icon_scale=1.5）。
        self.canvas_size = self.size - 4
        self.center = self.canvas_size / 2.0
        self.icon_scale = 1.5 * self.canvas_size / 44.0

        self.command_key = ""
        self.hwnd = 0
        self.icon_name = "fallback"
        self.selected = False
        self.is_enabled = True
        self._is_dragging = False
        self._press_x = 0
        self._press_y = 0
        self.photo_img = None

        self.canvas = tk.Canvas(
            self,
            width=self.canvas_size,
            height=self.canvas_size,
            bg=self.bg_color,
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

        Tooltip(self, self.name, offset_x=self.size + 8)
        Tooltip(self.canvas, self.name, offset_x=self.size + 8)

    @staticmethod
    def _wrap_label(name, size=48):
        # 「1/4」のような分数表記や、半角ｶﾀｶﾅの濁点/半濁点(前の文字と
        # 離れて改行されると読めなくなる)が行の途中で切れないよう、
        # それぞれひとかたまりのトークンとして抜き出し、それ以外は
        # 1文字ずつのトークンにする。
        tokens = re.findall(r"\d+/\d+|[ｦ-ﾝ][ﾞﾟ]?|.", name)
        n = len(tokens)
        scale = size / 48.0

        def _f(base):
            return max(6, int(round(base * scale)))

        if n <= 1:
            return name, _f(18)

        # 👑 半角ｶﾀｶﾅ等、文字幅が細いものは3文字以上でも1行に収まる
        # ことがある。「2トークンごとに固定改行」という決め打ちをやめ、
        # 実際のフォントでの描画幅を測って1行に入るかどうかを判定する
        # （ユーザー要望：「ハッチ」「コピー」を半角にした時に改行なしで
        # 表示できないか、から着手）。
        try:
            import tkinter.font as tkfont
            f_one_line = tkfont.Font(family="Meiryo UI", size=_f(18), weight="bold")
            max_width = size - 8
            if f_one_line.measure(name) <= max_width:
                return name, _f(18)
        except Exception:
            if n <= 2:
                return name, _f(18)

        rows = ["".join(tokens[i:i + 2]) for i in range(0, n, 2)]
        num_rows = len(rows)
        if num_rows == 1:
            # 👑 n<=2のトークンが1行測定で収まらなかったケース（幅の広い
            # 全角2文字等）。ここに来てもrows自体は1行のままなので、
            # 最小フォント(9)へ落とさず、1行用の大きめサイズを使う。
            base = 18
        elif num_rows == 2:
            base = 14
        elif num_rows == 3:
            base = 11
        else:
            base = 9
        return "\n".join(rows), _f(base)

    def load_and_draw(self):
        self.canvas.delete("all")
        drawn = False

        if self.icon_name:
            png_path = png_icon_path(self.icon_name)
            if os.path.exists(png_path):
                try:
                    self.photo_img = tk.PhotoImage(file=png_path)
                    self.canvas.create_image(self.center, self.center, image=self.photo_img)
                    drawn = True
                except Exception:
                    pass

            if not drawn and self.icon_module:
                try:
                    if hasattr(self.icon_module, "draw"):
                        scaled = ScaledCanvas(self.canvas, self.icon_scale)
                        self.icon_module.draw(scaled, x=4, y=4)
                        drawn = True
                    elif hasattr(self.icon_module, "draw_icon"):
                        scaled = ScaledCanvas(self.canvas, self.icon_scale)
                        self.icon_module.draw_icon(scaled, x=4, y=4)
                        drawn = True
                except Exception:
                    pass

        if not drawn:
            display_text, f_size = self._wrap_label(self.name, self.size)

            self.canvas.create_text(
                self.center,
                self.center,
                text=display_text,
                font=("Meiryo UI", f_size, "bold"),
                fill=_contrast_text_color(self.bg_color),
                justify="center",
            )

        if not self.is_enabled:
            # 無効（グレーアウト）表示：内容の上から半透明のグレーを重ねる
            self.canvas.create_rectangle(
                0, 0, self.canvas_size, self.canvas_size,
                fill="#808080", stipple="gray50", outline="",
            )

    def set_enabled(self, enabled):
        if enabled == self.is_enabled:
            return
        self.is_enabled = enabled
        self.canvas.configure(cursor="hand2" if enabled else "arrow")
        self.load_and_draw()

    DRAG_THRESHOLD_PX = 8

    def press(self, event):
        if not self.is_enabled:
            return "break"
        self._is_dragging = False
        self._press_x = event.x
        self._press_y = event.y
        return "break"

    def motion(self, event):
        if not self.is_enabled:
            return "break"
        dx = event.x - self._press_x
        dy = event.y - self._press_y
        if (dx * dx + dy * dy) ** 0.5 > self.DRAG_THRESHOLD_PX:
            self._is_dragging = True
        return "break"

    def release(self, event):
        if not self.is_enabled:
            return "break"
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
        selected_color = _darken_color(self.bg_color)
        self.configure(bg=selected_color, relief="sunken")
        self.canvas.configure(bg=selected_color)

    def clear_selected(self):
        self.selected = False
        self.configure(bg=self.bg_color, relief="raised")
        self.canvas.configure(bg=self.bg_color)


# ===== ✂️ widgets/button.py END PART 2 ✂️ =====
