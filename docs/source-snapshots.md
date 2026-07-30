# Portable source snapshots

## Purpose

Source snapshots are maintainer handoffs containing the complete repository source. They are distinct from
native desktop bundles and from user adventure exports. A descriptive ZIP filename may identify the version,
workstream, and session, but that description must not be repeated inside the archive.

Every maintained snapshot uses this shape:

```text
adventure-graph/
  README.md
  pyproject.toml
  src/
  tests/
  docs/
  examples/
```

## Audit and build

Audit the current tree before packaging:

```bash
make source-audit
```

Build the default archive under `dist/source/`:

```bash
make source-package
```

Use a descriptive external filename for a handoff:

```bash
make source-package \
  SOURCE_SNAPSHOT_PATH=dist/source/adventure-graph-0.10.0-next-session.zip
```

The builder writes files in a deterministic order with fixed ZIP metadata, excludes local and generated
build state, and verifies the finished archive before returning success. The output filename does not affect
archive bytes because every archive uses the stable `adventure-graph/` root.

Verify a received or copied snapshot independently:

```bash
make source-verify \
  SOURCE_SNAPSHOT_PATH=dist/source/adventure-graph-0.10.0-next-session.zip
```

The direct commands are:

```bash
python scripts/source_snapshot.py audit
python scripts/source_snapshot.py build path/to/snapshot.zip
python scripts/source_snapshot.py verify path/to/snapshot.zip
```

## Path budget

The project reserves 120 characters for the extraction destination, including the drive and selected output
folder. Archive members are capped at 138 characters, so the complete extracted path remains within the
project's 259-character legacy-Windows ceiling. Beneath the 15-character `adventure-graph` root, repository
relative paths therefore have a 122-character ceiling.

This is a conservative portability contract. It does not claim that every Windows API, third-party tool,
network share, or organization policy behaves identically. A candidate snapshot still requires one ordinary
Windows Explorer **Extract All** acceptance check before it becomes the continuation baseline.

## Windows extraction check

1. Put the ZIP in an ordinary location such as Downloads.
2. Select **Extract All** in Windows Explorer.
3. Accept the ordinary destination or choose another normal working directory.
4. Open the extracted `adventure-graph/README.md` and the longest reported member from the build output.
5. Record the destination prefix and whether extraction completed without skips or error `0x80010135`.

Do not treat moving the archive to `C:\`, enabling machine-wide long-path policy, or requiring 7-Zip as the
acceptance test. Those may be useful recovery options for an old archive, but the maintained snapshot should
work through the ordinary path.

## Exclusions

Source snapshots exclude `.git`, virtual environments, caches, `dist`, `build`, coverage output, mutation
output, `node_modules`, `.env` files, and symbolic links. `.env.example` remains eligible. Handoff documents
are distributed beside the source ZIP rather than copied into the repository root.
