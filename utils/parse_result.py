# ===== ✂️ utils/parse_result.py START ✂️ =====
import re
from dataclasses import dataclass
from utils.state_patterns import RuleId

@dataclass
class CompiledRule:
    regex: re.Pattern
    state_id: str
    rule_enum: RuleId
    pattern_str: str

@dataclass
class ParseResult:
    raw_text: str
    state_id: str
    rule_name: str
    pattern: str
# ===== ✂️ utils/parse_result.py END ✂️ =====
