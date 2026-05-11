import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

PLUGIN_PARENT = Path(__file__).resolve().parents[2]
if str(PLUGIN_PARENT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_PARENT))

from astrbot_plugin_live2d_adapter.adapters.planner_followup import (  # noqa: E402
    build_planner_followup_sequence,
)


class FakeConverter:
    def extract_text_summary(self, message_chain) -> str:
        return getattr(message_chain, "text", "")


class FakePlanner:
    def __init__(self):
        self.calls: list[dict] = []

    def is_enabled(self) -> bool:
        return True

    async def build_followup_sequence(
        self,
        reply_text: str,
        client_model_info: dict,
        reset_policy: str,
    ) -> list[dict]:
        self.calls.append(
            {
                "reply_text": reply_text,
                "client_model_info": client_model_info,
                "reset_policy": reset_policy,
            }
        )
        return [{"type": "expression", "id": "Smile"}]


class PlannerFollowupTest(unittest.IsolatedAsyncioTestCase):
    async def test_builds_followup_when_sequence_has_no_explicit_controls(self) -> None:
        planner = FakePlanner()
        model_info = {"expressions": ["Smile"]}

        sequence = await build_planner_followup_sequence(
            expression_planner=planner,
            output_converter=FakeConverter(),
            message_chain=SimpleNamespace(text="你好"),
            sequence=[{"type": "text", "content": "你好"}],
            client_model_info=model_info,
            reset_policy="previous",
        )

        self.assertEqual(sequence, [{"type": "expression", "id": "Smile"}])
        self.assertEqual(
            planner.calls,
            [
                {
                    "reply_text": "你好",
                    "client_model_info": model_info,
                    "reset_policy": "previous",
                }
            ],
        )

    async def test_skips_followup_when_sequence_has_explicit_controls(self) -> None:
        planner = FakePlanner()

        sequence = await build_planner_followup_sequence(
            expression_planner=planner,
            output_converter=FakeConverter(),
            message_chain=SimpleNamespace(text="你好"),
            sequence=[{"type": "expression", "id": "Smile"}],
            client_model_info={"expressions": ["Smile"]},
            reset_policy="previous",
        )

        self.assertEqual(sequence, [])
        self.assertEqual(planner.calls, [])


if __name__ == "__main__":
    unittest.main()
