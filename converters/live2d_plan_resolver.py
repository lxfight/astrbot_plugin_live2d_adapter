"""将语义规划结果映射为显式 Live2D 表演指令"""

from __future__ import annotations

from typing import Any

from ..core.live2d_plan_schema import Live2DPerformPlan
from ..core.protocol import create_expression_element, create_motion_element

TAG_ALIASES = {
    "happy": {"happy", "joy", "cheerful", "smile", "开心", "高兴", "快乐", "笑"},
    "sad": {"sad", "down", "cry", "难过", "伤心", "沮丧", "哭"},
    "angry": {"angry", "mad", "rage", "生气", "愤怒", "恼火"},
    "surprised": {"surprised", "surprise", "shock", "惊讶", "震惊"},
    "thinking": {"thinking", "think", "ponder", "思考", "沉思"},
    "neutral": {"neutral", "calm", "default", "normal", "平静", "默认", "普通"},
    "speaking": {"speaking", "talk", "speak", "chat", "说话", "讲话"},
}


class Live2DPlanResolver:
    """规划结果解析器"""

    def __init__(self, client_model_info: dict[str, Any] | None = None):
        self.client_model_info = client_model_info or {}

    def _normalize_tag(self, value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip().lower()
        if not normalized:
            return None
        for canonical, aliases in TAG_ALIASES.items():
            if normalized == canonical or normalized in aliases:
                return canonical
        return normalized

    def _get_capabilities(self) -> dict[str, Any]:
        capabilities = self.client_model_info.get("capabilities")
        return capabilities if isinstance(capabilities, dict) else {}

    def _get_motion_groups(self) -> dict[str, list[dict[str, Any]]]:
        motion_groups = self.client_model_info.get("motionGroups")
        return motion_groups if isinstance(motion_groups, dict) else {}

    def _get_expression_catalog(self) -> list[dict[str, Any]]:
        catalog = self.client_model_info.get("expressionCatalog")
        return catalog if isinstance(catalog, list) else []

    def _get_semantic_presets(self) -> dict[str, list[str]]:
        presets = self.client_model_info.get("semanticPresets")
        if not isinstance(presets, dict):
            return {}

        normalized: dict[str, list[str]] = {}
        for key, value in presets.items():
            normalized_key = self._normalize_tag(key)
            if not normalized_key or not isinstance(value, list):
                continue
            items = [str(item or "").strip() for item in value]
            items = [item for item in items if item]
            if items:
                normalized[normalized_key] = items
        return normalized

    def _supports_combo(self) -> bool:
        capabilities = self._get_capabilities()
        return bool(capabilities.get("expressionCombo"))

    def _supports_semantic(self) -> bool:
        capabilities = self._get_capabilities()
        return bool(capabilities.get("semanticExpression"))

    def _supports_expression_combo_id(self, expression_id: str) -> bool:
        normalized = str(expression_id or "").strip()
        if not normalized:
            return False

        for entry in self._get_expression_catalog():
            entry_id = str(entry.get("id", "") or "").strip()
            if entry_id == normalized:
                return bool(entry.get("supportsCombo"))
        return False

    def _collect_tags(self, plan: Live2DPerformPlan) -> list[str]:
        tags: list[str] = []
        for item in [*plan.emotion_tags, plan.expression_intent, plan.motion_intent]:
            normalized = self._normalize_tag(item)
            if normalized and normalized not in tags:
                tags.append(normalized)
        return tags

    def _find_expression_by_intent(self, expression_intent: str | None) -> str | None:
        if not expression_intent:
            return None

        normalized = expression_intent.strip().lower()
        if not normalized:
            return None

        for entry in self._get_expression_catalog():
            entry_id = str(entry.get("id", "") or "").strip()
            aliases = entry.get("aliases") or []
            candidates = [entry_id, *aliases] if isinstance(aliases, list) else [entry_id]
            for candidate in candidates:
                if isinstance(candidate, str) and candidate.strip().lower() == normalized:
                    return entry_id

        for entry in self._get_expression_catalog():
            entry_id = str(entry.get("id", "") or "").strip()
            aliases = entry.get("aliases") or []
            candidates = [entry_id, *aliases] if isinstance(aliases, list) else [entry_id]
            for candidate in candidates:
                if isinstance(candidate, str) and normalized in candidate.strip().lower():
                    return entry_id
        return None

    def _resolve_expression_ids(self, plan: Live2DPerformPlan) -> list[str]:
        resolved: list[str] = []
        seen: set[str] = set()

        exact_match = self._find_expression_by_intent(plan.expression_intent)
        if exact_match:
            seen.add(exact_match)
            resolved.append(exact_match)

        tags = self._collect_tags(plan)
        presets = self._get_semantic_presets()
        for tag in tags:
            for candidate in presets.get(tag, []):
                candidate_id = str(candidate or "").strip()
                if candidate_id and candidate_id not in seen:
                    seen.add(candidate_id)
                    resolved.append(candidate_id)
                    break

        if len(resolved) >= 3:
            return resolved[:3]

        for tag in tags:
            for entry in self._get_expression_catalog():
                entry_id = str(entry.get("id", "") or "").strip()
                entry_tags = entry.get("tags") or []
                if (
                    entry_id
                    and entry_id not in seen
                    and isinstance(entry_tags, list)
                    and tag in {self._normalize_tag(item) for item in entry_tags}
                ):
                    seen.add(entry_id)
                    resolved.append(entry_id)
                    if len(resolved) >= 3:
                        return resolved

        return resolved

    def _resolve_motion(self, plan: Live2DPerformPlan) -> dict[str, Any] | None:
        motion_groups = self._get_motion_groups()
        if not motion_groups:
            return None

        tags = self._collect_tags(plan)
        intents = [item for item in [plan.motion_intent, *tags] if item]
        best_group = None
        best_score = 0

        for group_name, motions in motion_groups.items():
            if not isinstance(motions, list) or not motions:
                continue

            name_lower = str(group_name).strip().lower()
            score = 0
            for intent in intents:
                intent_lower = str(intent).strip().lower()
                if not intent_lower:
                    continue
                if name_lower == intent_lower:
                    score = max(score, 5)
                elif intent_lower in name_lower:
                    score = max(score, 4)
                elif any(alias in name_lower for alias in TAG_ALIASES.get(intent_lower, set())):
                    score = max(score, 3)

            if score > best_score:
                best_group = group_name
                best_score = score

        if not best_group and "neutral" in tags:
            for group_name, motions in motion_groups.items():
                if isinstance(motions, list) and motions and group_name.lower() == "idle":
                    best_group = group_name
                    break

        if not best_group:
            return None

        motion = create_motion_element(group=best_group, index=0, priority=2)
        motion_intent = self._normalize_tag(plan.motion_intent)
        if motion_intent:
            motion["motionType"] = motion_intent
        return motion

    def _resolve_expression(self, plan: Live2DPerformPlan, reset_policy: str) -> dict[str, Any] | None:
        intensity = max(0.25, min(plan.intensity or 0.7, 1.0))
        motion_intent = self._normalize_tag(plan.motion_intent)
        expression_ids = self._resolve_expression_ids(plan)

        combo_candidates = [
            expression_id
            for expression_id in expression_ids
            if self._supports_expression_combo_id(expression_id)
        ]
        if self._supports_combo() and combo_candidates:
            combo = [{"id": expression_id, "weight": intensity} for expression_id in combo_candidates]
            return create_expression_element(
                combo=combo,
                hold_ms=plan.hold_ms,
                reset_policy=reset_policy,
                motion_type=motion_intent,
            )

        if expression_ids:
            return create_expression_element(
                expression_id=expression_ids[0],
                hold_ms=plan.hold_ms,
                reset_policy=reset_policy,
                motion_type=motion_intent,
            )

        if self._supports_semantic():
            tags = self._collect_tags(plan)
            if tags:
                semantic = [{"tag": tag, "weight": intensity} for tag in tags[:3]]
                return create_expression_element(
                    semantic=semantic,
                    hold_ms=plan.hold_ms,
                    reset_policy=reset_policy,
                    motion_type=motion_intent,
                )

        return None

    def resolve(self, plan: Live2DPerformPlan, reset_policy: str = "keep") -> list[dict[str, Any]]:
        sequence: list[dict[str, Any]] = []

        motion = self._resolve_motion(plan)
        if motion:
            sequence.append(motion)

        expression = self._resolve_expression(plan, reset_policy=reset_policy)
        if expression:
            sequence.append(expression)

        return sequence
