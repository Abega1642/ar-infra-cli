"""Tests for InteractivePrompt class."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.ar_infra.cli.prompt.interactive_prompt import InteractivePrompt


class TestInteractivePrompt:
    @pytest.fixture
    def prompt(self) -> InteractivePrompt:
        return InteractivePrompt()

    @patch("src.ar_infra.cli.prompt.interactive_prompt.Messages")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    def test_collect_inputs_success(
        self,
        mock_confirm: Mock,
        mock_checkbox: Mock,
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
        mock_checkbox.return_value.ask.return_value = ["postgresql", "email"]

        mock_confirm.return_value.ask.side_effect = [True, True]

        result = prompt.collect_inputs()

        assert result["group_id"] == "com.example"
        assert result["artifact_id"] == "my-app"
        assert result["version"] == "1.0.0"
        assert result["destination"] == tmp_path
        assert result["project_dir_name"] == "my-app"
        assert result["enabled_features"] == {"postgresql", "email"}
        assert result["use_template_cache"] is True

        # Verify summary was shown
        mock_messages.project_summary.assert_called_once()

    @patch("src.ar_infra.cli.prompt.interactive_prompt.Messages")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    def test_collect_inputs_no_features(
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
        # First confirm: use_cache=False, Second confirm: proceed=True
        mock_confirm.return_value.ask.side_effect = [False, True]

        result = prompt.collect_inputs()

        assert result["group_id"] == "dev.razafindratelo"
        assert result["artifact_id"] == "backend-api"
        assert result["version"] == "2.0.0"
        assert result["destination"] == tmp_path
        assert result["project_dir_name"] == "backend-api"
        assert result["enabled_features"] == set()
        assert result["use_template_cache"] is False

    @patch("src.ar_infra.cli.prompt.interactive_prompt.Messages")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    def test_collect_inputs_all_features(
        self,
        mock_confirm: Mock,
        mock_checkbox: Mock,
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
        mock_checkbox.return_value.ask.return_value = [
            "postgresql",
            "rabbitmq",
            "s3_bucket",
            "email",
        ]

        mock_confirm.return_value.ask.side_effect = [True, True]

        result = prompt.collect_inputs()

        assert len(result["enabled_features"]) == 4
        assert "postgresql" in result["enabled_features"]
        assert "rabbitmq" in result["enabled_features"]
        assert "s3_bucket" in result["enabled_features"]
        assert "email" in result["enabled_features"]
        assert result["project_dir_name"] == "full-app"

    @patch("src.ar_infra.cli.prompt.interactive_prompt.Messages")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    def test_collect_inputs_custom_project_dir_name(
        self,
        mock_confirm: Mock,
        mock_checkbox: Mock,
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
        mock_checkbox.return_value.ask.return_value = ["postgresql"]

        mock_confirm.return_value.ask.side_effect = [True, True]

        result = prompt.collect_inputs()

        assert result["artifact_id"] == "my-app"
        assert result["project_dir_name"] == "custom-project-name"
        assert result["destination"] == tmp_path

    @patch("src.ar_infra.cli.prompt.interactive_prompt.Messages")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("builtins.print")
    def test_collect_inputs_user_declines_and_cancels(
        self,
        mock_print: Mock,
        mock_confirm: Mock,
        mock_checkbox: Mock,
        mock_text: Mock,
        mock_messages: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        """Test when user declines to proceed and then cancels."""
        mock_text.return_value.ask.side_effect = [
            "com.example",
            "my-app",
            "1.0.0",
            str(tmp_path),
            "my-app",
        ]
        mock_checkbox.return_value.ask.return_value = ["postgresql"]
        # First confirm: use_cache=True, Second confirm: proceed=False, Third confirm: start_over=False
        mock_confirm.return_value.ask.side_effect = [True, False, False]

        with pytest.raises(KeyboardInterrupt, match="Configuration cancelled by user"):
            prompt.collect_inputs()

    @patch("src.ar_infra.cli.prompt.interactive_prompt.Messages")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    @patch("builtins.print")
    def test_collect_inputs_user_starts_over(
        self,
        mock_print: Mock,
        mock_confirm: Mock,
        mock_checkbox: Mock,
        mock_text: Mock,
        mock_messages: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        """Test when user declines to proceed but chooses to start over."""
        mock_text.return_value.ask.side_effect = [
            "com.example",
            "my-app",
            "1.0.0",
            str(tmp_path),
            "my-app",
            # Second attempt (after starting over)
            "org.newcompany",
            "new-app",
            "2.0.0",
            str(tmp_path),
            "new-app",
        ]
        mock_checkbox.return_value.ask.side_effect = [
            ["postgresql"],  # First attempt
            ["email"],  # Second attempt
        ]
        # Sequence: use_cache=True, proceed=False, start_over=True, use_cache=True, proceed=True
        mock_confirm.return_value.ask.side_effect = [True, False, True, True, True]

        result = prompt.collect_inputs()

        assert result["group_id"] == "org.newcompany"
        assert result["artifact_id"] == "new-app"
        assert result["version"] == "2.0.0"
        assert result["enabled_features"] == {"email"}

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
