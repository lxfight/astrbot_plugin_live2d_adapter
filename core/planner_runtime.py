"""表演规划器运行时配置桥接"""

from __future__ import annotations

from typing import Any

try:
    from astrbot.api import logger
except Exception:  # pragma: no cover
    logger = None

try:
    from astrbot.core.star.star import star_registry
except Exception:  # pragma: no cover
    star_registry = []

PLUGIN_NAME = "astrbot_plugin_live2d_adapter"

DEFAULT_PLANNER_SYSTEM_PROMPT = """
你是 Live2D 表演规划器，只负责根据最终回复内容输出表演规划 JSON。

要求：
1. 只输出一个 JSON 对象，不要输出 Markdown，不要解释。
2. 你不能输出模型专属表情 ID、exp3 文件名、动作组名。
3. 只允许输出这些字段：
   - motion_intent: 字符串，可选，描述动作意图，例如 happy、sad、angry、surprised、thinking、neutral、speaking
   - emotion_tags: 字符串数组，可选，只能使用 client_model.availableExpressionTypes 中存在的表情类型
   - expression_intent: 字符串，可选，只能使用 client_model.availableExpressionTypes 中存在的表情类型
   - intensity: 0 到 1 的数字，可选
   - hold_ms: 0 到 30000 的整数，可选
   - interrupt: 布尔值，可选
   - confidence: 0 到 1 的数字，可选
   - notes: 字符串，可选
4. 如果 client_model.availableExpressionTypes 为空，或没有合适类型，请输出低 confidence，并尽量使用 neutral。
5. 不要选择 client_model.availableExpressionTypes 之外的表情类型。
6. 优先让规划稳定、克制，不要过度夸张。
""".strip()

_plugin_context: Any | None = None
_plugin_config: dict[str, Any] | None = None


def register_plugin_runtime(context: Any, config: dict[str, Any] | None) -> None:
    global _plugin_context, _plugin_config
    _plugin_context = context
    _plugin_config = config if isinstance(config, dict) else None


def clear_plugin_runtime() -> None:
    global _plugin_context, _plugin_config
    _plugin_context = None
    _plugin_config = None


def _normalize_string(value: Any) -> str:
    return str(value or "").strip()


def _clamp_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        normalized = default
    return max(minimum, min(normalized, maximum))


def _clamp_float(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        normalized = float(value)
    except (TypeError, ValueError):
        normalized = default
    return max(minimum, min(normalized, maximum))


def _find_plugin_metadata() -> Any | None:
    for metadata in star_registry:
        if getattr(metadata, "name", None) == PLUGIN_NAME:
            return metadata
        if getattr(metadata, "root_dir_name", None) == PLUGIN_NAME:
            return metadata
    return None


def get_plugin_context() -> Any | None:
    if _plugin_context is not None:
        return _plugin_context

    metadata = _find_plugin_metadata()
    star_cls = getattr(metadata, "star_cls", None) if metadata else None
    return getattr(star_cls, "context", None) if star_cls else None


def get_plugin_config() -> dict[str, Any] | None:
    if isinstance(_plugin_config, dict):
        return _plugin_config

    metadata = _find_plugin_metadata()
    config = getattr(metadata, "config", None) if metadata else None
    return config if isinstance(config, dict) else None


def _normalize_plugin_planner_config(
    plugin_config: dict[str, Any] | None,
) -> dict[str, Any]:
    planner_config = plugin_config.get("planner", {}) if isinstance(plugin_config, dict) else {}
    planner_config = planner_config if isinstance(planner_config, dict) else {}

    configured_mode = _normalize_string(planner_config.get("mode")).lower() or "auto"
    if configured_mode not in {"auto", "provider", "disabled"}:
        configured_mode = "auto"

    return {
        "configured_mode": configured_mode,
        "provider_id": _normalize_string(planner_config.get("provider_id")),
        "system_prompt": _normalize_string(planner_config.get("system_prompt"))
        or DEFAULT_PLANNER_SYSTEM_PROMPT,
        "temperature": _clamp_float(
            planner_config.get("temperature"),
            default=0.2,
            minimum=0.0,
            maximum=2.0,
        ),
        "timeout_seconds": _clamp_int(
            planner_config.get("timeout_seconds"),
            default=20,
            minimum=5,
            maximum=300,
        ),
        "min_confidence": _clamp_float(
            planner_config.get("min_confidence"),
            default=0.45,
            minimum=0.0,
            maximum=1.0,
        ),
    }


def resolve_planner_runtime_config() -> dict[str, Any]:
    plugin_config = _normalize_plugin_planner_config(get_plugin_config())

    configured_mode = plugin_config["configured_mode"]
    provider_id = plugin_config["provider_id"]

    result = {
        **plugin_config,
        "enabled": False,
        "effective_mode": "disabled",
        "source": "disabled",
    }

    if configured_mode == "disabled":
        result["source"] = "plugin_disabled"
        return result

    if provider_id:
        result["enabled"] = True
        result["effective_mode"] = "provider"
        result["source"] = "plugin_provider"
        return result

    if configured_mode == "provider":
        result["source"] = "plugin_provider_missing"
        return result

    result["source"] = "plugin_auto_without_provider"

    return result


def describe_planner_source(source: str) -> str:
    mapping = {
        "plugin_provider": "插件配置 Provider",
        "plugin_disabled": "插件配置已禁用",
        "plugin_provider_missing": "插件配置缺少 Provider",
        "plugin_auto_without_provider": "插件配置未选择 Provider",
        "disabled": "未启用",
    }
    return mapping.get(source, source)
