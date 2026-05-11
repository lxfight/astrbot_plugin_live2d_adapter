import sys
import unittest
from pathlib import Path

PLUGIN_PARENT = Path(__file__).resolve().parents[2]
if str(PLUGIN_PARENT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_PARENT))

from astrbot_plugin_live2d_adapter.core.live2d_plan_schema import (  # noqa: E402
    Live2DPerformPlan,
)
from astrbot_plugin_live2d_adapter.core.planner_runtime import (  # noqa: E402
    clear_plugin_runtime,
    register_plugin_runtime,
)
from astrbot_plugin_live2d_adapter.services.expression_planner_service import (  # noqa: E402
    ExpressionPlannerService,
)


class FakePlannerClient:
    def __init__(self, plan: Live2DPerformPlan | None):
        self.plan = plan
        self.calls: list[dict] = []

    async def plan_reply(self, reply_text, client_model_info=None, planner_config=None):
        self.calls.append(
            {
                "reply_text": reply_text,
                "client_model_info": client_model_info,
                "planner_config": planner_config,
            }
        )
        return self.plan


class ExpressionPlannerServiceTest(unittest.IsolatedAsyncioTestCase):
    def tearDown(self) -> None:
        clear_plugin_runtime()

    async def test_build_followup_sequence_resolves_motion_and_combo_expression(self) -> None:
        register_plugin_runtime(
            object(),
            {
                "planner": {
                    "mode": "provider",
                    "provider_id": "planner_provider",
                    "min_confidence": 0.4,
                }
            },
        )

        service = ExpressionPlannerService()
        service.client = FakePlannerClient(
            Live2DPerformPlan(
                motion_intent="happy",
                emotion_tags=["开心"],
                expression_intent="Smile",
                intensity=0.8,
                hold_ms=1200,
                confidence=0.95,
                raw={
                    "motion_intent": "happy",
                    "emotion_tags": ["开心"],
                    "expression_intent": "Smile",
                    "intensity": 0.8,
                    "hold_ms": 1200,
                    "confidence": 0.95,
                },
            )
        )

        client_model_info = {
            "capabilities": {
                "expressionCombo": True,
                "semanticExpression": True,
            },
            "motionGroups": {
                "Happy": [{"index": 0, "file": "motions/happy.motion3.json"}],
                "Idle": [{"index": 0, "file": "motions/idle.motion3.json"}],
            },
            "expressionCatalog": [
                {
                    "id": "Smile",
                    "aliases": ["开心"],
                    "tags": ["happy"],
                    "conflictGroups": ["emotion"],
                    "supportsCombo": True,
                }
            ],
            "semanticPresets": {"happy": ["Smile"]},
        }

        sequence = await service.build_followup_sequence(
            "今天真的很开心",
            client_model_info,
            reset_policy="previous",
        )

        self.assertEqual(len(sequence), 2)
        self.assertEqual(sequence[0]["type"], "motion")
        self.assertEqual(sequence[0]["group"], "Happy")
        self.assertEqual(sequence[1]["type"], "expression")
        self.assertEqual(sequence[1]["semantic"], [{"tag": "happy", "weight": 0.8}])
        self.assertEqual(sequence[1]["holdMs"], 1200)
        self.assertEqual(sequence[1]["resetPolicy"], "previous")

    async def test_build_followup_sequence_skips_when_client_has_no_actionable_expression_capability(self) -> None:
        register_plugin_runtime(
            object(),
            {
                "planner": {
                    "mode": "provider",
                    "provider_id": "planner_provider",
                    "min_confidence": 0.4,
                }
            },
        )

        service = ExpressionPlannerService()
        service.client = FakePlannerClient(
            Live2DPerformPlan(
                emotion_tags=["开心"],
                intensity=0.8,
                confidence=0.95,
            )
        )

        sequence = await service.build_followup_sequence(
            "今天真的很开心",
            {
                "capabilities": {
                    "expressionCombo": True,
                    "semanticExpression": True,
                },
                "expressionCatalog": [
                    {
                        "id": "Smile",
                        "aliases": ["开心"],
                        "tags": ["happy"],
                        "supportsCombo": False,
                    }
                ],
                "semanticPresets": {},
                "expressions": [],
            },
            reset_policy="previous",
        )

        self.assertEqual(sequence, [])


if __name__ == "__main__":
    unittest.main()
