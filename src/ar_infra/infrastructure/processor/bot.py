"""Git repository initialization with bot commit."""

import gc
import platform
import shutil
import stat
import subprocess  # nosec B404
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ar_infra.infrastructure.config import BOT_ID, BOT_SLUG
from src.ar_infra.infrastructure.fs_utilities import try_rename_locked_directory
from src.ar_infra.logger import get_logger


log = get_logger()


@dataclass(frozen=True)
class BotIdentity:
    name: str
    email: str

    @classmethod
    def from_config(cls, bot_slug: str, bot_id: str) -> "BotIdentity":
        """Create bot identity from config values."""
        return cls(
            name=f"{bot_slug}[bot]",
            email=f"{bot_id}+{bot_slug}[bot]@users.noreply.github.com",
        )


class GitRepositoryError(Exception):
    """Base exception for git repository operations."""


class GitCommandError(GitRepositoryError):
    """Raised when a git command fails."""

    def __init__(self, command: str, returncode: int, stderr: str):
        self.command = command
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"Git command failed: '{command}' (exit code {returncode}): {stderr}")


class BotGitHandler:
    """Handles project generation and Git initialization with bot-authored commit."""

    def __init__(
        self,
        bot_identity: BotIdentity | None = None,
        bot_slug: str | None = None,
    ):
        if bot_identity is None:
            bot_slug = bot_slug or BOT_SLUG
            bot_id = BOT_ID
            self.bot_identity = BotIdentity.from_config(bot_slug, bot_id)
        else:
            self.bot_identity = bot_identity

    def initialize_repository(
        self,
        project_path: Path,
        initial_branch: str = "preprod",
        commit_message: str = "infra: generate the spring boot infrastructure",
    ) -> None:
        if not project_path.exists():
            raise GitRepositoryError(f"Project path does not exist: {project_path}")

        self._remove_existing_git_directory(project_path)

        # On Windows, wait for file system to settle after removal
        if platform.system() == "Windows":
            log.info("Windows: Waiting for file system to settle...")
            time.sleep(2)

        self._initialize_git(project_path)
        self._configure_bot_identity(project_path)
        self._set_initial_branch(project_path, initial_branch)
        self._stage_all_files(project_path)
        self._create_initial_commit(project_path, commit_message)

        log.info("Git repository initialized with bot commit at: %s", project_path)

    def generate_and_initialize_repo(
        self,
        output_path: Path,
        cli_args: list[str],
        initial_branch: str = "preprod",
        commit_message: str = "infra: generate the spring boot infrastructure",
    ) -> None:
        disallowed_flags = {"--shell", "--exec", "--help", "--version"}  # block risky ones

        for arg in cli_args:
            if arg.startswith(("-", "--")):
                if arg in disallowed_flags:
                    raise ValueError(f"Disallowed CLI argument: {arg}")
                if not arg[2:].replace("-", "").isalnum():
                    raise ValueError(f"Invalid CLI argument format: {arg}")

        if output_path.exists():
            shutil.rmtree(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        cli_command = ["ar-infra-cli", *cli_args, "--output", str(output_path)]
        self._run_command(cli_command)

        self.initialize_repository(output_path, initial_branch, commit_message)

        log.info("Project generated and initial commit created by bot at: %s", output_path)

    def _remove_existing_git_directory(self, path: Path) -> None:
        git_dir = path / ".git"
        if git_dir.exists():
            self._safe_rmtree(git_dir)

    def _safe_rmtree(self, path: Path, max_retries: int = 10) -> None:
        is_windows = platform.system() == "Windows"

        def handle_remove_readonly(func: Callable[[str], None], path_str: str, _exc: Any) -> None:
            if is_windows:
                Path(path_str).chmod(stat.S_IWRITE)
                func(path_str)

        last_exception: Exception | None = None

        for attempt in range(max_retries):
            try:
                if is_windows:
                    gc.collect()

                shutil.rmtree(path, onerror=handle_remove_readonly)
            except (OSError, PermissionError) as exc:
                last_exception = exc
                if attempt < max_retries - 1:
                    self._log_retry_attempt(attempt, max_retries, exc)
                    time.sleep(8)
                else:
                    self._handle_final_removal_failure(path, max_retries, last_exception)
            else:
                return

    def _log_retry_attempt(self, attempt: int, max_retries: int, exc: Exception) -> None:
        log.warning(
            "Failed to remove directory (attempt %d/%d): %s. Retrying in 8s...",
            attempt + 1,
            max_retries,
            exc,
        )

    def _handle_final_removal_failure(
        self, path: Path, max_retries: int, last_exception: Exception
    ) -> None:
        """Handle final failure to remove directory after all retries.

        On Windows, as a last resort, attempts to rename the locked directory
        to allow continuation. This is necessary because Git pack files can
        remain locked by background processes (git-index-pack, antivirus scanners)
        for extended periods on Windows, even after the main Git operation completes.
        """
        is_windows = platform.system() == "Windows"

        if is_windows and self._try_rename_locked_directory(path, max_retries):
            return

        raise last_exception

    def _try_rename_locked_directory(self, path: Path, max_retries: int) -> bool:
        return try_rename_locked_directory(path, max_retries, context="Windows")

    def _initialize_git(self, path: Path) -> None:
        self._run_git_command(["git", "init"], cwd=path)

    def _configure_bot_identity(self, path: Path) -> None:
        self._run_git_command(["git", "config", "user.name", self.bot_identity.name], cwd=path)
        self._run_git_command(["git", "config", "user.email", self.bot_identity.email], cwd=path)

    def _set_initial_branch(self, path: Path, branch_name: str) -> None:
        self._run_git_command(["git", "branch", "-M", branch_name], cwd=path)

    def _stage_all_files(self, path: Path) -> None:
        self._run_git_command_with_retry(["git", "add", "."], cwd=path)

    def _create_initial_commit(self, path: Path, message: str) -> None:
        self._run_git_command(["git", "commit", "-m", message], cwd=path)

    def _run_git_command(self, command: list[str], cwd: Path) -> None:
        self._run_command(command, cwd=cwd)

    def _run_git_command_with_retry(
        self, command: list[str], cwd: Path, max_retries: int = 5
    ) -> None:
        """Run git command with retry logic for Windows file lock issues."""
        is_windows = platform.system() == "Windows"

        for attempt in range(max_retries):
            try:
                self._run_command(command, cwd=cwd)
            except (GitCommandError, GitRepositoryError) as exc:
                if is_windows and attempt < max_retries - 1:
                    log.warning(
                        "Git command failed (attempt %d/%d): %s. Retrying in 3s...",
                        attempt + 1,
                        max_retries,
                        exc,
                    )
                    time.sleep(3)
                else:
                    raise
            else:
                return

    def _run_command(
        self,
        command: list[str],
        cwd: Path | None = None,
    ) -> None:
        cmd = command

        try:
            subprocess.run(  # noqa: S603
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
                shell=False,
                timeout=300,
            )
        except subprocess.CalledProcessError as e:
            raise GitCommandError(" ".join(cmd), e.returncode, e.stderr.strip()) from e
        except FileNotFoundError as e:
            raise GitRepositoryError(
                f"Command not found: {cmd[0]}. Is it installed and in PATH?"
            ) from e
        except subprocess.TimeoutExpired:
            raise GitCommandError(" ".join(cmd), -1, "Command timed out") from None
