# ===== ✂️ utils/diagnostics.py START ✂️ =====
"""
「探したが見つからなかった」を黙って握りつぶさないための、共通の記録先。

👑 2026-09-16に作成。きっかけはkosakaPCの「レイヤ保存が一度も動かない」を
丸1日かけて追ったこと。原因は、jw_cadのプロファイルにGCOM行が無いのを
**無言でスキップ**していたことだった。同じ形の処理がコード全体にあり、
`except Exception: pass` を全件(88箇所)分類したところ、37件が自動操作の
中核に集中していた(utils/line_attr_dialog.py、utils/layer_snapshot.py、
utils/send_command.py = レイヤ保存・モードボタン・状態連動)。

分類して分かった一番大事なこと:

    直すべきは`except`そのものではない。中身はほぼ全部この形だった。

        def cb(child, _extra):
            try:
                if win32gui.GetClassName(child) == ...:
                    found.append(child)
            except Exception:
                pass          # ← ここは無視でよい(消えた窓を触っただけ)
            return True
        try:
            win32gui.EnumChildWindows(hwnd, cb, None)
        except Exception:
            pass
        return found[0] if found else None   # ← **本当の問題はここ**

    例外を潰していることより、**「見つからなかったことが誰にも伝わらない」**
    ことが問題。呼び出し元はNoneを受け取って静かに諦め、利用者には
    「なぜか動かない」としか見えない。

そこでこのモジュールでは:
  - note(key, message) で「今どうなっているか」を記録する
  - 前回と同じ内容なら**ログには出さない**(毎tick呼ばれても溢れない)
  - 変化した時だけログへ出す(復旧も「見つかりました」として1回出る)
  - describe() で現在の全記録を取り出せる(起動時の環境スナップショット用)

スレッドから呼ばれることがあるため、辞書の更新だけに留めて重い処理はしない。
"""
import threading

_lock = threading.Lock()
_sink = None
_last = {}


def set_log_sink(fn):
    """ログ出力先を1回だけ登録する(main.pyのwrite_system_logを想定)。
    登録前のnote()は記録だけ行い、ログには出ない(起動直後の取りこぼしは
    describe()で後からまとめて拾える)。"""
    global _sink
    _sink = fn


def note(key, message, level="⚠️"):
    """`key`(探した対象の名前)の現在の状況を記録する。前回と内容が変われば
    ログにも出す。成功時はok()を使う。"""
    with _lock:
        if _last.get(key) == message:
            return
        _last[key] = message
    if _sink:
        try:
            _sink(f"{level} [診断] {key}: {message}")
        except Exception:
            pass


def ok(key, message="見つかりました"):
    """正常に見つかった時。直前が異常だった場合だけ「直った」ことがログに
    残る(毎回出すとログが埋まるため)。"""
    note(key, message, level="✅")


def describe():
    """現在の全記録。起動時の環境スナップショット等でまとめて出す用。"""
    with _lock:
        return dict(_last)
# ===== ✂️ utils/diagnostics.py END ✂️ =====
