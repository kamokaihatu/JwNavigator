# ===== ✂️ utils/event_engine.py START ✂️ =====
from enum import Enum, auto
import time

class JwwEvent(Enum):
    NONE = auto()
    EVENT_ENTER_STATE = auto()
    EVENT_RESET_IDLE = auto()

class JwwEventEngine:
    def __init__(self, required_duration_sec: float = 1.0):
        # 👑 呼び出し頻度が一定でなくなった（WinEvent通知導入後は1秒間隔の
        # ポーリングだけでなく、jw_cadのステータスバー更新のたびに即座に
        # 呼ばれる）ため、「連続何回」ではなく「同じ状態が何秒続いたか」
        # という経過時間ベースの安定判定にしている。回数ベースだと、
        # 呼び出し頻度が上がるほど短いホバーでも安定扱いされてしまう
        # （実測: 0.26秒のホバーで誤反映したことがある）。
        self.required_duration_sec = required_duration_sec
        self.last_state = "STATE_IDLE"
        self.stable_state = "STATE_IDLE"
        self._candidate_since = None

    def reset(self):
        self.last_state = "STATE_IDLE"
        self.stable_state = "STATE_IDLE"
        self._candidate_since = None

    def process_state(self, current_state: str) -> str:
        now = time.time()
        if current_state != self.last_state:
            self.last_state = current_state
            self._candidate_since = now

        if self._candidate_since is not None and (now - self._candidate_since) >= self.required_duration_sec:
            if self.stable_state != current_state:
                self.stable_state = current_state
                if current_state == "STATE_IDLE":
                    return "EVENT_RESET_IDLE"
                elif current_state != "STATE_UNKNOWN":
                    return f"EVENT_ENTER_{current_state}"
        return "NONE"

_engine_instance = JwwEventEngine()

def detect_pipeline_event(current_state: str) -> str:
    return _engine_instance.process_state(current_state)
# ===== ✂️ utils/event_engine.py END ✂️ =====
