"""消息处理器"""

import logging
from collections.abc import Callable

from ..core.protocol import BasePacket, Protocol

logger = logging.getLogger(__name__)


class MessageHandler:
    """消息处理器"""

    def __init__(self, config):
        self.config = config
        # 消息接收回调函数（由平台适配器注入）
        self.on_message_received: Callable | None = None

    async def handle_packet(
        self, packet: BasePacket, client_id: str
    ) -> BasePacket | None:
        """
        处理接收到的数据包

        Args:
            packet: 接收到的数据包
            client_id: 客户端ID

        Returns:
            响应数据包（如果需要响应）
        """
        logger.info(f"处理来自客户端 {client_id} 的消息: op={packet.op}")

        if packet.op == Protocol.OP_HANDSHAKE:
            return await self.handle_handshake(packet, client_id)

        elif packet.op == Protocol.OP_PING:
            return await self.handle_ping(packet)

        elif packet.op == Protocol.OP_INPUT_TOUCH:
            return await self.handle_touch_input(packet, client_id)

        elif packet.op == Protocol.OP_INPUT_MESSAGE:
            return await self.handle_message_input(packet, client_id)

        elif packet.op == Protocol.OP_INPUT_SHORTCUT:
            return await self.handle_shortcut_input(packet, client_id)

        else:
            logger.warning(f"未知的操作码: {packet.op}")
            return None

    async def handle_handshake(self, packet: BasePacket, client_id: str) -> BasePacket:
        """处理握手请求"""
        payload = packet.payload or {}

        # 验证版本
        client_version = payload.get("version", "")
        if not client_version.startswith("1."):
            logger.error(f"版本不匹配: {client_version}")
            return Protocol.create_error_packet(
                Protocol.ERROR_VERSION_MISMATCH,
                "协议版本不兼容，请更新客户端",
                packet.id,
            )

        # 验证 Token
        if self.config.auth_token:
            client_token = payload.get("token", "")
            if client_token != self.config.auth_token:
                logger.error(f"Token 验证失败: {client_token}")
                return Protocol.create_error_packet(
                    Protocol.ERROR_AUTH_FAILED, "认证失败", packet.id
                )

        # 生成会话信息
        session_id = f"live2d_session_{client_id}"
        user_id = f"live2d_user_{client_id}"

        logger.info(
            f"客户端 {client_id} 握手成功，分配 session_id: {session_id}, user_id: {user_id}"
        )
        return Protocol.create_handshake_ack(
            request_id=packet.id, session_id=session_id, user_id=user_id
        )

    async def handle_ping(self, packet: BasePacket) -> BasePacket:
        """处理 Ping 请求"""
        return Protocol.create_packet(Protocol.OP_PONG, packet_id=packet.id)

    async def handle_touch_input(
        self, packet: BasePacket, client_id: str
    ) -> BasePacket | None:
        """处理触摸输入"""
        payload = packet.payload or {}
        part = payload.get("part", "Unknown")
        action = payload.get("action", "tap")

        logger.info(f"客户端 {client_id} 触摸了 {part} ({action})")

        # 示例：触摸头部时播放特定动作
        if part == "Head":
            from core.protocol import (
                create_expression_element,
                create_motion_element,
                create_text_element,
            )

            return Protocol.create_perform_show(
                sequence=[
                    create_text_element("别摸我的头啦~", duration=2000),
                    create_expression_element("happy", fade=300),
                    create_motion_element("TapHead", index=0, priority=3),
                ],
                interrupt=True,
            )

        return None

    async def handle_message_input(
        self, packet: BasePacket, client_id: str
    ) -> BasePacket | None:
        """处理消息输入（input.message）"""
        payload = packet.payload or {}
        content = payload.get("content", [])

        logger.info(f"客户端 {client_id} 发送消息: {content}")

        # 如果注入了消息处理回调，调用它（由平台适配器处理并提交到 AstrBot）
        if self.on_message_received:
            try:
                await self.on_message_received(client_id, packet)
            except Exception as e:
                logger.error(f"消息处理回调失败: {e}", exc_info=True)
        else:
            # 如果没有回调（独立运行模式），返回简单回显
            logger.warning("未注入消息处理回调，使用回显模式")
            text_preview = ""
            for item in content:
                if item.get("type") == "text":
                    text_preview += item.get("text", "")

            from core.protocol import create_text_element

            return Protocol.create_perform_show(
                sequence=[
                    create_text_element(f"收到了消息：{text_preview}", duration=3000)
                ],
                interrupt=True,
                packet_id=packet.id,
            )

        # 消息已交给 AstrBot 处理，不立即返回响应
        # AstrBot 处理完成后会通过 Live2DMessageEvent.send() 发送响应
        return None

    async def handle_shortcut_input(
        self, packet: BasePacket, client_id: str
    ) -> BasePacket | None:
        """处理快捷键输入"""
        payload = packet.payload or {}
        key = payload.get("key", "")

        logger.info(f"客户端 {client_id} 触发快捷键: {key}")

        # 根据快捷键执行不同操作
        if key == "random_action":
            from core.protocol import create_motion_element, create_text_element

            return Protocol.create_perform_show(
                sequence=[
                    create_text_element("随机动作！", duration=2000),
                    create_motion_element("Idle", index=0, priority=2),
                ],
                interrupt=True,
            )

        return None
