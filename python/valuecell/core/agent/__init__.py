from typing import TYPE_CHECKING

from .responses import streaming

if TYPE_CHECKING:
    from .client import AgentClient
    from .connect import RemoteConnections
    from .decorator import create_wrapped_agent

__all__ = [
    "AgentClient",
    "RemoteConnections",
    "streaming",
    "create_wrapped_agent",
]


def __getattr__(name: str):
    if name == "AgentClient":
        from .client import AgentClient

        return AgentClient
    if name == "RemoteConnections":
        from .connect import RemoteConnections

        return RemoteConnections
    if name == "create_wrapped_agent":
        from .decorator import create_wrapped_agent

        return create_wrapped_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
