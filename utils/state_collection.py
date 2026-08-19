import datetime
from typing import Optional


class StateCollectionLogger:
    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
        self._enabled = False

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def is_enabled(self) -> bool:
        return self._enabled

    def _timestamp(self) -> str:
        return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def record(
        self,
        event_type: str,
        detail: str,
        state: Optional[str] = None,
        rule: Optional[str] = None,
        raw_status_text: Optional[str] = None,
    ):
        if not self._enabled:
            return
        line = build_state_collection_line(
            timestamp=self._timestamp(),
            event_type=event_type,
            detail=detail,
            state=state,
            rule=rule,
            raw_status_text=raw_status_text,
        )
        with open(self.log_file_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def build_state_collection_line(
    timestamp: str,
    event_type: str,
    detail: str,
    state: Optional[str] = None,
    rule: Optional[str] = None,
    raw_status_text: Optional[str] = None,
) -> str:
    detail_text = detail or ""
    suffix = []
    if state:
        suffix.append(f"state={state}")
    if rule:
        suffix.append(f"rule={rule}")
    if raw_status_text:
        suffix.append(f"raw_status_text={raw_status_text}")

    if suffix:
        return (
            f"{timestamp} | {event_type} | detail={detail_text} | {' | '.join(suffix)}"
        )
    return f"{timestamp} | {event_type} | detail={detail_text}"
