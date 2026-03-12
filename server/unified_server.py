"""单端口 Live2D 服务。"""

from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import WSMsgType, web

from astrbot.api import logger

from ..core.config import ConfigLike
from ..core.protocol import BasePacket
from ..core.protocol import Protocol as ProtocolClass
from .base_server import BaseConnectionManager
from .message_handler import ConnectionContext
from .resource_server import ResourceServer


class SinglePortLive2DServer(BaseConnectionManager):
    """在同一端口上同时提供 WebSocket 与资源路由。"""

    def __init__(self, config: ConfigLike, resource_manager: Any | None = None):
        super().__init__(config, resource_manager=resource_manager)
        self.app: web.Application | None = None
        self.runner: web.AppRunner | None = None
        self.site: web.TCPSite | None = None
        self.resource_server: ResourceServer | None = None
        if resource_manager is not None:
            self.resource_server = ResourceServer(
                manager=resource_manager,
                host=config.server_host,
                port=config.server_port,
                resource_path=config.resource_path,
                token=config.resource_token,
            )

    async def _close_ws(self, websocket: Any, code: int, reason: str = "") -> None:
        await websocket.close(code=code, message=reason.encode() if reason else b"")

    async def _send_ws(self, websocket: Any, data: str) -> None:
        await websocket.send_str(data)

    @staticmethod
    def _extract_request_origin(request: web.Request) -> str:
        """仅从 HTTP 请求头中推导 origin，不涉及 config 优先级。"""
        forwarded_proto = (
            request.headers.get("X-Forwarded-Proto", "").split(",")[0].strip()
        )
        forwarded_host = (
            request.headers.get("X-Forwarded-Host", "").split(",")[0].strip()
        )
        scheme = forwarded_proto or request.scheme or "http"
        host = forwarded_host or request.host or ""
        if not host:
            return ""
        return f"{scheme}://{host}".rstrip("/")

    def _build_connection_context(self, request: web.Request) -> ConnectionContext:
        return {"request_origin": self._extract_request_origin(request)}

    async def _send_packet(
        self, websocket: web.WebSocketResponse, packet: BasePacket
    ) -> None:
        await websocket.send_str(packet.to_json())

    @staticmethod
    def _decode_message(message: web.WSMessage) -> str | None:
        if message.type == WSMsgType.TEXT:
            return message.data
        if message.type == WSMsgType.BINARY:
            return message.data.decode("utf-8", errors="replace")
        return None

    async def handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        websocket = web.WebSocketResponse(max_msg_size=10 * 1024 * 1024, heartbeat=30)
        await websocket.prepare(request)

        client_id: str | None = None
        connection_context = self._build_connection_context(request)

        try:
            first_message = await asyncio.wait_for(websocket.receive(), timeout=10.0)
            message_text = self._decode_message(first_message)
            if not message_text:
                logger.error("等待握手超时或首帧为空")
                await websocket.close(code=1008)
                return websocket

            packet = BasePacket.from_json(message_text)
            if packet.op != ProtocolClass.OP_HANDSHAKE:
                logger.error(f"首个消息不是握手: {packet.op}")
                await self._send_packet(
                    websocket,
                    ProtocolClass.create_error_packet(
                        ProtocolClass.ERROR_INVALID_PAYLOAD,
                        "首个消息必须是握手",
                    ),
                )
                await websocket.close(code=1008)
                return websocket

            payload = packet.payload or {}
            client_id = (
                payload.get("clientId")
                or payload.get("deviceId")
                or payload.get("client")
                or BasePacket.generate_id()
            )

            response = await self.handler.handle_packet(
                packet,
                client_id,
                connection_context=connection_context,
            )
            if response is None:
                logger.error("握手响应为空")
                await websocket.close(code=1011)
                return websocket

            await self._send_packet(websocket, response)
            if response.op == ProtocolClass.OP_ERROR:
                await websocket.close(code=1008)
                return websocket

            if not await self.register(websocket, client_id):
                return websocket

            ready_packet = ProtocolClass.create_packet(
                ProtocolClass.OP_STATE_READY,
                payload={"clientId": client_id},
            )
            await self._send_packet(websocket, ready_packet)

            async for message in websocket:
                if message.type in {
                    WSMsgType.CLOSE,
                    WSMsgType.CLOSED,
                    WSMsgType.CLOSING,
                }:
                    break
                if message.type == WSMsgType.ERROR:
                    logger.error(f"客户端连接异常: {websocket.exception()}")
                    break

                message_text = self._decode_message(message)
                if not message_text:
                    continue

                try:
                    packet = BasePacket.from_json(message_text)
                    response = await self.handler.handle_packet(packet, client_id)
                    if response:
                        await self._send_packet(websocket, response)
                except Exception as error:
                    logger.error(f"处理消息时出错: {error}", exc_info=True)
                    await self._send_packet(
                        websocket,
                        ProtocolClass.create_error_packet(
                            ProtocolClass.ERROR_INVALID_PAYLOAD,
                            f"消息处理失败: {error!s}",
                        ),
                    )
        except asyncio.TimeoutError:
            logger.error("等待握手超时")
        except Exception as error:
            logger.error(f"处理客户端连接时出错: {error}", exc_info=True)
        finally:
            if client_id:
                await self.unregister(client_id)

        return websocket

    _SCHEME_MAP = {"http": "ws", "https": "wss"}

    @classmethod
    def _http_to_ws(cls, origin: str) -> str:
        """将 HTTP(S) 协议转换为对应的 WS(S) 协议。"""
        for http_scheme, ws_scheme in cls._SCHEME_MAP.items():
            prefix = f"{http_scheme}://"
            if origin.startswith(prefix):
                return f"{ws_scheme}://{origin[len(prefix):]}"
        return origin

    def _build_local_origin(self) -> str:
        host = self.config.server_host
        if host in {"0.0.0.0", "::"}:
            host = "127.0.0.1"
        return f"http://{host}:{self.config.server_port}"

    async def start(self) -> None:
        max_body_size = int(
            getattr(self.config, "resource_max_total_bytes", 1073741824) or 1073741824
        )
        if max_body_size < 1024 * 1024:
            max_body_size = 1024 * 1024

        self.app = web.Application(client_max_size=max_body_size)

        ws_paths = {self.config.ws_path, "/ws", "/astrbot/live2d"}
        for ws_path in sorted("/" + path.strip("/") for path in ws_paths if path):
            self.app.router.add_get(ws_path, self.handle_websocket)

        if self.resource_server is not None:
            resource_path = self.resource_server.resource_path
            self.app.router.add_get(
                f"{resource_path}/{{rid}}", self.resource_server.handle_get
            )
            self.app.router.add_put(
                f"{resource_path}/{{rid}}", self.resource_server.handle_put
            )
            self.app.router.add_delete(
                f"{resource_path}/{{rid}}", self.resource_server.handle_delete
            )

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(
            self.runner, self.config.server_host, self.config.server_port
        )
        await self.site.start()
        self.server = self.site

        local_origin = self._build_local_origin()
        logger.info(
            f"[Live2D] 单端口服务已启动: ws={self._http_to_ws(local_origin)}{self.config.ws_path}"
        )
        if self.resource_server is not None:
            logger.info(
                f"[Live2D] 资源接口复用同端口: {local_origin}{self.resource_server.resource_path}/{{rid}}"
            )

    async def stop(self) -> None:
        await self.shutdown_clients()

        if self.site:
            await self.site.stop()
            self.site = None
            self.server = None
        if self.runner:
            await self.runner.cleanup()
            self.runner = None
        self.app = None
        logger.info("[Live2D] 单端口服务已停止")
