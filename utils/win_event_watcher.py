# ===== ✂️ utils/win_event_watcher.py START ✂️ =====
"""
jw_cadのステータスバー(msctls_statusbar32)のテキストが更新された瞬間を
OBJECT_NAMECHANGE通知(SetWinEventHook)で捕まえる。

過去に不安定だった低レベル入力フック(SetWindowsHookExW / WH_MOUSE_LL等)
とは別のWin32 API。SetWinEventHookはアクセシビリティ通知専用の仕組みで、
対象プロセスへのコード注入を伴わない（WINEVENT_OUTOFCONTEXTモードでは、
イベントは呼び出し元スレッドのメッセージキューへ配送されるだけ）ため、
リスクの性質が異なる。

念のため、コールバック内では一切の重い処理を行わずキューへ積むだけに
徹する（低レベル入力フックで得た教訓をそのまま踏襲）。
"""
import ctypes
from ctypes import wintypes
import queue
import threading
import time

EVENT_OBJECT_NAMECHANGE = 0x800C
WINEVENT_OUTOFCONTEXT = 0x0000
WINEVENT_SKIPOWNPROCESS = 0x0002

_WinEventProcType = ctypes.WINFUNCTYPE(
    None, wintypes.HANDLE, wintypes.DWORD, wintypes.HWND,
    wintypes.LONG, wintypes.LONG, wintypes.DWORD, wintypes.DWORD
)


class WinEventWatcher:
    def __init__(self):
        self.event_queue = queue.Queue()
        self._command_queue = queue.Queue()
        self._hooks = {}  # pid -> hook handle
        self._thread = None
        self._running = False
        self._callback = _WinEventProcType(self._on_event)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def watch_pid(self, pid):
        if pid:
            self._command_queue.put(("watch", pid))

    def unwatch_pid(self, pid):
        if pid:
            self._command_queue.put(("unwatch", pid))

    def _on_event(self, hWinEventHook, event, hwnd, idObject, idChild, idEventThread, dwmsEventTime):
        try:
            self.event_queue.put_nowait(hwnd)
        except Exception:
            pass

    def _run(self):
        # 👑 SetWinEventHookは「呼び出したスレッド」にイベントが配送される
        # ため、フックの登録・解除もこのスレッド自身で行う必要がある。
        # メインスレッドからのwatch_pid/unwatch_pid要求はcommand_queue経由
        # で受け取り、このループの中で実際に登録する。
        user32 = ctypes.windll.user32
        msg = wintypes.MSG()
        while self._running:
            while True:
                try:
                    action, pid = self._command_queue.get_nowait()
                except queue.Empty:
                    break
                try:
                    if action == "watch" and pid not in self._hooks:
                        h = user32.SetWinEventHook(
                            EVENT_OBJECT_NAMECHANGE, EVENT_OBJECT_NAMECHANGE,
                            0, self._callback, pid, 0,
                            WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS,
                        )
                        if h:
                            self._hooks[pid] = h
                    elif action == "unwatch" and pid in self._hooks:
                        user32.UnhookWinEvent(self._hooks.pop(pid))
                except Exception:
                    pass

            if user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, 1):
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            else:
                time.sleep(0.01)

        for h in list(self._hooks.values()):
            try:
                user32.UnhookWinEvent(h)
            except Exception:
                pass
        self._hooks.clear()
# ===== ✂️ utils/win_event_watcher.py END ✂️ =====
