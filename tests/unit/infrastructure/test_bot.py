"""Tests for bot.py components."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests
from pytest_mock import MockerFixture

from src.ar_infra.infrastructure.processor.bot import (
    BotGitHandler,
    BotIdentity,
    GitCommandError,
    GitRepositoryError,
)


class TestBotIdentity:
    def test_from_github_app_with_provided_id(self) -> None:
        identity = BotIdentity.from_github_app(bot_slug="my-bot", bot_id=123456)
        assert identity.name == "my-bot[bot]"
        assert identity.email == "123456+my-bot[bot]@users.noreply.github.com"

    @patch("src.ar_infra.infrastructure.processor.bot.requests.get")
    def test_from_github_app_fetches_id_from_api(self, mock_get: Mock) -> None:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"id": 987654}
        mock_get.return_value = mock_response

        identity = BotIdentity.from_github_app(bot_slug="fetch-bot")

        assert identity.name == "fetch-bot[bot]"
        assert identity.email == "987654+fetch-bot[bot]@users.noreply.github.com"
        mock_get.assert_called_once_with(
            "https://api.github.com/users/fetch-bot%5Bbot%5D",
            timeout=10,
        )

    @patch("src.ar_infra.infrastructure.processor.bot.requests.get")
    def test_from_github_app_raises_on_api_failure(self, mock_get: Mock) -> None:
        mock_get.side_effect = requests.RequestException("Connection failed")

        with pytest.raises(RuntimeError, match="Failed to fetch bot user ID"):
            BotIdentity.from_github_app(bot_slug="fail-bot")


class TestBotGitHandler:
    @pytest.fixture
    def handler(self) -> BotGitHandler:
        """Handler with a fixed test identity."""
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
    def test_run_command_raises_gitcommanderror_on_failure(
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
    def test_run_command_raises_repositoryerror_when_command_missing(
        self,
        mock_run: Mock,
        handler: BotGitHandler,
    ) -> None:
        mock_run.side_effect = FileNotFoundError("git")

        with pytest.raises(GitRepositoryError, match="git"):
            handler._run_command(["git", "init"])

    @patch("src.ar_infra.infrastructure.processor.bot.BotIdentity.from_github_app")
    @patch("src.ar_infra.infrastructure.processor.bot.BOT_ID", "123456")
    @patch("src.ar_infra.infrastructure.processor.bot.BOT_SLUG", "env-bot")
    def test_init_uses_env_vars_when_no_identity_provided(
        self,
        mock_from_github: Mock,
    ) -> None:
        expected_identity = BotIdentity(
            name="env-bot[bot]", email="123456+env-bot[bot]@users.noreply.github.com"
        )
        mock_from_github.return_value = expected_identity

        handler = BotGitHandler()  # No explicit identity

        assert handler.bot_identity == expected_identity
        mock_from_github.assert_called_once_with("env-bot", 123456)

    @patch("src.ar_infra.infrastructure.processor.bot.BotIdentity.from_github_app")
    @patch("src.ar_infra.infrastructure.processor.bot.BOT_ID", None)
    def test_init_falls_back_to_api_when_no_env_id(
        self,
        mock_from_github: Mock,
    ) -> None:
        BotGitHandler()
        mock_from_github.assert_called_once_with("ar-infra-bot")
