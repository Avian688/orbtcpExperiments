#!/usr/bin/env python3

"""
Recursively removes simulation outputs.

Deletes:
- All .csv, .vec, .vci, .anf files anywhere
- All contents inside folders named 'csvs' or 'results'

The script is expected to be inside 'pythonScripts/' and will
start cleaning from its parent directory.
"""

import os
import shutil
from pathlib import Path

TARGET_EXTENSIONS = {".csv", ".vec", ".vci", ".anf"}
TARGET_FOLDERS = {"csvs", "results"}

# Start from project root (parent of pythonScripts)
BASE_DIR = Path(__file__).resolve().parent.parent


def clear_folder(folder: Path):
    """Delete everything inside the given folder."""
    for item in folder.iterdir():
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        except Exception as e:
            print(f"Failed to delete {item}: {e}")


def main():
    for root, dirs, files in os.walk(BASE_DIR, topdown=True):
        root_path = Path(root)

        # Handle csvs/results folders (may appear at any depth)
        for d in list(dirs):
            if d in TARGET_FOLDERS:
                folder = root_path / d
                print(f"Clearing folder: {folder}")
                clear_folder(folder)

                # Do not descend into it since it's already empty
                dirs.remove(d)

        # Remove extension files anywhere
        for f in files:
            file_path = root_path / f
            if file_path.suffix in TARGET_EXTENSIONS:
                try:
                    file_path.unlink()
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")


if __name__ == "__main__":
    main()