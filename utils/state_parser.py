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
]
# 上記の衝突文言側にマッチした時だけ発動するルール名（各コマンド固有の
# ツールチップ文言側は衝突していないので対象外）。
AMBIGUOUS_RULES = {"CORNER_WAIT", "SHIKI_WAIT", "LINE_WAIT", "RECT_WAIT"}


class JwwStateParser:
    def __init__(self):
        self.compiled_rules = []
        self._last_state_id = None
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
            self._last_state_id = "STATE_IDLE"
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
                # 👑 衝突文言（AMBIGUOUS_RULES）にマッチした場合、文言だけでは
                # 本来どちらのコマンドか区別できない。直前に確定していた状態が
                # 同じ衝突グループのもう一方なら、それをそのまま維持する
                # （切り替え直後に各コマンド固有のツールチップ文言で一度確定して
                # いるはずなので、直前状態を信頼する方が文言の力技より正確）。
                if rule.rule_enum.name in AMBIGUOUS_RULES:
                    group = next((g for g in AMBIGUOUS_GROUPS if state_id in g), None)
                    if group and self._last_state_id in group and self._last_state_id != state_id:
                        state_id = self._last_state_id
                self._last_state_id = state_id
                return ParseResult(
                    raw_text=raw_text,
                    state_id=state_id,
                    rule_name=rule.rule_enum.name,
                    pattern=rule.pattern_str
                )

        # 👑 未一致（STATE_UNKNOWN）はマウス移動中の一時的な文言などで頻発する。
        # ここで_last_state_idを上書きすると、直後に衝突文言へ戻った時の
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
