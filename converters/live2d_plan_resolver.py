"""将语义规划结果映射为显式 Live2D 表演指令"""

from __future__ import annotations

import re
from typing import Any

from ..core.expression_types import (
    LIVE2D_EXPRESSION_TYPE_SET,
    TAG_ALIASES,
    normalize_expression_type,
)
from ..core.live2d_plan_schema import Live2DPerformPlan
from ..core.model_protocol import (
    build_legacy_motion_groups_from_v2,
    is_v2_model_info,
    iter_v2_motions,
    normalize_expression_entries,
)
from ..core.protocol import (
    create_expression_element,
    create_expression_element_v2,
    create_motion_element,
    create_motion_element_v2,
)

TOKEN_PATTERN = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+", re.IGNORECASE)


def _contains_alias(text: str, alias: str) -> bool:
    if not text or not alias:
        return False

    if re.search(r"[a-z0-9]", alias, re.IGNORECASE):
        return alias in TOKEN_PATTERN.findall(text)
    return alias in text


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
            if any(_contains_alias(normalized, alias) for alias in aliases):
                return canonical
        return normalized

    def _get_capabilities(self) -> dict[str, Any]:
        capabilities = self.client_model_info.get("capabilities")
        return capabilities if isinstance(capabilities, dict) else {}

    def _get_motion_groups(self) -> dict[str, list[dict[str, Any]]]:
        motion_groups = self.client_model_info.get("motionGroups")
        if isinstance(motion_groups, dict):
            return motion_groups
        if is_v2_model_info(self.client_model_info):
            return build_legacy_motion_groups_from_v2(self.client_model_info)
        return {}

    def _get_expression_catalog(self) -> list[dict[str, Any]]:
        catalog = self.client_model_info.get("expressionCatalog")
        return catalog if isinstance(catalog, list) else []

    def _get_expressions(self) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for item in normalize_expression_entries(self.client_model_info):
            expression_id = str(
                item.get("name") if is_v2_model_info(self.client_model_info) else item.get("id")
            ).strip()
            key = expression_id.lower()
            if expression_id and key not in seen:
                seen.add(key)
                normalized.append(expression_id)
        return normalized

    def _get_semantic_presets(self) -> dict[str, list[str]]:
        presets = self.client_model_info.get("semanticPresets")
        if not isinstance(presets, dict):
            return {}

        normalized: dict[str, list[str]] = {}
        for key, value in presets.items():
            normalized_key = normalize_expression_type(key)
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

    def _has_expression_catalog_entry(self, expression_id: str) -> bool:
        normalized = str(expression_id or "").strip()
        if not normalized:
            return False
        return any(
            str(entry.get("id", "") or "").strip() == normalized
            for entry in self._get_expression_catalog()
        )

    def _collect_tags(self, plan: Live2DPerformPlan) -> list[str]:
        tags: list[str] = []
        for item in [*plan.emotion_tags, plan.expression_intent, plan.motion_intent]:
            normalized = self._normalize_tag(item)
            if normalized and normalized not in tags:
                tags.append(normalized)
        return tags

    def _expression_matches_intent(self, candidate: Any, intent: str) -> bool:
        if not isinstance(candidate, str):
            return False

        candidate_text = candidate.strip()
        intent_text = intent.strip()
        if not candidate_text or not intent_text:
            return False

        candidate_lower = candidate_text.lower()
        intent_lower = intent_text.lower()
        if candidate_lower == intent_lower or intent_lower in candidate_lower:
            return True

        normalized_candidate = self._normalize_tag(candidate_text)
        normalized_intent = self._normalize_tag(intent_text)
        if normalized_candidate and normalized_intent and normalized_candidate == normalized_intent:
            return True

        aliases = set(TAG_ALIASES.get(normalized_intent or "", set()))
        if normalized_intent:
            aliases.add(normalized_intent)
        for alias in aliases:
            alias_lower = str(alias or "").strip().lower()
            if alias_lower and _contains_alias(candidate_lower, alias_lower):
                return True

        return False

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
                if self._expression_matches_intent(candidate, normalized):
                    return entry_id

        for expression_id in self._get_expressions():
            if self._expression_matches_intent(expression_id, normalized):
                return expression_id
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

        for tag in tags:
            candidate_id = self._find_expression_by_intent(tag)
            if candidate_id and candidate_id not in seen:
                seen.add(candidate_id)
                resolved.append(candidate_id)
                if len(resolved) >= 3:
                    return resolved

        return resolved

    def summarize_resolution_context(self, plan: Live2DPerformPlan) -> dict[str, Any]:
        catalog = self._get_expression_catalog()
        return {
            "tags": self._collect_tags(plan),
            "resolvedExpressionIds": self._resolve_expression_ids(plan),
            "supportsCombo": self._supports_combo(),
            "supportsSemantic": self._supports_semantic(),
            "expressions": self._get_expressions()[:16],
            "semanticPresetKeys": sorted(self._get_semantic_presets().keys())[:16],
            "catalog": [
                {
                    "id": str(entry.get("id", "") or "").strip(),
                    "aliases": entry.get("aliases") if isinstance(entry.get("aliases"), list) else [],
                    "tags": entry.get("tags") if isinstance(entry.get("tags"), list) else [],
                    "supportsCombo": bool(entry.get("supportsCombo")),
                }
                for entry in catalog[:12]
                if isinstance(entry, dict)
            ],
            "motionGroups": list(self._get_motion_groups().keys())[:16],
        }

    def _resolve_motion(self, plan: Live2DPerformPlan) -> dict[str, Any] | None:
        if is_v2_model_info(self.client_model_info):
            return self._resolve_motion_v2(plan)

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

    def _resolve_motion_v2(self, plan: Live2DPerformPlan) -> dict[str, Any] | None:
        motions = [
            motion
            for motion in iter_v2_motions(self.client_model_info)
            if motion.get("category") == "action"
        ]
        if not motions:
            return None

        tags = self._collect_tags(plan)
        intents = [item for item in [plan.motion_intent, *tags] if item]
        best_motion = None
        best_score = 0

        for motion in motions:
            candidates = [
                str(motion.get("name") or "").strip().lower(),
                str(motion.get("id") or "").strip().lower(),
                str(motion.get("description") or "").strip().lower(),
            ]
            score = 0
            for intent in intents:
                intent_lower = str(intent).strip().lower()
                if not intent_lower:
                    continue
                for candidate in candidates:
                    if not candidate:
                        continue
                    if candidate == intent_lower:
                        score = max(score, 5)
                    elif intent_lower in candidate:
                        score = max(score, 4)
                    elif any(alias in candidate for alias in TAG_ALIASES.get(intent_lower, set())):
                        score = max(score, 3)
            if score > best_score:
                best_motion = motion
                best_score = score

        if not best_motion:
            return None

        motion_name = str(best_motion.get("name") or "").strip()
        if not motion_name:
            return None

        motion = create_motion_element_v2(name=motion_name, priority=2)
        motion_intent = self._normalize_tag(plan.motion_intent)
        if motion_intent:
            motion["motionType"] = motion_intent
        return motion

    def _resolve_expression(self, plan: Live2DPerformPlan, reset_policy: str) -> dict[str, Any] | None:
        intensity = max(0.25, min(plan.intensity or 0.7, 1.0))
        motion_intent = self._normalize_tag(plan.motion_intent)
        tags = self._collect_tags(plan)
        semantic_tags = [
            tag
            for tag in tags
            if tag in LIVE2D_EXPRESSION_TYPE_SET
            and tag in self._get_semantic_presets()
        ]
        if self._supports_semantic() and semantic_tags:
            return create_expression_element(
                semantic=[{"tag": tag, "weight": intensity} for tag in semantic_tags[:3]],
                hold_ms=plan.hold_ms,
                reset_policy=reset_policy,
                motion_type=motion_intent,
            )

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
            if is_v2_model_info(self.client_model_info):
                return create_expression_element_v2(
                    name=expression_ids[0],
                    hold_ms=plan.hold_ms,
                    reset_policy=reset_policy,
                )
            return create_expression_element(
                expression_id=expression_ids[0],
                hold_ms=plan.hold_ms,
                reset_policy=reset_policy,
                motion_type=motion_intent,
            )

        if self._supports_semantic():
            catalog = self._get_expression_catalog()
            supports_direct_semantic = not catalog or any(
                not self._has_expression_catalog_entry(expression_id)
                for expression_id in self._get_expressions()
            )
            if tags:
                semantic = [{"tag": tag, "weight": intensity} for tag in tags[:3]]
                if supports_direct_semantic:
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
