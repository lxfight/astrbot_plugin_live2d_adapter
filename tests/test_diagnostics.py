import sys
import unittest
from pathlib import Path

PLUGIN_PARENT = Path(__file__).resolve().parents[2]
if str(PLUGIN_PARENT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_PARENT))

from astrbot_plugin_live2d_adapter.core.diagnostics import (  # noqa: E402
    preview_text,
    summarize_client_model_info,
    summarize_expression_type_assignments,
    summarize_perform_sequence,
)


class DiagnosticsTest(unittest.TestCase):
    def test_preview_text_collapses_and_truncates(self) -> None:
        self.assertEqual(preview_text("  你好\n世界  ", limit=10), "你好 世界")
        self.assertEqual(preview_text("abcdef", limit=3), "abc...")

    def test_summarize_client_model_info_counts_capabilities(self) -> None:
        summary = summarize_client_model_info(
            {
                "capabilities": {"expressionCombo": True},
                "expressions": ["Smile"],
                "expressionCatalog": [{"id": "Smile"}],
                "semanticPresets": {"happy": ["Smile"], "sad": []},
                "motionGroups": {"Idle": []},
            }
        )

        self.assertEqual(
            summary,
            {
                "capabilities": {"expressionCombo": True},
                "expressions": 1,
                "expressionCatalog": 1,
                "semanticPresets": 2,
                "availableExpressionTypes": ["happy"],
                "motionGroups": 1,
            },
        )

    def test_summarize_expression_type_assignments_normalizes_non_empty_types(self) -> None:
        assignments = summarize_expression_type_assignments(
            {
                "semanticPresets": {
                    "happy": ["Smile", "Smile", ""],
                    "sad": [],
                    "unknown": ["Mystery"],
                    "blush": ["Blush"],
                }
            }
        )

        self.assertEqual(
            assignments,
            {
                "happy": ["Smile"],
                "blush": ["Blush"],
            },
        )

    def test_summarize_perform_sequence_expands_expression_and_motion(self) -> None:
        summary = summarize_perform_sequence(
            [
                {"type": "motion", "group": "Happy", "index": 0, "priority": 2},
                {
                    "type": "expression",
                    "combo": [{"id": "Smile", "weight": 0.8}],
                    "holdMs": 1200,
                    "resetPolicy": "previous",
                    "fade": 300,
                },
            ]
        )

        self.assertEqual(
            summary,
            [
                {"type": "motion", "group": "Happy", "index": 0, "priority": 2},
                {
                    "type": "expression",
                    "combo": [{"id": "Smile", "weight": 0.8}],
                    "holdMs": 1200,
                    "resetPolicy": "previous",
                    "fade": 300,
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
