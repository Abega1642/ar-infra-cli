"""REST exception handler manager for feature-based exception pruning."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from src.ar_infra.domain.enums.template_feature import TemplateFeature


if TYPE_CHECKING:
    from pathlib import Path


class RestExceptionHandlerManager:
    """Prune ApiExceptionHandler.java based on enabled infrastructure features."""

    _FEATURE_EXCEPTION_MAPPING: Final[dict[TemplateFeature, set[str]]] = {
        TemplateFeature.S3_BUCKET: {
            "BucketHealthCheckException",
            "BucketOperationException",
            "DirectoryUploadException",
        },
        TemplateFeature.EMAIL: {
            "EmailHealthCheckException",
            "EmailSendException",
        },
        TemplateFeature.POSTGRESQL: {
            "EntityNotFoundException",
            "ConstraintViolationException",
            "DataIntegrityViolationException",
        },
    }

    def apply_feature_selection(
        self,
        template_dir: Path,
        enabled_features: set[TemplateFeature],
    ) -> None:
        handler_path = self._find_exception_handler(template_dir)
        if handler_path is None:
            return

        disabled_exceptions = self._get_disabled_exceptions(enabled_features)
        if not disabled_exceptions:
            return

        content = handler_path.read_text(encoding="utf-8")
        filtered = self._remove_exception_handlers(content, disabled_exceptions)
        handler_path.write_text(filtered, encoding="utf-8")

    def _get_disabled_exceptions(self, enabled_features: set[TemplateFeature]) -> set[str]:
        disabled_features = set(self._FEATURE_EXCEPTION_MAPPING) - enabled_features
        return {
            exc for feature in disabled_features for exc in self._FEATURE_EXCEPTION_MAPPING[feature]
        }

    @staticmethod
    def _find_exception_handler(template_dir: Path) -> Path | None:
        matches = list(template_dir.rglob("ApiExceptionHandler.java"))
        if not matches:
            return None
        if len(matches) > 1:
            raise RuntimeError("Multiple ApiExceptionHandler.java files found")
        return matches[0]

    @staticmethod
    def _remove_exception_handlers(content: str, disabled_exceptions: set[str]) -> str:
        """Remove exception handler methods based on disabled exceptions."""
        lines = content.splitlines(keepends=True)

        methods_to_remove = RestExceptionHandlerManager._find_methods_to_remove(
            lines, disabled_exceptions
        )

        if not methods_to_remove:
            return content

        for start_line, end_line in sorted(methods_to_remove, reverse=True):
            del lines[start_line : end_line + 1]

        return "".join(lines)

    @staticmethod
    def _extract_exception_classes(annotation_line: str) -> set[str]:
        """Extract exception class names from @ExceptionHandler annotation."""
        exceptions: set[str] = set()

        match = re.search(r"@ExceptionHandler\s*\((.*?)\)", annotation_line)
        if not match:
            return exceptions

        content = match.group(1)

        exception_matches = re.findall(r"(\w+Exception)\.class", content)
        exceptions.update(exception_matches)

        return exceptions

    @staticmethod
    def _find_methods_to_remove(
        lines: list[str], disabled_exceptions: set[str]
    ) -> list[tuple[int, int]]:
        """Find the line ranges of methods that should be removed."""
        methods_to_remove: list[tuple[int, int]] = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            if not line.startswith("@ExceptionHandler"):
                i += 1
                continue

            next_index = RestExceptionHandlerManager._process_exception_handler(
                lines, i, disabled_exceptions, methods_to_remove
            )
            i = next_index

        return methods_to_remove

    @staticmethod
    def _process_exception_handler(
        lines: list[str],
        current_line: int,
        disabled_exceptions: set[str],
        methods_to_remove: list[tuple[int, int]],
    ) -> int:
        """Process an @ExceptionHandler annotation and determine if method should be removed."""
        line = lines[current_line].strip()
        handled_exceptions = RestExceptionHandlerManager._extract_exception_classes(line)

        if "Exception" in handled_exceptions:
            return current_line + 1

        if not handled_exceptions & disabled_exceptions:
            return current_line + 1

        start_line = RestExceptionHandlerManager._find_method_start(lines, current_line)

        end_line = RestExceptionHandlerManager._find_method_end(lines, current_line)

        methods_to_remove.append((start_line, end_line))
        return end_line + 1

    @staticmethod
    def _find_method_start(lines: list[str], annotation_line: int) -> int:
        """Find the starting line of a method by looking backwards for annotations."""
        start_line = annotation_line
        while start_line > 0 and lines[start_line - 1].strip().startswith("@"):
            start_line -= 1
        return start_line

    @staticmethod
    def _find_method_end(lines: list[str], start_line: int) -> int:
        """Find the closing brace of a method starting from the annotation line."""
        brace_depth = 0
        found_opening = False

        for i in range(start_line, len(lines)):
            closing_brace_line = RestExceptionHandlerManager._process_line_braces(
                lines[i], brace_depth, found_opening=found_opening
            )

            if closing_brace_line is not None:
                return i

            brace_depth += lines[i].count("{") - lines[i].count("}")
            if "{" in lines[i]:
                found_opening = True

        return len(lines) - 1

    @staticmethod
    def _process_line_braces(line: str, brace_depth: int, *, found_opening: bool) -> int | None:
        """Process braces in a line and return line number if method end is found."""
        for char in line:
            if char == "{":
                found_opening = True
                brace_depth += 1
            elif char == "}":
                brace_depth -= 1

                if found_opening and brace_depth == 0:
                    return 0  # Signal that we found the end

        return None
