"""AstrBot Live2D Adapter - AstrBot 插件入口"""

from astrbot.api.star import Context, Star, register

from .adapters.platform_adapter import Live2DPlatformAdapter


@register("Live2DAdapter", "lxfight", "Live2DAdapter 插件", "1.0.0")
class Live2DAdapter(Star):
    """Live2D 平台适配器插件"""

    def __init__(self, context: Context):
        super().__init__(context)


__all__ = ["Live2DAdapter", "Live2DPlatformAdapter"]
