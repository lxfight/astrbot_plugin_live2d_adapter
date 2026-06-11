"""LLM Planner Prompt 定义"""

# v2.0 System Prompt
PLANNER_SYSTEM_PROMPT_V2 = """
你是 Live2D 角色的表演导演，负责将对话内容转换为表演序列。

# 可用动作
{motions_list}

# 可用表情
{expressions_list}

# 输出格式
返回 JSON 数组，每个元素是一个表演步骤：

[
  {{
    "type": "motion",
    "name": "挥手",
    "priority": 2
  }},
  {{
    "type": "expression",
    "name": "微笑",
    "holdMs": 3000,
    "resetPolicy": "fadeOut"
  }},
  {{
    "type": "text",
    "content": "你好！今天天气真好啊。"
  }}
]

# 设计原则
1. **动作使用**：
   - 播放一次即结束，不会循环
   - 适合打招呼、道别、强调等场景
   - 避免频繁使用（每句话最多1个）

2. **表情控制**：
   - 必须指定 holdMs（持续时间）
   - 短暂情绪（惊讶、尴尬）：1000-2000ms
   - 持续情绪（微笑、沉思）：3000-5000ms
   - 长对话保持：整段语音时长 + 500ms

3. **resetPolicy 选择**：
   - fadeOut（推荐）：淡出到无表情，自然过渡
   - default：重置到默认表情
   - hold：保持表情不重置（用于连续对话）

4. **时序安排**：
   - 动作和表情可同时播放
   - 文字和语音自动同步
   - 先设置表情，再输出文字

# 示例
输入：你好！今天天气真不错呢。
输出：
[
  {{"type": "motion", "name": "挥手", "priority": 2}},
  {{"type": "expression", "name": "微笑", "holdMs": 4000, "resetPolicy": "fadeOut"}},
  {{"type": "text", "content": "你好！今天天气真不错呢。"}}
]
"""

# v2.0 Output Schema
PLANNER_OUTPUT_SCHEMA_V2 = {
    "type": "array",
    "items": {
        "oneOf": [
            {
                "type": "object",
                "properties": {
                    "type": {"const": "motion"},
                    "name": {"type": "string"},
                    "priority": {"type": "integer", "minimum": 1, "maximum": 3}
                },
                "required": ["type", "name"]
            },
            {
                "type": "object",
                "properties": {
                    "type": {"const": "expression"},
                    "name": {"type": "string"},
                    "holdMs": {"type": "integer", "minimum": 500},
                    "resetPolicy": {"enum": ["default", "fadeOut", "hold"]}
                },
                "required": ["type", "name", "holdMs"]
            },
            {
                "type": "object",
                "properties": {
                    "type": {"const": "text"},
                    "content": {"type": "string"}
                },
                "required": ["type", "content"]
            }
        ]
    }
}


def format_planner_prompt_v2(reply_text: str, planner_context: dict) -> str:
    """
    格式化 Planner Prompt v2

    Args:
        reply_text: 回复文本
        planner_context: 规划器上下文（来自 build_planner_context_v2）

    Returns:
        格式化后的 prompt
    """
    motions = planner_context.get("available_motions", [])
    expressions = planner_context.get("available_expressions", [])

    motions_list = "\n".join([
        f"- {m['name']}: {m.get('description', '')} (时长约{m.get('duration_ms', 0)/1000:.1f}秒)"
        for m in motions
    ]) if motions else "（无可用动作）"

    expressions_list = "\n".join([
        f"- {e['name']}: {e.get('description', '')}"
        for e in expressions
    ]) if expressions else "（无可用表情）"

    system_prompt = PLANNER_SYSTEM_PROMPT_V2.format(
        motions_list=motions_list,
        expressions_list=expressions_list
    )

    return f"{system_prompt}\n\n# 当前回复内容\n{reply_text}"
