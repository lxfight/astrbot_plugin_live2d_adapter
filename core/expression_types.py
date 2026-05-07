"""Live2D 固定表情类型"""

from __future__ import annotations

from typing import Any

LIVE2D_EXPRESSION_TYPES = (
    "neutral",
    "calm",
    "happy",
    "laugh",
    "excited",
    "warm",
    "relieved",
    "proud",
    "smug",
    "sad",
    "cry",
    "disappointed",
    "angry",
    "annoyed",
    "fear",
    "anxious",
    "surprised",
    "confused",
    "thinking",
    "curious",
    "bored",
    "tired",
    "sleepy",
    "disgusted",
    "contempt",
    "shy",
    "embarrassed",
    "blush",
    "pout",
    "wink",
    "eyes_closed",
    "sparkle",
    "sweat",
    "shadow",
    "dizzy",
    "speaking",
)

LIVE2D_EXPRESSION_TYPE_SET = set(LIVE2D_EXPRESSION_TYPES)

TAG_ALIASES: dict[str, set[str]] = {
    "neutral": {"neutral", "default", "normal", "中性", "默认", "普通"},
    "calm": {"calm", "peaceful", "平静", "冷静"},
    "happy": {
        "happy",
        "joy",
        "cheer",
        "cheery",
        "cheerful",
        "delight",
        "delighted",
        "playful",
        "smile",
        "smiling",
        "开心",
        "高兴",
        "快乐",
        "愉快",
        "俏皮",
        "微笑",
        "笑",
    },
    "laugh": {"laugh", "laughing", "big smile", "grin", "grinning", "大笑", "笑容"},
    "excited": {"excited", "exciting", "thrilled", "兴奋", "激动"},
    "warm": {"warm", "friendly", "sweet", "gentle", "温柔", "温暖", "亲切"},
    "relieved": {"relieved", "relief", "安心", "放心", "放松"},
    "proud": {"proud", "confident", "自信", "骄傲"},
    "smug": {"smug", "smirk", "得意", "坏笑"},
    "sad": {"sad", "down", "难过", "伤心", "沮丧"},
    "cry": {"cry", "crying", "tear", "tears", "哭", "哭泣", "流泪"},
    "disappointed": {"disappointed", "失望", "低落"},
    "angry": {"angry", "mad", "rage", "生气", "愤怒"},
    "annoyed": {"annoyed", "upset", "irritated", "恼火", "不爽", "烦躁"},
    "fear": {"fear", "afraid", "scared", "害怕", "恐惧"},
    "anxious": {"anxious", "nervous", "worried", "紧张", "不安", "担心"},
    "surprised": {"surprised", "surprise", "shock", "shocked", "wow", "惊讶", "震惊"},
    "confused": {"confused", "confusing", "疑惑", "困惑"},
    "thinking": {"thinking", "think", "ponder", "思考", "沉思"},
    "curious": {"curious", "curiosity", "好奇"},
    "bored": {"bored", "boring", "无聊"},
    "tired": {"tired", "fatigued", "疲惫", "累"},
    "sleepy": {"sleepy", "sleep", "困", "困倦", "想睡"},
    "disgusted": {"disgusted", "disgust", "厌恶", "嫌弃"},
    "contempt": {"contempt", "disdain", "鄙夷", "轻蔑"},
    "shy": {"shy", "bashful", "害羞"},
    "embarrassed": {"embarrassed", "awkward", "尴尬"},
    "blush": {"blush", "blushing", "脸红"},
    "pout": {"pout", "pouting", "撅嘴", "闹别扭"},
    "wink": {"wink", "winking", "眨眼"},
    "eyes_closed": {"eyes closed", "closed eyes", "闭眼"},
    "sparkle": {"sparkle", "sparkly", "star eyes", "星星眼", "高光"},
    "sweat": {"sweat", "sweating", "冷汗", "汗"},
    "shadow": {"shadow", "dark", "阴影", "黑线"},
    "dizzy": {"dizzy", "confounded", "晕", "晕眩", "混乱"},
    "speaking": {"speaking", "talk", "speak", "chat", "说话", "讲话"},
}


def normalize_expression_type(value: Any) -> str | None:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return None

    for canonical, aliases in TAG_ALIASES.items():
        if normalized == canonical or normalized in aliases:
            return canonical
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
