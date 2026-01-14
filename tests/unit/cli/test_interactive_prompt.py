"""Tests for InteractivePrompt class."""

import re
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.ar_infra.cli.prompt.interactive_prompt import InteractivePrompt
from src.ar_infra.domain.entities.path_resolver import (
    DangerousPathError,
    PathSecurityError,
)


class TestInteractivePrompt:
    @pytest.fixture
    def prompt(self) -> InteractivePrompt:
        return InteractivePrompt()

    @patch("src.ar_infra.cli.prompt.interactive_prompt.Messages")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.select")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    def test_collect_inputs_success_with_postgresql(
        self,
        mock_confirm: Mock,
        mock_checkbox: Mock,
        mock_select: Mock,
        mock_text: Mock,
        mock_messages: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        mock_text.return_value.ask.side_effect = [
            "com.example",
            "my-app",
            "1.0.0",
            str(tmp_path),
            "my-app",
        ]
        mock_confirm.return_value.ask.side_effect = [True, True, True]
        mock_select.return_value.ask.return_value = "postgresql"
        mock_checkbox.return_value.ask.return_value = ["email"]

        result = prompt.collect_inputs(skip_github_app=True)

        assert result["group_id"] == "com.example"
        assert result["artifact_id"] == "my-app"
        assert result["version"] == "1.0.0"
        assert result["destination"] == tmp_path
        assert result["project_dir_name"] == "my-app"
        assert result["enabled_features"] == {"postgresql", "email"}
        assert result["use_template_cache"] is True

        mock_messages.project_summary.assert_called_once()

    @patch("src.ar_infra.cli.prompt.interactive_prompt.Messages")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.select")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    def test_collect_inputs_success_with_mysql(
        self,
        mock_confirm: Mock,
        mock_checkbox: Mock,
        mock_select: Mock,
        mock_text: Mock,
        mock_messages: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        mock_text.return_value.ask.side_effect = [
            "com.example",
            "my-app",
            "1.0.0",
            str(tmp_path),
            "my-app",
        ]
        mock_confirm.return_value.ask.side_effect = [True, True, True]
        mock_select.return_value.ask.return_value = "mysql"
        mock_checkbox.return_value.ask.return_value = ["rabbitmq"]

        result = prompt.collect_inputs(skip_github_app=True)

        assert result["group_id"] == "com.example"
        assert result["artifact_id"] == "my-app"
        assert result["version"] == "1.0.0"
        assert result["destination"] == tmp_path
        assert result["project_dir_name"] == "my-app"
        assert result["enabled_features"] == {"mysql", "rabbitmq"}
        assert result["use_template_cache"] is True

    @patch("src.ar_infra.cli.prompt.interactive_prompt.Messages")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    def test_collect_inputs_no_database(
        self,
        mock_confirm: Mock,
        mock_checkbox: Mock,
        mock_text: Mock,
        mock_messages: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        mock_text.return_value.ask.side_effect = [
            "dev.razafindratelo",
            "backend-api",
            "2.0.0",
            str(tmp_path),
            "backend-api",
        ]
        mock_checkbox.return_value.ask.return_value = []
        mock_confirm.return_value.ask.side_effect = [False, False, True]

        result = prompt.collect_inputs(skip_github_app=True)

        assert result["group_id"] == "dev.razafindratelo"
        assert result["artifact_id"] == "backend-api"
        assert result["version"] == "2.0.0"
        assert result["destination"] == tmp_path
        assert result["project_dir_name"] == "backend-api"
        assert result["enabled_features"] == set()
        assert result["use_template_cache"] is False

    @patch("src.ar_infra.cli.prompt.interactive_prompt.Messages")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.select")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    def test_collect_inputs_all_features(
        self,
        mock_confirm: Mock,
        mock_checkbox: Mock,
        mock_select: Mock,
        mock_text: Mock,
        mock_messages: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        mock_text.return_value.ask.side_effect = [
            "com.company",
            "full-app",
            "1.0.0",
            str(tmp_path),
            "full-app",
        ]
        mock_confirm.return_value.ask.side_effect = [True, True, True]
        mock_select.return_value.ask.return_value = "postgresql"
        mock_checkbox.return_value.ask.return_value = [
            "rabbitmq",
            "s3_bucket",
            "email",
        ]

        result = prompt.collect_inputs(skip_github_app=True)

        assert len(result["enabled_features"]) == 4
        assert "postgresql" in result["enabled_features"]
        assert "rabbitmq" in result["enabled_features"]
        assert "s3_bucket" in result["enabled_features"]
        assert "email" in result["enabled_features"]
        assert result["project_dir_name"] == "full-app"

    @patch("src.ar_infra.cli.prompt.interactive_prompt.Messages")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.select")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    def test_collect_inputs_custom_project_dir_name(
        self,
        mock_confirm: Mock,
        mock_checkbox: Mock,
        mock_select: Mock,
        mock_text: Mock,
        mock_messages: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        mock_text.return_value.ask.side_effect = [
            "com.example",
            "my-app",
            "1.0.0",
            str(tmp_path),
            "custom-project-name",
        ]
        mock_confirm.return_value.ask.side_effect = [True, True, True]
        mock_select.return_value.ask.return_value = "postgresql"
        mock_checkbox.return_value.ask.return_value = []

        result = prompt.collect_inputs(skip_github_app=True)

        assert result["artifact_id"] == "my-app"
        assert result["project_dir_name"] == "custom-project-name"
        assert result["destination"] == tmp_path

    @patch("src.ar_infra.cli.prompt.interactive_prompt.Messages")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.select")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("builtins.print")
    def test_collect_inputs_user_declines_and_cancels(
        self,
        mock_print: Mock,
        mock_confirm: Mock,
        mock_checkbox: Mock,
        mock_select: Mock,
        mock_text: Mock,
        mock_messages: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        mock_text.return_value.ask.side_effect = [
            "com.example",
            "my-app",
            "1.0.0",
            str(tmp_path),
            "my-app",
        ]
        mock_confirm.return_value.ask.side_effect = [True, True, False, False]
        mock_select.return_value.ask.return_value = "postgresql"
        mock_checkbox.return_value.ask.return_value = []

        with pytest.raises(KeyboardInterrupt, match="Configuration cancelled by user"):
            prompt.collect_inputs(skip_github_app=True)

    @patch("src.ar_infra.cli.prompt.interactive_prompt.Messages")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.select")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("builtins.print")
    def test_collect_inputs_user_starts_over(
        self,
        mock_print: Mock,
        mock_confirm: Mock,
        mock_checkbox: Mock,
        mock_select: Mock,
        mock_text: Mock,
        mock_messages: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        mock_text.return_value.ask.side_effect = [
            "com.example",
            "my-app",
            "1.0.0",
            str(tmp_path),
            "my-app",
            "org.newcompany",
            "new-app",
            "2.0.0",
            str(tmp_path),
            "new-app",
        ]
        mock_confirm.return_value.ask.side_effect = [
            True,
            True,
            False,
            True,  # First iteration: wants DB, proceed with config, declines, starts over
            False,
            False,
            True,  # Second iteration: no DB, no cache, proceeds
        ]
        mock_select.return_value.ask.return_value = "postgresql"
        mock_checkbox.return_value.ask.side_effect = [
            [],  # First iteration: no other features
            ["email"],  # Second iteration: email feature
        ]

        result = prompt.collect_inputs(skip_github_app=True)

        assert result["group_id"] == "org.newcompany"
        assert result["artifact_id"] == "new-app"
        assert result["version"] == "2.0.0"
        assert result["enabled_features"] == {"email"}

    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    def test_prompt_group_id_cancelled(
        self,
        mock_text: Mock,
        prompt: InteractivePrompt,
    ) -> None:
        mock_text.return_value.ask.return_value = None

        with pytest.raises(
            KeyboardInterrupt, match=re.escape("The operation was cancelled by the user.")
        ):
            prompt._prompt_group_id()

    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    def test_prompt_artifact_id_cancelled(
        self,
        mock_text: Mock,
        prompt: InteractivePrompt,
    ) -> None:
        mock_text.return_value.ask.return_value = None

        with pytest.raises(
            KeyboardInterrupt, match=re.escape("The operation was cancelled by the user.")
        ):
            prompt._prompt_artifact_id()

    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    def test_prompt_version_cancelled(
        self,
        mock_text: Mock,
        prompt: InteractivePrompt,
    ) -> None:
        mock_text.return_value.ask.return_value = None

        with pytest.raises(
            KeyboardInterrupt, match=re.escape("The operation was cancelled by the user.")
        ):
            prompt._prompt_version()

    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.select")
    def test_prompt_features_postgresql(
        self,
        mock_select: Mock,
        mock_confirm: Mock,
        prompt: InteractivePrompt,
    ) -> None:
        mock_confirm.return_value.ask.return_value = True
        mock_select.return_value.ask.return_value = "postgresql"

        with patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox") as mock_checkbox:
            mock_checkbox.return_value.ask.return_value = ["email"]
            result = prompt._prompt_features()

        assert result == ["postgresql", "email"]

    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.select")
    def test_prompt_features_mysql(
        self,
        mock_select: Mock,
        mock_confirm: Mock,
        prompt: InteractivePrompt,
    ) -> None:
        mock_confirm.return_value.ask.return_value = True
        mock_select.return_value.ask.return_value = "mysql"

        with patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox") as mock_checkbox:
            mock_checkbox.return_value.ask.return_value = ["rabbitmq"]
            result = prompt._prompt_features()

        assert result == ["mysql", "rabbitmq"]

    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    def test_prompt_features_no_database(
        self,
        mock_confirm: Mock,
        prompt: InteractivePrompt,
    ) -> None:
        mock_confirm.return_value.ask.return_value = False

        with patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox") as mock_checkbox:
            mock_checkbox.return_value.ask.return_value = []
            result = prompt._prompt_features()

        assert result == []

    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    def test_prompt_features_database_prompt_cancelled(
        self,
        mock_confirm: Mock,
        prompt: InteractivePrompt,
    ) -> None:
        mock_confirm.return_value.ask.return_value = None

        with pytest.raises(
            KeyboardInterrupt, match=re.escape("The operation was cancelled by the user.")
        ):
            prompt._prompt_features()

    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.select")
    def test_prompt_features_database_selection_cancelled(
        self,
        mock_select: Mock,
        mock_confirm: Mock,
        prompt: InteractivePrompt,
    ) -> None:
        mock_confirm.return_value.ask.return_value = True
        mock_select.return_value.ask.return_value = None

        with pytest.raises(
            KeyboardInterrupt, match=re.escape("The operation was cancelled by the user.")
        ):
            prompt._prompt_features()

    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.select")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    def test_prompt_features_other_features_cancelled(
        self,
        mock_checkbox: Mock,
        mock_select: Mock,
        mock_confirm: Mock,
        prompt: InteractivePrompt,
    ) -> None:
        mock_confirm.return_value.ask.return_value = True
        mock_select.return_value.ask.return_value = "postgresql"
        mock_checkbox.return_value.ask.return_value = None

        with pytest.raises(
            KeyboardInterrupt, match=re.escape("The operation was cancelled by the user.")
        ):
            prompt._prompt_features()

    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    def test_prompt_use_cache_cancelled(
        self,
        mock_confirm: Mock,
        prompt: InteractivePrompt,
    ) -> None:
        mock_confirm.return_value.ask.return_value = None

        with pytest.raises(
            KeyboardInterrupt, match=re.escape("The operation was cancelled by the user.")
        ):
            prompt._prompt_use_cache()

    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("builtins.print")
    def test_prompt_destination_path_nonexistent_create(
        self,
        mock_print: Mock,
        mock_text: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        new_dir = tmp_path / "new_project_dir"
        mock_text.return_value.ask.return_value = str(new_dir)

        with patch("src.ar_infra.cli.prompt.interactive_prompt.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            result = prompt._prompt_destination_path()

        assert result == new_dir
        assert new_dir.exists()
        assert new_dir.is_dir()

    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("builtins.print")
    def test_prompt_destination_path_nonexistent_decline_and_retry(
        self,
        mock_print: Mock,
        mock_confirm: Mock,
        mock_text: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        new_dir = tmp_path / "nonexistent"
        mock_text.return_value.ask.side_effect = [str(new_dir), str(tmp_path)]
        mock_confirm.return_value.ask.side_effect = [False, True]

        result = prompt._prompt_destination_path()

        assert result == tmp_path

    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("builtins.print")
    def test_prompt_destination_path_nonexistent_decline_and_cancel(
        self,
        mock_print: Mock,
        mock_confirm: Mock,
        mock_text: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        new_dir = tmp_path / "nonexistent"
        mock_text.return_value.ask.return_value = str(new_dir)
        mock_confirm.return_value.ask.side_effect = [False, False]

        with pytest.raises(
            KeyboardInterrupt, match=re.escape("The operation was cancelled by the user.")
        ):
            prompt._prompt_destination_path()

    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("builtins.print")
    def test_prompt_destination_path_file_exists(
        self,
        mock_print: Mock,
        mock_text: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        file_path = tmp_path / "somefile.txt"
        file_path.touch()

        mock_text.return_value.ask.side_effect = [str(file_path), str(tmp_path)]

        with patch("src.ar_infra.cli.prompt.interactive_prompt.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            result = prompt._prompt_destination_path()

        assert result == tmp_path

    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("builtins.print")
    def test_prompt_destination_path_security_error(
        self,
        mock_print: Mock,
        mock_confirm: Mock,
        mock_text: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        mock_text.return_value.ask.side_effect = ["../../../etc", str(tmp_path)]
        mock_confirm.return_value.ask.return_value = True

        with patch.object(
            prompt.security_validator,
            "validate_destination_path",
            side_effect=[PathSecurityError("Security violation"), tmp_path],
        ):
            result = prompt._prompt_destination_path()

        assert result == tmp_path
        mock_print.assert_any_call("\nSecurity Error: Security violation\n")

    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("builtins.print")
    def test_prompt_destination_path_dangerous_path_error(
        self,
        mock_print: Mock,
        mock_confirm: Mock,
        mock_text: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        mock_text.return_value.ask.side_effect = ["/etc/passwd", str(tmp_path)]
        mock_confirm.return_value.ask.return_value = True

        with patch.object(
            prompt.security_validator,
            "validate_destination_path",
            side_effect=[DangerousPathError("Dangerous path detected"), tmp_path],
        ):
            result = prompt._prompt_destination_path()

        assert result == tmp_path
        mock_print.assert_any_call("\nSECURITY WARNING: Dangerous path detected\n")

    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("builtins.print")
    def test_prompt_destination_path_security_error_user_cancels(
        self,
        mock_print: Mock,
        mock_confirm: Mock,
        mock_text: Mock,
        prompt: InteractivePrompt,
    ) -> None:
        """Test cancelling after security error."""
        mock_text.return_value.ask.return_value = "dangerous/path"
        mock_confirm.return_value.ask.return_value = False

        with (
            patch.object(
                prompt.security_validator,
                "validate_destination_path",
                side_effect=PathSecurityError("Security violation"),
            ),
            pytest.raises(PathSecurityError),
        ):
            prompt._prompt_destination_path()

    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("builtins.print")
    def test_prompt_project_directory_name_success(
        self,
        mock_print: Mock,
        mock_text: Mock,
        prompt: InteractivePrompt,
    ) -> None:
        mock_text.return_value.ask.return_value = "valid-project-name"

        result = prompt._prompt_project_directory_name("default-name")

        assert result == "valid-project-name"

    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("builtins.print")
    def test_prompt_project_directory_name_invalid_then_valid(
        self,
        mock_print: Mock,
        mock_confirm: Mock,
        mock_text: Mock,
        prompt: InteractivePrompt,
    ) -> None:
        mock_text.return_value.ask.side_effect = ["../invalid", "valid-name"]
        mock_confirm.return_value.ask.return_value = True

        with patch.object(
            prompt.security_validator,
            "validate_project_directory_name",
            side_effect=[ValueError("Invalid name"), "valid-name"],
        ):
            result = prompt._prompt_project_directory_name("default")

        assert result == "valid-name"

    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("builtins.print")
    def test_prompt_project_directory_name_invalid_user_cancels(
        self,
        mock_print: Mock,
        mock_confirm: Mock,
        mock_text: Mock,
        prompt: InteractivePrompt,
    ) -> None:
        mock_text.return_value.ask.return_value = "../invalid"
        mock_confirm.return_value.ask.return_value = False

        with (
            patch.object(
                prompt.security_validator,
                "validate_project_directory_name",
                side_effect=ValueError("Invalid name"),
            ),
            pytest.raises(ValueError, match="Invalid name"),
        ):
            prompt._prompt_project_directory_name("default")

    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    def test_prompt_project_directory_name_cancelled(
        self,
        mock_text: Mock,
        prompt: InteractivePrompt,
    ) -> None:
        mock_text.return_value.ask.return_value = None

        with pytest.raises(
            KeyboardInterrupt, match=re.escape("The operation was cancelled by the user.")
        ):
            prompt._prompt_project_directory_name("default")

    def test_handle_existing_directory_not_exists(
        self,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        result = prompt._handle_existing_directory(tmp_path, "nonexistent")

        assert result == "proceed"

    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("builtins.print")
    def test_handle_existing_directory_empty(
        self,
        mock_print: Mock,
        mock_confirm: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        empty_dir = tmp_path / "empty_project"
        empty_dir.mkdir()

        mock_confirm.return_value.ask.return_value = True

        result = prompt._handle_existing_directory(tmp_path, "empty_project")

        assert result == "proceed"

    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("builtins.print")
    def test_handle_existing_directory_empty_decline(
        self,
        mock_print: Mock,
        mock_confirm: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        empty_dir = tmp_path / "empty_project"
        empty_dir.mkdir()

        mock_confirm.return_value.ask.return_value = False

        result = prompt._handle_existing_directory(tmp_path, "empty_project")

        assert result == "rename"

    @patch("src.ar_infra.cli.prompt.interactive_prompt.select")
    @patch("builtins.print")
    def test_handle_existing_directory_has_content_rename(
        self,
        mock_print: Mock,
        mock_select: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        project_dir = tmp_path / "existing_project"
        project_dir.mkdir()
        (project_dir / "file.txt").touch()

        mock_select.return_value.ask.return_value = "rename"

        result = prompt._handle_existing_directory(tmp_path, "existing_project")

        assert result == "rename"

    @patch("src.ar_infra.cli.prompt.interactive_prompt.select")
    @patch("builtins.print")
    def test_handle_existing_directory_has_content_change_dest(
        self,
        mock_print: Mock,
        mock_select: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        project_dir = tmp_path / "existing_project"
        project_dir.mkdir()
        (project_dir / "file.txt").touch()

        mock_select.return_value.ask.return_value = "change_dest"

        result = prompt._handle_existing_directory(tmp_path, "existing_project")

        assert result == "change_dest"

    @patch("src.ar_infra.cli.prompt.interactive_prompt.select")
    @patch("builtins.print")
    def test_handle_existing_directory_has_content_cancel(
        self,
        mock_print: Mock,
        mock_select: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        project_dir = tmp_path / "existing_project"
        project_dir.mkdir()
        (project_dir / "file.txt").touch()

        mock_select.return_value.ask.return_value = "cancel"

        result = prompt._handle_existing_directory(tmp_path, "existing_project")

        assert result == "cancel"

    @patch("src.ar_infra.cli.prompt.interactive_prompt.select")
    @patch("builtins.print")
    def test_handle_existing_directory_user_closes_prompt(
        self,
        mock_print: Mock,
        mock_select: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        project_dir = tmp_path / "existing_project"
        project_dir.mkdir()
        (project_dir / "file.txt").touch()

        mock_select.return_value.ask.return_value = None

        result = prompt._handle_existing_directory(tmp_path, "existing_project")

        assert result == "cancel"

    @patch("builtins.print")
    def test_handle_existing_directory_file_not_directory(
        self,
        mock_print: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        file_path = tmp_path / "somefile.txt"
        file_path.touch()

        result = prompt._handle_existing_directory(tmp_path, "somefile.txt")

        assert result == "rename"

    @patch("src.ar_infra.cli.prompt.interactive_prompt.Messages")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.select")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    def test_collect_inputs_with_github_app_success(
        self,
        mock_confirm: Mock,
        mock_checkbox: Mock,
        mock_select: Mock,
        mock_text: Mock,
        mock_messages: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        mock_text.return_value.ask.side_effect = [
            "com.example",
            "my-app",
            "1.0.0",
            str(tmp_path),
            "my-app",
        ]
        mock_confirm.return_value.ask.side_effect = [False, False, True]
        mock_checkbox.return_value.ask.return_value = []

        with patch.object(prompt.github_app_handler, "prompt_installation") as mock_gh:
            result = prompt.collect_inputs(skip_github_app=False)

        mock_gh.assert_called_once()
        assert result["group_id"] == "com.example"

    @patch("src.ar_infra.cli.prompt.interactive_prompt.Messages")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.select")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("builtins.print")
    def test_collect_inputs_github_app_cancelled_continue(
        self,
        mock_print: Mock,
        mock_confirm: Mock,
        mock_checkbox: Mock,
        mock_select: Mock,
        mock_text: Mock,
        mock_messages: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        mock_text.return_value.ask.side_effect = [
            "com.example",
            "my-app",
            "1.0.0",
            str(tmp_path),
            "my-app",
        ]
        mock_confirm.return_value.ask.side_effect = [False, False, True, True]
        mock_checkbox.return_value.ask.return_value = []

        with patch.object(
            prompt.github_app_handler,
            "prompt_installation",
            side_effect=KeyboardInterrupt(),
        ):
            result = prompt.collect_inputs(skip_github_app=False)

        assert result["group_id"] == "com.example"

    @patch("src.ar_infra.cli.prompt.interactive_prompt.Messages")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.select")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("builtins.print")
    def test_collect_inputs_github_app_cancelled_abort(
        self,
        mock_print: Mock,
        mock_confirm: Mock,
        mock_checkbox: Mock,
        mock_select: Mock,
        mock_text: Mock,
        mock_messages: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        mock_text.return_value.ask.side_effect = [
            "com.example",
            "my-app",
            "1.0.0",
            str(tmp_path),
            "my-app",
        ]
        mock_confirm.return_value.ask.side_effect = [False, False, True, False]
        mock_checkbox.return_value.ask.return_value = []

        with (
            patch.object(
                prompt.github_app_handler,
                "prompt_installation",
                side_effect=KeyboardInterrupt(),
            ),
            pytest.raises(
                KeyboardInterrupt, match=re.escape("The operation was cancelled by the user.")
            ),
        ):
            prompt.collect_inputs(skip_github_app=False)

    @patch("src.ar_infra.cli.prompt.interactive_prompt.Messages")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.select")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("builtins.print")
    def test_collect_inputs_directory_conflict_cancel(
        self,
        mock_print: Mock,
        mock_confirm: Mock,
        mock_checkbox: Mock,
        mock_select: Mock,
        mock_text: Mock,
        mock_messages: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        existing_dir = tmp_path / "my-app"
        existing_dir.mkdir()
        (existing_dir / "file.txt").touch()

        mock_text.return_value.ask.side_effect = [
            "com.example",
            "my-app",
            "1.0.0",
            str(tmp_path),
            "my-app",
        ]
        mock_confirm.return_value.ask.side_effect = [False, False]
        mock_select.return_value.ask.side_effect = ["cancel"]
        mock_checkbox.return_value.ask.return_value = []

        with pytest.raises(
            KeyboardInterrupt, match=re.escape("The operation was cancelled by the user.")
        ):
            prompt.collect_inputs(skip_github_app=True)

    def test_prompt_has_validators(self, prompt: InteractivePrompt) -> None:
        assert prompt.validators is not None
        assert hasattr(prompt.validators, "group_id")
        assert hasattr(prompt.validators, "artifact_id")
        assert hasattr(prompt.validators, "version")
        assert hasattr(prompt.validators, "path")

    def test_prompt_has_security_validator(self, prompt: InteractivePrompt) -> None:
        assert prompt.security_validator is not None
        assert hasattr(prompt.security_validator, "validate_destination_path")
        assert hasattr(prompt.security_validator, "validate_project_directory_name")

    def test_prompt_has_github_app_handler(self, prompt: InteractivePrompt) -> None:
        assert prompt.github_app_handler is not None
        assert hasattr(prompt.github_app_handler, "prompt_installation")
