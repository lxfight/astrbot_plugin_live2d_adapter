import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PLUGIN_PARENT = Path(__file__).resolve().parents[2]
if str(PLUGIN_PARENT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_PARENT))

from astrbot_plugin_live2d_adapter.core.protocol import Protocol  # noqa: E402
from astrbot_plugin_live2d_adapter.server.message_handler import MessageHandler  # noqa: E402


class MessageHandlerTest(unittest.IsolatedAsyncioTestCase):
    async def test_handle_state_model_records_available_expression_types(self) -> None:
        handler = MessageHandler(SimpleNamespace())
        payload = {
            "name": "测试模型",
            "motionGroups": {"Idle": [{"index": 0, "file": "idle.motion3.json"}]},
            "expressions": ["Smile", "Blush"],
            "capabilities": {
                "expressionCombo": True,
                "semanticExpression": True,
                "expressionProfile": True,
            },
            "expressionCatalog": [
                {"id": "Smile", "tags": ["happy"], "supportsCombo": True},
                {"id": "Blush", "tags": ["blush"], "supportsCombo": True},
            ],
            "semanticPresets": {
                "happy": ["Smile"],
                "sad": [],
                "blush": ["Blush"],
            },
        }
        packet = Protocol.create_packet(Protocol.OP_STATE_MODEL, payload=payload)

        with patch(
            "astrbot_plugin_live2d_adapter.server.message_handler.logger.debug"
        ) as debug:
            result = await handler.handle_state_model(packet, "client-1")

        self.assertIsNone(result)
        self.assertEqual(handler.client_states["client-1"]["model"], payload)
        debug.assert_any_call(
            "可用表情类型: %s",
            {
                "happy": {"count": 1, "expressions": ["Smile"]},
                "blush": {"count": 1, "expressions": ["Blush"]},
            },
        )

    async def test_handle_state_model_v2_records_alias_capabilities(self) -> None:
        handler = MessageHandler(SimpleNamespace())
        payload = {
            "version": "2.0",
            "modelName": "Haru",
            "motions": [
                {"id": "Idle_00", "name": "待机", "category": "idle", "duration": 3000},
                {
                    "id": "HappyLoop_00",
                    "name": "开心动作",
                    "category": "action",
                    "duration": 2400,
                },
            ],
            "expressions": [{"id": "Smile", "name": "微笑"}],
            "capabilities": {
                "idleMode": "noise+motion",
                "llmControlled": True,
            },
        }
        packet = Protocol.create_packet(Protocol.OP_STATE_MODEL, payload=payload)

        result = await handler.handle_state_model(packet, "client-2")

        self.assertIsNone(result)
        state = handler.client_states["client-2"]
        self.assertEqual(state["model"], payload)
        self.assertEqual(state["model_version"], "2.0")
        self.assertEqual(state["available_motions"], ["开心动作"])
        self.assertEqual(state["available_expressions"], ["微笑"])


if __name__ == "__main__":
    unittest.main()
