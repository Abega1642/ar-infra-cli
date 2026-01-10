"""GitHub template fetcher."""

import gc
import platform
import re
import shutil
import stat
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final
from urllib.parse import urlparse

import git

from src.ar_infra.infrastructure.fs_utilities import try_rename_locked_directory
from src.ar_infra.infrastructure.template.exception import (
    InvalidTemplateError,
    SecurityViolationError,
    TemplateFetchError,
)
from src.ar_infra.logger import get_logger


log = get_logger()

BLOCKED_HOSTS: Final[set[str]] = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",  # nosec B104
    "169.254.169.254",
}

GITHUB_URL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(https://github\.com/|git@github\.com:)[\w\-]+/[\w\-]+(\.git)?$"
)


class GitHubTemplateFetcher:
    """Fetch Spring Boot templates from GitHub repositories."""

    def fetch(
        self,
        url: str,
        destination: Path,
        *,
        use_cache: bool = True,
    ) -> str:
        log.info("Fetching template from: %s", url)
        log.info("Destination: %s", destination.absolute())

        self._validate_url(url)

        if use_cache and destination.exists():
            log.info("Using cached template")
            return self._process_template(destination)

        return self._fetch_to_destination(url, destination)

    def _fetch_to_destination(self, url: str, destination: Path) -> str:
        temp_dir = None

        try:
            temp_dir = self._create_temp_directory()
            log.info("Cloning to temporary directory: %s", temp_dir)

            self._clone_repository(url, temp_dir)
            self._process_template(temp_dir)

            log.info("Template validated, moving to destination...")
            self._move_to_destination(temp_dir, destination)
            log.info("Template successfully installed")

            return self._detect_placeholder_package(destination)

        except Exception:
            log.exception("Error during template fetch")

            if temp_dir and temp_dir.exists():
                log.info("Cleaning up temporary directory after error...")
                try:
                    self._safe_rmtree(temp_dir)
                    log.info("Cleanup completed")
                except OSError as cleanup_error:
                    log.warning("Failed to cleanup temp directory: %s", cleanup_error)

            raise

    def _create_temp_directory(self) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="ar-infra-template-"))
        log.info("Created temporary directory: %s", temp_dir)
        return temp_dir

    def _move_to_destination(self, source: Path, destination: Path) -> None:
        try:
            if destination.exists():
                log.info("Removing existing destination: %s", destination)
                self._safe_rmtree(destination)

            log.info("Moving template: %s -> %s", source, destination)

            shutil.copytree(str(source), str(destination))
            log.info("Template copied successfully")

            log.info("Cleaning up temporary directory...")
            self._safe_rmtree(source)
            log.info("Cleanup completed")

        except (OSError, shutil.Error) as e:
            log.exception(
                "Failed to move template to destination. Source: %s, Destination: %s",
                source,
                destination,
            )
            raise TemplateFetchError(f"Failed to move template to destination: {e}") from e

    def _clone_repository(self, url: str, destination: Path) -> None:
        log.info("Starting git clone (this may take a moment)...")

        try:
            git.Repo.clone_from(url, str(destination), depth=1)
            log.info("Clone completed successfully")
            self._wait_for_git_locks()

        except git.exc.GitCommandError as e:
            self._handle_clone_error(url, e)

        except (OSError, RuntimeError) as e:
            self._handle_unexpected_error(url, e)

    def _wait_for_git_locks(self) -> None:
        if platform.system() == "Windows":
            log.info("Windows: waiting for Git to release file locks...")
            time.sleep(10)

    def _handle_clone_error(self, url: str, error: git.exc.GitCommandError) -> None:
        log.error("Git clone failed!")
        log.error("URL: %s", url)
        log.error("Exit code: %s", error.status)
        log.error("Command: %s", error.command)

        if error.stderr:
            log.error("Error output: %s", error.stderr)
        if error.stdout:
            log.error("Standard output: %s", error.stdout)

        hint = self._get_error_hint(error)
        raise TemplateFetchError(f"Git clone failed: {hint}. Check logs for details.") from error

    def _handle_unexpected_error(self, url: str, error: Exception) -> None:
        log.error("Unexpected error: %s", type(error).__name__)
        log.error("Message: %s", error)

        raise TemplateFetchError(f"Failed to fetch template from {url}: {error}") from error

    def _get_error_hint(self, error: git.exc.GitCommandError) -> str:
        error_text = str(error.stderr or error.stdout or "").lower()

        if "could not resolve" in error_text or "name resolution" in error_text:
            return "Network/DNS issue - check internet connection"
        if "permission denied" in error_text or "access denied" in error_text:
            return "Permission issue - check repository access"
        if "repository not found" in error_text:
            return "Repository not found or inaccessible"
        if "authentication failed" in error_text:
            return "Authentication failed - check credentials"

        return "Git error"

    def _process_template(self, template_dir: Path) -> str:
        log.info("Validating template structure...")
        self._validate_template_structure(template_dir)

        log.info("Detecting placeholder package...")
        package = self._detect_placeholder_package(template_dir)
        log.info("Template validated with package: %s", package)

        return package

    def _safe_rmtree(self, path: Path, max_retries: int = 10) -> None:
        for attempt in range(max_retries):
            try:
                if platform.system() == "Windows":
                    gc.collect()

                shutil.rmtree(path, onerror=self._handle_readonly_file)

            except OSError as e:
                if attempt < max_retries - 1:
                    log.warning("Retry %d/%d: %s", attempt + 1, max_retries, e)
                    time.sleep(8)
                else:
                    self._handle_locked_directory(path, max_retries, e)
            else:
                return

    def _handle_readonly_file(self, func: Callable[[str], None], path_str: str, _exc: Any) -> None:
        if platform.system() == "Windows":
            Path(path_str).chmod(stat.S_IWRITE)
            func(path_str)

    def _handle_locked_directory(self, path: Path, max_retries: int, error: Exception) -> None:
        if platform.system() == "Windows" and self._try_rename_locked_dir(path, max_retries):
            return

        log.error("Failed to remove directory after %d attempts", max_retries)
        raise error

    def _try_rename_locked_dir(self, path: Path, max_retries: int) -> bool:
        return try_rename_locked_directory(path, max_retries)

    def _validate_url(self, url: str) -> None:
        if not GITHUB_URL_PATTERN.match(url):
            log.error("Invalid URL format: %s", url)
            raise SecurityViolationError("Only GitHub URLs are allowed")

        parsed = urlparse(url)

        if parsed.scheme and parsed.scheme not in ["https", "git"]:
            log.error("Invalid scheme: %s", parsed.scheme)
            raise SecurityViolationError(f"Invalid URL scheme: {parsed.scheme}")

        if parsed.hostname and parsed.hostname.lower() in BLOCKED_HOSTS:
            log.error("Blocked hostname: %s", parsed.hostname)
            raise SecurityViolationError(f"Blocked hostname: {parsed.hostname}")

    def _validate_template_structure(self, template_dir: Path) -> None:
        if not (template_dir / "build.gradle").exists():
            log.error("Missing build.gradle")
            raise InvalidTemplateError("build.gradle not found in template")

        src_main_java = template_dir / "src" / "main" / "java"
        if not src_main_java.exists():
            log.error("Missing src/main/java directory")
            raise InvalidTemplateError("src/main/java directory not found in template")

    def _detect_placeholder_package(self, template_dir: Path) -> str:
        src_main_java = template_dir / "src" / "main" / "java"

        for path in src_main_java.rglob("*"):
            if path.is_dir() and self._is_base_package(path):
                relative = path.relative_to(src_main_java)
                return relative.as_posix().replace("/", ".")

        log.error("Could not detect base package in template")
        raise InvalidTemplateError(
            "Could not detect placeholder package in template. "
            "Expected structure: src/main/java/com/example/arinfra"
        )

    def _is_base_package(self, path: Path) -> bool:
        java_files = list(path.glob("*.java"))
        if not java_files:
            return False

        subdirs = [d for d in path.iterdir() if d.is_dir()]
        return len(subdirs) > 0 or len(java_files) > 0
