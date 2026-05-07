import json
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
from astrbot_plugin_live2d_adapter.llm.planner_client import (  # noqa: E402
    PlannerLLMClient,
)


class FakeLLMResponse:
    def __init__(self, completion_text: str):
        self.completion_text = completion_text


class FakeProvider:
    def __init__(self, completion_text: str):
        self.completion_text = completion_text
        self.calls: list[dict] = []

    async def text_chat(self, **kwargs):
        self.calls.append(kwargs)
        return FakeLLMResponse(self.completion_text)


class FakeContext:
    def __init__(self, provider: FakeProvider):
        self.provider = provider

    def get_provider_by_id(self, provider_id: str):
        if provider_id == "planner_provider":
            return self.provider
        return None


class PlannerClientTest(unittest.IsolatedAsyncioTestCase):
    def tearDown(self) -> None:
        clear_plugin_runtime()

    async def test_plan_reply_uses_astrbot_provider(self) -> None:
        provider = FakeProvider(
            '```json\n{"motion_intent":"happy","emotion_tags":["开心"],"confidence":0.92}\n```'
        )
        register_plugin_runtime(
            FakeContext(provider),
            {
                "planner": {
                    "mode": "provider",
                    "provider_id": "planner_provider",
                    "system_prompt": "仅输出 JSON",
                    "temperature": 0.35,
                    "timeout_seconds": 12,
                }
            },
        )

        runtime_config = resolve_planner_runtime_config()
        client = PlannerLLMClient()

        plan = await client.plan_reply(
            "今天很开心",
            {
                "name": "测试模型",
                "motionGroups": {"Happy": [{"index": 0, "file": "happy.motion3.json"}]},
                "expressions": ["Smile"],
            },
            planner_config=runtime_config,
        )

        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan.motion_intent, "happy")
        self.assertEqual(plan.emotion_tags, ["开心"])
        self.assertAlmostEqual(plan.confidence, 0.92)
        self.assertEqual(len(provider.calls), 1)
        self.assertEqual(provider.calls[0]["system_prompt"], "仅输出 JSON")
        self.assertAlmostEqual(provider.calls[0]["temperature"], 0.35)

        prompt_payload = json.loads(provider.calls[0]["prompt"])
        self.assertEqual(prompt_payload["reply_text"], "今天很开心")
        self.assertEqual(prompt_payload["client_model"]["name"], "测试模型")


if __name__ == "__main__":
    unittest.main()
