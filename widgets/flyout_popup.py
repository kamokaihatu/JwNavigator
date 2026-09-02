# ===== ✂️ widgets/flyout_popup.py START ✂️ =====
"""
グループボタン（フライアウト種別）を押した時に出る、中身のコマンド
一覧ポップアップ。パレット本体のボタンと同じNavButtonを小さく並べる。

このアプリには「クリック外しで自動的に閉じるポップアップ」の前例が
無かった（既存のダイアログ群はモーダル、Tooltipはホバー式）。ここでは
Toplevel自体のフォーカスが外れた瞬間（＝別のトップレベルウィンドウが
アクティブになった＝外側クリックとみなせる）に閉じる方式を採用する。
子ウィジェット間でのフォーカス移動ではToplevel自体のFocusOutは発火
しない（X11/Win32どちらのフォーカスモデルでも、同じトップレベル内の
移動は対象外）ため、追加の判定は不要だった（実測で確認）。
"""
import tkinter as tk

from widgets.button import NavButton, import_icon_module as _import_icon_module


class FlyoutPopup(tk.Toplevel):
    def __init__(self, trigger_btn, entry, on_pick, on_pick_auto_attr=None, on_close=None):
        super().__init__(trigger_btn)
        self.trigger_btn = trigger_btn
        self._on_pick = on_pick
        self._on_pick_auto_attr = on_pick_auto_attr
        self._on_close = on_close
        self._closed = False

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg="#888888")

        inner = tk.Frame(self, bg="#f0f0f0")
        inner.pack(padx=1, pady=1)

        size = trigger_btn.size
        sub_buttons = entry.get("sub_buttons", [])
        if not sub_buttons:
            # 👑 「先に空の箱を作る」フローで、まだ何も追加していない状態で
            # 開いた時に、ただの空白ではなく分かるようにしておく。
            tk.Label(
                inner, text="(まだ何も入っていません)", bg="#f0f0f0",
                fg="#888888", font=("Meiryo UI", 9), padx=8, pady=8,
            ).pack()
        for sub in sub_buttons:
            icon_module = _import_icon_module(sub.get("icon"))
            # 👑 「グループボタンの中には線属性ボタン作れますか？」への
            # 対応。中身が補助線系(kind="auto_attr")の場合は、単純な
            # コマンド送信(_pick)ではなく実際の自動化シーケンス
            # (線属性を覚えて切替→直線へ→離脱で復帰)を起動する別経路
            # に振り分ける。
            if sub.get("kind") == "auto_attr":
                click_cmd = lambda s=sub: self._pick_auto_attr(s)
            else:
                click_cmd = lambda s=sub: self._pick(s)
            btn = NavButton(
                master=inner, name=sub.get("name", ""), icon_module=icon_module,
                cmd_color=sub.get("color"),
                command=click_cmd,
                size=size,
            )
            btn.icon_name = sub.get("icon", "")
            btn.entry = sub
            btn.load_and_draw()
            btn.pack(side="left", padx=1, pady=1)

        self.bind("<Escape>", lambda e: self.close())
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.update_idletasks()
        self._position_near(trigger_btn)
        # 👑 生成直後は自分自身への表示処理でフォーカスが不安定なため、
        # 少し待ってからfocus_force()する（即座にbindすると生成時の
        # イベントを誤って外側クリックとして拾ってしまう可能性がある）。
        self.after(80, self._activate)

    def _position_near(self, widget):
        x = widget.winfo_rootx() + widget.winfo_width() + 4
        y = widget.winfo_rooty()
        popup_w = self.winfo_width()
        popup_h = self.winfo_height()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        if x + popup_w > screen_w:
            x = max(0, widget.winfo_rootx() - popup_w - 4)
        if y + popup_h > screen_h:
            y = max(0, screen_h - popup_h)
        self.geometry(f"+{x}+{y}")

    def _activate(self):
        if self._closed:
            return
        try:
            self.focus_force()
        except Exception:
            pass
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_out(self, event):
        self.close()

    def _pick(self, sub_entry):
        self.close()
        if self._on_pick:
            self._on_pick(sub_entry)

    def _pick_auto_attr(self, sub_entry):
        self.close()
        if self._on_pick_auto_attr:
            self._on_pick_auto_attr(sub_entry)

    def close(self):
        if self._closed:
            return
        self._closed = True
        callback = self._on_close
        self._on_close = None
        try:
            self.destroy()
        except Exception:
            pass
        if callback:
            callback()
# ===== ✂️ widgets/flyout_popup.py END ✂️ =====
