"""Live2D 固定表情类型"""

from __future__ import annotations

from typing import Any

LIVE2D_EXPRESSION_TYPES = (
    "neutral",
    "happy",
    "sad",
    "angry",
    "anxious",
    "surprised",
    "thinking",
    "tired",
    "disgusted",
    "blush",
    "playful",
    "sweat",
    "special",
    "speaking",
)

LIVE2D_EXPRESSION_TYPE_SET = set(LIVE2D_EXPRESSION_TYPES)

TAG_ALIASES: dict[str, set[str]] = {
    "neutral": {
        "neutral",
        "default",
        "normal",
        "calm",
        "peaceful",
        "warm",
        "friendly",
        "sweet",
        "gentle",
        "relieved",
        "relief",
        "中性",
        "默认",
        "普通",
        "平静",
        "冷静",
        "温柔",
        "温暖",
        "亲切",
        "安心",
        "放心",
        "放松",
    },
    "happy": {
        "happy",
        "joy",
        "cheer",
        "cheery",
        "cheerful",
        "delight",
        "delighted",
        "smile",
        "smiling",
        "laugh",
        "laughing",
        "big smile",
        "grin",
        "grinning",
        "excited",
        "exciting",
        "thrilled",
        "proud",
        "confident",
        "smug",
        "smirk",
        "开心",
        "高兴",
        "快乐",
        "愉快",
        "微笑",
        "笑",
        "大笑",
        "笑容",
        "兴奋",
        "激动",
        "自信",
        "骄傲",
        "得意",
        "坏笑",
    },
    "sad": {
        "sad",
        "down",
        "cry",
        "crying",
        "tear",
        "tears",
        "disappointed",
        "难过",
        "伤心",
        "沮丧",
        "哭",
        "哭泣",
        "流泪",
        "失望",
        "低落",
    },
    "angry": {
        "angry",
        "mad",
        "rage",
        "annoyed",
        "upset",
        "irritated",
        "生气",
        "愤怒",
        "恼火",
        "不爽",
        "烦躁",
    },
    "anxious": {
        "anxious",
        "nervous",
        "worried",
        "fear",
        "afraid",
        "scared",
        "紧张",
        "不安",
        "担心",
        "害怕",
        "恐惧",
    },
    "surprised": {"surprised", "surprise", "shock", "shocked", "wow", "惊讶", "震惊"},
    "thinking": {
        "thinking",
        "think",
        "ponder",
        "confused",
        "confusing",
        "curious",
        "curiosity",
        "思考",
        "沉思",
        "疑惑",
        "困惑",
        "好奇",
    },
    "tired": {
        "tired",
        "fatigued",
        "bored",
        "boring",
        "sleepy",
        "sleep",
        "疲惫",
        "累",
        "无聊",
        "困",
        "困倦",
        "想睡",
    },
    "disgusted": {
        "disgusted",
        "disgust",
        "contempt",
        "disdain",
        "厌恶",
        "嫌弃",
        "鄙夷",
        "轻蔑",
    },
    "blush": {
        "blush",
        "blushing",
        "shy",
        "bashful",
        "embarrassed",
        "awkward",
        "脸红",
        "害羞",
        "尴尬",
    },
    "playful": {
        "playful",
        "pout",
        "pouting",
        "wink",
        "winking",
        "eyes closed",
        "closed eyes",
        "sparkle",
        "sparkly",
        "star eyes",
        "俏皮",
        "撅嘴",
        "闹别扭",
        "眨眼",
        "闭眼",
        "星星眼",
        "高光",
    },
    "sweat": {"sweat", "sweating", "冷汗", "汗"},
    "special": {
        "special",
        "shadow",
        "dark",
        "dizzy",
        "confounded",
        "特殊",
        "特殊效果",
        "阴影",
        "黑线",
        "晕",
        "晕眩",
        "混乱",
    },
    "speaking": {"speaking", "talk", "speak", "chat", "说话", "讲话"},
}


def normalize_expression_type(value: Any) -> str | None:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return None
    return normalized if normalized in LIVE2D_EXPRESSION_TYPE_SET else None


def _normalize_expression_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        expression_id = str(item or "").strip()
        key = expression_id.lower()
        if expression_id and key not in seen:
            seen.add(key)
            result.append(expression_id)
    return result


def get_available_expression_type_assignments(
    client_model_info: dict[str, Any] | None,
) -> dict[str, list[str]]:
    if not isinstance(client_model_info, dict):
        return {}

    presets = client_model_info.get("semanticPresets")
    if not isinstance(presets, dict):
        return {}

    assignments: dict[str, list[str]] = {}
    seen_by_type: dict[str, set[str]] = {}
    for raw_type, raw_items in presets.items():
        expression_type = normalize_expression_type(raw_type)
        if not expression_type:
            continue

        for expression_id in _normalize_expression_ids(raw_items):
            seen = seen_by_type.setdefault(expression_type, set())
            key = expression_id.lower()
            if key in seen:
                continue
            seen.add(key)
            assignments.setdefault(expression_type, []).append(expression_id)

    return {
        expression_type: assignments[expression_type]
        for expression_type in LIVE2D_EXPRESSION_TYPES
        if assignments.get(expression_type)
    }


def get_available_expression_types(
    client_model_info: dict[str, Any] | None,
) -> list[str]:
    return list(get_available_expression_type_assignments(client_model_info).keys())
