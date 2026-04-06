from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .agent import create_agent_router
    from .i18n import create_i18n_router, get_i18n_router
    from .system import create_system_router
    from .task import create_task_router

__all__ = [
    "create_i18n_router",
    "get_i18n_router",
    "create_system_router",
    "create_agent_router",
    "create_task_router",
]


def __getattr__(name: str):
    if name == "create_agent_router":
        from .agent import create_agent_router

        return create_agent_router
    if name == "create_i18n_router":
        from .i18n import create_i18n_router

        return create_i18n_router
    if name == "get_i18n_router":
        from .i18n import get_i18n_router

        return get_i18n_router
    if name == "create_system_router":
        from .system import create_system_router

        return create_system_router
    if name == "create_task_router":
        from .task import create_task_router

        return create_task_router
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
