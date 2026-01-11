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
            ["git", "config", "--local", "user.name", "test-bot[bot]"],
            [
                "git",
                "config",
                "--local",
                "user.email",
                "999+test-bot[bot]@users.noreply.github.com",
            ],
            ["git", "branch", "-M", "main"],
            ["git", "add", "."],
            ["git", "commit", "-m", "chore: initial setup"],
            ["git", "config", "--unset", "user.name"],
            ["git", "config", "--unset", "user.email"],
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

    @patch("src.ar_infra.infrastructure.processor.bot.subprocess.run")
    def test_unset_bot_identity_is_called_after_commit(
        self,
        mock_run: Mock,
        handler: BotGitHandler,
        temp_output: Path,
    ) -> None:
        """Verify that bot identity is removed after initial commit."""
        temp_output.mkdir(parents=True, exist_ok=True)
        mock_run.side_effect = None

        handler.initialize_repository(
            project_path=temp_output,
            initial_branch="main",
            commit_message="initial commit",
        )

        git_calls = [c[0][0] for c in mock_run.call_args_list]

        commit_index = next(i for i, call in enumerate(git_calls) if call[:2] == ["git", "commit"])
        unset_name_index = next(
            i
            for i, call in enumerate(git_calls)
            if call == ["git", "config", "--unset", "user.name"]
        )
        unset_email_index = next(
            i
            for i, call in enumerate(git_calls)
            if call == ["git", "config", "--unset", "user.email"]
        )

        assert unset_name_index > commit_index
        assert unset_email_index > commit_index

    @patch("src.ar_infra.infrastructure.processor.bot.subprocess.run")
    def test_unset_bot_identity_handles_errors_gracefully(
        self,
        mock_run: Mock,
        handler: BotGitHandler,
        temp_output: Path,
    ) -> None:
        temp_output.mkdir(parents=True, exist_ok=True)

        def side_effect(cmd, **kwargs):
            if "--unset" in cmd:
                raise subprocess.CalledProcessError(
                    returncode=1,
                    cmd=cmd,
                    stderr="error: key does not contain a section",
                )
            return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = side_effect

        handler.initialize_repository(
            project_path=temp_output,
            initial_branch="main",
            commit_message="initial commit",
        )

        assert mock_run.call_count > 0

    @patch("src.ar_infra.infrastructure.processor.bot.subprocess.run")
    def test_configure_bot_identity_uses_local_flag(
        self,
        mock_run: Mock,
        handler: BotGitHandler,
        temp_output: Path,
    ) -> None:
        temp_output.mkdir(parents=True, exist_ok=True)
        mock_run.side_effect = None

        handler.initialize_repository(
            project_path=temp_output,
            initial_branch="main",
            commit_message="initial commit",
        )

        git_calls = [c[0][0] for c in mock_run.call_args_list]

        config_name = next(
            call
            for call in git_calls
            if len(call) > 2 and call[1] == "config" and call[3] == "user.name"
        )
        config_email = next(
            call
            for call in git_calls
            if len(call) > 2 and call[1] == "config" and call[3] == "user.email"
        )

        assert "--local" in config_name
        assert "--local" in config_email
