# ===== ✂️ controllers/auto_attr.py START ✂️ =====
"""
「補助線」「配線」等のモードボタン(kind="auto_attr")の処理一式。
押した瞬間の線属性を覚えて指定の線属性へ切替→切替先コマンドへ移動し、
他コマンドへ切り替わったら自動で元へ戻す。詳細はdoc/補助線ボタン_要件書.md。

👑 2026-09-16: main.pyから切り出した(理由はcontrollers/layer_save.pyの
冒頭コメント参照)。**動作は一切変えていない**。メソッドをそのまま
mixinへ移しただけで、状態(self._auto_attr_pending)はJwNavigatorManager.
__init__のまま置いてある。
"""
import time

from utils import auto_attr_state
from utils import command_master
from utils import line_attr_dialog
from utils.send_command import get_command_checked_states, get_command_pressed_states


class AutoAttrMixin:
    # 👑 「補助線」「配線」等(kind="auto_attr")。押した瞬間の線属性を覚えて
    # 指定の線属性へ切替→切替先コマンドへ移動、その後hwndごとに監視して
    # 他コマンドへ切り替わったら自動で元の線属性へ戻す。詳細はdoc/
    # 補助線ボタン_要件書.md参照。_auto_attr_pendingは__init__で初期化。
    # 切替先コマンドはボタンごとに設定可能(既定は直線=C001、ユーザー要望:
    # 「他のコマンド選択することできる？連続線とか」)。
    AUTO_ATTR_DEFAULT_TARGET_COMMAND = "C001"  # 直線
    # 👑 対象コマンドへの切替がjw_cad側で確認できないまま補助線モードに
    # 閉じ込められるのを防ぐための上限(_check_auto_attr_revert参照)。
    # 正常時はtick1回(1秒未満)でconfirmedになるため、余裕を持った値。
    AUTO_ATTR_CONFIRM_TIMEOUT_SEC = 5.0

    def start_auto_attr_sequence(self, hwnd, entry, trigger_btn=None):
        # 👑 既にこのhwndで補助線系モードが有効な状態でもう一度押した場合
        # (同じボタンの連打、または別の補助線系ボタンへの切替)、今の
        # jw_cad側の線属性は既に補助線系プリセットに変わってしまっている
        # ため、ここで読み直すと本来の「元の線属性」を上書きして失って
        # しまう(ユーザー報告: 「もう一度押すと逃がした線種情報が消える」)。
        # 既にpendingがあれば、その"original"を引き継ぐ。
        existing = self._auto_attr_pending.get(hwnd)
        # 👑 「補助線2回目押したときに水平垂直のチェック外すのお願いする
        # の忘れてた」→「そこは直線と同じ挙動にしたい」。jw_cadは同じ
        # 描画ツールを再選択すると水平・垂直チェックを自分で外す(実機
        # 確認済み、_check_auto_attr_revert付近の既存コメント参照)。
        # 初回押下時だけJwNavigator側で明示的にONへ再アサートし、同じ
        # 補助線ボタンの2回目以降の押下ではその上書きをせず、直線を
        # 再選択した時と同じ(jw_cad任せの)挙動に任せる。
        same_button_repress = bool(existing and existing.get("trigger_btn") is trigger_btn)
        if existing:
            original = existing["original"]
            old_trigger = existing.get("trigger_btn")
            if old_trigger and old_trigger is not trigger_btn:
                try:
                    old_trigger.clear_selected()
                except Exception:
                    pass
        else:
            original = line_attr_dialog.read_current_attr(hwnd)
            if original is None:
                self.write_system_log("❌ [補助線系ボタン] 線属性の読み取りに失敗しました。")
                return
            orig_group, orig_layer = line_attr_dialog.read_current_layer_group(hwnd)
            original["group"] = orig_group
            original["layer"] = orig_layer
        ok = line_attr_dialog.apply_attr(
            hwnd, entry.get("line_color"), entry.get("line_type"), entry.get("line_width") or None
        )
        if not ok:
            self.write_system_log("❌ [補助線系ボタン] 線属性の変更に失敗しました。")
            return
        target_group = entry.get("layer_group")
        target_layer = entry.get("layer_number")
        if target_group is not None or target_layer is not None:
            if not line_attr_dialog.set_layer_group(hwnd, target_group, target_layer):
                self.write_system_log("⚠️ [補助線系ボタン] レイヤ切替に失敗しました(線属性は変更済み)。")
            else:
                # 👑 2026-09-16: 切り替えた「結果」を必ず残す。狙いどおりに
                # なったかはログを見れば一発で分かるようにしておく
                # (レイヤとレイヤグループの取り違えを、今日ログから推測で
                # 追う羽目になったため。line_attr_dialogの
                # describe_layer_bar_detection()も参照)。
                got_group, got_layer = line_attr_dialog.read_current_layer_group(hwnd)
                ok = (target_group is None or got_group == target_group) and (
                    target_layer is None or got_layer == target_layer
                )
                self.write_system_log(
                    f"{'🔎' if ok else '⚠️'} [補助線系ボタン] レイヤ切替 "
                    f"目標=(G{target_group}, L{target_layer}) → "
                    f"実際=(G{got_group}, L{got_layer}){'' if ok else ' ← 一致しません'}"
                )
        target_command = entry.get("target_command") or self.AUTO_ATTR_DEFAULT_TARGET_COMMAND
        self._auto_attr_pending[hwnd] = {
            "original": original, "confirmed": False, "trigger_btn": trigger_btn,
            "horizontal_vertical": bool(entry.get("horizontal_vertical")),
            "target_command": target_command,
            # 👑 2026-09-16: 対象コマンドがCHECKEDにならないまま固まった場合の
            # 保険用(_check_auto_attr_revert参照)。
            "started_at": time.time(),
        }
        auto_attr_state.save_pending(self._auto_attr_pending)
        # 👑 2026-09-16: 他人のPCでの解析用。凹んだまま戻らなくなった時に
        # 「何を適用して、どのコマンドへ切り替えようとしたのか」がログだけで
        # 追えるようにする(kosakaPCの調査で、この情報が無いため往復した)。
        self.write_system_log(
            f"🔎 [補助線系ボタン] 開始 name={entry.get('name')} "
            f"線色={entry.get('line_color')} 線種={entry.get('line_type')} "
            f"線幅={entry.get('line_width')} レイヤG={target_group} レイヤ={target_layer} "
            f"対象コマンド={target_command}(idCommand={command_master.get_id_command(target_command)}) "
            f"水平垂直={bool(entry.get('horizontal_vertical'))} "
            f"元の属性={original}"
        )
        if trigger_btn:
            # 👑 「凹むの遅い」という指摘のため、tickでのCHECKEDビット監視を
            # 待たず即座に凹ませる。この凹み表示は独立管理(トリガー自身の
            # command_keyは変更しない)なので、本物の「線」ボタンの表示には
            # 一切影響しない。
            trigger_btn.set_selected()
        self.logged_execute_command(hwnd, target_command)
        if entry.get("horizontal_vertical") and not same_button_repress:
            # 👑 「水平･垂直」は直線コマンドの条件設定バー上のコントロール
            # で、切替直後は反映がまだ間に合っていないことがあるため、
            # 少し待ってからクリックする(実機調整の値)。ただし同じ補助線
            # ボタンの2回目以降の押下では強制ONし直さない(「そこは直線と
            # 同じ挙動にしたい」＝jw_cad自身が同じツール再選択時に外す
            # 動きへ任せる)。
            self.root.after(200, lambda: line_attr_dialog.set_horizontal_vertical(hwnd, True))

    def _check_auto_attr_revert(self, hwnd):
        pending = self._auto_attr_pending.get(hwnd)
        if not pending:
            return
        line_id = command_master.get_id_command(pending["target_command"])
        checked = get_command_checked_states(hwnd, [line_id]).get(line_id)
        # 👑 2026-09-16: CHECKED判定の遷移だけを残す(毎tickは出さない)。
        # Noneが出続けるのか、Falseのままなのかで原因が分かれるため
        # (send_command.pyのコメント: None=対象ボタンが表示中のツールバーに
        # 無い=判定不能)。他人のPCで1回動かせば切り分く材料になる。
        if pending.get("last_checked", "init") != checked:
            pending["last_checked"] = checked
            self.write_system_log(
                f"🔎 [補助線系ボタン] CHECKED判定={checked} "
                f"(対象={pending['target_command']}, confirmed={pending['confirmed']})"
            )
        if checked is True:
            # 👑 直線への切替がjw_cad側に反映されたことを確認できるまでは
            # 「まだ切り替わっていないだけ」の可能性があるので戻し判定に
            # 入らない(切替直後の1tick目でFalse/Noneを誤って「離脱した」と
            # 判定してしまう競合を避けるため)。
            if not pending["confirmed"]:
                pending["confirmed"] = True
                auto_attr_state.save_pending(self._auto_attr_pending)
            # 👑 「補助線から抜ける時、jw_cad本体の直線ボタンでは抜けられ
            # ないのか」への対応。C001は既にCHECKEDのままなので上のFalse
            # 判定では検知できないが、jw_cad自身のツールバーを物理的に
            # クリックした瞬間だけTBSTATE_PRESSEDが立つ(JwNavigator経由の
            # 送信では立たない)ので、それを「抜ける合図」として拾う。
            # logged_execute_command側のフック(JwNavigatorパレット経由の
            # 「線」クリック用)と対になる、jw_cad本体側クリック用の経路。
            pressed = get_command_pressed_states(hwnd, [line_id]).get(line_id)
            if pressed is True:
                self._revert_auto_attr(hwnd)
            return
        if checked is False and pending["confirmed"]:
            self._revert_auto_attr(hwnd)
            return

        # 👑 2026-09-16: ここから下は「対象コマンドが一度もCHECKEDにならない」
        # 環境向けの保険(kosakaPCで発覚: ボタンが凹んだまま戻らず、線属性が
        # 補助線のまま固定されて「線がひけない」状態になった)。
        # 上の2分岐は両方とも`confirmed`がTrueになることが前提で、confirmedは
        # `checked is True`でしか立たない。つまりCHECKEDが読めない(None=対象の
        # ボタンが今表示中のツールバーページに無い、send_command.pyのコメント
        # 参照)か、ずっとFalse(コマンド切替自体が効いていない)環境では、
        # **モードから抜ける経路が一切存在しなかった**。
        if pending["confirmed"]:
            return
        started_at = pending.get("started_at")
        if started_at is None:
            # JwNavigator再起動をまたいで復元されたpendingには無いので、
            # 見つけた時点を起点にする(即座に保険が働かないようにする)。
            pending["started_at"] = time.time()
            return
        if time.time() - started_at < self.AUTO_ATTR_CONFIRM_TIMEOUT_SEC:
            return
        self.write_system_log(
            f"⚠️ [補助線系ボタン] 対象コマンド({pending['target_command']})の選択状態を"
            f"{self.AUTO_ATTR_CONFIRM_TIMEOUT_SEC:.0f}秒間確認できなかったため、"
            f"線属性を元に戻します(CHECKED判定={checked})。"
        )
        self._revert_auto_attr(hwnd)

    def _revert_auto_attr(self, hwnd):
        pending = self._auto_attr_pending.pop(hwnd, None)
        if not pending:
            return
        auto_attr_state.save_pending(self._auto_attr_pending)
        trigger_btn = pending.get("trigger_btn")
        if trigger_btn:
            try:
                trigger_btn.clear_selected()
                # 👑 箱(フライアウト)の中身として補助線系ボタンが選ばれて
                # いた場合、command_keyを使わない独自ハイライト管理のため
                # clear_selected()内蔵の箱復帰ロジックでは拾えない。
                # 明示的に箱自身の顔へ戻す(単体の補助線ボタンならkindが
                # auto_attrなので中で何もしない)。
                trigger_btn.revert_group_face()
            except Exception:
                pass
        original = pending["original"]
        line_attr_dialog.apply_attr(hwnd, original["color"], original["type"], original["width"] or None)
        orig_group = original.get("group")
        orig_layer = original.get("layer")
        if orig_group is not None or orig_layer is not None:
            line_attr_dialog.set_layer_group(hwnd, orig_group, orig_layer)
        if pending.get("horizontal_vertical"):
            # 👑 「補助線と直線は別コマンドとして扱いたいので、直線を押して
            # 抜けた際に水平垂直が外れるのを回避してほしい」への対応。
            # jw_cad自身が「線」を再選択した時に条件設定バーの水平･垂直
            # チェックを内部的にリセットしてしまう挙動が実機で見られた
            # ため、少し待ってから改めてONを再アサートし直す(まだ直線
            # コマンドのままなのでコントロール自体は引き続き存在する。
            # 別コマンドへ離脱した場合はコントロールが見つからずFalseに
            # なるだけで無害)。
            self.root.after(200, lambda: line_attr_dialog.set_horizontal_vertical(hwnd, True))
        self.write_system_log("↩️ [補助線系ボタン] 線属性・レイヤを元に戻しました。")
# ===== ✂️ controllers/auto_attr.py END ✂️ =====
