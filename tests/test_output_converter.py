import sys
import types
import unittest
from pathlib import Path

PLUGIN_PARENT = Path(__file__).resolve().parents[2]
if str(PLUGIN_PARENT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_PARENT))


def install_astrbot_stubs() -> None:
    if "astrbot.api.message_components" in sys.modules:
        return

    astrbot_module = types.ModuleType("astrbot")
    api_module = types.ModuleType("astrbot.api")
    event_module = types.ModuleType("astrbot.api.event")
    components_module = types.ModuleType("astrbot.api.message_components")

    api_module.logger = types.SimpleNamespace(
        info=lambda *args, **kwargs: None,
        warning=lambda *args, **kwargs: None,
        debug=lambda *args, **kwargs: None,
        error=lambda *args, **kwargs: None,
    )

    class MessageChain:
        def __init__(self, chain=None):
            self.chain = chain or []

    class Plain:
        def __init__(self, text: str = ""):
            self.text = text

    component_names = [
        "At",
        "AtAll",
        "Face",
        "File",
        "Forward",
        "Image",
        "Json",
        "Node",
        "Nodes",
        "Poke",
        "Record",
        "Reply",
        "Video",
    ]

    event_module.MessageChain = MessageChain
    components_module.Plain = Plain
    for name in component_names:
        setattr(components_module, name, type(name, (), {}))

    sys.modules["astrbot"] = astrbot_module
    sys.modules["astrbot.api"] = api_module
    sys.modules["astrbot.api.event"] = event_module
    sys.modules["astrbot.api.message_components"] = components_module


install_astrbot_stubs()

from astrbot_plugin_live2d_adapter.converters.output_converter import (  # noqa: E402
    OutputMessageConverter,
)


class OutputMessageConverterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.converter = OutputMessageConverter(
            client_model_info={
                "motionGroups": {
                    "Idle": [{"index": 0, "file": "idle.motion3.json"}]
                },
                "expressions": ["Smile", "Sad"],
                "expressionCatalog": [
                    {"id": "Smile", "aliases": ["smile", "开心"]},
                    {"id": "Sad", "aliases": ["sad", "难过"]},
                ],
            }
        )

    def test_perform_plan_component_is_canonicalized(self) -> None:
        component = types.SimpleNamespace(
            group="idle",
            index=0,
            combo=[
                {"id": "smile", "weight": 0.7},
                {"id": "难过", "weight": 0.2},
            ],
            hold_ms=1600,
            reset_policy="previous",
            motion_type="happy",
        )

        sequence = self.converter._build_perform_plan_from_component(component)

        self.assertEqual(
            sequence,
            [
                {
                    "type": "motion",
                    "group": "Idle",
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
                    "combo": [
                        {"id": "Smile", "weight": 0.7},
                        {"id": "Sad", "weight": 0.2},
                    ],
                    "holdMs": 1600,
                    "resetPolicy": "previous",
                    "motionType": "happy",
                },
            ],
        )

    def test_expression_index_resolves_to_canonical_name(self) -> None:
        component = types.SimpleNamespace(expression_id=1)

        expression = self.converter._build_expression_from_component(component)

        self.assertEqual(
            expression,
            {
                "type": "expression",
                "fade": 300,
                "id": "Sad",
            },
        )


if __name__ == "__main__":
    unittest.main()
