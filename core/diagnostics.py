"""Live2D 适配器诊断日志辅助函数"""

from __future__ import annotations

from typing import Any

from .expression_types import get_available_expression_type_assignments
from .model_protocol import normalize_expression_entries


def preview_text(value: Any, limit: int = 120) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def summarize_message_chain(message_chain: Any) -> list[str]:
    chain = getattr(message_chain, "chain", None)
    if not isinstance(chain, list):
        return []

    names: list[str] = []
    for component in chain:
        component_type = getattr(component, "type", None)
        type_value = getattr(component_type, "value", None)
        if isinstance(type_value, str) and type_value:
            names.append(type_value)
            continue
        names.append(component.__class__.__name__)
    return names


def summarize_client_model_info(client_model_info: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(client_model_info, dict):
        return {}

    expressions = normalize_expression_entries(client_model_info)
    catalog = client_model_info.get("expressionCatalog")
    presets = client_model_info.get("semanticPresets")
    motion_groups = client_model_info.get("motionGroups")
    capabilities = client_model_info.get("capabilities")
    available_type_assignments = get_available_expression_type_assignments(
        client_model_info
    )

    return {
        "capabilities": capabilities if isinstance(capabilities, dict) else {},
        "expressions": len(expressions),
        "expressionCatalog": len(catalog) if isinstance(catalog, list) else 0,
        "semanticPresets": len(presets) if isinstance(presets, dict) else 0,
        "availableExpressionTypes": list(available_type_assignments.keys()),
        "motionGroups": len(motion_groups) if isinstance(motion_groups, dict) else 0,
    }


def summarize_expression_type_assignments(
    client_model_info: dict[str, Any] | None,
) -> dict[str, list[str]]:
    return get_available_expression_type_assignments(client_model_info)


def summarize_perform_sequence(sequence: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if not isinstance(sequence, list):
        return []

    summary: list[dict[str, Any]] = []
    for element in sequence:
        if not isinstance(element, dict):
            summary.append({"type": type(element).__name__})
            continue

        element_type = str(element.get("type") or "")
        item: dict[str, Any] = {"type": element_type}
        if element_type == "motion":
            item["name"] = element.get("name")
            item["group"] = element.get("group")
            item["index"] = element.get("index")
            item["priority"] = element.get("priority")
            item["motionType"] = element.get("motionType")
        elif element_type == "expression":
            item["name"] = element.get("name")
            item["id"] = element.get("id")
            if isinstance(element.get("combo"), list):
                item["combo"] = [
                    {
                        "id": candidate.get("id"),
                        "weight": candidate.get("weight"),
                    }
                    for candidate in element["combo"]
                    if isinstance(candidate, dict)
                ]
            if isinstance(element.get("semantic"), list):
                item["semantic"] = [
                    {
                        "tag": candidate.get("tag"),
                        "weight": candidate.get("weight"),
                    }
                    for candidate in element["semantic"]
                    if isinstance(candidate, dict)
                ]
            item["holdMs"] = element.get("holdMs")
            item["resetPolicy"] = element.get("resetPolicy")
            item["fade"] = element.get("fade")
            item["motionType"] = element.get("motionType")
        elif element_type in {"text", "tts", "audio"}:
            text = element.get("content") if element_type == "text" else element.get("text")
            item["text"] = preview_text(text, 60)
        elif element_type in {"image", "video"}:
            item["hasUrl"] = bool(element.get("url"))
            item["hasRid"] = bool(element.get("rid"))
            item["hasInline"] = bool(element.get("inline"))
        summary.append({key: value for key, value in item.items() if value is not None})
    return summary
