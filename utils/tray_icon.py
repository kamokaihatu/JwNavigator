# ===== ✂️ utils/tray_icon.py START ✂️ =====
"""
タスクトレイアイコン。pystray等の外部ライブラリは使わず、既にpywin32が
入っていることを利用してShell_NotifyIconを直接叩く軽量実装。

👑 別スレッドは立てない。この隠しウィンドウはTkinterのrootと同じ
メインスレッド上に作る。Windowsのメッセージキューはスレッド単位なので、
Tcl/Tkのメインループが既にこのスレッドのメッセージポンプを回して
おり、そこにこの隠しウィンドウ宛てのメッセージも自然に配送される
（追加のポーリングやPumpMessages呼び出しは不要）。
"""
import win32gui
import win32con
import win32api

WM_TRAYICON = win32con.WM_USER + 20
_CLASS_NAME = "JwNavigatorTrayIconWindow"


class TrayIcon:
    def __init__(self, tooltip, menu_items_provider, on_default_click=None):
        # menu_items_provider: () -> [(label, callback_or_None, checked_bool_or_None), ...]
        #   callback=Noneならセパレータとして扱う。呼び出しのたびに評価する
        #   関数にしているのは、「詳細ログ有効」のチェック状態のように
        #   都度変わりうる項目をメニューを開くたびに最新化するため。
        self.menu_items_provider = menu_items_provider
        self.on_default_click = on_default_click
        self._hicon = None
        self.hwnd = self._create_window()
        self._add_icon(tooltip)

    def _create_window(self):
        wc = win32gui.WNDCLASS()
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = _CLASS_NAME
        wc.lpfnWndProc = self._wndproc
        try:
            win32gui.RegisterClass(wc)
        except Exception:
            pass  # 既に登録済み（複数回起動テスト等）は無視してよい
        return win32gui.CreateWindow(
            _CLASS_NAME, "JwNavigator Tray", 0, 0, 0, 0, 0, 0, 0, wc.hInstance, None
        )

    def _add_icon(self, tooltip):
        self._hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
        nid = (self.hwnd, 0, flags, WM_TRAYICON, self._hicon, tooltip)
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)

    def _wndproc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAYICON:
            if lparam in (win32con.WM_RBUTTONUP, win32con.WM_LBUTTONUP):
                self._show_menu()
            elif lparam == win32con.WM_LBUTTONDBLCLK and self.on_default_click:
                self.on_default_click()
            return 0
        if msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _show_menu(self):
        menu = win32gui.CreatePopupMenu()
        menu_items = self.menu_items_provider()
        # 👑 コマンドIDをそのままcallback呼び出しに使うと、動的に増減する
        # メニュー（今のところ固定だが将来のため）にも対応しやすいので、
        # インデックス+1をIDとして割り当てる（0はTrackPopupMenuの
        # 「キャンセルされた」を表す予約値のため避ける）。
        for i, (label, callback, checked) in enumerate(menu_items):
            item_id = i + 1
            if callback is None:
                win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
                continue
            flags = win32con.MF_STRING
            if checked:
                flags |= win32con.MF_CHECKED
            win32gui.AppendMenu(menu, flags, item_id, label)

        pos = win32gui.GetCursorPos()
        # 👑 ポップアップメニュー表示前にSetForegroundWindow、表示後に
        # 空メッセージを送るのは、トレイメニューが「外側クリックで
        # 閉じない」不具合を避けるためのMicrosoft公式の定石。
        win32gui.SetForegroundWindow(self.hwnd)
        cmd = win32gui.TrackPopupMenu(
            menu,
            win32con.TPM_LEFTALIGN | win32con.TPM_RETURNCMD | win32con.TPM_RIGHTBUTTON,
            pos[0], pos[1], 0, self.hwnd, None,
        )
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
        win32gui.DestroyMenu(menu)
        if cmd:
            _, callback, _ = menu_items[cmd - 1]
            if callback:
                callback()

    def update_tooltip(self, tooltip):
        flags = win32gui.NIF_TIP
        nid = (self.hwnd, 0, flags, WM_TRAYICON, self._hicon, tooltip)
        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, nid)

    def destroy(self):
        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self.hwnd, 0))
        except Exception:
            pass
        try:
            win32gui.DestroyWindow(self.hwnd)
        except Exception:
            pass
# ===== ✂️ utils/tray_icon.py END ✂️ =====
