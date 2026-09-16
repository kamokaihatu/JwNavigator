# ===== ✂️ controllers/layer_save.py START ✂️ =====
"""
「電灯配線図」のようなレイヤ状態の保存/復元ボタン(kind="layer_snapshot")の
処理一式。

👑 2026-09-16: main.pyから切り出した。切り出す前のmain.pyは2,300行・60超の
メソッドを持つ1クラスで、パレット生成・状態監視・レイヤ保存・モードボタン・
トレイを全部抱えていた。同日「パレットを1枚にできない」不具合を追ったとき、
`SIDES[0]`(=左パレットが必ず在る)という前提が3箇所に散らばっていて修正漏れ
しかけたのが直接のきっかけ。

**動作は一切変えていない**。メソッドをそのままmixinへ移しただけで、
`self.xxx`の参照先は従来どおりJwNavigatorManagerのインスタンス。状態
(self._pending_layer_saves等)もJwNavigatorManager.__init__のまま置いてある
(状態まで動かすと変更が大きくなり、動作が変わらないことを確認しづらい)。
"""
import os
import threading
import time
import uuid
import tkinter as tk
from tkinter import messagebox

from utils import command_master
from utils import layer_snapshot
from utils import palette_config
from utils.send_command import get_command_checked_states
from widgets.settings_window import TextInputDialog


