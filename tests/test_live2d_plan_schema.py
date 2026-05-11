import sys
import unittest
from pathlib import Path

PLUGIN_PARENT = Path(__file__).resolve().parents[2]
if str(PLUGIN_PARENT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_PARENT))

from astrbot_plugin_live2d_adapter.core.live2d_plan_schema import (  # noqa: E402
    MAX_HOLD_MS,
    parse_live2d_perform_plan,
)


class Live2DPlanSchemaTest(unittest.TestCase):
    def test_parse_normalizes_payload(self) -> None:
        plan = parse_live2d_perform_plan(
            {
                "motion_intent": " happy ",
                "emotion_tags": ["开心", "开心", "  ", "Happy"],
                "expression_intent": " smile ",
                "intensity": 2,
                "hold_ms": MAX_HOLD_MS + 999,
                "confidence": -0.5,
                "notes": "  补发表情  ",
            }
        )

        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan.motion_intent, "happy")
        self.assertEqual(plan.emotion_tags, ["开心", "Happy"])
        self.assertEqual(plan.expression_intent, "smile")
        self.assertEqual(plan.intensity, 1.0)
        self.assertEqual(plan.hold_ms, MAX_HOLD_MS)
        self.assertEqual(plan.confidence, 0.0)
        self.assertEqual(plan.notes, "补发表情")

    def test_parse_returns_none_without_any_intent(self) -> None:
        plan = parse_live2d_perform_plan({"confidence": 0.9, "notes": "noop"})
        self.assertIsNone(plan)


if __name__ == "__main__":
    unittest.main()
