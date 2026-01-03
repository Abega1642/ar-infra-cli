"""Git repository initialization with bot commit."""

import os
import shutil
import subprocess  # nosec B404
from dataclasses import dataclass
from pathlib import Path

import requests
from dotenv import load_dotenv

from src.ar_infra.logger import get_logger


load_dotenv()

log = get_logger(__name__)

BOT_ID = os.getenv("BOT_ID")
BOT_SLUG = os.getenv("BOT_SLUG", "ar-infra-bot")


@dataclass(frozen=True)
class BotIdentity:
    """Bot identity for git commits using GitHub's official format."""

    name: str
    email: str

    @classmethod
    def from_github_app(
        cls, bot_slug: str = "ar-infra-bot", bot_id: int | None = None
    ) -> "BotIdentity":
        """Create proper GitHub App bot identity."""
        if bot_id is None:
            try:
                response = requests.get(
                    f"https://api.github.com/users/{bot_slug}%5Bbot%5D",
                    timeout=10,
                )
                response.raise_for_status()
                bot_id = response.json()["id"]
            except requests.RequestException as exc:
                raise RuntimeError(
                    f"Failed to fetch bot user ID for {bot_slug}[bot]. "
                    "Set BOT_ID in .env or check network/app slug."
                ) from exc

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
            bot_id_str = BOT_ID

            if bot_id_str:
                try:
                    bot_id = int(bot_id_str)
                except (TypeError, ValueError) as exc:
                    raise ValueError("BOT_ID in .env must be a valid integer") from exc
                self.bot_identity = BotIdentity.from_github_app(bot_slug, bot_id)
            else:
                self.bot_identity = BotIdentity.from_github_app(bot_slug)
        else:
            self.bot_identity = bot_identity

    def initialize_repository(
        self,
        project_path: Path,
        initial_branch: str = "preprod",
        commit_message: str = "infra: generate the spring boot infrastructure",
    ) -> None:
        """Initialize Git repository with bot commit in existing project."""
        if not project_path.exists():
            raise GitRepositoryError(f"Project path does not exist: {project_path}")

        self._remove_existing_git_directory(project_path)
        self._initialize_git(project_path)
        self._configure_bot_identity(project_path)
        self._set_initial_branch(project_path, initial_branch)
        self._stage_all_files(project_path)
        self._create_initial_commit(project_path, commit_message)

        log.info("\nGit repository initialized with bot commit at: %s\n", project_path)

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

        log.info("\nProject generated and initial commit created by bot at: %s\n", output_path)

    def _remove_existing_git_directory(self, path: Path) -> None:
        git_dir = path / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir)

    def _initialize_git(self, path: Path) -> None:
        self._run_git_command(["git", "init"], cwd=path)

    def _configure_bot_identity(self, path: Path) -> None:
        self._run_git_command(["git", "config", "user.name", self.bot_identity.name], cwd=path)
        self._run_git_command(["git", "config", "user.email", self.bot_identity.email], cwd=path)

    def _set_initial_branch(self, path: Path, branch_name: str) -> None:
        self._run_git_command(["git", "branch", "-M", branch_name], cwd=path)

    def _stage_all_files(self, path: Path) -> None:
        self._run_git_command(["git", "add", "."], cwd=path)

    def _create_initial_commit(self, path: Path, message: str) -> None:
        self._run_git_command(["git", "commit", "-m", message], cwd=path)

    def _run_git_command(self, command: list[str], cwd: Path) -> None:
        self._run_command(command, cwd=cwd)

    def _run_command(
        self,
        command: list[str],
        cwd: Path | None = None,
    ) -> None:
        """
        Run a command safely using subprocess.run with a list (shell=False).

        Security notes:
        - shell=False prevents shell injection.
        - Inputs are validated before this method.
        - Bandit false positives B603/B404 are safe here.
        """
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
