"""AstrBot Live2D Adapter - AstrBot 插件入口"""

from astrbot.api import logger
from astrbot.api.star import Context, Star, register
from astrbot.core.config.default import CONFIG_METADATA_2

from .adapters.platform_adapter import Live2DPlatformAdapter


@register("Live2DAdapter", "lxfight", "Live2DAdapter 插件", "1.0.0")
class Live2DAdapter(Star):
    """Live2D 平台适配器插件"""

    _registered: bool = False

    _live2d_items = {
        "ws_host": {
            "description": "WebSocket 监听地址",
            "type": "string",
            "hint": "WebSocket 服务监听地址，默认 0.0.0.0",
        },
        "ws_port": {
            "description": "WebSocket 端口",
            "type": "int",
            "hint": "WebSocket 服务端口，默认 9090",
        },
        "ws_path": {
            "description": "WebSocket 路径",
            "type": "string",
            "hint": "WebSocket 连接路径，默认 /astrbot/live2d",
        },
        "auth_token": {
            "description": "认证令牌",
            "type": "string",
            "hint": "认证令牌(可选)，用于客户端连接验证",
        },
        "max_connections": {
            "description": "最大连接数",
            "type": "int",
            "hint": "允许的最大客户端连接数，默认 1",
        },
        "kick_old": {
            "description": "断开旧连接",
            "type": "bool",
            "hint": "新连接时是否断开旧连接，默认 true",
        },
        "enable_tts": {
            "description": "启用 TTS",
            "type": "bool",
            "hint": "是否启用语音合成功能，默认 false",
        },
        "tts_mode": {
            "description": "TTS 模式",
            "type": "string",
            "hint": "TTS 模式：local(本地) 或 remote(远程)，默认 local",
        },
        "enable_streaming": {
            "description": "启用流式推送",
            "type": "bool",
            "hint": "是否启用流式消息推送，默认 true",
        },
        "resource_enabled": {
            "description": "启用资源服务",
            "type": "bool",
            "hint": "是否启用资源服务器，默认 true",
        },
        "resource_host": {
            "description": "资源服务监听地址",
            "type": "string",
            "hint": "资源服务监听地址，默认 0.0.0.0",
        },
        "resource_port": {
            "description": "资源服务端口",
            "type": "int",
            "hint": "资源服务端口，默认 9091",
        },
        "resource_path": {
            "description": "资源访问路径",
            "type": "string",
            "hint": "资源访问路径，默认 /resources",
        },
        "resource_dir": {
            "description": "资源存储目录",
            "type": "string",
            "hint": "资源文件存储目录，默认 live2d_resources",
        },
        "resource_base_url": {
            "description": "资源基础 URL",
            "type": "string",
            "hint": "资源基础 URL，留空则自动生成",
        },
        "resource_token": {
            "description": "资源访问令牌",
            "type": "string",
            "hint": "资源访问令牌，留空则复用 auth_token",
        },
        "resource_max_inline_bytes": {
            "description": "内联资源最大字节",
            "type": "int",
            "hint": "内联资源最大字节数，默认 262144 (256KB)",
        },
        "resource_ttl_seconds": {
            "description": "资源 TTL(秒)",
            "type": "int",
            "hint": "资源生存时间(秒)，默认 604800 (7天)",
        },
        "resource_max_total_bytes": {
            "description": "最大总字节",
            "type": "int",
            "hint": "资源最大总字节数，默认 1073741824 (1GB)",
        },
        "resource_max_files": {
            "description": "最大文件数",
            "type": "int",
            "hint": "资源最大文件数，默认 2000",
        },
        "temp_dir": {
            "description": "临时文件目录",
            "type": "string",
            "hint": "临时文件存储目录，默认 live2d_temp",
        },
        "temp_ttl_seconds": {
            "description": "临时文件 TTL(秒)",
            "type": "int",
            "hint": "临时文件生存时间(秒)，默认 21600 (6小时)",
        },
        "temp_max_total_bytes": {
            "description": "临时文件最大总字节",
            "type": "int",
            "hint": "临时文件最大总字节数，默认 268435456 (256MB)",
        },
        "temp_max_files": {
            "description": "临时文件最大数量",
            "type": "int",
            "hint": "临时文件最大数量，默认 5000",
        },
        "cleanup_interval_seconds": {
            "description": "清理检查间隔(秒)",
            "type": "int",
            "hint": "资源清理检查间隔(秒)，默认 600 (10分钟)",
        },
    }

    def __init__(self, context: Context):
        super().__init__(context)

    def _register_config(self):
        if self._registered:
            return False
        try:
            target_dict = CONFIG_METADATA_2["platform_group"]["metadata"]["platform"]["items"]
            for name in list(self._live2d_items):
                if name not in target_dict:
                    target_dict[name] = self._live2d_items[name]
        except Exception as e:
            logger.error(f"[Live2D] 注册平台元数据时出现问题: {e}", exc_info=True)
            return False
        self._registered = True
        return True

    def _unregister_config(self):
        if not self._registered:
            return False
        try:
            target_dict = CONFIG_METADATA_2["platform_group"]["metadata"]["platform"]["items"]
            for name in list(self._live2d_items):
                if name in target_dict:
                    target_dict.pop(name, None)
        except Exception as e:
            logger.error(f"[Live2D] 清理平台元数据时出现问题: {e}", exc_info=True)
            return False
        self._registered = False
        return True

    async def initialize(self):
        self._register_config()

    async def terminate(self):
        self._unregister_config()


__all__ = ["Live2DAdapter", "Live2DPlatformAdapter"]
