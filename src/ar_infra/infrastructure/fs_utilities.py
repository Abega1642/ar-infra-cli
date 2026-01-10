import uuid
from pathlib import Path

from src.ar_infra.logger import get_logger


log = get_logger()


def try_rename_locked_directory(
    path: Path,
    max_retries: int,
    *,
    context: str = "",
) -> bool:
    """
    Attempt to rename a locked directory that cannot be deleted.

    This is primarily used on Windows where directory locks can prevent deletion.
    The directory is renamed with a unique suffix to allow the operation to proceed.

    Args:
        path: The directory path to rename
        max_retries: Number of deletion attempts that were made before this
        context: Optional context string to include in the warning message

    Returns:
        True if rename succeeded, False if rename also failed

    """
    backup_name = f"{path.name}.old.{uuid.uuid4().hex[:8]}"
    backup_path = path.parent / backup_name

    try:
        path.rename(backup_path)
    except OSError:
        # Rename failure is extremely rare but possible if parent directory
        # is also locked or filesystem is corrupted. No recovery possible,
        # so we return False to allow the original exception to propagate.
        return False

    if context:
        log.warning(
            "%s: Could not delete %s after %d attempts. "
            "Renamed to %s. New directory will be created.",
            context,
            path,
            max_retries,
            backup_name,
        )
    else:
        log.warning(
            "Could not delete %s after %d attempts. Renamed to %s",
            path,
            max_retries,
            backup_name,
        )
    return True
