"""Live2D 补发表演触发辅助逻辑"""

from __future__ import annotations

from typing import Any


def extract_planner_reply_text(output_converter: Any, message_chain: Any) -> str:
    extractor = getattr(output_converter, "extract_text_summary", None)
    if not callable(extractor):
        return ""
    return str(extractor(message_chain) or "").strip()


def has_explicit_perform_controls(sequence: list[dict[str, Any]]) -> bool:
    return any(
        isinstance(element, dict) and element.get("type") in {"motion", "expression"}
        for element in sequence
    )


async def build_planner_followup_sequence(
    *,
    expression_planner: Any,
    output_converter: Any,
    message_chain: Any,
    sequence: list[dict[str, Any]],
    client_model_info: dict[str, Any] | None,
    reset_policy: str,
    reply_text: str | None = None,
) -> list[dict[str, Any]]:
    normalized_reply = (
        str(reply_text or "").strip()
        if reply_text is not None
        else extract_planner_reply_text(output_converter, message_chain)
    )
    if (
        not normalized_reply
        or has_explicit_perform_controls(sequence)
        or not isinstance(client_model_info, dict)
        or not client_model_info
    ):
        return []

    is_enabled = getattr(expression_planner, "is_enabled", None)
    if not callable(is_enabled) or not is_enabled():
        return []

    builder = getattr(expression_planner, "build_followup_sequence", None)
    if not callable(builder):
        return []

    followup_sequence = await builder(
        normalized_reply,
        client_model_info,
        reset_policy=reset_policy,
    )
    return followup_sequence if isinstance(followup_sequence, list) else []
