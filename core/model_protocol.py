"""Helpers for reading Live2D model capability payloads."""

from __future__ import annotations

import re
from typing import Any


def is_v2_model_info(client_model_info: dict[str, Any] | None) -> bool:
    return isinstance(client_model_info, dict) and str(client_model_info.get("version")) == "2.0"


def parse_motion_id_parts(motion_id: str) -> tuple[str, int]:
    match = re.match(r"^(.*)_(\d+)$", str(motion_id or ""))
    if not match:
        return str(motion_id or ""), 0
    return match.group(1), int(match.group(2) or 0)


def iter_v2_motions(client_model_info: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(client_model_info, dict):
        return []
    motions = client_model_info.get("motions")
    return [item for item in motions if isinstance(item, dict)] if isinstance(motions, list) else []


def iter_v2_expressions(client_model_info: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(client_model_info, dict):
        return []
    expressions = client_model_info.get("expressions")
    return (
        [item for item in expressions if isinstance(item, dict)]
        if isinstance(expressions, list)
        else []
    )


def normalize_expression_entries(client_model_info: dict[str, Any] | None) -> list[dict[str, str]]:
    if not isinstance(client_model_info, dict):
        return []

    expressions = client_model_info.get("expressions")
    if not isinstance(expressions, list):
        return []

    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in expressions:
        if isinstance(item, dict):
            expression_id = str(item.get("id") or item.get("name") or "").strip()
            name = str(item.get("name") or expression_id).strip()
        else:
            expression_id = str(item or "").strip()
            name = expression_id

        key = expression_id.lower()
        if expression_id and key not in seen:
            seen.add(key)
            result.append({"id": expression_id, "name": name})
    return result


def resolve_v2_motion_by_name(
    client_model_info: dict[str, Any] | None,
    name: str | None,
) -> dict[str, Any] | None:
    normalized = str(name or "").strip().lower()
    if not normalized:
        return None

    for motion in iter_v2_motions(client_model_info):
        candidates = [
            str(motion.get("name") or "").strip(),
            str(motion.get("id") or "").strip(),
        ]
        if normalized in {candidate.lower() for candidate in candidates if candidate}:
            return motion
    return None


def resolve_v2_expression_by_name(
    client_model_info: dict[str, Any] | None,
    name: str | None,
) -> dict[str, str] | None:
    normalized = str(name or "").strip().lower()
    if not normalized:
        return None

    for expression in normalize_expression_entries(client_model_info):
        candidates = [expression["id"], expression["name"]]
        if normalized in {candidate.lower() for candidate in candidates if candidate}:
            return expression
    return None


def build_legacy_motion_groups_from_v2(
    client_model_info: dict[str, Any] | None,
) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for motion in iter_v2_motions(client_model_info):
        motion_id = str(motion.get("id") or "").strip()
        if not motion_id:
            continue
        group, index = parse_motion_id_parts(motion_id)
        groups.setdefault(group, []).append({"index": index, "name": motion.get("name")})
    return groups
