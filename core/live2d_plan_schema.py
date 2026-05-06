"""Live2D 表演规划结果结构"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

MAX_HOLD_MS = 30000


def _normalize_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_float(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number < minimum:
        return minimum
    if number > maximum:
        return maximum
    return number


def _normalize_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    if number < minimum:
        return minimum
    if number > maximum:
        return maximum
    return number


def _normalize_tags(value: Any) -> list[str]:
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = value
    else:
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = _normalize_text(item)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(text)
    return normalized


@dataclass(slots=True)
class Live2DPerformPlan:
    """结构化表演规划结果"""

    motion_intent: str | None = None
    emotion_tags: list[str] = field(default_factory=list)
    expression_intent: str | None = None
    intensity: float = 0.7
    hold_ms: int = 0
    confidence: float = 0.0
    notes: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


def parse_live2d_perform_plan(payload: dict[str, Any] | None) -> Live2DPerformPlan | None:
    """将 LLM 的 JSON 输出归一化为标准规划结果"""

    if not isinstance(payload, dict):
        return None

    motion_intent = _normalize_text(payload.get("motion_intent"))
    emotion_tags = _normalize_tags(payload.get("emotion_tags"))
    expression_intent = _normalize_text(payload.get("expression_intent"))
    intensity = _normalize_float(payload.get("intensity"), 0.7, 0.0, 1.0)
    hold_ms = _normalize_int(payload.get("hold_ms"), 0, 0, MAX_HOLD_MS)
    confidence = _normalize_float(payload.get("confidence"), 0.0, 0.0, 1.0)
    notes = _normalize_text(payload.get("notes"))

    if not motion_intent and not emotion_tags and not expression_intent:
        return None

    return Live2DPerformPlan(
        motion_intent=motion_intent,
        emotion_tags=emotion_tags,
        expression_intent=expression_intent,
        intensity=intensity,
        hold_ms=hold_ms,
        confidence=confidence,
        notes=notes,
        raw=payload,
    )
