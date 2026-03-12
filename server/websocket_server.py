"""WebSocket 服务器（双端口模式，基于 websockets 库）"""

from __future__ import annotations

import asyncio
from typing import Any

import websockets

from astrbot.api import logger

from ..core.protocol import BasePacket
from ..core.protocol import Protocol as ProtocolClass
from .base_server import BaseConnectionManager


class WebSocketServer(BaseConnectionManager):
    """基于 websockets 库的 WebSocket 服务器"""

    async def _close_ws(self, websocket: Any, code: int, reason: str = "") -> None:
        await websocket.close(code, reason)

    async def _send_ws(self, websocket: Any, data: str) -> None:
        await websocket.send(data)

    async def handle_client(self, websocket):
        """处理客户端连接"""
        path = getattr(websocket, "path", None)
        if path is None:
            req = getattr(websocket, "request", None)
            path = getattr(req, "path", None)

        if path and self.config.ws_path:
            allowed_paths = {self.config.ws_path, "/ws", "/astrbot/live2d"}
            if path not in allowed_paths:
                logger.warning(
                    f"拒绝连接: 路径不匹配 (期望: {self.config.ws_path}, 实际: {path})"
                )
                error = ProtocolClass.create_error_packet(
                    ProtocolClass.ERROR_INVALID_PAYLOAD,
                    f"路径不匹配，期望: {self.config.ws_path}",
                )
                await websocket.send(error.to_json())
                await websocket.close(1008, "路径不匹配")
                return

        client_id = None

        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            if isinstance(message, bytes):
                message = message.decode("utf-8", errors="replace")
            packet = BasePacket.from_json(message)

            if packet.op != ProtocolClass.OP_HANDSHAKE:
                logger.error(f"首个消息不是握手: {packet.op}")
                error = ProtocolClass.create_error_packet(
                    ProtocolClass.ERROR_INVALID_PAYLOAD, "首个消息必须是握手"
                )
                await websocket.send(error.to_json())
                return

            payload = packet.payload or {}
            client_id = (
                payload.get("clientId")
                or payload.get("deviceId")
                or payload.get("client")
                or BasePacket.generate_id()
            )

            response = await self.handler.handle_packet(packet, client_id)
            if response is None:
                logger.error("握手响应为空")
                return
            await websocket.send(response.to_json())

            if response.op == ProtocolClass.OP_ERROR:
                return

            if not await self.register(websocket, client_id):
                return

            ready_packet = ProtocolClass.create_packet(
                ProtocolClass.OP_STATE_READY, payload={"clientId": client_id}
            )
            await websocket.send(ready_packet.to_json())

            async for message in websocket:
                try:
                    if isinstance(message, bytes):
                        message = message.decode("utf-8", errors="replace")
                    packet = BasePacket.from_json(message)
                    response = await self.handler.handle_packet(packet, client_id)

                    if response:
                        await websocket.send(response.to_json())

                except Exception as e:
                    logger.error(f"处理消息时出错: {e}", exc_info=True)
                    error = ProtocolClass.create_error_packet(
                        ProtocolClass.ERROR_INVALID_PAYLOAD, f"消息处理失败: {e!s}"
                    )
                    await websocket.send(error.to_json())

        except asyncio.TimeoutError:
            logger.error("等待握手超时")

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"客户端连接关闭: {client_id}")

        except Exception as e:
            logger.error(f"处理客户端连接时出错: {e}", exc_info=True)

        finally:
            if client_id:
                await self.unregister(client_id)

    async def start(self):
        logger.info(
            f"启动 WebSocket 服务器: ws://{self.config.server_host}:{self.config.server_port}{self.config.ws_path}"
        )

        self.server = await websockets.serve(
            self.handle_client, self.config.server_host, self.config.server_port,
            max_size=10 * 1024 * 1024,
        )

        logger.info("WebSocket 服务器已启动")

    async def stop(self):
        if self.server:
            logger.info("正在停止 WebSocket 服务器...")
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket 服务器已停止")

    async def run_forever(self):
        await self.start()

        try:
            await asyncio.Future()
        except KeyboardInterrupt:
            logger.info("收到中断信号")
        finally:
            await self.stop()
