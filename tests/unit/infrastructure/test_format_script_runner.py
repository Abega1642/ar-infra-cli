"""Tests for FormatScriptRunner."""

import re
import subprocess
from unittest.mock import patch

import pytest

from src.ar_infra.infrastructure.processor.format_script_runner import (
    FormatScriptRunner,
)


class TestFormatScriptRunner:
    @pytest.fixture
    def runner(self):
        return FormatScriptRunner()

    @pytest.fixture
    def mock_project_root(self, tmp_path):
        project_root = tmp_path / "project"
        project_root.mkdir(parents=True)
        return project_root

    # -------------------------------------------------------------------
    # Unix/Linux/macOS Tests
    # -------------------------------------------------------------------

    @pytest.mark.parametrize("system_name", ["Linux", "Darwin"])
    def test_unix_format_executes_when_script_exists_and_executable(
        self, runner, mock_project_root, system_name
    ):
        script_path = mock_project_root / "format.sh"
        script_path.touch(mode=0o755)

        with (
            patch("platform.system", return_value=system_name),
            patch("subprocess.run") as mock_run,
        ):
            runner.run(mock_project_root)

            mock_run.assert_called_once_with(
                [str(script_path)],
                cwd=mock_project_root,
                check=True,
            )

    @pytest.mark.parametrize("system_name", ["Linux", "Darwin"])
    def test_unix_format_skips_when_script_missing(self, runner, mock_project_root, system_name):
        with (
            patch("platform.system", return_value=system_name),
            patch("subprocess.run") as mock_run,
        ):
            runner.run(mock_project_root)

            mock_run.assert_not_called()

    @pytest.mark.parametrize("system_name", ["Linux", "Darwin"])
    def test_unix_format_raises_when_script_not_executable(
        self, runner, mock_project_root, system_name
    ):
        script_path = mock_project_root / "format.sh"
        script_path.touch(mode=0o644)  # Not executable

        with (
            patch("platform.system", return_value=system_name),
            pytest.raises(RuntimeError, match=re.escape("format.sh is not executable")),
        ):
            runner.run(mock_project_root)

    @pytest.mark.parametrize("system_name", ["Linux", "Darwin"])
    def test_unix_format_raises_when_script_is_directory(
        self, runner, mock_project_root, system_name
    ):
        (mock_project_root / "format.sh").mkdir()

        with (
            patch("platform.system", return_value=system_name),
            pytest.raises(RuntimeError, match=re.escape("format.sh exists but is not a file")),
        ):
            runner.run(mock_project_root)

    @pytest.mark.parametrize("system_name", ["Linux", "Darwin"])
    def test_unix_format_raises_when_script_fails(self, runner, mock_project_root, system_name):
        script_path = mock_project_root / "format.sh"
        script_path.touch(mode=0o755)

        with (
            patch("platform.system", return_value=system_name),
            patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(1, "format.sh"),
            ),
            pytest.raises(RuntimeError, match=re.escape("Project formatting failed")),
        ):
            runner.run(mock_project_root)

    @pytest.mark.parametrize("system_name", ["Linux", "Darwin"])
    def test_unix_format_refuses_script_outside_project_root(self, runner, tmp_path, system_name):
        project_root = tmp_path / "project"
        project_root.mkdir()

        outside_script = tmp_path / "outside" / "format.sh"
        outside_script.parent.mkdir()
        outside_script.touch(mode=0o755)

        # Create symlink inside project pointing to outside script
        script_link = project_root / "format.sh"
        script_link.symlink_to(outside_script)

        # Verify the test setup: symlink should resolve outside project root
        assert script_link.resolve() == outside_script
        assert not script_link.resolve().is_relative_to(project_root)

        with (
            patch("platform.system", return_value=system_name),
            pytest.raises(
                RuntimeError, match=re.escape("Refusing to execute format.sh outside project root")
            ),
        ):
            runner.run(project_root)

    # -------------------------------------------------------------------
    # Windows Tests - Batch File (.bat)
    # -------------------------------------------------------------------

    def test_windows_executes_bat_when_available(self, runner, mock_project_root):
        script_path = mock_project_root / "format.bat"
        script_path.touch()

        with (
            patch("platform.system", return_value="Windows"),
            patch("shutil.which", return_value="cmd.exe"),
            patch("subprocess.run") as mock_run,
        ):
            runner.run(mock_project_root)

            mock_run.assert_called_once_with(
                ["cmd.exe", "/c", str(script_path)],
                cwd=mock_project_root,
                check=True,
            )

    def test_windows_prefers_bat_over_sh_when_both_exist(self, runner, mock_project_root):
        bat_path = mock_project_root / "format.bat"
        sh_path = mock_project_root / "format.sh"
        bat_path.touch()
        sh_path.touch()

        with (
            patch("platform.system", return_value="Windows"),
            patch("shutil.which", return_value="cmd.exe"),  # Return cmd.exe for which("cmd")
            patch("subprocess.run") as mock_run,
        ):
            runner.run(mock_project_root)

            # Should call bat, not sh
            mock_run.assert_called_once_with(
                ["cmd.exe", "/c", str(bat_path)],
                cwd=mock_project_root,
                check=True,
            )

    def test_windows_bat_raises_when_execution_fails(self, runner, mock_project_root):
        script_path = mock_project_root / "format.bat"
        script_path.touch()

        with (
            patch("platform.system", return_value="Windows"),
            patch("shutil.which", return_value="cmd.exe"),
            patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(1, "format.bat"),
            ),
            pytest.raises(RuntimeError, match=re.escape("Project formatting failed")),
        ):
            runner.run(mock_project_root)

    def test_windows_bat_refuses_script_outside_project_root(self, runner, tmp_path):
        project_root = tmp_path / "project"
        project_root.mkdir()

        outside_script = tmp_path / "outside" / "format.bat"
        outside_script.parent.mkdir()
        outside_script.touch()

        script_link = project_root / "format.bat"
        script_link.symlink_to(outside_script)

        assert not script_link.resolve().is_relative_to(project_root)

        with (
            patch("platform.system", return_value="Windows"),
            patch("shutil.which", return_value="cmd.exe"),
            pytest.raises(
                RuntimeError,
                match=re.escape("Refusing to execute format.bat outside project root"),
            ),
        ):
            runner.run(project_root)

    # -------------------------------------------------------------------
    # Windows Tests - Bash Script (.sh) with Bash Available
    # -------------------------------------------------------------------

    def test_windows_executes_sh_with_bash_when_bat_unavailable(self, runner, mock_project_root):
        script_path = mock_project_root / "format.sh"
        script_path.touch()

        with (
            patch("platform.system", return_value="Windows"),
            patch("shutil.which", return_value="/usr/bin/bash"),
            patch("subprocess.run") as mock_run,
        ):
            runner.run(mock_project_root)

            mock_run.assert_called_once_with(
                ["/usr/bin/bash", str(script_path)],
                cwd=mock_project_root,
                check=True,
            )

    def test_windows_sh_with_bash_raises_when_execution_fails(self, runner, mock_project_root):
        script_path = mock_project_root / "format.sh"
        script_path.touch()

        with (
            patch("platform.system", return_value="Windows"),
            patch("shutil.which", return_value="/usr/bin/bash"),
            patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(1, "format.sh"),
            ),
            pytest.raises(RuntimeError, match=re.escape("Project formatting failed")),
        ):
            runner.run(mock_project_root)

    def test_windows_bash_refuses_script_outside_project_root(self, runner, tmp_path):
        project_root = tmp_path / "project"
        project_root.mkdir()

        outside_script = tmp_path / "outside" / "format.sh"
        outside_script.parent.mkdir()
        outside_script.touch()

        # Create symlink inside project pointing to outside script
        script_link = project_root / "format.sh"
        script_link.symlink_to(outside_script)

        assert not script_link.resolve().is_relative_to(project_root)

        with (
            patch("platform.system", return_value="Windows"),
            patch("shutil.which", return_value="/usr/bin/bash"),
            pytest.raises(
                RuntimeError, match=re.escape("Refusing to execute format.sh outside project root")
            ),
        ):
            runner.run(project_root)

    # -------------------------------------------------------------------
    # Windows Tests - No Bash Available
    # -------------------------------------------------------------------

    def test_windows_raises_when_only_sh_exists_and_no_bash(self, runner, mock_project_root):
        script_path = mock_project_root / "format.sh"
        script_path.touch()

        with (
            patch("platform.system", return_value="Windows"),
            patch("shutil.which", return_value=None),  # bash not available
            pytest.raises(RuntimeError, match=re.escape("Cannot execute format.sh without bash")),
        ):
            runner.run(mock_project_root)

    def test_windows_skips_when_no_scripts_exist(self, runner, mock_project_root):
        with (
            patch("platform.system", return_value="Windows"),
            patch("subprocess.run") as mock_run,
        ):
            runner.run(mock_project_root)

            mock_run.assert_not_called()

    # -------------------------------------------------------------------
    # Edge Cases and Integration Tests
    # -------------------------------------------------------------------

    def test_windows_checks_bat_existence_before_sh(self, runner, mock_project_root):
        sh_path = mock_project_root / "format.sh"
        sh_path.touch()

        with (
            patch("platform.system", return_value="Windows"),
            patch("shutil.which") as mock_which,
            patch("subprocess.run") as mock_run,
        ):
            # Bash is available, so .sh should be executed
            mock_which.return_value = "/usr/bin/bash"
            runner.run(mock_project_root)

            # which() should have been called to check for bash
            mock_which.assert_called_once_with("bash")

            # subprocess should execute with bash
            mock_run.assert_called_once_with(
                ["/usr/bin/bash", str(sh_path)],
                cwd=mock_project_root,
                check=True,
            )

    @pytest.mark.parametrize(
        ("system_name", "script_name", "expected_called"),
        [
            ("Linux", "format.sh", True),
            ("Darwin", "format.sh", True),
            ("Windows", "format.bat", True),
            ("Windows", "format.sh", True),  # with bash available
        ],
    )
    def test_cross_platform_script_execution(
        self, runner, mock_project_root, system_name, script_name, expected_called
    ):
        script_path = mock_project_root / script_name

        if script_name.endswith(".sh"):
            script_path.touch(mode=0o755)
        else:
            script_path.touch()

        which_return = None
        if system_name == "Windows":
            which_return = "cmd.exe" if script_name.endswith(".bat") else "/usr/bin/bash"

        with (
            patch("platform.system", return_value=system_name),
            patch("shutil.which", return_value=which_return),
            patch("subprocess.run") as mock_run,
        ):
            runner.run(mock_project_root)

            if expected_called:
                assert mock_run.call_count == 1
            else:
                mock_run.assert_not_called()

    def test_error_message_includes_helpful_context(self, runner, mock_project_root):
        script_path = mock_project_root / "format.sh"
        script_path.touch()

        with (
            patch("platform.system", return_value="Windows"),
            patch("shutil.which", return_value=None),
            pytest.raises(RuntimeError) as exc_info,
        ):
            runner.run(mock_project_root)

        error_message = str(exc_info.value)
        assert "bash" in error_message.lower()
        assert "format.sh" in error_message.lower()
