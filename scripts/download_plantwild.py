#!/usr/bin/env python3
"""Download and extract the PlantWild v2 dataset from Hugging Face.

The default layout matches DATA.md:

    data/raw/plantwild/<plantwild-label>/<image>

The dataset is licensed CC BY-NC-ND 4.0. Check the dataset card before
redistributing the files: https://huggingface.co/datasets/uqtwei2/PlantWild
"""

from __future__ import annotations

import argparse
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath


DOWNLOAD_URL = (
    "https://huggingface.co/datasets/uqtwei2/PlantWild/resolve/main/"
    "plantwild_v2.zip?download=true"
)
DEFAULT_ARCHIVE = Path("data/raw/plantwild_v2.zip")
DEFAULT_OUTPUT = Path("data/raw/plantwild")
CHUNK_SIZE = 1024 * 1024


def download_file(url: str, destination: Path) -> None:
    """Stream a remote file to disk and show progress when size is known."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "plant-disease-project"})
    with urllib.request.urlopen(request) as response, destination.open("wb") as file:
        total = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        while chunk := response.read(CHUNK_SIZE):
            file.write(chunk)
            downloaded += len(chunk)
            if total:
                percent = downloaded / total * 100
                print(f"\rDownloaded {downloaded / 1e9:.2f} / {total / 1e9:.2f} GB ({percent:5.1f}%)", end="")
            else:
                print(f"\rDownloaded {downloaded / 1e9:.2f} GB", end="")
    print()


def safe_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    """Reject archive members that could write outside the extraction folder."""
    members = archive.infolist()
    for member in members:
        path = PurePosixPath(member.filename)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"Unsafe path in archive: {member.filename}")
    return members


def extraction_names(members: list[zipfile.ZipInfo]) -> dict[str, str]:
    """Return archive-to-output names, removing one common wrapper directory."""
    file_names = [member.filename for member in members if not member.is_dir()]
    first_parts = {PurePosixPath(name).parts[0] for name in file_names if PurePosixPath(name).parts}
    has_wrapper = len(first_parts) == 1 and all(len(PurePosixPath(name).parts) > 1 for name in file_names)
    wrapper = next(iter(first_parts)) if has_wrapper else None
    names = {}
    for member in members:
        path = PurePosixPath(member.filename)
        if wrapper and path.parts[0] == wrapper:
            path = PurePosixPath(*path.parts[1:])
        if path.as_posix():
            names[member.filename] = path.as_posix()
    return names


def extract_archive(archive_path: Path, output_dir: Path) -> int:
    """Extract an archive after validating all member paths."""
    with zipfile.ZipFile(archive_path) as archive:
        members = safe_members(archive)
        names = extraction_names(members)
        extracted = 0
        for member in members:
            relative_name = names.get(member.filename)
            if not relative_name or member.is_dir():
                continue
            destination = output_dir / relative_name
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target, length=CHUNK_SIZE)
            extracted += 1
    return extracted


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE, help="Local zip path.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Extraction directory.")
    parser.add_argument("--url", default=DOWNLOAD_URL, help="Archive URL.")
    parser.add_argument("--keep-archive", action="store_true", help="Keep the downloaded zip after extraction.")
    parser.add_argument("--force", action="store_true", help="Replace an existing output directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output.exists():
        if not args.force:
            print(f"Refusing to overwrite existing directory: {args.output}", file=sys.stderr)
            print("Use --force only if you intend to replace it.", file=sys.stderr)
            return 2
        shutil.rmtree(args.output)

    if args.archive.exists():
        print(f"Using existing archive: {args.archive}")
    else:
        print(f"Downloading PlantWild v2 from {args.url}")
        try:
            download_file(args.url, args.archive)
        except Exception as error:
            args.archive.unlink(missing_ok=True)
            print(f"Download failed: {error}", file=sys.stderr)
            return 1

    try:
        with zipfile.ZipFile(args.archive) as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                raise zipfile.BadZipFile(f"corrupt member: {bad_member}")
    except (OSError, zipfile.BadZipFile) as error:
        print(f"Invalid zip archive {args.archive}: {error}", file=sys.stderr)
        return 1

    try:
        extracted = extract_archive(args.archive, args.output)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        shutil.rmtree(args.output, ignore_errors=True)
        print(f"Extraction failed: {error}", file=sys.stderr)
        return 1

    print(f"Extracted {extracted:,} files to {args.output}")
    if not args.keep_archive:
        args.archive.unlink()
        print(f"Removed archive: {args.archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())