"""ValueCell - A community-driven, multi-agent platform for financial applications."""

__version__ = "0.1.0"
__author__ = "ValueCell Team"
__description__ = "A community-driven, multi-agent platform for financial applications"

__all__ = [
    "__version__",
    "__author__",
    "__description__",
]

import logging

# Load environment variables as early as possible
import os
from pathlib import Path

from valuecell.utils.env import ensure_system_env_dir, get_system_env_path

logger = logging.getLogger(__name__)


def load_env_file_early() -> None:
    """Load environment variables from system and repository .env files.

    Behavior:
    - Loads from system path (e.g., ~/Library/Application Support/ValueCell/.env on macOS)
    - If repository root .env exists, load it last as local override
    - Auto-creates from .env.example if not exists
    - Used by both local development and packaged client
    """
    try:
        from dotenv import load_dotenv

        # Resolve system `.env` and fallback create from example
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parents[1]
        sys_env = get_system_env_path()
        repo_env = project_root / ".env"
        example_file = project_root / ".env.example"

        try:
            import shutil

            if not sys_env.exists() and example_file.exists():
                ensure_system_env_dir()
                shutil.copy(example_file, sys_env)
                if os.getenv("AGENT_DEBUG_MODE", "false").lower() == "true":
                    logger.info(f"✓ Created system .env from example: {sys_env}")
        except Exception as e:
            if os.getenv("AGENT_DEBUG_MODE", "false").lower() == "true":
                logger.info(f"⚠️  Failed to prepare system .env: {e}")

        if sys_env.exists():
            load_dotenv(sys_env, override=True)

            if os.getenv("AGENT_DEBUG_MODE", "false").lower() == "true":
                logger.info(f"✓ Environment variables loaded from {sys_env}")

        if repo_env.exists():
            load_dotenv(repo_env, override=True)
            if os.getenv("AGENT_DEBUG_MODE", "false").lower() == "true":
                logger.info(f"✓ Environment variables loaded from {repo_env}")
                logger.info(f"  LANG: {os.environ.get('LANG', 'not set')}")
                logger.info(f"  TIMEZONE: {os.environ.get('TIMEZONE', 'not set')}")
        elif not sys_env.exists():
            # Only log if debug mode is enabled
            if os.getenv("AGENT_DEBUG_MODE", "false").lower() == "true":
                logger.info(f"ℹ️  No system .env file found at {sys_env}")

    except ImportError:
        # Fallback to manual parsing if python-dotenv is not available
        # This ensures backward compatibility
        _load_env_file_manual()
    except Exception as e:
        # Only log errors if debug mode is enabled
        if os.getenv("AGENT_DEBUG_MODE", "false").lower() == "true":
            logger.info(f"⚠️  Error loading .env file: {e}")


def _load_env_file_manual() -> None:
    """Fallback manual parsing for system and repository .env files."""
    try:
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parents[1]
        sys_env = get_system_env_path()
        repo_env = project_root / ".env"
        example_file = project_root / ".env.example"

        try:
            import shutil

            if not sys_env.exists() and example_file.exists():
                ensure_system_env_dir()
                shutil.copy(example_file, sys_env)
        except Exception:
            # Fail silently to avoid breaking imports
            pass

        env_files = []
        if sys_env.exists():
            env_files.append(sys_env)
        if repo_env.exists():
            env_files.append(repo_env)

        for env_file in env_files:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        if (value.startswith('"') and value.endswith('"')) or (
                            value.startswith("'") and value.endswith("'")
                        ):
                            value = value[1:-1]
                        os.environ[key] = value
    except Exception:
        # Fail silently to avoid breaking imports
        pass


# Load environment variables immediately when package is imported
load_env_file_early()
