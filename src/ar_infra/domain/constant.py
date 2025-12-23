"""Domain-level constants shared across value objects and entities."""

import re
from typing import Final


JAVA_RESERVED_KEYWORDS: Final[set[str]] = {
    "abstract",
    "assert",
    "boolean",
    "break",
    "byte",
    "case",
    "catch",
    "char",
    "class",
    "const",
    "continue",
    "default",
    "do",
    "double",
    "else",
    "enum",
    "extends",
    "final",
    "finally",
    "float",
    "for",
    "goto",
    "if",
    "implements",
    "import",
    "instanceof",
    "int",
    "interface",
    "long",
    "native",
    "new",
    "package",
    "private",
    "protected",
    "public",
    "return",
    "short",
    "static",
    "strictfp",
    "super",
    "switch",
    "synchronized",
    "this",
    "throw",
    "throws",
    "transient",
    "try",
    "void",
    "volatile",
    "while",
    "true",
    "false",
    "null",
}

MAX_GROUP_ID_LENGTH: Final[int] = 255
MAX_SEGMENT_LENGTH: Final[int] = 50
MAX_ARTIFACT_ID_LENGTH: Final[int] = 50
MIN_ARTIFACT_ID_LENGTH: Final[int] = 3
MAX_FILE_SIZE: Final[int] = 5 * 1024 * 1024


VALID_SEGMENT_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*$",
)

VALID_ARTIFACT_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$",
)

SEMANTIC_VERSION_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9._-]+))?$",
)

DANGEROUS_CHARACTERS = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]

MALICIOUS_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"System\.exit\("),
    re.compile(r"Runtime\.getRuntime\(\)"),
    re.compile(r"ProcessBuilder"),
    re.compile(r"\.\.\/\.\.\/"),
    re.compile(r"exec\("),
    re.compile(r"`[^`]+`"),
    re.compile(r"\$\([^\)]+\)"),
]

DEPENDENCY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(implementation|testImplementation|runtimeOnly|compileOnly|"
    r"annotationProcessor|testRuntimeOnly)\s*\(?\s*['\"]([^'\"]+)['\"]",
    re.MULTILINE | re.DOTALL,
)

PLUGIN_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"id\s+['\"]([^'\"]+)['\"]\s*(?:version\s+['\"]([^'\"]+)['\"])?",
)

JAVA_VERSION_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"sourceCompatibility\s*=\s*['\"]?(\d+)['\"]?",
)

VERSION_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"version\s*=\s*['\"]([^'\"]+)['\"]",
)

GROUP_PATTERN: Final[re.Pattern[str]] = re.compile(r"group\s*=\s*['\"]([^'\"]+)['\"]")
