"""Verify downloaded Adventure Graph desktop archives and manifests."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

if __package__:
    from scripts.desktop_artifacts import SUPPORTED_PLATFORMS, verify_artifact_set
else:
    from desktop_artifacts import SUPPORTED_PLATFORMS, verify_artifact_set


def main(argv: Sequence[str] | None = None) -> int:
    """Verify one directory of desktop build evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument(
        "--require-platforms",
        nargs="*",
        choices=sorted(SUPPORTED_PLATFORMS),
        default=(),
    )
    parser.add_argument("--source-revision")
    args = parser.parse_args(argv)

    evidence = verify_artifact_set(
        args.directory,
        required_platforms=args.require_platforms,
        expected_source_revision=args.source_revision,
    )
    for item in evidence:
        print(
            f"Verified {item.platform}/{item.architecture}: "
            f"{item.artifact_path.name} ({item.source_revision}; "
            f"{item.runner_image}/{item.runner_image_version})"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        raise SystemExit(str(error)) from None
