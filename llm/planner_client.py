"""独立表演规划 LLM 客户端"""

from __future__ import annotations

import asyncio
import json
from typing import Any

try:
    from astrbot.api import logger
except Exception:  # pragma: no cover
    logger = None

from ..core.live2d_plan_schema import Live2DPerformPlan, parse_live2d_perform_plan
from ..core.planner_runtime import get_plugin_context
from ..core.expression_types import get_available_expression_types
from .planner_prompts import format_planner_prompt_v2


class PlannerLLMClient:
    """优先通过 AstrBot Provider 调用的规划客户端"""

    @staticmethod
    def _build_model_summary(
        client_model_info: dict[str, Any] | None,
    ) -> dict[str, Any]:
        model_info = client_model_info or {}
        return {
            "name": model_info.get("name"),
            "capabilities": model_info.get("capabilities") or {},
            "motionGroups": list((model_info.get("motionGroups") or {}).keys())[:32],
            "availableExpressionTypes": get_available_expression_types(model_info),
        }

    @staticmethod
    def _build_model_summary_v2(
        client_model_info: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """构建 v2.0 协议的模型摘要"""
        model_info = client_model_info or {}
        version = model_info.get("version", "1.0")

        if version == "2.0":
            return {
                "version": "2.0",
                "name": model_info.get("modelName"),
                "motions": model_info.get("motions", []),
                "expressions": model_info.get("expressions", []),
                "capabilities": model_info.get("capabilities", {})
            }

        # 回退到 v1.0 格式
        return PlannerLLMClient._build_model_summary(client_model_info)

    @staticmethod
    def _extract_response_text(payload: dict[str, Any]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""

        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if not isinstance(message, dict):
            return ""

        content = message.get("content")
        if isinstance(content, str):
            return content.strip()

        if not isinstance(content, list):
            return ""

        parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
        return "\n".join(parts).strip()

    @staticmethod
    def _extract_json_payload(text: str) -> dict[str, Any] | None:
        if not text:
            return None

        try:
            payload = json.loads(text)
            return payload if isinstance(payload, dict) else None
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            return None

        try:
            payload = json.loads(text[start : end + 1])
            return payload if isinstance(payload, dict) else None
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _parse_plan_from_text(text: str) -> Live2DPerformPlan | None:
        payload = PlannerLLMClient._extract_json_payload(text)
        plan = parse_live2d_perform_plan(payload)
        if logger and plan:
            logger.debug(
                f"[Live2DPlanner] 规划结果: {json.dumps(plan.raw, ensure_ascii=False)}"
            )
        return plan

    async def _plan_with_provider(
        self,
        reply_text: str,
        client_model_info: dict[str, Any] | None,
        planner_config: dict[str, Any],
    ) -> Live2DPerformPlan | None:
        context = get_plugin_context()
        if not context:
            if logger:
                logger.warning("[Live2DPlanner] 插件上下文不可用，无法调用独立 Provider")
            return None

        provider_id = str(planner_config.get("provider_id", "") or "").strip()
        if not provider_id:
            return None

        provider = context.get_provider_by_id(provider_id)
        if provider is None or not callable(getattr(provider, "text_chat", None)):
            if logger:
                logger.warning(
                    f"[Live2DPlanner] 规划 Provider 不可用: provider_id={provider_id}"
                )
            return None

        # 检测协议版本
        version = (client_model_info or {}).get("version", "1.0")
        if version == "2.0":
            # 使用 v2.0 格式化 prompt
            model_summary = self._build_model_summary_v2(client_model_info)
        else:
            # 使用 v1.0 格式
            model_summary = self._build_model_summary(client_model_info)

        request_payload = {
            "reply_text": reply_text,
            "client_model": model_summary,
        }
        timeout_seconds = float(planner_config.get("timeout_seconds", 20) or 20)

        try:
            response = await asyncio.wait_for(
                provider.text_chat(
                    prompt=json.dumps(request_payload, ensure_ascii=False),
                    system_prompt=str(planner_config.get("system_prompt", "") or "").strip(),
                    temperature=float(planner_config.get("temperature", 0.2) or 0.2),
                ),
                timeout=max(5, timeout_seconds),
            )
        except asyncio.TimeoutError:
            if logger:
                logger.warning(
                    f"[Live2DPlanner] 规划 Provider 请求超时: provider_id={provider_id}"
                )
            return None
        except Exception as exc:
            if logger:
                logger.warning(f"[Live2DPlanner] 规划 Provider 请求失败: {exc}")
            return None

        response_text = str(getattr(response, "completion_text", "") or "").strip()
        return self._parse_plan_from_text(response_text)

    async def plan_reply(
        self,
        reply_text: str,
        client_model_info: dict[str, Any] | None = None,
        planner_config: dict[str, Any] | None = None,
    ) -> Live2DPerformPlan | None:
        normalized_reply = str(reply_text or "").strip()
        if not normalized_reply:
            return None

        runtime_config = planner_config or {}
        effective_mode = str(runtime_config.get("effective_mode", "") or "").strip()
        if not runtime_config.get("enabled") or not effective_mode:
            return None

        if effective_mode == "provider":
            return await self._plan_with_provider(
                normalized_reply,
                client_model_info,
                runtime_config,
            )

        return None
