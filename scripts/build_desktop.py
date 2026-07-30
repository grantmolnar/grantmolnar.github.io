"""Build, smoke-test, and archive one native Adventure Graph desktop bundle."""

from __future__ import annotations

import argparse
import gzip
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from collections.abc import Iterable, Sequence
from pathlib import Path

if __package__:
    from scripts.desktop_artifacts import (
        BUNDLE_LIMIT_BYTES,
        FORBIDDEN_USER_DATA_NAMES,
        write_artifact_manifest,
    )
    from scripts.desktop_build_environment import (
        build_requirements_sha256,
        require_build_environment,
    )
else:
    from desktop_artifacts import (
        BUNDLE_LIMIT_BYTES,
        FORBIDDEN_USER_DATA_NAMES,
        write_artifact_manifest,
    )
    from desktop_build_environment import (
        build_requirements_sha256,
        require_build_environment,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "dist" / "desktop"
_FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
_FIXED_EPOCH = 315532800


def main(argv: Sequence[str] | None = None) -> int:
    """Build the desktop bundle for the current operating system."""
    args = _parse_args(argv)
    output_dir = _validated_output_dir(args.output_dir)
    version = _project_version()
    platform_tag = _platform_tag()
    build_dependencies = require_build_environment(platform_tag)

    bundle_dist = PROJECT_ROOT / "build" / "desktop-dist"
    work_path = PROJECT_ROOT / "build" / "desktop-work"
    if not args.no_clean:
        shutil.rmtree(bundle_dist, ignore_errors=True)
        shutil.rmtree(work_path, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    _run_pyinstaller(bundle_dist, work_path)
    bundle = _locate_bundle(bundle_dist)
    _reject_canonical_user_data(bundle)
    _smoke_test_bundle(bundle)

    artifact = _archive_bundle(bundle, output_dir, version)
    artifact_size = artifact.stat().st_size
    if artifact_size > BUNDLE_LIMIT_BYTES:
        raise RuntimeError(
            f"Compressed desktop artifact is {artifact_size:,} bytes; "
            f"the limit is {BUNDLE_LIMIT_BYTES:,} bytes."
        )
    manifest = write_artifact_manifest(
        artifact,
        bundle,
        version=version,
        platform_tag=platform_tag,
        architecture_tag=_architecture_tag(),
        python_version=platform.python_version(),
        pyinstaller_version=build_dependencies["pyinstaller"],
        source_revision=_source_revision(),
        build_dependencies=build_dependencies,
        build_requirements_sha256=build_requirements_sha256(),
        build_operating_system=platform.platform(),
        runner_image=os.environ.get("ImageOS", "local"),
        runner_image_version=os.environ.get("ImageVersion", "local"),
    )
    print(artifact)
    print(manifest)
    return 0


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-clean", action="store_true")
    return parser.parse_args(argv)


def _validated_output_dir(path: Path) -> Path:
    output = path.expanduser().resolve()
    dist_root = (PROJECT_ROOT / "dist").resolve()
    if output != dist_root and dist_root not in output.parents:
        raise ValueError(f"Desktop output must stay inside {dist_root}: {output}.")
    return output


def _project_version() -> str:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = pyproject["project"]["version"]
    if not isinstance(version, str):
        raise TypeError("Project version must be a string.")
    return version


def _run_pyinstaller(bundle_dist: Path, work_path: Path) -> None:
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = str(_FIXED_EPOCH)
    environment["PYTHONHASHSEED"] = "0"
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--distpath",
        str(bundle_dist),
        "--workpath",
        str(work_path),
        str(PROJECT_ROOT / "packaging" / "adventure_graph_desktop.spec"),
    ]
    subprocess.run(command, cwd=PROJECT_ROOT, env=environment, check=True)


def _locate_bundle(bundle_dist: Path) -> Path:
    candidate = (
        bundle_dist / "Adventure Graph.app"
        if sys.platform == "darwin"
        else bundle_dist / "Adventure Graph"
    )
    if not candidate.exists():
        raise FileNotFoundError(f"PyInstaller did not produce the expected bundle: {candidate}.")
    return candidate


def _bundle_executable(bundle: Path) -> Path:
    if sys.platform == "darwin":
        return bundle / "Contents" / "MacOS" / "Adventure Graph"
    if sys.platform == "win32":
        return bundle / "Adventure Graph.exe"
    return bundle / "Adventure Graph"


def _smoke_test_bundle(bundle: Path) -> None:
    executable = _bundle_executable(bundle)
    if not executable.is_file():
        raise FileNotFoundError(f"Desktop executable is missing: {executable}.")
    with tempfile.TemporaryDirectory(prefix="adventure-graph-desktop-smoke-") as raw_temp:
        temporary = Path(raw_temp)
        workspace = temporary / "workspace"
        workspace.mkdir()
        config_home = temporary / "config"
        environment = os.environ.copy()
        environment["ADVENTURE_GRAPH_CONFIG_HOME"] = str(config_home)
        subprocess.run(
            [str(executable), "--smoke-test", str(workspace)],
            cwd=temporary,
            env=environment,
            check=True,
            timeout=30,
        )
        if config_home.exists():
            raise RuntimeError("Desktop smoke mode must not persist launcher settings.")


def _reject_canonical_user_data(bundle: Path) -> None:
    violations = [
        path
        for path in bundle.rglob("*")
        if path.name.casefold() in FORBIDDEN_USER_DATA_NAMES
    ]
    if violations:
        names = ", ".join(str(path.relative_to(bundle)) for path in violations)
        raise RuntimeError(f"Desktop bundle contains canonical user data: {names}.")


def _archive_bundle(bundle: Path, output_dir: Path, version: str) -> Path:
    stem = f"Adventure-Graph-{version}-{_platform_tag()}-{_architecture_tag()}"
    if sys.platform == "linux":
        destination = output_dir / f"{stem}.tar.gz"
        _write_deterministic_tar_gz(bundle, destination, archive_root=stem)
    else:
        destination = output_dir / f"{stem}.zip"
        archive_root = bundle.name if sys.platform == "darwin" else stem
        _write_deterministic_zip(bundle, destination, archive_root=archive_root)
    return destination


def _platform_tag() -> str:
    return {"darwin": "macos", "win32": "windows"}.get(sys.platform, "linux")


def _architecture_tag() -> str:
    machine = platform.machine().lower().replace(" ", "-")
    aliases = {"amd64": "x86_64", "x64": "x86_64", "aarch64": "arm64"}
    return aliases.get(machine, machine or "unknown")


def _iter_bundle_paths(bundle: Path) -> Iterable[Path]:
    yield bundle
    yield from sorted(bundle.rglob("*"), key=lambda path: path.as_posix())


def _write_deterministic_zip(bundle: Path, destination: Path, *, archive_root: str) -> None:
    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in _iter_bundle_paths(bundle):
            relative = path.relative_to(bundle)
            archive_name = Path(archive_root, *relative.parts).as_posix()
            if path.is_dir() and not path.is_symlink():
                info = zipfile.ZipInfo(f"{archive_name}/", _FIXED_ZIP_TIME)
                info.create_system = 3
                info.external_attr = (stat.S_IFDIR | 0o755) << 16
                archive.writestr(info, b"")
                continue
            info = zipfile.ZipInfo(archive_name, _FIXED_ZIP_TIME)
            info.create_system = 3
            if path.is_symlink():
                mode = stat.S_IMODE(path.lstat().st_mode)
                info.external_attr = (stat.S_IFLNK | mode) << 16
                archive.writestr(info, os.readlink(path).encode("utf-8"))
            else:
                mode = path.stat().st_mode & 0o777
                info.external_attr = (stat.S_IFREG | mode) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())


def _write_deterministic_tar_gz(bundle: Path, destination: Path, *, archive_root: str) -> None:
    with destination.open("wb") as raw_output:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_output, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for path in _iter_bundle_paths(bundle):
                    relative = path.relative_to(bundle)
                    archive_name = Path(archive_root, *relative.parts).as_posix()
                    archive.add(
                        path,
                        arcname=archive_name,
                        recursive=False,
                        filter=_normalized_tar_info,
                    )


def _normalized_tar_info(info: tarfile.TarInfo) -> tarfile.TarInfo:
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    return info


def _source_revision() -> str:
    return (
        os.environ.get("ADVENTURE_GRAPH_SOURCE_REVISION")
        or os.environ.get("GITHUB_SHA")
        or "local-uncommitted"
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error)) from None
