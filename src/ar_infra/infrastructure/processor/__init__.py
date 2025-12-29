"""File and package processors."""

from src.ar_infra.infrastructure.processor.bot import (
    BotGitHandler,
    BotIdentity,
    GitCommandError,
    GitRepositoryError,
)
from src.ar_infra.infrastructure.processor.package_renamer import PackageRenamer


GitRepositoryInitializer = BotGitHandler

__all__ = [
    "BotGitHandler",
    "BotIdentity",
    "GitCommandError",
    "GitRepositoryError",
    "GitRepositoryInitializer",  # Alias for compatibility
    "PackageRenamer",
]
