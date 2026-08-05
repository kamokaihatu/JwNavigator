import unittest

from utils.state_collection import build_state_collection_line


class StateCollectionTests(unittest.TestCase):
    def test_builds_compact_transition_line(self):
        line = build_state_collection_line(
            timestamp="12:00:01",
            event_type="HOVER",
            detail="複写",
            state="STATE_COPY",
            rule="COPY_TOOLTIP",
        )
        self.assertEqual(
            line,
            "12:00:01 | HOVER | detail=複写 | state=STATE_COPY | rule=COPY_TOOLTIP"
        )


if __name__ == "__main__":
    unittest.main()
