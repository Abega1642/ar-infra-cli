"""Platform-specific path constants for security validation.

This module contains all dangerous and safe path definitions for
cross-platform path security validation. Paths are organized by
operating system and validation type.
"""

from typing import Final


# ===>  UNIX/Linux Dangerous Paths

DANGEROUS_UNIX_EXACT_PATHS: Final[frozenset[str]] = frozenset(
    {
        "/",
        "/bin",
        "/boot",
        "/dev",
        "/etc",
        "/lib",
        "/lib64",
        "/proc",
        "/root",
        "/sbin",
        "/sys",
        "/usr",
        "/usr/bin",
        "/usr/sbin",
        "/usr/lib",
        "/usr/lib64",
    }
)

DANGEROUS_UNIX_PREFIX_PATHS: Final[frozenset[str]] = frozenset(
    {
        "/bin/",
        "/boot/",
        "/dev/",
        "/etc/",
        "/lib/",
        "/lib64/",
        "/proc/",
        "/root/",
        "/sbin/",
        "/sys/",
        "/usr/",
        "/usr/bin/",
        "/usr/sbin/",
        "/usr/lib/",
        "/usr/lib64/",
    }
)

# ===>  Windows Dangerous Paths

DANGEROUS_WINDOWS_EXACT_PATHS: Final[frozenset[str]] = frozenset(
    {
        "c:\\",
        "c:/",
        "c:\\windows",
        "c:/windows",
        "c:\\windows\\system32",
        "c:/windows/system32",
        "c:\\program files",
        "c:/program files",
        "c:\\program files (x86)",
        "c:/program files (x86)",
        "c:\\programdata",
        "c:/programdata",
    }
)

DANGEROUS_WINDOWS_PREFIX_PATHS: Final[frozenset[str]] = frozenset(
    {
        "c:\\windows\\",
        "c:/windows/",
        "c:\\program files\\",
        "c:/program files/",
        "c:\\program files (x86)\\",
        "c:/program files (x86)/",
        "c:\\programdata\\",
        "c:/programdata/",
    }
)

# ===>  macOS Dangerous Paths

DANGEROUS_MACOS_EXACT_PATHS: Final[frozenset[str]] = frozenset(
    {
        "/System",
        "/Library",
        "/Applications",
        "/private/etc",
        "/etc",  # May symlink to /private/etc
    }
)

DANGEROUS_MACOS_PREFIX_PATHS: Final[frozenset[str]] = frozenset(
    {
        "/System/",
        "/Library/",
        "/Applications/",
        "/private/etc/",
        "/etc/",  # Covers both /etc/ and symlinked /etc -> /private/etc
    }
)


# ===>  Safe Paths (Exceptions to dangerous path rules)

# These paths are under typically dangerous prefixes but are safe for use
SAFE_UNIX_PATHS: Final[frozenset[str]] = frozenset(
    {
        "/tmp",  # noqa: S108
        "/var/tmp",  # noqa: S108
    }
)

SAFE_UNIX_PREFIX_PATHS: Final[frozenset[str]] = frozenset(
    {
        "/tmp/",  # noqa: S108
        "/var/tmp/",  # noqa: S108
    }
)

# On macOS, temporary directories are under /private/var but are safe
SAFE_MACOS_PATHS: Final[frozenset[str]] = frozenset(
    {
        "/tmp",  # noqa: S108
        "/var/tmp",  # noqa: S108
        "/private/tmp",
        "/private/var/tmp",
    }
)

SAFE_MACOS_PREFIX_PATHS: Final[frozenset[str]] = frozenset(
    {
        "/tmp/",  # noqa: S108
        "/var/tmp/",  # noqa: S108
        "/private/tmp/",
        "/private/var/tmp/",
        "/private/var/folders/",  # macOS temporary directory structure
    }
)
