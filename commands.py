"""Live2D Adapter 命令注册模块"""

from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.star import Star
from astrbot.core.star.register.star_handler import register_command
from astrbot.core.star.filter.permission import PermissionType, register_permission_type


def register_commands(plugin: Star):
    """注册所有 Live2D 管理命令

    Args:
        plugin: Live2DAdapter 插件实例
    """

    @register_command("live2d.status", alias={"l2d.status"})
    async def cmd_status(self, event: AstrMessageEvent):
        """显示 Live2D 适配器状态"""
        return await plugin.handle_command(event, "status")

    @register_command("live2d.info", alias={"l2d.info"})
    async def cmd_info(self, event: AstrMessageEvent):
        """显示当前客户端详细信息"""
        return await plugin.handle_command(event, "info")

    @register_command("live2d.list", alias={"l2d.list", "l2d.clients"})
    async def cmd_list(self, event: AstrMessageEvent):
        """列出所有连接的客户端"""
        return await plugin.handle_command(event, "list")

    @register_command("live2d.resources", alias={"l2d.resources", "l2d.res"})
    async def cmd_resources(self, event: AstrMessageEvent):
        """显示资源使用情况"""
        return await plugin.handle_command(event, "resources")

    @register_command("live2d.cleanup", alias={"l2d.cleanup"})
    @register_permission_type(PermissionType.ADMIN)
    async def cmd_cleanup(self, event: AstrMessageEvent):
        """手动触发资源清理（管理员）"""
        return await plugin.handle_command(event, "cleanup")

    @register_command("live2d.config", alias={"l2d.config", "l2d.cfg"})
    @register_permission_type(PermissionType.ADMIN)
    async def cmd_config(self, event: AstrMessageEvent):
        """显示当前配置（管理员）"""
        return await plugin.handle_command(event, "config")

    # 将命令方法绑定到插件实例
    plugin.cmd_status = cmd_status.__get__(plugin, type(plugin))
    plugin.cmd_info = cmd_info.__get__(plugin, type(plugin))
    plugin.cmd_list = cmd_list.__get__(plugin, type(plugin))
    plugin.cmd_resources = cmd_resources.__get__(plugin, type(plugin))
    plugin.cmd_cleanup = cmd_cleanup.__get__(plugin, type(plugin))
    plugin.cmd_config = cmd_config.__get__(plugin, type(plugin))
