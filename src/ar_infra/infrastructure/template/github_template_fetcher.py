"""Secure GitHub template fetcher."""

import re
import shutil
from pathlib import Path
from typing import Final
from urllib.parse import urlparse

import git

from src.ar_infra.infrastructure.template.exception import (
    InvalidTemplateError,
    SecurityViolationError,
    TemplateFetchError,
)


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
        """
        Fetch template from GitHub URL.

        Returns:
            Detected placeholder package name (e.g., 'com.example.arinfra').
        """
        self._validate_url(url)

        if use_cache and destination.exists():
            self._validate_template_structure(destination)
            return self._detect_placeholder_package(destination)

        if destination.exists():
            shutil.rmtree(destination)

        try:
            git.Repo.clone_from(url, str(destination), depth=1)
        except Exception as e:
            if destination.exists():
                shutil.rmtree(destination)
            raise TemplateFetchError(f"Failed to fetch template from {url}: {e}") from e

        self._validate_template_structure(destination)
        return self._detect_placeholder_package(destination)

    def _validate_url(self, url: str) -> None:
        if not GITHUB_URL_PATTERN.match(url):
            raise SecurityViolationError("Only GitHub URLs are allowed")

        parsed = urlparse(url)

        if parsed.scheme and parsed.scheme not in ["https", "git"]:
            raise SecurityViolationError(f"Invalid URL scheme: {parsed.scheme}")

        if parsed.hostname and parsed.hostname.lower() in BLOCKED_HOSTS:
            raise SecurityViolationError(f"Blocked hostname: {parsed.hostname}")

    def _validate_template_structure(self, template_dir: Path) -> None:
        if not (template_dir / "build.gradle").exists():
            raise InvalidTemplateError("build.gradle not found in template")

        src_main_java = template_dir / "src" / "main" / "java"
        if not src_main_java.exists():
            raise InvalidTemplateError("src/main/java directory not found in template")

    def _detect_placeholder_package(self, template_dir: Path) -> str:
        src_main_java = template_dir / "src" / "main" / "java"

        for path in src_main_java.rglob("*"):
            if path.is_dir() and self._looks_like_base_package(path):
                relative = path.relative_to(src_main_java)
                return relative.as_posix().replace("/", ".")

        raise InvalidTemplateError(
            "Could not detect placeholder package in template. "
            "Expected structure: src/main/java/com/example/arinfra"
        )

    def _looks_like_base_package(self, path: Path) -> bool:
        java_files = list(path.glob("*.java"))
        if not java_files:
            return False

        subdirs = [d for d in path.iterdir() if d.is_dir()]
        return len(subdirs) > 0 or len(java_files) > 0
