# ===== ✂️ widgets/side_panel_edit.py START ✂️ =====
"""
設定画面のパレット編集操作(ボタンの追加/削除/並べ替え、グループ化/解除)。

👑 2026-09-16: widgets/settings_window.pyのSidePanel(1,082行・45メソッド)から
切り出した。この範囲は連続した346行にまとまっており、責務も
「一覧に対する編集操作」で一貫している。

**動作は一切変えていない**。メソッドをそのままmixinへ移しただけで、
`self.xxx`の解決先は従来どおりSidePanelのインスタンス。UIの組み立て
(_build_*)や詳細フォームの読み書き(_load_detail等)は移していないため、
状態の持ち方は変わっていない。
"""
import os
import tkinter as tk
from tkinter import messagebox

from utils import palette_config
from widgets.dialogs import CommandPickerDialog, GroupContentsDialog, TextInputDialog


class SidePanelEditMixin:
    def _move_up(self):
        # 👑 複数選択時は、選ばれた全ボタンをまとめて1つ上へ移動する
        # （昇順に処理すると、隣接した選択でも正しく塊のまま繰り上がる）。
        if self._selected_group is None or not self._selected_indices:
            return
        gi = self._selected_group
        buttons = self.side_cfg["groups"][gi]["buttons"]
        indices = sorted(self._selected_indices)
        if indices[0] <= 0:
            return
        for ii in indices:
            buttons[ii - 1], buttons[ii] = buttons[ii], buttons[ii - 1]
        self._selected_indices = [ii - 1 for ii in indices]
        self._rebuild_groups()

    def _move_down(self):
        if self._selected_group is None or not self._selected_indices:
            return
        gi = self._selected_group
        buttons = self.side_cfg["groups"][gi]["buttons"]
        indices = sorted(self._selected_indices, reverse=True)
        if indices[0] >= len(buttons) - 1:
            return
        for ii in indices:
            buttons[ii + 1], buttons[ii] = buttons[ii], buttons[ii + 1]
        self._selected_indices = [ii + 1 for ii in indices]
        self._rebuild_groups()

    def _move_prev_group(self):
        if self._selected_group is None or not self._selected_indices:
            return
        gi = self._selected_group
        if gi <= 0:
            return
        groups = self.side_cfg["groups"]
        indices = sorted(self._selected_indices)
        moved = [groups[gi]["buttons"][ii] for ii in indices]
        for ii in reversed(indices):
            groups[gi]["buttons"].pop(ii)
        target = groups[gi - 1]["buttons"]
        insert_at = len(target)
        target[insert_at:insert_at] = moved
        self._selected_group = gi - 1
        self._selected_indices = list(range(insert_at, insert_at + len(moved)))
        self._rebuild_groups()

    def _move_next_group(self):
        if self._selected_group is None or not self._selected_indices:
            return
        gi = self._selected_group
        groups = self.side_cfg["groups"]
        if gi >= len(groups) - 1:
            return
        indices = sorted(self._selected_indices)
        moved = [groups[gi]["buttons"][ii] for ii in indices]
        for ii in reversed(indices):
            groups[gi]["buttons"].pop(ii)
        target = groups[gi + 1]["buttons"]
        insert_at = len(target)
        target[insert_at:insert_at] = moved
        self._selected_group = gi + 1
        self._selected_indices = list(range(insert_at, insert_at + len(moved)))
        self._rebuild_groups()

    # ---- 追加・削除 ----

    def _existing_ids(self):
        ids = set()
        for group in self.side_cfg["groups"]:
            for btn in group["buttons"]:
                ids.add(btn["command_id"])
        return ids

    def _on_add(self):
        # 👑 「箱を作る」「線属性ボタンを作る」を別メニューに分けたら、
        # コマンドをたくさん追加したい時に毎回そのメニューが挟まって
        # 邪魔という指摘があったため、同じCommandPickerDialogのリストに
        # special_kindsとして混ぜて出す方式にした(常に直接コマンド一覧が
        # 開く、特殊行も同じ多重選択でまとめて拾える)。
        dlg = CommandPickerDialog(
            self.winfo_toplevel(), existing_ids=self._existing_ids(),
            special_kinds=("box", "auto_attr", "layer_snapshot_fast_auto"),
            # 👑 2026-09-14: 通常版・要選択版は実機検証で「全自動」の方が
            # 確実だと分かったため、普段は選ばせずテストモード的に隠す
            # (ユーザー決定、DECISIONS.md参照)。削除はしない。
            test_kinds=("layer_snapshot", "layer_snapshot_fast"),
        )
        self.winfo_toplevel().wait_window(dlg)
        rows = dlg.result
        specials = dlg.result_specials
        if not rows and not specials:
            return

        if rows:
            groups = self.side_cfg["groups"]
            if not groups:
                groups.append(palette_config.new_group())
            gi = self.selected[0] if self.selected is not None else 0
            gi = min(gi, len(groups) - 1)
            insert_at = self.selected[1] + 1 if self.selected is not None and self.selected[0] == gi else len(groups[gi]["buttons"])

            last_index = insert_at
            known_icons = set(palette_config.list_all_icon_names())
            for row in rows:
                default_color = (
                    palette_config.SUB_COMMAND_DEFAULT_COLOR
                    if row.get("command_kind") == "サブ"
                    else palette_config.DEFAULT_COLOR
                )
                default_icon = row.get("default_icon") or palette_config.NO_ICON
                if default_icon not in known_icons:
                    default_icon = palette_config.NO_ICON
                new_btn = palette_config.new_button(
                    row["command_id"], row["toolbar_name"], icon=default_icon, color=default_color
                )
                groups[gi]["buttons"].insert(insert_at, new_btn)
                insert_at += 1
                last_index = insert_at - 1

            # 👑 self.selectedだけ更新しても_rebuild_groups()が古い
            # self._selected_group/_selected_indicesを元に選択を復元して
            # 上書きしてしまう不具合があったため、3つとも合わせて更新する
            # (ユーザー報告: 「すべてが前の状態に戻ってるよ」)。
            # 👑 複数個まとめて選択状態にすると_select_multi()が
            # self.selectedをNoneにしてしまう(単一タプルで表せないため)。
            # このあと特殊行(箱/線属性ボタン)の追加がself.selectedに
            # 依存するので、最後の1個だけを単一選択にしておく。
            self.selected = (gi, last_index)
            self._selected_group = gi
            self._selected_indices = [last_index]
            self._rebuild_groups()

        # 👑 実コマンドの追加を終えてから、特殊行(箱/線属性ボタン)を順に
        # 作る(名前入力を挟むため、まとめての多重選択とは別処理になる)。
        for key in specials:
            if key == "box":
                self._on_add_box()
            elif key == "auto_attr":
                self._on_add_auto_attr()
            elif key == "layer_snapshot":
                self._on_add_layer_snapshot()
            elif key == "layer_snapshot_fast":
                self._on_add_layer_snapshot(fast=True)
            elif key == "layer_snapshot_fast_auto":
                self._on_add_layer_snapshot(fast=True, auto=True)

    def _on_remove(self):
        if self._selected_group is None or not self._selected_indices:
            return
        gi = self._selected_group
        buttons = self.side_cfg["groups"][gi]["buttons"]
        indices = sorted(i for i in self._selected_indices if i < len(buttons))
        if not indices:
            return
        # 👑 レイヤ復元ボタンを削除する時は、保存済みの.JWLファイルも
        # 一緒に消す(ユーザー指摘:「保存したレイヤ情報の削除って
        # 作ってないね」。今まではボタンだけ消えてファイルが孤児として
        # 残り続けていた)。
        has_layer_snapshot = any(
            buttons[i].get("kind") == palette_config.BUTTON_KIND_LAYER_SNAPSHOT
            and buttons[i].get("role") == palette_config.LAYER_SNAPSHOT_ROLE_RESTORE
            for i in indices
        )
        if len(indices) == 1:
            msg = f"「{buttons[indices[0]]['name']}」を削除しますか?"
        else:
            names = "、".join(buttons[i]["name"] for i in indices)
            msg = f"{len(indices)}個({names})を削除しますか?"
        if has_layer_snapshot:
            msg += "\n\n(保存済みのレイヤ情報も一緒に削除されます)"
        if not messagebox.askyesno("確認", msg, parent=self.winfo_toplevel()):
            return
        for i in reversed(indices):
            btn = buttons[i]
            if (
                btn.get("kind") == palette_config.BUTTON_KIND_LAYER_SNAPSHOT
                and btn.get("role") == palette_config.LAYER_SNAPSHOT_ROLE_RESTORE
            ):
                try:
                    os.remove(palette_config.layer_snapshot_path(btn.get("snapshot_id", "")))
                except OSError:
                    pass
            buttons.pop(i)
        self.selected = None
        self._selected_group = None
        self._selected_indices = []
        self._rebuild_groups()

    def _on_add_box(self):
        # 👑 「先に空のフライアウト箱を作って、あとから中身を詰める」
        # フロー。マクロ型は後回しなので、ここでは種別を聞かずフライアウト
        # 固定にする(ユーザー決定: 2026-08-31/2026-09-01)。
        dlg = TextInputDialog(self.winfo_toplevel(), title="グループボタンを追加", label="名前:", initial="新しいグループ")
        self.winfo_toplevel().wait_window(dlg)
        name = dlg.result
        if not name:
            return

        groups = self.side_cfg["groups"]
        if not groups:
            groups.append(palette_config.new_group())
        gi = self.selected[0] if self.selected is not None else 0
        gi = min(gi, len(groups) - 1)
        insert_at = self.selected[1] + 1 if self.selected is not None and self.selected[0] == gi else len(groups[gi]["buttons"])

        new_btn = palette_config.new_group_button(name, palette_config.BUTTON_KIND_FLYOUT, [])
        groups[gi]["buttons"].insert(insert_at, new_btn)
        # 👑 self.selectedだけ更新しても、_rebuild_groups()は
        # self._selected_group/_selected_indices(以前の選択)を元に選択を
        # 復元してしまい、せっかく指したはずの新規ボタンが元の選択に
        # 上書きされて消えてしまう不具合があった(ユーザー報告:「新しい
        # グループつくっても設定画面開かないよ」「すべてが前の状態に
        # 戻ってるよ」)。3つとも合わせて更新する。
        self.selected = (gi, insert_at)
        self._selected_group = gi
        self._selected_indices = [insert_at]
        self._rebuild_groups()
        # 👑 「中身を編集…」ボタンの位置が分かりにくいという指摘のため、
        # 箱を作った流れのまま、名前を決めたら続けて中身編集を開く。
        self._on_edit_group()

    def _on_add_auto_attr(self):
        # 👑 「補助線」「配線」等(kind="auto_attr")の追加。既定値は補助線色/
        # 補助線種(jw_cad標準プリセット)にしておき、配線等で使う場合は
        # 追加後に詳細パネルの線色・線種から選び直してもらう想定
        # (doc/補助線ボタン_要件書.md参照: 標準プリセットが無いので
        # ユーザーが決める方針)。
        dlg = TextInputDialog(self.winfo_toplevel(), title="モードボタンを追加", label="名前:", initial="補助線")
        self.winfo_toplevel().wait_window(dlg)
        name = dlg.result
        if not name:
            return

        groups = self.side_cfg["groups"]
        if not groups:
            groups.append(palette_config.new_group())
        gi = self.selected[0] if self.selected is not None else 0
        gi = min(gi, len(groups) - 1)
        insert_at = self.selected[1] + 1 if self.selected is not None and self.selected[0] == gi else len(groups[gi]["buttons"])

        new_btn = palette_config.new_auto_attr_button(name, horizontal_vertical=True)
        groups[gi]["buttons"].insert(insert_at, new_btn)
        self.selected = (gi, insert_at)
        self._selected_group = gi
        self._selected_indices = [insert_at]
        self._rebuild_groups()

    def _on_add_layer_snapshot(self, fast=False, auto=False):
        # 👑 「電灯配線図」のようなレイヤ状態の保存/復元ボタン(kind=
        # "layer_snapshot")の追加。2026-09-04の設計変更: 保存ボタンは
        # 名前を持たない汎用の1個のみをここで作る(「保存ボタんは1個で
        # 復元ボタンをたくさん」「保存の度に名前を付けたい」という
        # ユーザー要望)。名前を聞くのも、名前ごとに復元ボタンを新設
        # するのも、押した瞬間(main.py: _start_layer_snapshot_save)に
        # 動的に行う。
        # 👑 2026-09-14: fast=Trueは高速版(利用者が事前に選択しておく
        # 前提、utils/layer_snapshot.pyのtrigger_save_fast()参照)。
        # auto=Trueはさらに選択も全自動(trigger_save_fast_auto()参照)。
        # 👑 2026-09-14(名称訂正): 当初「(速)」/「(全自動)」としていたが、
        # 全自動版も同じ高速経路(Ctrl+K直結)を使っており速度は同等なので、
        # 「(速)」という名前が全自動版を遅く見せてしまう誤解を避けるため
        # 「(要選択)」に変更した(DECISIONS.md参照)。
        if auto:
            label = "ﾚｲﾔ\n保存\n(全自動)"
        elif fast:
            label = "ﾚｲﾔ\n保存\n(要選択)"
        else:
            label = "ﾚｲﾔ\n保存"
        new_btn = palette_config.new_layer_snapshot_button(
            label, palette_config.LAYER_SNAPSHOT_ROLE_SAVE, fast=fast, auto=auto,
        )
        groups = self.side_cfg["groups"]
        if not groups:
            groups.append(palette_config.new_group())
        gi = self.selected[0] if self.selected is not None else 0
        gi = min(gi, len(groups) - 1)
        insert_at = self.selected[1] + 1 if self.selected is not None and self.selected[0] == gi else len(groups[gi]["buttons"])
        groups[gi]["buttons"].insert(insert_at, new_btn)
        self.selected = (gi, insert_at)
        self._selected_group = gi
        self._selected_indices = [insert_at]
        self._rebuild_groups()

    def _on_edit_group(self):
        btn = self._selected_button()
        if btn is None or btn.get("kind") not in (palette_config.BUTTON_KIND_FLYOUT, palette_config.BUTTON_KIND_MACRO):
            return
        dlg = GroupContentsDialog(
            self.winfo_toplevel(), btn.get("sub_buttons") or [], manager_ref=self.manager_ref,
            swatch_cache=self.swatch_cache,
        )
        self.winfo_toplevel().wait_window(dlg)
        if dlg.result is not None:
            btn["sub_buttons"] = dlg.result
            self._load_detail()

    def _on_ungroup(self):
        btn = self._selected_button()
        if btn is None or btn.get("kind") not in (palette_config.BUTTON_KIND_FLYOUT, palette_config.BUTTON_KIND_MACRO):
            return
        gi, ii = self.selected
        sub_buttons = btn.get("sub_buttons") or []
        if sub_buttons and not messagebox.askyesno(
            "確認",
            f"「{btn['name']}」を解除して、中の{len(sub_buttons)}個を個別ボタンに戻しますか?",
            parent=self.winfo_toplevel(),
        ):
            return
        buttons = self.side_cfg["groups"][gi]["buttons"]
        buttons[ii:ii + 1] = [dict(sb) for sb in sub_buttons]
        self.selected = None
        self._selected_group = None
        self._selected_indices = []
        self._rebuild_groups()

    def _on_add_group(self):
        # 👑 新しい列を作った直後、選択状態(self.selected等)を更新して
        # いなかったため、そのままボタンを追加すると古い(前から選択中の)
        # 列に入ってしまっていた(ユーザー報告:「新しい列にボタンを直接
        # 配置できない」)。新しい列を選択済み状態にする。
        groups = self.side_cfg["groups"]
        groups.append(palette_config.new_group())
        new_gi = len(groups) - 1
        self.selected = (new_gi, -1)
        self._selected_group = new_gi
        self._selected_indices = []
        self._rebuild_groups()

    def _on_remove_group(self):
        groups = self.side_cfg["groups"]
        if len(groups) <= 1:
            messagebox.showwarning("削除できません", f"{self._group_noun()}は最低1つ必要です。", parent=self.winfo_toplevel())
            return
        gi = self.selected[0] if self.selected is not None else len(groups) - 1
        target = groups[gi]
        if target["buttons"]:
            if not messagebox.askyesno(
                "確認",
                f"{self._group_noun()} {gi + 1} には{len(target['buttons'])}個のボタンがあります。まとめて削除しますか?",
                parent=self.winfo_toplevel(),
            ):
                return
        groups.pop(gi)
        self.selected = None
        self._rebuild_groups()
# ===== ✂️ widgets/side_panel_edit.py END ✂️ =====
