"""情感分析器 - 根据文本内容推测情感并生成对应的动作和表情"""

from typing import Any


class EmotionAnalyzer:
    """情感分析器 - 根据文本内容推测情感并生成对应的动作和表情"""

    # 情感关键词映射
    EMOTION_KEYWORDS = {
        "happy": {
            "keywords": [
                "开心",
                "高兴",
                "哈哈",
                "嘿嘿",
                "😄",
                "😊",
                "笑",
                "好棒",
                "太好了",
                "棒",
            ],
            "expression": "happy",
            "motion": {"group": "Idle", "index": 0},
        },
        "sad": {
            "keywords": ["难过", "伤心", "哭", "😢", "😭", "呜呜", "不开心"],
            "expression": "sad",
            "motion": {"group": "Idle", "index": 1},
        },
        "angry": {
            "keywords": ["生气", "愤怒", "讨厌", "😠", "😡", "可恶"],
            "expression": "angry",
            "motion": {"group": "Shake", "index": 0},
        },
        "surprise": {
            "keywords": ["惊讶", "哇", "天啊", "😲", "😮", "震惊", "不会吧"],
            "expression": "surprise",
            "motion": {"group": "Greeting", "index": 0},
        },
        "think": {
            "keywords": ["想想", "思考", "嗯", "让我想想", "🤔"],
            "expression": "normal",
            "motion": {"group": "Idle", "index": 2},
        },
    }

    @classmethod
    def analyze(cls, text: str) -> tuple[str | None, dict[str, Any] | None]:
        """分析文本情感，返回 (表情ID, 动作配置)"""
        text_lower = text.lower()

        for emotion, config in cls.EMOTION_KEYWORDS.items():
            for keyword in config["keywords"]:
                if keyword in text or keyword.lower() in text_lower:
                    return config["expression"], config["motion"]

        # 默认返回 None，表示没有特殊情感
        return None, None


# 使用示例
if __name__ == "__main__":
    # 测试情感分析
    text = "太好了！我很开心！"
    expression, motion = EmotionAnalyzer.analyze(text)
    print(f"文本: {text}")
    print(f"表情: {expression}, 动作: {motion}")
