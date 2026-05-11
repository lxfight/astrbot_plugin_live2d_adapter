import sys
import unittest
from pathlib import Path

PLUGIN_PARENT = Path(__file__).resolve().parents[2]
if str(PLUGIN_PARENT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_PARENT))

from astrbot_plugin_live2d_adapter.core.planner_runtime import (  # noqa: E402
    clear_plugin_runtime,
    register_plugin_runtime,
    resolve_planner_runtime_config,
)


class PlannerRuntimeTest(unittest.TestCase):
    def tearDown(self) -> None:
        clear_plugin_runtime()

    def test_auto_mode_prefers_plugin_provider(self) -> None:
        register_plugin_runtime(
            object(),
            {
                "planner": {
                    "mode": "auto",
                    "provider_id": "planner_provider",
                    "temperature": 0.3,
                    "timeout_seconds": 18,
                    "min_confidence": 0.6,
                }
            },
        )

        resolved = resolve_planner_runtime_config()

        self.assertTrue(resolved["enabled"])
        self.assertEqual(resolved["effective_mode"], "provider")
        self.assertEqual(resolved["source"], "plugin_provider")
        self.assertEqual(resolved["provider_id"], "planner_provider")
        self.assertAlmostEqual(resolved["temperature"], 0.3)
        self.assertEqual(resolved["timeout_seconds"], 18)
        self.assertAlmostEqual(resolved["min_confidence"], 0.6)

    def test_auto_mode_without_provider_keeps_disabled(self) -> None:
        register_plugin_runtime(object(), {"planner": {"mode": "auto"}})

        resolved = resolve_planner_runtime_config()

        self.assertFalse(resolved["enabled"])
        self.assertEqual(resolved["effective_mode"], "disabled")
        self.assertEqual(resolved["source"], "plugin_auto_without_provider")

    def test_disabled_mode_stays_disabled(self) -> None:
        register_plugin_runtime(object(), {"planner": {"mode": "disabled"}})

        resolved = resolve_planner_runtime_config()

        self.assertFalse(resolved["enabled"])
        self.assertEqual(resolved["effective_mode"], "disabled")
        self.assertEqual(resolved["source"], "plugin_disabled")


if __name__ == "__main__":
    unittest.main()
