"""配置接口定义模块"""

from typing import Protocol


class ConfigLike(Protocol):
    @property
    def server_host(self) -> str: ...

    @property
    def server_port(self) -> int: ...

    @property
    def auth_token(self) -> str: ...

    @property
    def ws_path(self) -> str: ...

    @property
    def max_connections(self) -> int: ...

    @property
    def kick_old(self) -> bool: ...

    @property
    def resource_enabled(self) -> bool: ...

    @property
    def resource_host(self) -> str: ...

    @property
    def resource_port(self) -> int: ...

    @property
    def resource_path(self) -> str: ...

    @property
    def resource_dir(self) -> str: ...

    @property
    def resource_base_url(self) -> str: ...

    @property
    def resource_token(self) -> str: ...

    @property
    def resource_max_inline_bytes(self) -> int: ...
