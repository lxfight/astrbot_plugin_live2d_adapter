"""独立表情规划服务"""

from __future__ import annotations

from typing import Any

try:
    from astrbot.api import logger
except Exception:  # pragma: no cover
    logger = None

from ..core.diagnostics import (
    preview_text,
    summarize_client_model_info,
    summarize_perform_sequence,
)
from ..core.planner_runtime import resolve_planner_runtime_config
from ..converters.live2d_plan_resolver import Live2DPlanResolver
from ..llm.planner_client import PlannerLLMClient


class ExpressionPlannerService:
    """在主回复完成后生成 Live2D 表演补充序列"""

    def __init__(self):
        self.client = PlannerLLMClient()

    def get_runtime_config(self) -> dict[str, Any]:
        return resolve_planner_runtime_config()

    def is_enabled(self) -> bool:
        return bool(self.get_runtime_config().get("enabled"))

    def _has_actionable_expression_capability(
        self, client_model_info: dict[str, Any] | None
    ) -> bool:
        if not isinstance(client_model_info, dict) or not client_model_info:
            return False

        capabilities = client_model_info.get("capabilities")
        if not isinstance(capabilities, dict):
            return False

        if capabilities.get("expressionCombo"):
            catalog = client_model_info.get("expressionCatalog")
            if isinstance(catalog, list) and any(
                isinstance(entry, dict) and bool(entry.get("supportsCombo"))
                for entry in catalog
            ):
                return True

        if capabilities.get("semanticExpression"):
            presets = client_model_info.get("semanticPresets")
            if isinstance(presets, dict) and any(
                isinstance(value, list) and any(str(item or "").strip() for item in value)
                for value in presets.values()
            ):
                return True

        expressions = client_model_info.get("expressions")
        if isinstance(expressions, list) and any(str(item or "").strip() for item in expressions):
            return True

        return False

    async def build_followup_sequence(
        self,
        reply_text: str,
        client_model_info: dict[str, Any] | None = None,
        reset_policy: str = "keep",
    ) -> list[dict[str, Any]]:
        planner_config = self.get_runtime_config()
        if not planner_config.get("enabled"):
            if logger:
                logger.debug("[Live2DPlanner] 规划器未启用，跳过补发表演")
            return []
        if not self._has_actionable_expression_capability(client_model_info):
            if logger:
                logger.debug(
                    "[Live2DPlanner] 客户端缺少可用表情能力，跳过补发表演: "
                    f"model={summarize_client_model_info(client_model_info)}"
                )
            return []

        if logger:
            logger.debug(
                "[Live2DPlanner] 准备规划补发表演: "
                f"reply_len={len(str(reply_text or ''))}, "
                f"reply_preview={preview_text(reply_text)}, "
                f"model={summarize_client_model_info(client_model_info)}, "
                f"reset_policy={reset_policy}"
            )

        resolver = Live2DPlanResolver(client_model_info)
        plan = await self.client.plan_reply(
            reply_text,
            client_model_info,
            planner_config=planner_config,
        )
        if not plan:
            if logger:
                logger.debug("[Live2DPlanner] 规划 Provider 未返回有效结果，跳过补发表演")
            return []

        min_confidence = float(planner_config.get("min_confidence", 0.45) or 0.45)
        if logger:
            logger.debug(
                "[Live2DPlanner] 规划摘要: "
                f"motion_intent={plan.motion_intent}, "
                f"expression_intent={plan.expression_intent}, "
                f"emotion_tags={plan.emotion_tags}, "
                f"intensity={plan.intensity:.2f}, "
                f"hold_ms={plan.hold_ms}, "
                f"confidence={plan.confidence:.2f}, "
                f"min_confidence={min_confidence:.2f}"
            )
        if plan.confidence < min_confidence:
            if logger:
                logger.debug(
                    f"[Live2DPlanner] 规划置信度过低，已跳过: {plan.confidence:.2f} < {min_confidence:.2f}"
                )
            return []

        sequence = resolver.resolve(plan, reset_policy=reset_policy)
        if logger and sequence:
            logger.info(
                f"[Live2DPlanner] 已生成补发表演: source={planner_config.get('source')}, "
                f"motion_intent={plan.motion_intent}, "
                f"emotion_tags={plan.emotion_tags}, "
                f"sequence={summarize_perform_sequence(sequence)}"
            )
        elif logger:
            logger.debug("[Live2DPlanner] 规划结果未映射到可执行序列，跳过补发表演")
        return sequence
