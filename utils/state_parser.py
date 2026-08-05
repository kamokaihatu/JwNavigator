# ===== ✂️ utils/state_parser.py START ✂️ =====
import re
from utils.state_patterns import STATE_DATABASE, RuleId
from utils.parse_result import CompiledRule, ParseResult

class JwwStateParser:
    def __init__(self):
        self.compiled_rules = []
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
                return ParseResult(
                    raw_text=raw_text, 
                    state_id=rule.state_id, 
                    rule_name=rule.rule_enum.name, 
                    pattern=rule.pattern_str
                )
                
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
