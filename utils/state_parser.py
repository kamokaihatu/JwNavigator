# ===== ✂️ utils/state_parser.py START ✂️ =====
import re
from utils.state_patterns import STATE_DATABASE, RuleId
from utils.parse_result import CompiledRule, ParseResult

# 👑 ステータスバー文言が複数コマンドで完全一致してしまい、文言だけでは
# 区別できないことが実測で確認済みの組み合わせ（state_patterns.pyの
# コメント参照）。片方のWAIT文言しか登録できていない/衝突していて長い方が
# 常に勝つ、という理由でこうなっている。
AMBIGUOUS_GROUPS = [
    frozenset({"STATE_CORNER", "STATE_CHAMFER"}),
    frozenset({"STATE_COORD", "STATE_SHIKI"}),
    frozenset({"STATE_LINE", "STATE_RECT"}),
    frozenset({"STATE_RANGE", "STATE_COPY", "STATE_MOVE"}),
    frozenset({"STATE_CIRCLE", "STATE_POLYGON"}),
]
# 上記の衝突文言側にマッチした時だけ発動するルール名（各コマンド固有の
# ツールチップ文言側は衝突していないので対象外）。
AMBIGUOUS_RULES = {
    "CORNER_WAIT", "SHIKI_WAIT", "LINE_WAIT", "RECT_WAIT",
    "RANGE_WAIT", "COPY_WAIT", "MOVE_WAIT", "CIRCLE_WAIT", "POLYGON_WAIT",
}


class JwwStateParser:
    def __init__(self):
        self.compiled_rules = []
        # 👑 単一の「直前の状態」ではなく、衝突グループごとに「そのグループ内で
        # 最後に確定したのはどれか」を別々に覚える（キー=グループのfrozenset）。
        # 単一トラッカーだと、無関係な別コマンド（測定・ハッチ等）を一瞬でも
        # 経由しただけで記憶が上書きされ、コーナー/面取りのような衝突判定が
        # 不安定になる（実測で確認：連続テスト中に無関係なボタンを挟むと
        # ふらついた）。グループ単位にすることで、無関係な状態は影響しない。
        self._last_group_member = {}
        self._load_and_compile_database()

    def _load_and_compile_database(self):
        flat_list = []
        for state_id, pattern_tuples in STATE_DATABASE.items():
            for regex_str, rule_enum in pattern_tuples:
                flat_list.append((regex_str, state_id, rule_enum))
        # 👑 【完全一本道ソート】最長パターンから順にマッチングをかけることで誤判定を完全シールド
        sorted_flat = sorted(flat_list, key=lambda x: len(x[0]), reverse=True)
        for regex_str, state_id, rule_enum in sorted_flat:
            self.compiled_rules.append(CompiledRule(
                regex=re.compile(regex_str),
                state_id=state_id,
                rule_enum=rule_enum if isinstance(rule_enum, RuleId) else RuleId.LINE_WAIT,
                pattern_str=regex_str
            ))

    def parse(self, raw_text: str) -> ParseResult:
        if not raw_text or "コマンドを選択してください" in raw_text or "ﾍﾙﾌﾟを表示するには" in raw_text:
            # 本当にIdleに戻った＝どのコマンドもアクティブでないので、
            # グループごとの記憶も全部リセットしてよい。
            self._last_group_member = {}
            return ParseResult(
                raw_text=raw_text or "(Empty)",
                state_id="STATE_IDLE",
                rule_name="IDLE_READY",
                pattern="^コマンドを選択してください"
            )

        # 👑 【物理不整合バグ埋葬】古い特定の状態ID決め打ちのcontinue処理を全廃。
        # データベースマスタ（STATE_DATABASE）の定義順・最長一致のみを極めてシンプルかつ安全に実行。
        for rule in self.compiled_rules:
            if rule.regex.search(raw_text):
                state_id = rule.state_id
                group = next((g for g in AMBIGUOUS_GROUPS if state_id in g), None)
                # 👑 衝突文言（AMBIGUOUS_RULES）にマッチした場合、文言だけでは
                # 本来どちらのコマンドか区別できない。同じ衝突グループの中で
                # 最後に確定していた方があれば、それをそのまま維持する
                # （切り替え直後に各コマンド固有のツールチップ文言で一度確定して
                # いるはずなので、直前状態を信頼する方が文言の力技より正確）。
                if group and rule.rule_enum.name in AMBIGUOUS_RULES:
                    last_member = self._last_group_member.get(group)
                    if last_member and last_member != state_id:
                        state_id = last_member
                # 衝突文言かどうかに関わらず、このstate_idが何らかの衝突グループの
                # 一員なら「このグループの最新の確定状態」として記録しておく
                # （固有のツールチップ文言もここで記録され、次の衝突判定に使われる）。
                if group:
                    self._last_group_member[group] = state_id
                return ParseResult(
                    raw_text=raw_text,
                    state_id=state_id,
                    rule_name=rule.rule_enum.name,
                    pattern=rule.pattern_str
                )

        # 👑 未一致（STATE_UNKNOWN）はマウス移動中の一時的な文言などで頻発する。
        # ここでグループ記憶を上書きすると、直後に衝突文言へ戻った時の
        # 判定材料を失ってしまうため、あえて更新しない。
        return ParseResult(
            raw_text=raw_text,
            state_id="STATE_UNKNOWN",
            rule_name="NONE_MATCH",
            pattern="None"
        )

_parser_instance = JwwStateParser()

def parse_statusbar_text(raw_text: str):
    res = _parser_instance.parse(raw_text)
    return res.state_id, res.rule_name
# ===== ✂️ utils/state_parser.py END ✂️ =====
