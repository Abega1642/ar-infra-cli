"""Tests for GitHub App handler."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.ar_infra.infrastructure.processor.github_app import (
    GitHubAppConfig,
    GitHubAppHandler,
)


class TestGitHubAppHandler:
    @pytest.fixture
    def handler(self) -> GitHubAppHandler:
        return GitHubAppHandler()

    @pytest.fixture
    def custom_config(self) -> GitHubAppConfig:
        return GitHubAppConfig(
            app_name="test-bot",
            app_url="https://github.com/apps/test-bot",
            installation_url="https://github.com/apps/test-bot/installations/new",
        )

    def test_default_config(self, handler: GitHubAppHandler) -> None:
        assert handler.app_config.app_name == "ar-infra-bot"
        assert handler.app_config.app_url == "https://github.com/apps/ar-infra-bot"
        assert (
            handler.app_config.installation_url
            == "https://github.com/apps/ar-infra-bot/installations/new"
        )

    def test_custom_config(self, custom_config: GitHubAppConfig) -> None:
        handler = GitHubAppHandler(app_config=custom_config)
        assert handler.app_config.app_name == "test-bot"
        assert handler.app_config.app_url == "https://github.com/apps/test-bot"

    @patch("src.ar_infra.infrastructure.processor.github_app.webbrowser.open")
    @patch("src.ar_infra.infrastructure.processor.github_app.select")
    def test_prompt_installation_yes_and_completed(
        self,
        mock_select: Mock,
        mock_webbrowser: Mock,
        handler: GitHubAppHandler,
    ) -> None:
        mock_select.side_effect = [
            MagicMock(ask=MagicMock(return_value="install")),  # First choice: install
            MagicMock(ask=MagicMock(return_value="yes")),  # Confirmation: yes
        ]

        result = handler.prompt_installation()

        assert result is True
        mock_webbrowser.assert_called_once_with(
            "https://github.com/apps/ar-infra-bot/installations/new"
        )

    @patch("src.ar_infra.infrastructure.processor.github_app.select")
    def test_prompt_installation_already_installed(
        self,
        mock_select: Mock,
        handler: GitHubAppHandler,
    ) -> None:
        mock_select.return_value = MagicMock(ask=MagicMock(return_value="already_installed"))

        result = handler.prompt_installation()

        assert result is True

    @patch("src.ar_infra.infrastructure.processor.github_app.select")
    def test_prompt_installation_skip(
        self,
        mock_select: Mock,
        handler: GitHubAppHandler,
    ) -> None:
        mock_select.return_value = MagicMock(ask=MagicMock(return_value="skip"))

        result = handler.prompt_installation()

        assert result is False

    @patch("src.ar_infra.infrastructure.processor.github_app.webbrowser.open")
    @patch("src.ar_infra.infrastructure.processor.github_app.select")
    def test_prompt_installation_install_then_decline_completion(
        self,
        mock_select: Mock,
        mock_webbrowser: Mock,
        handler: GitHubAppHandler,
    ) -> None:
        mock_select.side_effect = [
            MagicMock(ask=MagicMock(return_value="install")),
            MagicMock(ask=MagicMock(return_value="no")),
        ]

        result = handler.prompt_installation()

        assert result is False
        mock_webbrowser.assert_called_once()

    @patch("src.ar_infra.infrastructure.processor.github_app.select")
    def test_prompt_installation_cancelled(
        self,
        mock_select: Mock,
        handler: GitHubAppHandler,
    ) -> None:
        mock_select.return_value = MagicMock(ask=MagicMock(return_value=None))

        with pytest.raises(KeyboardInterrupt):
            handler.prompt_installation()

    @patch("src.ar_infra.infrastructure.processor.github_app.webbrowser.open")
    @patch("src.ar_infra.infrastructure.processor.github_app.select")
    def test_browser_open_failure_handled(
        self,
        mock_select: Mock,
        mock_webbrowser: Mock,
        handler: GitHubAppHandler,
    ) -> None:
        """Test that browser open failures are handled gracefully."""
        mock_webbrowser.side_effect = OSError("Browser not available")
        mock_select.side_effect = [
            MagicMock(ask=MagicMock(return_value="install")),
            MagicMock(ask=MagicMock(return_value="yes")),
        ]

        result = handler.prompt_installation()

        assert result is True

    @patch("src.ar_infra.infrastructure.processor.github_app.select")
    def test_confirm_installation_cancelled(
        self,
        mock_select: Mock,
        handler: GitHubAppHandler,
    ) -> None:
        mock_select.return_value = MagicMock(ask=MagicMock(return_value=None))

        with pytest.raises(KeyboardInterrupt):
            handler._confirm_installation_completed()

    def test_check_installation_optional_with_skip(
        self,
        handler: GitHubAppHandler,
    ) -> None:
        result = handler.check_installation_optional(skip_prompt=True)

        assert result is False

    @patch("src.ar_infra.infrastructure.processor.github_app.select")
    def test_check_installation_optional_without_skip(
        self,
        mock_select: Mock,
        handler: GitHubAppHandler,
    ) -> None:
        mock_select.return_value = MagicMock(ask=MagicMock(return_value="already_installed"))

        result = handler.check_installation_optional(skip_prompt=False)

        assert result is True
        mock_select.assert_called_once()
