"""Module for removing development artifacts from generated projects."""

import logging
from pathlib import Path
from typing import Final


logger = logging.getLogger(__name__)


class DevelopmentArtifactCleaner:
    """
    Removes development-specific files and directories from generated projects.

    This class safely removes files and directories that were used during
    infrastructure development but should not be included in the generated
    project output.

    Security considerations:
    - Validates all paths to prevent directory traversal attacks
    - Only operates within the specified project root
    - Uses Path.resolve() to normalize and validate paths
    """

    DEFAULT_ARTIFACTS: Final[list[str]] = [
        ".github/dependabot.yml",
        ".github/CODEOWNERS",
        "ar-infra-logo.png",
        "code_of_conduct.md",
        "readme.md",
        "security.md",
        "contributing.md",
        "licence",
    ]

    def __init__(self, project_root: Path) -> None:
        """
        Initialize the cleaner with a project root directory.

        Args:
            project_root: The root directory of the generated project.
                         All operations are constrained to this directory.

        Raises:
            ValueError: If project_root doesn't exist or isn't a directory.
        """
        if not project_root.exists():
            raise ValueError(f"Project root does not exist: {project_root}")

        if not project_root.is_dir():
            raise ValueError(f"Project root is not a directory: {project_root}")

        self._project_root = project_root.resolve()
        logger.info("Initialized DevelopmentArtifactCleaner for: %s", self._project_root)

    def _validate_path(self, target_path: Path) -> Path:
        """
        Validate that a path is within the project root.

        Args:
            target_path: The path to validate.

        Returns:
            The resolved absolute path.

        Raises:
            ValueError: If the path escapes the project root.
        """
        resolved = target_path.resolve()

        try:
            resolved.relative_to(self._project_root)
        except ValueError as exc:
            raise ValueError(
                f"Path {target_path} is outside project root {self._project_root}"
            ) from exc

        return resolved

    def remove_artifact(self, relative_path: str) -> bool:
        """
        Remove a single file or directory artifact.

        Args:
            relative_path: Path relative to project root (e.g., "readme.md").

        Returns:
            True if the artifact was removed, False if it didn't exist.

        Raises:
            ValueError: If the path is invalid or outside project root.
            OSError: If removal fails due to permissions or other OS errors.
        """
        target = self._project_root / relative_path
        validated_target = self._validate_path(target)

        if not validated_target.exists():
            logger.debug("Artifact does not exist, skipping: %s", relative_path)
            return False

        try:
            if validated_target.is_file() or validated_target.is_symlink():
                validated_target.unlink()
                logger.info("Removed file: %s", relative_path)
                removed = True
            elif validated_target.is_dir():
                self._remove_directory_recursive(validated_target)
                logger.info("Removed directory: %s", relative_path)
                removed = True
            else:
                logger.warning("Unknown artifact type, skipping: %s", relative_path)
                removed = False
        except OSError:
            logger.exception("Failed to remove %s", relative_path)
            raise

        return removed

    def _remove_directory_recursive(self, directory: Path) -> None:
        """
        Recursively remove a directory and all its contents.

        Args:
            directory: The directory to remove (must be validated).

        Raises:
            OSError: If removal fails.
        """
        for child in directory.iterdir():
            if child.is_file() or child.is_symlink():
                child.unlink()
            elif child.is_dir():
                self._remove_directory_recursive(child)

        directory.rmdir()

    def clean(self, artifacts: list[str] | None = None) -> int:
        """
        Remove multiple development artifacts from the project.

        Args:
            artifacts: List of relative paths to remove.
                      If None, uses DEFAULT_ARTIFACTS.

        Returns:
            Number of artifacts successfully removed.

        Raises:
            ValueError: If any path is invalid.
            OSError: If removal fails.
        """
        artifacts_to_remove = artifacts if artifacts is not None else self.DEFAULT_ARTIFACTS
        removed_count = 0

        logger.info("Starting cleanup of %d artifacts", len(artifacts_to_remove))

        for artifact in artifacts_to_remove:
            if self.remove_artifact(artifact):
                removed_count += 1

        logger.info(
            "Cleanup complete. Removed %d/%d artifacts", removed_count, len(artifacts_to_remove)
        )

        return removed_count

    def clean_empty_parent_directories(self, relative_path: str) -> int:
        """
        Remove empty parent directories after artifact removal.

        Useful for cleaning up empty .github directories after removing all files.

        Args:
            relative_path: Path whose parent directories to check.

        Returns:
            Number of empty directories removed.

        Raises:
            ValueError: If the path is invalid.
        """
        target = self._project_root / relative_path
        validated_target = self._validate_path(target)

        removed_count = 0
        current = validated_target.parent

        while current != self._project_root:
            try:
                if current.exists() and current.is_dir() and not any(current.iterdir()):
                    current.rmdir()
                    logger.info(
                        "Removed empty directory: %s", current.relative_to(self._project_root)
                    )
                    removed_count += 1
                    current = current.parent
                else:
                    break
            except OSError as exc:
                logger.debug("Could not remove directory %s: %s", current, exc)
                break

        return removed_count
