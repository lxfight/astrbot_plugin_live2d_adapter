"""AstrBot Live2D Adapter - AstrBot 插件入口"""

import time

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageEventResult, filter
from astrbot.api.star import Context, Star

from .adapters.platform_adapter import Live2DPlatformAdapter


class Live2DAdapter(Star):
    """Live2D 平台适配器插件"""

    def __init__(self, context: Context):
        super().__init__(context)
        self.context = context

    def _get_adapter(self) -> Live2DPlatformAdapter | None:
        """获取 Live2D 平台适配器实例"""
        try:
            platform_manager = self.context.platform_manager
            for platform in platform_manager.platform_insts:
                if isinstance(platform, Live2DPlatformAdapter):
                    return platform
            return None
        except Exception as e:
            logger.error(f"获取 Live2D 适配器失败: {e}")
            return None

    def _format_bytes(self, bytes_size: int) -> str:
        """格式化字节大小"""
        size = float(bytes_size)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}TB"

    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            return f"{seconds // 60}分钟"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}小时{minutes}分钟"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days}天{hours}小时"

    @filter.command_group("live2d", alias={"l2d"})
    def live2d_cmd(self):
        """Live2D 适配器管理命令组"""

        pass

    @live2d_cmd.command("status")
    async def cmd_status(self, event: AstrMessageEvent) -> MessageEventResult:
        """显示 Live2D 适配器状态"""
        adapter = self._get_adapter()
        if not adapter:
            return MessageEventResult().message(
                "[Live2D Adapter] 错误: 适配器未启动或未找到"
            )
        return await self._cmd_status(adapter)

    @live2d_cmd.command("info")
    async def cmd_info(self, event: AstrMessageEvent) -> MessageEventResult:
        """显示当前客户端详细信息"""
        adapter = self._get_adapter()
        if not adapter:
            return MessageEventResult().message(
                "[Live2D Adapter] 错误: 适配器未启动或未找到"
            )
        return await self._cmd_info(adapter)

    @live2d_cmd.command("list", alias={"clients"})
    async def cmd_list(self, event: AstrMessageEvent) -> MessageEventResult:
        """列出所有连接的客户端"""
        adapter = self._get_adapter()
        if not adapter:
            return MessageEventResult().message(
                "[Live2D Adapter] 错误: 适配器未启动或未找到"
            )
        return await self._cmd_list(adapter)

    @live2d_cmd.command("resources", alias={"res"})
    async def cmd_resources(self, event: AstrMessageEvent) -> MessageEventResult:
        """显示资源使用情况"""
        adapter = self._get_adapter()
        if not adapter:
            return MessageEventResult().message(
                "[Live2D Adapter] 错误: 适配器未启动或未找到"
            )
        return await self._cmd_resources(adapter)

    @filter.permission_type(filter.PermissionType.ADMIN)
    @live2d_cmd.command("cleanup")
    async def cmd_cleanup(self, event: AstrMessageEvent) -> MessageEventResult:
        """手动触发资源清理（仅管理员）"""
        adapter = self._get_adapter()
        if not adapter:
            return MessageEventResult().message(
                "[Live2D Adapter] 错误: 适配器未启动或未找到"
            )
        return await self._cmd_cleanup(adapter)

    @filter.permission_type(filter.PermissionType.ADMIN)
    @live2d_cmd.command("config", alias={"cfg"})
    async def cmd_config(self, event: AstrMessageEvent) -> MessageEventResult:
        """显示当前配置（仅管理员）"""
        adapter = self._get_adapter()
        if not adapter:
            return MessageEventResult().message(
                "[Live2D Adapter] 错误: 适配器未启动或未找到"
            )
        return await self._cmd_config(adapter)

    async def _cmd_status(self, adapter: Live2DPlatformAdapter) -> MessageEventResult:
        """显示适配器状态"""
        try:
            # 连接信息
            ws_server = adapter.ws_server
            client_count = len(ws_server.clients) if ws_server else 0
            max_connections = adapter.config_obj.max_connections
            current_client = adapter.current_client_id

            # 资源使用情况
            resource_info = ""
            if adapter.resource_manager:
                rm = adapter.resource_manager
                resource_files = len(rm.resources)
                max_files = rm.max_total_files or 1
                total_bytes = sum(r.size for r in rm.resources.values())
                max_bytes = rm.max_total_bytes or 1
                usage_percent = (total_bytes / max_bytes * 100) if max_bytes > 0 else 0

                resource_info = f"""
资源使用:
  - 资源文件: {resource_files}/{max_files} ({resource_files / max_files * 100:.1f}%)
  - 存储空间: {self._format_bytes(total_bytes)}/{self._format_bytes(max_bytes)} ({usage_percent:.1f}%)"""

            # 临时文件信息
            temp_info = ""
            if adapter.input_converter and hasattr(
                adapter.input_converter, "get_temp_files_info"
            ):
                temp_info_data = adapter.input_converter.get_temp_files_info()
                temp_files = temp_info_data["count"]
                temp_bytes = temp_info_data["total_bytes"]
                max_temp_files = getattr(adapter.input_converter, "temp_max_files", 1)
                max_temp_bytes = getattr(
                    adapter.input_converter, "temp_max_total_bytes", 1
                )
                temp_usage = (
                    (temp_bytes / max_temp_bytes * 100) if max_temp_bytes > 0 else 0
                )

                temp_info = f"""
  - 临时文件: {temp_files}/{max_temp_files}
  - 临时空间: {self._format_bytes(temp_bytes)}/{self._format_bytes(max_temp_bytes)} ({temp_usage:.1f}%)"""

            # 服务器状态
            ws_status = "运行中" if ws_server and ws_server.server else "未运行"
            ws_addr = (
                f"{adapter.config_obj.server_host}:{adapter.config_obj.server_port}"
            )

            resource_server_status = "未启用"
            resource_addr = ""
            if (
                adapter.config_obj.resource_enabled
                and adapter.config_obj.single_port_mode
            ):
                resource_server_status = "与 WebSocket 共用端口"
                resource_addr = f"{adapter.config_obj.server_host}:{adapter.config_obj.server_port}{adapter.config_obj.resource_path}"
            elif adapter.resource_server:
                resource_server_status = "运行中"
                resource_addr = f"{adapter.config_obj.resource_host}:{adapter.config_obj.resource_port}{adapter.config_obj.resource_path}"

            streaming_status = (
                "已启用"
                if getattr(adapter.config_obj, "enable_streaming", False)
                else "未启用"
            )

            status_msg = f"""[Live2D Adapter] 适配器状态

连接信息:
  - 当前连接数: {client_count}/{max_connections}
  - 当前客户端: {current_client or "无"}
{resource_info}{temp_info}

服务器状态:
  - WebSocket: {ws_status} ({ws_addr})
  - 资源服务器: {resource_server_status} {f"({resource_addr})" if resource_addr else ""}
  - 流式消息: {streaming_status}
  - 语音输出: 跟随 AstrBot 的 TTS/音频消息"""

            return MessageEventResult().message(status_msg)

        except Exception as e:
            logger.exception(f"获取状态失败: {e}")
            return MessageEventResult().message(
                f"[Live2D Adapter] 错误: 获取状态失败 - {e}"
            )

    async def _cmd_info(self, adapter: Live2DPlatformAdapter) -> MessageEventResult:
        """显示详细信息"""
        try:
            if not adapter.current_client_id:
                return MessageEventResult().message(
                    "[Live2D Adapter] 当前没有连接的客户端"
                )

            client_id = adapter.current_client_id
            ws_server = adapter.ws_server

            # 获取客户端信息
            if ws_server and hasattr(ws_server, "handler"):
                client_info = ws_server.handler.client_states.get(client_id, {})
            else:
                client_info = {}
            model_info = client_info.get("model", {})
            session_info = client_info.get("session", {})

            model_name = model_info.get("name", "未知")
            motion_groups = model_info.get("motionGroups", {})
            expressions = model_info.get("expressions", [])

            # 计算连接时长
            connect_time = session_info.get("connect_time")
            if connect_time:
                duration = int(time.time() - connect_time)
                duration_str = self._format_duration(duration)
            else:
                duration_str = "未知"

            # 动作组信息
            motion_info = ""
            if motion_groups:
                total_motions = sum(len(motions) for motions in motion_groups.values())
                motion_info = (
                    f"\n  - 动作组: {len(motion_groups)} 组，共 {total_motions} 个动作"
                )

            # 表情信息
            expression_info = ""
            if expressions:
                expression_info = f"\n  - 表情: {len(expressions)} 个"

            info_msg = f"""[Live2D Adapter] 客户端详细信息

客户端 ID: {client_id}
模型名称: {model_name}
连接时长: {duration_str}{motion_info}{expression_info}

提示: 使用 /live2d test_motion <组名> 测试动作
      使用 /live2d test_expression <表情ID> 测试表情"""

            return MessageEventResult().message(info_msg)

        except Exception as e:
            logger.exception(f"获取详细信息失败: {e}")
            return MessageEventResult().message(
                f"[Live2D Adapter] 错误: 获取详细信息失败 - {e}"
            )

    async def _cmd_list(self, adapter: Live2DPlatformAdapter) -> MessageEventResult:
        """列出所有连接的客户端"""
        try:
            ws_server = adapter.ws_server
            if not ws_server or not ws_server.clients:
                return MessageEventResult().message(
                    "[Live2D Adapter] 当前没有连接的客户端"
                )

            client_list = []
            for client_id in ws_server.clients.keys():
                client_info = ws_server.handler.client_states.get(client_id, {})
                model_info = client_info.get("model", {})
                model_name = model_info.get("name", "未知")

                is_current = (
                    "[当前]" if client_id == adapter.current_client_id else "      "
                )
                client_list.append(f"{is_current} {client_id[:8]}... - {model_name}")

            list_msg = f"""[Live2D Adapter] 连接的客户端列表 ({len(client_list)})

""" + "\n".join(client_list)

            return MessageEventResult().message(list_msg)

        except Exception as e:
            logger.exception(f"获取客户端列表失败: {e}")
            return MessageEventResult().message(
                f"[Live2D Adapter] 错误: 获取客户端列表失败 - {e}"
            )

    async def _cmd_resources(
        self, adapter: Live2DPlatformAdapter
    ) -> MessageEventResult:
        """显示资源信息"""
        try:
            if not adapter.resource_manager:
                return MessageEventResult().message("[Live2D Adapter] 资源管理器未启用")

            rm = adapter.resource_manager
            resources = rm.resources

            if not resources:
                return MessageEventResult().message(
                    "[Live2D Adapter] 当前没有存储的资源"
                )

            # 按类型统计
            type_stats = {}
            total_size = 0
            for resource in resources.values():
                kind = resource.kind
                type_stats[kind] = type_stats.get(kind, 0) + 1
                total_size += resource.size

            stats_lines = [
                f"  - {kind}: {count} 个" for kind, count in type_stats.items()
            ]

            resource_msg = (
                f"""[Live2D Adapter] 资源统计

总计: {len(resources)} 个文件，{self._format_bytes(total_size)}

按类型:
"""
                + "\n".join(stats_lines)
                + f"""

配额: {len(resources)}/{rm.max_total_files or 0} 文件
      {self._format_bytes(total_size)}/{self._format_bytes(rm.max_total_bytes or 0)} 空间"""
            )

            return MessageEventResult().message(resource_msg)

        except Exception as e:
            logger.exception(f"获取资源信息失败: {e}")
            return MessageEventResult().message(
                f"[Live2D Adapter] 错误: 获取资源信息失败 - {e}"
            )

    async def _cmd_cleanup(self, adapter: Live2DPlatformAdapter) -> MessageEventResult:
        """手动触发清理"""
        try:
            cleaned_resources = 0
            cleaned_temp = 0

            # 清理资源
            if adapter.resource_manager:
                before = len(adapter.resource_manager.resources)
                # ResourceManager 只有 cleanup 方法
                if hasattr(adapter.resource_manager, "cleanup"):
                    adapter.resource_manager.cleanup()  # type: ignore[attr-defined]
                after = len(adapter.resource_manager.resources)
                cleaned_resources = before - after

            # 清理临时文件
            if adapter.input_converter and hasattr(
                adapter.input_converter, "get_temp_files_info"
            ):
                before_info = adapter.input_converter.get_temp_files_info()
                adapter.input_converter.cleanup_temp_files()
                after_info = adapter.input_converter.get_temp_files_info()
                cleaned_temp = before_info["count"] - after_info["count"]

            cleanup_msg = f"""[Live2D Adapter] 清理完成

  - 清理资源文件: {cleaned_resources} 个
  - 清理临时文件: {cleaned_temp} 个"""

            return MessageEventResult().message(cleanup_msg)

        except Exception as e:
            logger.exception(f"清理失败: {e}")
            return MessageEventResult().message(
                f"[Live2D Adapter] 错误: 清理失败 - {e}"
            )

    async def _cmd_config(self, adapter: Live2DPlatformAdapter) -> MessageEventResult:
        """显示当前配置"""
        try:
            config = adapter.config_obj
            token_masked = adapter._mask_token(config.auth_token)
            token_source = getattr(adapter, "_auth_token_source", "unknown")
            token_file = getattr(adapter, "_auth_token_file", None)
            token_file_line = f"\n  - 密钥文件: {token_file}" if token_file else ""

            config_msg = f"""[Live2D Adapter] 适配器配置

WebSocket:
  - 地址: {config.server_host}:{config.server_port}
  - 路径: {config.ws_path}
  - 认证: 已启用（强制）
  - 密钥(脱敏): {token_masked}
  - 密钥来源: {token_source}{token_file_line}
  - 最大连接: {config.max_connections}

功能:
  - 流式消息: {"已启用" if getattr(config, "enable_streaming", False) else "未启用"}
  - 语音输出: 跟随 AstrBot 的 TTS/音频消息
  - 单端口模式: {"已启用" if getattr(config, "single_port_mode", True) else "未启用"}
  - 资源服务器: {"已启用" if config.resource_enabled else "未启用"}
  - 公网入口: {getattr(config, "public_origin", "") or "自动推导"}

资源管理:
  - 资源目录: {config.resource_dir}
  - 资源 TTL: {self._format_duration(getattr(config, "resource_ttl_seconds", 0))}
  - 最大文件: {getattr(config, "resource_max_files", 0)}
  - 最大空间: {self._format_bytes(getattr(config, "resource_max_total_bytes", 0))}

临时文件:
  - 临时目录: {getattr(config, "temp_dir", "未知")}
  - 临时 TTL: {self._format_duration(getattr(config, "temp_ttl_seconds", 0))}
  - 最大文件: {getattr(config, "temp_max_files", 0)}"""

            return MessageEventResult().message(config_msg)

        except Exception as e:
            logger.exception(f"获取配置失败: {e}")
            return MessageEventResult().message(
                f"[Live2D Adapter] 错误: 获取配置失败 - {e}"
            )


__all__ = ["Live2DAdapter", "Live2DPlatformAdapter"]
