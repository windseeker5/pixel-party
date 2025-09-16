#!/usr/bin/env python3
"""
Automatic Duplicate Remover
Removes duplicate files automatically, keeping the one without (1), (2) etc. in filename
"""

import os
import subprocess
import tempfile
from pathlib import Path

def remove_duplicates_auto(library_path):
    """Remove duplicates automatically using fdupes"""
    print(f"Finding and removing duplicates in: {library_path}")

    # Get duplicate groups from fdupes
    result = subprocess.run([
        'fdupes', '-r', library_path
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error running fdupes: {result.stderr}")
        return 0

    # Parse duplicate groups
    duplicate_groups = []
    current_group = []

    for line in result.stdout.split('\n'):
        line = line.strip()
        if line and not line.startswith('/'):
            continue
        elif line:
            current_group.append(line)
        else:
            if current_group and len(current_group) > 1:
                duplicate_groups.append(current_group)
            current_group = []

    # Add last group if exists
    if current_group and len(current_group) > 1:
        duplicate_groups.append(current_group)

    print(f"Found {len(duplicate_groups)} duplicate groups")

    removed_count = 0

    for group in duplicate_groups:
        if len(group) < 2:
            continue

        # Sort files to prefer the one without (1), (2) etc.
        def sort_key(filepath):
            filename = os.path.basename(filepath)
            # Files without (1), (2) etc. get priority (lower score)
            if '(1)' in filename or '(2)' in filename or '(3)' in filename:
                return 1
            return 0

        sorted_group = sorted(group, key=sort_key)
        keep_file = sorted_group[0]  # Keep the first (best) file
        remove_files = sorted_group[1:]  # Remove the rest

        print(f"Keeping: {os.path.basename(keep_file)}")

        for remove_file in remove_files:
            try:
                os.remove(remove_file)
                print(f"  Removed: {os.path.basename(remove_file)}")
                removed_count += 1
            except Exception as e:
                print(f"  Error removing {remove_file}: {e}")

    return removed_count

def main():
    library_path = "/home/kdresdell/Music/cleaned_library"

    if not Path(library_path).exists():
        print(f"Library not found: {library_path}")
        return 1

    print("=== AUTOMATIC DUPLICATE REMOVAL ===")

    try:
        removed = remove_duplicates_auto(library_path)

        print(f"\n=== DUPLICATE REMOVAL COMPLETE ===")
        print(f"✓ Removed {removed} duplicate files")

        # Count remaining files
        remaining = sum(1 for root, dirs, files in os.walk(library_path)
                       for file in files
                       if any(file.lower().endswith(ext) for ext in ['.mp3', '.m4a', '.flac', '.wav', '.ogg', '.aac']))

        print(f"✓ Final library size: {remaining} audio files")
        print(f"✓ Clean library location: {library_path}")

        return 0

    except Exception as e:
        print(f"Error during duplicate removal: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())