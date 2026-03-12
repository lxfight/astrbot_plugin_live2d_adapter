"""WebSocket 连接管理公共基类。"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from astrbot.api import logger

from ..core.config import ConfigLike
from ..core.protocol import BasePacket
from .message_handler import MessageHandler


class BaseConnectionManager:
    """WebSocket 连接管理公共逻辑，子类实现传输层差异。"""

    def __init__(self, config: ConfigLike, resource_manager: Any | None = None):
        self.config = config
        self.handler = MessageHandler(config, resource_manager=resource_manager)
        self.clients: dict[str, Any] = {}
        self.server: Any | None = None
        self.on_client_connected: Callable[[str], Awaitable[None]] | None = None
        self.on_client_disconnected: Callable[[str], Awaitable[None]] | None = None

    async def _close_ws(self, websocket: Any, code: int, reason: str = "") -> None:
        """关闭 WebSocket 连接，子类必须实现。"""
        raise NotImplementedError

    async def _send_ws(self, websocket: Any, data: str) -> None:
        """发送文本消息到 WebSocket，子类必须实现。"""
        raise NotImplementedError

    async def register(self, websocket: Any, client_id: str) -> bool:
        if len(self.clients) >= self.config.max_connections:
            if self.config.kick_old and self.clients:
                old_id, old_ws = next(iter(self.clients.items()))
                logger.info(f"连接数已满，踢掉旧连接: {old_id}")
                await self.unregister(old_id)
                try:
                    await self._close_ws(old_ws, 1000, "新连接接入")
                except Exception:
                    pass
            else:
                logger.warning("连接数已达上限，拒绝新连接")
                await self._close_ws(websocket, 1008, "连接数已满")
                return False

        self.clients[client_id] = websocket
        logger.info(f"客户端已连接: {client_id} (总数: {len(self.clients)})")

        if self.on_client_connected:
            try:
                await self.on_client_connected(client_id)
            except Exception as e:
                logger.warning(f"on_client_connected callback failed: {e!s}")
        return True

    async def unregister(self, client_id: str) -> None:
        if self.clients.pop(client_id, None) is None:
            return

        logger.info(f"客户端已断开: {client_id} (总数: {len(self.clients)})")
        if self.on_client_disconnected:
            try:
                await self.on_client_disconnected(client_id)
            except Exception as e:
                logger.warning(f"on_client_disconnected callback failed: {e!s}")

    async def send_to(self, client_id: str, packet: BasePacket) -> None:
        websocket = self.clients.get(client_id)
        if not websocket:
            logger.debug(f"Client {client_id} is not connected.")
            return

        try:
            await self._send_ws(websocket, packet.to_json())
            logger.debug(f"发送消息到客户端 {client_id}: op={packet.op}")
        except Exception as e:
            logger.error(f"发送消息到客户端 {client_id} 失败: {e}")
            await self.unregister(client_id)

    async def broadcast(self, packet: BasePacket) -> None:
        if not self.clients:
            logger.debug("没有已连接的客户端")
            return

        message = packet.to_json()
        disconnected: list[str] = []
        for client_id, websocket in self.clients.items():
            try:
                await self._send_ws(websocket, message)
                logger.debug(f"发送消息到客户端 {client_id}: op={packet.op}")
            except Exception as e:
                logger.error(f"发送消息到客户端 {client_id} 失败: {e}")
                disconnected.append(client_id)

        for client_id in disconnected:
            await self.unregister(client_id)
