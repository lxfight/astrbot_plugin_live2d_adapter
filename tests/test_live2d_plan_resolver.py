import sys
import unittest
from pathlib import Path

PLUGIN_PARENT = Path(__file__).resolve().parents[2]
if str(PLUGIN_PARENT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_PARENT))

from astrbot_plugin_live2d_adapter.converters.live2d_plan_resolver import (  # noqa: E402
    Live2DPlanResolver,
)
from astrbot_plugin_live2d_adapter.core.live2d_plan_schema import (  # noqa: E402
    Live2DPerformPlan,
)


class Live2DPlanResolverTest(unittest.TestCase):
    def test_resolve_prefers_combo_and_motion_mapping(self) -> None:
        resolver = Live2DPlanResolver(
            {
                "capabilities": {
                    "expressionCombo": True,
                    "semanticExpression": True,
                },
                "motionGroups": {
                    "HappyLoop": [{"index": 0, "file": "happy.motion3.json"}],
                    "Idle": [{"index": 0, "file": "idle.motion3.json"}],
                },
                "expressionCatalog": [
                    {
                        "id": "Smile",
                        "aliases": ["smile", "开心"],
                        "tags": ["happy"],
                        "supportsCombo": True,
                    },
                    {
                        "id": "Think",
                        "aliases": ["think"],
                        "tags": ["thinking"],
                        "supportsCombo": False,
                    },
                ],
                "semanticPresets": {
                    "happy": ["Smile"],
                    "thinking": ["Think"],
                },
            }
        )

        plan = Live2DPerformPlan(
            motion_intent="happy",
            emotion_tags=["开心"],
            intensity=0.8,
            hold_ms=1800,
            confidence=0.9,
        )

        sequence = resolver.resolve(plan, reset_policy="previous")

        self.assertEqual(
            sequence,
            [
                {
                    "type": "motion",
                    "group": "HappyLoop",
                    "index": 0,
                    "priority": 2,
                    "loop": False,
                    "fadeIn": 300,
                    "fadeOut": 300,
                    "motionType": "happy",
                },
                {
                    "type": "expression",
                    "fade": 300,
                    "semantic": [{"tag": "happy", "weight": 0.8}],
                    "holdMs": 1800,
                    "resetPolicy": "previous",
                    "motionType": "happy",
                },
            ],
        )

    def test_resolve_does_not_build_combo_for_non_combo_catalog_entries(self) -> None:
        resolver = Live2DPlanResolver(
            {
                "capabilities": {
                    "expressionCombo": True,
                    "semanticExpression": True,
                },
                "expressionCatalog": [
                    {
                        "id": "Smile",
                        "aliases": ["smile"],
                        "tags": ["happy"],
                        "supportsCombo": False,
                    }
                ],
                "semanticPresets": {
                    "happy": ["Smile"],
                },
            }
        )

        plan = Live2DPerformPlan(
            emotion_tags=["开心"],
            intensity=0.7,
            confidence=0.9,
        )

        sequence = resolver.resolve(plan, reset_policy="previous")

        self.assertEqual(
            sequence,
            [
                {
                    "type": "expression",
                    "fade": 300,
                    "semantic": [{"tag": "happy", "weight": 0.7}],
                    "holdMs": 0,
                    "resetPolicy": "previous",
                }
            ],
        )

    def test_resolve_falls_back_to_semantic_expression(self) -> None:
        resolver = Live2DPlanResolver(
            {
                "capabilities": {
                    "expressionCombo": False,
                    "semanticExpression": True,
                }
            }
        )

        plan = Live2DPerformPlan(
            emotion_tags=["思考"],
            intensity=0.6,
            confidence=0.8,
        )

        sequence = resolver.resolve(plan, reset_policy="keep")

        self.assertEqual(
            sequence,
            [
                {
                    "type": "expression",
                    "fade": 300,
                    "semantic": [{"tag": "thinking", "weight": 0.6}],
                    "holdMs": 0,
                    "resetPolicy": "keep",
                }
            ],
        )

    def test_resolve_uses_legacy_expression_list_without_catalog(self) -> None:
        resolver = Live2DPlanResolver(
            {
                "capabilities": {},
                "expressions": ["Smile", "Sad"],
            }
        )

        plan = Live2DPerformPlan(
            expression_intent="smile",
            emotion_tags=["伤心"],
            intensity=0.7,
            confidence=0.9,
        )

        sequence = resolver.resolve(plan, reset_policy="previous")

        self.assertEqual(
            sequence,
            [
                {
                    "type": "expression",
                    "fade": 300,
                    "id": "Smile",
                    "holdMs": 0,
                    "resetPolicy": "previous",
                }
            ],
        )

    def test_resolve_uses_legacy_expression_list_from_emotion_tags(self) -> None:
        resolver = Live2DPlanResolver(
            {
                "capabilities": {},
                "expressions": ["Smile", "Sad"],
            }
        )

        plan = Live2DPerformPlan(
            emotion_tags=["伤心"],
            intensity=0.7,
            confidence=0.9,
        )

        sequence = resolver.resolve(plan, reset_policy="keep")

        self.assertEqual(
            sequence,
            [
                {
                    "type": "expression",
                    "fade": 300,
                    "id": "Sad",
                    "holdMs": 0,
                    "resetPolicy": "keep",
                }
            ],
        )

    def test_resolve_big_smile_intent_to_happy_expression(self) -> None:
        resolver = Live2DPlanResolver(
            {
                "capabilities": {
                    "expressionCombo": True,
                    "semanticExpression": True,
                },
                "expressions": ["Smile", "Sad"],
                "expressionCatalog": [
                    {
                        "id": "Smile",
                        "aliases": ["Smile"],
                        "tags": [],
                        "supportsCombo": True,
                    },
                    {
                        "id": "Sad",
                        "aliases": ["Sad"],
                        "tags": [],
                        "supportsCombo": True,
                    },
                ],
                "semanticPresets": {},
            }
        )

        plan = Live2DPerformPlan(
            motion_intent="happy",
            emotion_tags=["cheerful", "warm", "playful"],
            expression_intent="big smile",
            intensity=0.72,
            hold_ms=2200,
            confidence=0.88,
        )

        sequence = resolver.resolve(plan, reset_policy="previous")

        self.assertEqual(
            sequence,
            [
                {
                    "type": "expression",
                    "fade": 300,
                    "combo": [{"id": "Smile", "weight": 0.72}],
                    "holdMs": 2200,
                    "resetPolicy": "previous",
                    "motionType": "happy",
                }
            ],
        )

    def test_summarize_resolution_context_reports_unmatched_inputs(self) -> None:
        resolver = Live2DPlanResolver(
            {
                "capabilities": {
                    "expressionCombo": True,
                    "semanticExpression": True,
                },
                "expressions": ["Blink"],
                "expressionCatalog": [
                    {
                        "id": "Blink",
                        "aliases": ["blink"],
                        "tags": [],
                        "supportsCombo": True,
                    }
                ],
                "semanticPresets": {},
            }
        )

        plan = Live2DPerformPlan(
            motion_intent="happy",
            expression_intent="big smile",
            emotion_tags=["cheerful"],
            confidence=0.9,
        )

        self.assertEqual(resolver.resolve(plan), [])
        summary = resolver.summarize_resolution_context(plan)

        self.assertEqual(summary["tags"], ["happy"])
        self.assertEqual(summary["resolvedExpressionIds"], [])
        self.assertEqual(summary["expressions"], ["Blink"])
        self.assertEqual(summary["semanticPresetKeys"], [])
        self.assertEqual(summary["catalog"][0]["id"], "Blink")

    def test_resolve_uses_extended_fixed_expression_types(self) -> None:
        resolver = Live2DPlanResolver(
            {
                "capabilities": {
                    "expressionCombo": True,
                    "semanticExpression": True,
                },
                "expressionCatalog": [
                    {
                        "id": "Blush",
                        "aliases": ["Blush"],
                        "tags": ["blush"],
                        "supportsCombo": True,
                    },
                ],
                "semanticPresets": {
                    "blush": ["Blush"],
                    "happy": [],
                },
            }
        )

        plan = Live2DPerformPlan(
            emotion_tags=["脸红"],
            intensity=0.65,
            confidence=0.9,
        )

        sequence = resolver.resolve(plan, reset_policy="previous")

        self.assertEqual(
            sequence,
            [
                {
                    "type": "expression",
                    "fade": 300,
                    "semantic": [{"tag": "blush", "weight": 0.65}],
                    "holdMs": 0,
                    "resetPolicy": "previous",
                }
            ],
        )

    def test_resolve_ignores_non_fixed_semantic_preset_keys(self) -> None:
        resolver = Live2DPlanResolver(
            {
                "capabilities": {
                    "expressionCombo": True,
                    "semanticExpression": True,
                },
                "expressionCatalog": [
                    {
                        "id": "Smile",
                        "aliases": ["Smile"],
                        "tags": ["happy"],
                        "supportsCombo": True,
                    },
                ],
                "semanticPresets": {
                    "开心": ["Smile"],
                },
            }
        )

        plan = Live2DPerformPlan(
            emotion_tags=["开心"],
            intensity=0.7,
            confidence=0.9,
        )

        sequence = resolver.resolve(plan, reset_policy="previous")

        self.assertEqual(
            sequence,
            [
                {
                    "type": "expression",
                    "fade": 300,
                    "combo": [{"id": "Smile", "weight": 0.7}],
                    "holdMs": 0,
                    "resetPolicy": "previous",
                }
            ],
        )



if __name__ == "__main__":
    unittest.main()
