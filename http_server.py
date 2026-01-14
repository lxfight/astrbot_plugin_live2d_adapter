"""HTTP 静态文件服务器"""

import logging
from pathlib import Path

from aiohttp import web

logger = logging.getLogger(__name__)


class StaticFileServer:
    """HTTP 静态文件服务器，用于提供前端页面"""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        static_dir: str = "../astrbot-live2d-desktop/dist",
    ):
        self.host = host
        self.port = port
        self.static_dir = Path(static_dir).resolve()
        self.app = None
        self.runner = None
        self.site = None

    async def start(self):
        """启动 HTTP 服务器"""
        self.app = web.Application()

        # 仅在静态目录存在时添加静态文件路由
        if self.static_dir.exists():
            self.app.router.add_static("/", self.static_dir, name="static")

        # 启动服务器
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()

        logger.info(f"HTTP 服务器已启动: http://{self.host}:{self.port}")

    async def stop(self):
        """停止 HTTP 服务器"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("HTTP 服务器已停止")
