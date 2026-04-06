from typing import TYPE_CHECKING

from .agent.responses import notification, streaming
from .conversation import (
    Conversation,
    ConversationManager,
    ConversationStatus,
    ConversationStore,
    InMemoryConversationStore,
)
from .conversation.item_store import (
    InMemoryItemStore,
    ItemStore,
    SQLiteItemStore,
)

# Task management
from .task import Task, TaskManager, TaskStatus

# Type system
from .types import (
    BaseAgent,
    RemoteAgentResponse,
    StreamResponse,
    UserInput,
    UserInputMetadata,
)

if TYPE_CHECKING:
    from .agent.decorator import create_wrapped_agent

__all__ = [
    # Conversation exports
    "Conversation",
    "ConversationStatus",
    "ConversationManager",
    "ConversationStore",
    "InMemoryConversationStore",
    "ItemStore",
    "InMemoryItemStore",
    "SQLiteItemStore",
    # Task exports
    "Task",
    "TaskStatus",
    "TaskManager",
    # Type system exports
    "UserInput",
    "UserInputMetadata",
    "BaseAgent",
    "StreamResponse",
    "RemoteAgentResponse",
    # Agent utilities
    "create_wrapped_agent",
    # Response utilities
    "streaming",
    "notification",
]


def __getattr__(name: str):
    if name == "create_wrapped_agent":
        from .agent.decorator import create_wrapped_agent

        return create_wrapped_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