class LayerSaveMixin:
    # <snapshot_id>.jwl)が無ければ保存フロー、あれば復元フローへ分岐する。
    # 詳細はdoc/シート管理_設計メモ.md、doc/HANDOFF_layer_control.md参照。
    def handle_layer_snapshot_click(self, hwnd, entry, trigger_btn=None, side_type=None):
        # 👑 保存/復元は別ボタン(entry["role"])に分かれている(右クリック=
        # 保存は直感的でないというユーザー判断、2026-09-04)。
        # 👑 trigger_btnはtoolbar.py側で押した瞬間にset_selected()済み
        # (「押した瞬間に時間がかかる旨を表示したい」への対応、既存の
        # 凹み表示を流用)。この関数の全ての出口でclear_selected()を
        # 呼び戻す必要がある(即座に終わる分岐も含む)。
        if entry.get("role") == palette_config.LAYER_SNAPSHOT_ROLE_SAVE:
            self._start_layer_snapshot_save(hwnd, trigger_btn, side_type)
            return
        dest_path = palette_config.layer_snapshot_path(entry.get("snapshot_id", ""))
        if os.path.isfile(dest_path):
            self._restore_layer_snapshot(hwnd, dest_path, entry, trigger_btn)
        else:
            self.write_system_log(f"❌ [レイヤ復元] {entry.get('name')} はまだ保存されていません(対応する保存ボタンを先に押してください)")
            if trigger_btn:
                trigger_btn.clear_selected()

    def _capture_current_command(self, hwnd):
        # 👑 レイヤ保存/復元の自動化(外部変形の起動、環境設定ファイルの
        # 読込みダイアログ)は、進行中の作図コマンド(線・円等)を一旦
        # キャンセルしてしまう。押す前にどのコマンドがCHECKED中だったかを
        # 覚えておき、完了後に送り直すことで元の作図モードへ戻す
        # (ユーザー指摘:「これの操作の前のコマンドって記憶してないん
        # だっけ？」「いまは外部変形のコマンドになっちゃってるから」、
        # 2026-09-07)。既存のCHECKEDビット判定(_update_checked_highlight
        # と同じ仕組み)を流用する。
        id_map = {}
        for row in command_master.list_available_commands():
            if row.get("command_kind") != "メイン":
                continue
            id_cmd = command_master.get_id_command(row["command_id"])
            if id_cmd:
                id_map[id_cmd] = row["command_id"]
        if not id_map:
            return None
        checked_states = get_command_checked_states(hwnd, id_map.keys())
        checked_id = next((i for i, v in checked_states.items() if v is True), None)
        return id_map.get(checked_id) if checked_id is not None else None

    def _restore_captured_command(self, hwnd, command_id):
        if command_id:
            self.logged_execute_command(hwnd, command_id)

    def _show_save_notice(self):
        # 👑 保存中、裏でcmdが一瞬走るだけだと「やってる感が無く、
        # 終わったのが分かりにくい」との指摘(2026-09-09)。音は却下
        # だったので、常に最前面の目立つバナーを画面に出す。ボタンの
        # 「保存中…」表示より広い範囲でひと目で分かるようにする狙い。
        self._hide_save_notice()
        try:
            win = tk.Toplevel(self.root)
            win.overrideredirect(True)
            win.attributes("-topmost", True)
            win.configure(bg="#ffcc00")
            label = tk.Label(
                win, text="レイヤ情報保存中… 触らないでください", bg="#ffcc00", fg="#000000",
                font=("Meiryo UI", 14, "bold"), padx=20, pady=10,
            )
            label.pack()
            win.update_idletasks()
            w = win.winfo_reqwidth()
            h = win.winfo_reqheight()
            sw = win.winfo_screenwidth()
            win.geometry(f"{w}x{h}+{(sw - w) // 2}+40")
            self._save_notice_window = win
        except Exception as e:
            self.write_system_log(f"⚠️ 保存中バナー表示エラー: {str(e)}")
            self._save_notice_window = None

    def _hide_save_notice(self):
        if self._save_notice_window is not None:
            try:
                self._save_notice_window.destroy()
            except Exception:
                pass
            self._save_notice_window = None

    def _start_layer_snapshot_save(self, hwnd, trigger_btn, side_type):
        # 👑 2026-09-04設計: 保存ボタンは汎用の1個のみで、押すたびに名前を
        # 聞く(「保存の度に名前を付けたい」)。既存の復元ボタンに同名の
        # ものがあれば上書き確認、無ければ新しい復元ボタンをこの保存
        # ボタンのすぐ後ろに自動で追加する(「保存ボタンは1個で復元
        # ボタンをたくさん」)。
        if hwnd in self._pending_layer_saves:
            self.write_system_log("[レイヤ保存] 既に保存待機中です")
            if trigger_btn:
                trigger_btn.clear_selected()
            return

        save_entry = trigger_btn.entry if trigger_btn and trigger_btn.entry else None
        fast = bool(save_entry.get("fast")) if save_entry else False
        auto = bool(save_entry.get("auto")) if save_entry else False
        if fast and auto:
            note = "選択も自動で行います。保存には5〜10秒程度かかります"
        elif fast:
            note = "先に図形を1つ以上選択しておいてください。保存には5〜10秒程度かかります"
        else:
            note = "保存には10〜20秒程度かかります"
        dlg = TextInputDialog(
            self.root, title="レイヤ情報を保存", label="名前:", initial="",
            note=note,
        )
        self.root.wait_window(dlg)
        name = dlg.result
        if not name:
            if trigger_btn:
                trigger_btn.clear_selected()
            return

        config = palette_config.load_config()
        existing_id = None
        for side in palette_config.all_side_keys(config):
            for group in palette_config.side_config(config, side)["groups"]:
                for btn in group.get("buttons") or []:
                    if (
                        btn.get("kind") == palette_config.BUTTON_KIND_LAYER_SNAPSHOT
                        and btn.get("role") == palette_config.LAYER_SNAPSHOT_ROLE_RESTORE
                        and btn.get("snapshot_name") == name
                    ):
                        existing_id = btn.get("snapshot_id")
                        break
                if existing_id:
                    break
            if existing_id:
                break

        if existing_id:
            if not messagebox.askyesno(
                "レイヤ情報を保存", f"「{name}」は既に保存されています。上書きしますか?", parent=self.root,
            ):
                if trigger_btn:
                    trigger_btn.clear_selected()
                return
            snapshot_id = existing_id
        else:
            snapshot_id = uuid.uuid4().hex
            save_name = (save_entry.get("name") if save_entry else None) or "ﾚｲﾔ\n保存"
            # 👑 新規作成した復元ボタン自身の設定画面には普段来ないため
            # (ユーザー指摘)、保存ボタン側の「既定値」をここで引き継ぐ。
            default_keep = save_entry.get("default_keep_write_layer", True) if save_entry else True
            target_side, gi, insert_at = self._find_layer_save_insert_position(config, side_type, save_name)
            restore_btn = palette_config.new_layer_snapshot_button(
                name, palette_config.LAYER_SNAPSHOT_ROLE_RESTORE,
                snapshot_id=snapshot_id, snapshot_name=name,
            )
            restore_btn["keep_write_layer"] = default_keep
            palette_config.side_config(config, target_side)["groups"][gi]["buttons"].insert(insert_at, restore_btn)
            palette_config.save_config(config)
            self._refresh_all_toolbar_buttons()

        dest_path = palette_config.layer_snapshot_path(snapshot_id)
        captured_command = self._capture_current_command(hwnd)
        wait_note = "5〜10秒程度かかります" if fast else "10〜20秒程度かかります"
        self.write_system_log(f"[レイヤ保存] {name} を保存中です({wait_note})…")
        # 👑 凹み表示だけだと物足りない、保存中とはっきり分かる表示が
        # 欲しいとの要望(2026-09-08)。ボタンの表示名を一時的に「保存中…」
        # に差し替える(config側のnameは触らない、ウィジェット側の見た目
        # だけの一時変更)。完了時に元へ戻す(_check_pending_layer_saves)。
        # 👑 新しい名前で保存した直後は復元ボタンが自動追加され、
        # _refresh_all_toolbar_buttons()でパレット全体(このtrigger_btn
        # 自身も)が作り直される。widgets/button.pyのload_and_draw()側で
        # 破棄済みウィジェットへの呼び出しを無害化済みなので、ここでは
        # 素直に呼ぶだけでよい。
        original_label = None
        if trigger_btn:
            original_label = trigger_btn.name
            trigger_btn.name = "保存中…"
            trigger_btn.load_and_draw()
        self._show_save_notice()

        def worker():
            if fast and auto:
                trigger_fn = layer_snapshot.trigger_save_fast_auto
            elif fast:
                trigger_fn = layer_snapshot.trigger_save_fast
            else:
                trigger_fn = layer_snapshot.trigger_save
            pending = trigger_fn(hwnd, log=self.write_system_log)
            self.root.after(
                0,
                lambda: self._on_layer_save_triggered(
                    hwnd, dest_path, {"name": name}, pending, trigger_btn, captured_command, original_label,
                ),
            )

        threading.Thread(target=worker, daemon=True).start()

    def _find_layer_save_insert_position(self, config, preferred_side, save_name):
        # 👑 新しい復元ボタンは、押された保存ボタンのすぐ後ろに挿入する
        # (ユーザー決定: 「置き場所は保存ボタンのすぐ後ろが自然」)。
        # 同名の保存ボタンが複数ある場合はpreferred_side側を優先する。
        all_keys = palette_config.all_side_keys(config)
        sides_order = [preferred_side] + [s for s in all_keys if s != preferred_side] if preferred_side else all_keys
        for side in sides_order:
            groups = palette_config.side_config(config, side)["groups"]
            for gi, group in enumerate(groups):
                buttons = group.get("buttons") or []
                for bi, btn in enumerate(buttons):
                    if (
                        btn.get("kind") == palette_config.BUTTON_KIND_LAYER_SNAPSHOT
                        and btn.get("role") == palette_config.LAYER_SNAPSHOT_ROLE_SAVE
                        and btn.get("name") == save_name
                    ):
                        return side, gi, bi + 1
        # 見つからなければ、優先サイドの末尾グループの末尾へ
        side = preferred_side or (all_keys[0] if all_keys else palette_config.SIDES[0])
        groups = palette_config.side_config(config, side)["groups"]
        if not groups:
            groups.append(palette_config.new_group())
        return side, len(groups) - 1, len(groups[-1]["buttons"])

    def _refresh_all_toolbar_buttons(self):
        # 👑 新しい復元ボタンの追加はconfig.json全体(両面)に影響するため、
        # 開いている全てのjw_cadウィンドウのパレットを更新する。
        for hwnd in list(self.active_launchers.keys()):
            self._refresh_toolbar_buttons(hwnd)

    def _restore_trigger_label(self, trigger_btn, original_label):
        if trigger_btn and original_label is not None:
            trigger_btn.name = original_label
            trigger_btn.load_and_draw()

    def _on_layer_save_triggered(self, hwnd, dest_path, entry, pending, trigger_btn, captured_command=None, original_label=None):
        if not pending:
            self.write_system_log(f"❌ [レイヤ保存] 開始できませんでした(jw_cadの実行フォルダ特定失敗、またはjw_cadの前面化に失敗) name={entry.get('name')}")
            self._hide_save_notice()
            if trigger_btn:
                trigger_btn.clear_selected()
            self._restore_trigger_label(trigger_btn, original_label)
            self._restore_captured_command(hwnd, captured_command)
            return
        self._pending_layer_saves[hwnd] = {
            "pending": pending, "dest_path": dest_path, "started_at": time.time(), "name": entry.get("name"),
            "trigger_btn": trigger_btn, "captured_command": captured_command, "original_label": original_label,
        }
        # 👑 monitor_loop()の1秒周期だけに頼ると検知が最大1秒近く遅れる
        # ため、保存待ちの間だけ短い周期(0.3秒)で追加ポーリングする
        # (ユーザー要望:「保存もう少し早くならないかな」)。
        self.root.after(300, self._check_pending_layer_saves)

    def _restore_layer_snapshot(self, hwnd, jwl_path, entry, trigger_btn):
        # 👑 保存側と同じ理由でtrigger_restore()も別スレッドで実行する。
        keep_write_layer = entry.get("keep_write_layer", True)
        captured_command = self._capture_current_command(hwnd)

        def worker():
            ok = layer_snapshot.trigger_restore(
                hwnd, jwl_path, keep_write_layer=keep_write_layer, log=self.write_system_log,
            )
            self.root.after(0, lambda: self._on_layer_restore_done(hwnd, entry, ok, trigger_btn, captured_command))

        threading.Thread(target=worker, daemon=True).start()

    def _on_layer_restore_done(self, hwnd, entry, ok, trigger_btn, captured_command=None):
        if ok:
            self.write_system_log(f"[レイヤ復元] {entry.get('name')} を適用しました")
        else:
            self.write_system_log(f"❌ [レイヤ復元] {entry.get('name')} の適用に失敗しました(ダイアログが見つかりませんでした)")
        if trigger_btn:
            trigger_btn.clear_selected()
        self._restore_captured_command(hwnd, captured_command)

    def _check_pending_layer_saves(self):
        # 👑 monitor_loop()(1秒周期)に加え、保存待ちの間は_start_layer_
        # snapshot_save()から0.3秒周期でも自発的に呼ばれる(下の再スケジュール
        # 部分参照)。完了(LAYER_RESTORE.JWLの更新)をここで監視する。
        if not self._pending_layer_saves:
            return
        # 👑 編集可能なレイヤが無い等で外部変形が完了しない場合、以前は
        # 120秒待たないとボタンが凹んだまま(=押せない)戻らなかった
        # (ユーザー報告:「保存おしたら、レイヤ情報を保存が押せなくなった」)。
        # 正常な保存は10〜20秒程度で終わる(重い図面・jw_cadのundo履歴の
        # 蓄積状況次第で21秒台も実機で観測済み、2026-09-09)ため、
        # 誤タイムアウトを避けて余裕を見て30秒で見切る。
        LAYER_SAVE_TIMEOUT_SEC = 30
        now = time.time()
        for hwnd in list(self._pending_layer_saves.keys()):
            state = self._pending_layer_saves[hwnd]
            trigger_btn = state.get("trigger_btn")
            if now - state["started_at"] > LAYER_SAVE_TIMEOUT_SEC:
                self.write_system_log(
                    f"❌ [レイヤ保存] {state['name']} がタイムアウトしました"
                    f"(編集可能なレイヤが無い等で、選択する図形が無かった可能性があります)"
                )
                self._hide_save_notice()
                if trigger_btn:
                    trigger_btn.clear_selected()
                self._restore_trigger_label(trigger_btn, state.get("original_label"))
                self._restore_captured_command(hwnd, state.get("captured_command"))
                del self._pending_layer_saves[hwnd]
                continue
            if layer_snapshot.check_save_complete(state["pending"]):
                self._hide_save_notice()
                try:
                    layer_snapshot.finalize_save(state["pending"], state["dest_path"])
                    self.write_system_log(f"[レイヤ保存] {state['name']} を保存しました")
                    # 👑 保存の自動化(B_MARK)が書込レイヤに作図した目印点を、
                    # 「戻る」で後始末する(連鎖の2周バグで複数個できていても
                    # trace.txtの記録数ぶん消す、2026-09-09)。「戻る」の
                    # 間隔待ちでUIスレッドを固まらせないよう別スレッドで行う。
                    pending_for_cleanup = state["pending"]
                    threading.Thread(
                        target=layer_snapshot.cleanup_mark_points,
                        args=(hwnd, pending_for_cleanup),
                        kwargs={"log": self.write_system_log},
                        daemon=True,
                    ).start()
                    # 👑 _refresh_toolbar_buttons()はNavButtonを作り直す
                    # ため、古いtrigger_btnへのclear_selected()/ラベル
                    # 復元は不要(新しいボタンは元の名前で生成される)。
                    # 👑 保存済みバッジ(色)は`.jwl`ファイルの有無で決まる
                    # 全ウィンドウ共通の状態なのに、保存操作をした
                    # ウィンドウのパレットしか再描画していなかったため、
                    # 他のjw_cadウィンドウでは保存後もバッジがグレーの
                    # ままになっていた(kamo報告、2026-09-09)。全ウィンドウ
                    # 分を再描画するように修正。
                    self._refresh_all_toolbar_buttons()
                except Exception as exc:
                    self.write_system_log(f"❌ [レイヤ保存] {state['name']} の保存に失敗しました: {exc}")
                    if trigger_btn:
                        trigger_btn.clear_selected()
                    self._restore_trigger_label(trigger_btn, state.get("original_label"))
                self._restore_captured_command(hwnd, state.get("captured_command"))
                del self._pending_layer_saves[hwnd]
        if self._pending_layer_saves and not self._shutdown_requested:
            self.root.after(300, self._check_pending_layer_saves)

    def _refresh_toolbar_buttons(self, hwnd):
        # 👑 _manage_palette_lifecycle()はhwndの出現/消滅しか見ておらず、
        # 既存ツールバーの再描画はしないため、レイヤ保存ボタンの「保存済」
        # 表示切替のように「configは変わったがhwnd自体は変わっていない」
        # ケースでは明示的にload_and_build_buttons()を呼ぶ必要がある。
        launcher = self.active_launchers.get(hwnd)
        if not launcher:
            return
        for toolbar in launcher.values():
            if toolbar:
                try:
                    toolbar.load_and_build_buttons()
                except Exception as exc:
                    self.write_system_log(f"❌ ツールバー再描画失敗: {exc}")
# ===== ✂️ controllers/layer_save.py END ✂️ =====
