"""Runner for project format.sh script."""

from __future__ import annotations

import platform
import shutil
import subprocess
from typing import TYPE_CHECKING

from src.ar_infra.logger import get_logger


if TYPE_CHECKING:
    from pathlib import Path


log = get_logger(__name__)


class FormatScriptRunner:
    """Run the format.sh script at the root of a generated project."""

    _SCRIPT_NAME = "format.sh"

    def run(self, project_root: Path) -> None:
        """Locate and execute ./format.sh.

        :param project_root: Root directory of the generated project
        """
        script_path = project_root / self._SCRIPT_NAME

        if not script_path.exists():
            log.info("No format.sh found at project root — skipping formatting")
            return

        if not script_path.is_file():
            raise RuntimeError("format.sh exists but is not a file")

        if not script_path.is_relative_to(project_root):
            raise RuntimeError("Refusing to execute format.sh outside project root")

        is_windows = platform.system() == "Windows"

        if not is_windows and not script_path.stat().st_mode & 0o111:
            raise RuntimeError("format.sh is not executable")

        log.info("Running project formatter: %s", script_path)

        try:
            if is_windows:
                bash_path = shutil.which("bash")
                if not bash_path:
                    raise RuntimeError("bash not found in PATH")
                subprocess.run(  # noqa: S603
                    [bash_path, str(script_path)],
                    cwd=project_root,
                    check=True,
                )
            else:
                subprocess.run(  # noqa: S603
                    [str(script_path)],
                    cwd=project_root,
                    check=True,
                )
        except subprocess.CalledProcessError as exc:
            log.exception("format.sh failed with exit code %s", exc.returncode)
            raise RuntimeError("Project formatting failed") from exc
