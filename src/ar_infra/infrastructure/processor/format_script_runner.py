"""Runner for project format script."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from typing import TYPE_CHECKING

from src.ar_infra.logger import get_logger


if TYPE_CHECKING:
    from pathlib import Path


log = get_logger(__name__)


class FormatScriptRunner:
    """Run the format script at the root of a generated project."""

    _SCRIPT_NAME_UNIX = "format.sh"
    _SCRIPT_NAME_WINDOWS = "format.bat"

    def run(self, project_root: Path) -> None:
        is_windows = platform.system() == "Windows"

        if is_windows:
            self._run_windows_format(project_root)
        else:
            self._run_unix_format(project_root)

    def _run_windows_format(self, project_root: Path) -> None:
        script_sh = project_root / self._SCRIPT_NAME_UNIX
        script_bat = project_root / self._SCRIPT_NAME_WINDOWS

        has_sh = script_sh.exists() and script_sh.is_file()
        has_bat = script_bat.exists() and script_bat.is_file()

        if not has_sh and not has_bat:
            log.info("No format.sh or format.bat found at project root — skipping formatting")
            return

        # Prefer .bat on Windows, but try .sh if bash is available
        if has_bat:
            self._execute_windows_batch(script_bat, project_root)
        elif has_sh:
            self._handle_sh_on_windows(script_sh, project_root)

    def _handle_sh_on_windows(self, script_sh: Path, project_root: Path) -> None:
        bash_path = shutil.which("bash")
        if bash_path:
            log.info("format.bat not found, but bash is available. Attempting to run format.sh")
            self._execute_with_bash(script_sh, project_root, bash_path)
        else:
            log.error(
                "format.bat not found and bash is not available in PATH. "
                "Please install Git for Windows or ensure format.bat exists."
            )
            raise RuntimeError(
                "Cannot execute format.sh without bash. "
                "Install Git for Windows or provide format.bat"
            )

    def _run_unix_format(self, project_root: Path) -> None:
        script_path = project_root / self._SCRIPT_NAME_UNIX

        if not script_path.exists():
            log.info("No format.sh found at project root — skipping formatting")
            return

        if not script_path.is_file():
            raise RuntimeError("format.sh exists but is not a file")

        if not script_path.resolve().is_relative_to(project_root):
            raise RuntimeError("Refusing to execute format.sh outside project root")

        if os.name != "nt" and not script_path.stat().st_mode & 0o111:
            raise RuntimeError("format.sh is not executable")

        log.info("Running project formatter: %s", script_path)

        try:
            subprocess.run(  # noqa: S603
                [str(script_path)],
                cwd=project_root,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            log.exception("format.sh failed with exit code %s", exc.returncode)
            raise RuntimeError("Project formatting failed") from exc

    def _execute_windows_batch(self, script_path: Path, project_root: Path) -> None:
        if not script_path.resolve().is_relative_to(project_root):
            raise RuntimeError("Refusing to execute format.bat outside project root")

        log.info("Running project formatter: %s", script_path)

        try:
            cmd_path = shutil.which("cmd") or "cmd.exe"
            subprocess.run(  # noqa: S603
                [cmd_path, "/c", str(script_path)],
                cwd=project_root,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            log.exception("format.bat failed with exit code %s", exc.returncode)
            raise RuntimeError("Project formatting failed") from exc

    def _execute_with_bash(self, script_path: Path, project_root: Path, bash_path: str) -> None:
        if not script_path.resolve().is_relative_to(project_root):
            raise RuntimeError("Refusing to execute format.sh outside project root")

        log.info("Running project formatter with bash: %s", script_path)

        try:
            subprocess.run(  # noqa: S603
                [bash_path, str(script_path)],
                cwd=project_root,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            log.exception("format.sh failed with exit code %s", exc.returncode)
            raise RuntimeError("Project formatting failed") from exc
