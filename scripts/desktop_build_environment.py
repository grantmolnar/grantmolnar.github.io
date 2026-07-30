"""Define and verify the exact native desktop build toolchain."""

from __future__ import annotations

import hashlib
import importlib.metadata
import re
from collections.abc import Mapping
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DESKTOP_BUILD_REQUIREMENTS = PROJECT_ROOT / "packaging" / "desktop-build-requirements.txt"

_PLATFORM_MARKERS = {
    "linux": "linux",
    "macos": "darwin",
    "windows": "win32",
}
_REQUIREMENT_PATTERN = re.compile(
    r"^(?P<name>[a-z0-9][a-z0-9.-]*)==(?P<version>[^;\s]+)"
    r"(?:;\s*sys_platform\s*==\s*[\"'](?P<marker>linux|darwin|win32)[\"'])?$"
)


def expected_build_dependencies(platform_tag: str) -> dict[str, str]:
    """Return the exact locked build distributions for one target platform."""
    try:
        target_marker = _PLATFORM_MARKERS[platform_tag]
    except KeyError as error:
        raise ValueError(f"Unsupported desktop build platform: {platform_tag!r}.") from error

    dependencies: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        DESKTOP_BUILD_REQUIREMENTS.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _REQUIREMENT_PATTERN.fullmatch(line)
        if match is None:
            raise ValueError(
                "Desktop build requirement must be an exact distribution pin with an optional "
                f"supported sys_platform marker ({DESKTOP_BUILD_REQUIREMENTS}:{line_number})."
            )
        marker = match.group("marker")
        if marker is not None and marker != target_marker:
            continue
        distribution = match.group("name")
        if distribution in dependencies:
            raise ValueError(
                f"Duplicate desktop build requirement for {distribution!r} "
                f"({DESKTOP_BUILD_REQUIREMENTS}:{line_number})."
            )
        dependencies[distribution] = match.group("version")
    if not dependencies:
        raise ValueError(f"Desktop build lock is empty: {DESKTOP_BUILD_REQUIREMENTS}.")
    return dict(sorted(dependencies.items()))


def require_build_environment(platform_tag: str) -> dict[str, str]:
    """Verify installed build distributions and return their exact versions."""
    expected = expected_build_dependencies(platform_tag)
    missing: list[str] = []
    mismatched: list[str] = []
    installed: dict[str, str] = {}
    for distribution, required_version in expected.items():
        try:
            installed_version = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            missing.append(distribution)
            continue
        installed[distribution] = installed_version
        if installed_version != required_version:
            mismatched.append(
                f"{distribution}=={installed_version} (expected {required_version})"
            )
    if missing or mismatched:
        details = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if mismatched:
            details.append(f"version mismatch: {', '.join(mismatched)}")
        raise RuntimeError(
            "Desktop build environment does not match the checked-in lock "
            f"({'; '.join(details)}). Run `make install-desktop-build`."
        )
    return dict(sorted(installed.items()))


def validate_recorded_build_dependencies(
    recorded: Mapping[str, object],
    platform_tag: str,
) -> dict[str, str]:
    """Validate one manifest's build dependency map against the checked-in lock."""
    expected = expected_build_dependencies(platform_tag)
    normalized: dict[str, str] = {}
    for key, value in recorded.items():
        if not isinstance(key, str) or not isinstance(value, str) or not value:
            raise ValueError("Desktop build dependency names and versions must be strings.")
        normalized[key] = value
    if normalized != expected:
        raise ValueError(
            "Desktop artifact build dependencies do not match the checked-in lock; "
            f"expected={expected}, recorded={dict(sorted(normalized.items()))}."
        )
    return dict(sorted(normalized.items()))


def build_requirements_sha256() -> str:
    """Return a platform-independent digest of the desktop build requirements."""
    normalized = DESKTOP_BUILD_REQUIREMENTS.read_text(encoding="utf-8").encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()
