# ===== ✂️ utils/event_engine.py START ✂️ =====
from enum import Enum, auto

class JwwEvent(Enum):
    NONE = auto()
    EVENT_ENTER_STATE = auto()
    EVENT_RESET_IDLE = auto()

class JwwEventEngine:
    def __init__(self):
        self.last_state = "STATE_IDLE"
        self.stable_state = "STATE_IDLE"
        self.match_counter = 0

    def process_state(self, current_state: str) -> str:
        if current_state == self.last_state:
            self.match_counter += 1
        else:
            self.last_state = current_state
            self.match_counter = 1

        if self.match_counter >= 3:
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
