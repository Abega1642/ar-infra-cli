"""Tests for bot.py components."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from pytest_mock import MockerFixture

from src.ar_infra.infrastructure.processor.bot import (
    BotGitHandler,
    BotIdentity,
    GitCommandError,
    GitRepositoryError,
)


class TestBotIdentity:
    def test_from_config(self) -> None:
        identity = BotIdentity.from_config(bot_slug="my-bot", bot_id="123456")
        assert identity.name == "my-bot[bot]"
        assert identity.email == "123456+my-bot[bot]@users.noreply.github.com"


class TestBotGitHandler:
    @pytest.fixture
    def handler(self) -> BotGitHandler:
        identity = BotIdentity(
            name="test-bot[bot]", email="999+test-bot[bot]@users.noreply.github.com"
        )
        return BotGitHandler(bot_identity=identity)

    @pytest.fixture
    def temp_output(self, tmp_path: Path) -> Path:
        return tmp_path / "project"

    @patch("src.ar_infra.infrastructure.processor.bot.subprocess.run")
    @patch("src.ar_infra.infrastructure.processor.bot.shutil.rmtree")
    def test_generate_and_initialize_repo_full_flow(
        self,
        mock_rmtree: Mock,
        mock_run: Mock,
        handler: BotGitHandler,
        temp_output: Path,
        mocker: MockerFixture,
    ) -> None:
        mock_run.side_effect = None

        handler.generate_and_initialize_repo(
            output_path=temp_output,
            cli_args=["generate", "--spring-boot", "--react"],
            initial_branch="main",
            commit_message="chore: initial setup",
        )

        cli_call = mock_run.call_args_list[0]
        expected_cli = [
            "ar-infra-cli",
            "generate",
            "--spring-boot",
            "--react",
            "--output",
            str(temp_output),
        ]
        assert cli_call[0][0] == expected_cli

        git_calls = [c[0][0] for c in mock_run.call_args_list[1:]]
        expected_git = [
            ["git", "init"],
            ["git", "config", "user.name", "test-bot[bot]"],
            ["git", "config", "user.email", "999+test-bot[bot]@users.noreply.github.com"],
            ["git", "branch", "-M", "main"],
            ["git", "add", "."],
            ["git", "commit", "-m", "chore: initial setup"],
        ]
        assert git_calls == expected_git

    @patch("src.ar_infra.infrastructure.processor.bot.subprocess.run")
    @patch("src.ar_infra.infrastructure.processor.bot.shutil.rmtree")
    def test_generate_and_initialize_repo_removes_existing_git_dir(
        self,
        mock_rmtree: Mock,
        mock_run: Mock,
        handler: BotGitHandler,
        temp_output: Path,
    ) -> None:
        temp_output.mkdir(parents=True, exist_ok=True)
        (temp_output / ".git").mkdir()

        mock_run.side_effect = None

        handler.generate_and_initialize_repo(temp_output, cli_args=[])
        assert mock_rmtree.call_count == 2

        second_call_path = mock_rmtree.call_args_list[1][0][0]
        assert second_call_path == temp_output / ".git"

    @patch("src.ar_infra.infrastructure.processor.bot.subprocess.run")
    def test_run_command_raises_git_command_error_on_failure(
        self,
        mock_run: Mock,
        handler: BotGitHandler,
    ) -> None:
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["git", "status"],
            stderr="fatal: something wrong",
        )

        with pytest.raises(GitCommandError) as exc:
            handler._run_command(["git", "status"])

        assert exc.value.command == "git status"
        assert exc.value.returncode == 1
        assert "something wrong" in exc.value.stderr

    @patch("src.ar_infra.infrastructure.processor.bot.subprocess.run")
    def test_run_command_raises_repository_error_when_command_missing(
        self,
        mock_run: Mock,
        handler: BotGitHandler,
    ) -> None:
        mock_run.side_effect = FileNotFoundError("git")

        with pytest.raises(GitRepositoryError, match="git"):
            handler._run_command(["git", "init"])

    @patch("src.ar_infra.infrastructure.processor.bot.BOT_ID", "123456")
    @patch("src.ar_infra.infrastructure.processor.bot.BOT_SLUG", "env-bot")
    def test_init_uses_config_when_no_identity_provided(self) -> None:
        handler = BotGitHandler()

        assert handler.bot_identity.name == "env-bot[bot]"
        assert handler.bot_identity.email == "123456+env-bot[bot]@users.noreply.github.com"
