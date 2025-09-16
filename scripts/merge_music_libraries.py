#!/usr/bin/env python3
"""
Music Library Merger - Safely merge two music libraries while avoiding duplicates
"""

import os
import shutil
import hashlib
import subprocess
from pathlib import Path
from collections import defaultdict
import json

def calculate_file_hash(filepath):
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Error hashing {filepath}: {e}")
        return None

def scan_library(library_path):
    """Scan a music library and return file info"""
    files_info = {}
    audio_extensions = {'.mp3', '.m4a', '.flac', '.wav', '.ogg', '.aac'}

    print(f"Scanning {library_path}...")
    for root, dirs, files in os.walk(library_path):
        for file in files:
            filepath = Path(root) / file
            if filepath.suffix.lower() in audio_extensions:
                file_hash = calculate_file_hash(filepath)
                if file_hash:
                    files_info[str(filepath)] = {
                        'hash': file_hash,
                        'size': filepath.stat().st_size,
                        'name': file,
                        'relative_path': str(filepath.relative_to(library_path))
                    }

    return files_info

def find_duplicates(source_info, target_info):
    """Find duplicates between two libraries based on file hash"""
    duplicates = []
    hash_to_target = {info['hash']: path for path, info in target_info.items()}

    for source_path, source_info_data in source_info.items():
        source_hash = source_info_data['hash']
        if source_hash in hash_to_target:
            duplicates.append({
                'source': source_path,
                'target': hash_to_target[source_hash],
                'hash': source_hash
            })

    return duplicates

def create_merge_plan(source_lib, target_lib, output_dir):
    """Create a plan for merging libraries"""
    print("Creating merge plan...")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Scan both libraries
    print("Scanning source library (iTunes)...")
    source_info = scan_library(source_lib)
    print(f"Found {len(source_info)} files in source library")

    print("Scanning target library (existing)...")
    target_info = scan_library(target_lib)
    print(f"Found {len(target_info)} files in target library")

    # Find duplicates
    print("Finding duplicates...")
    duplicates = find_duplicates(source_info, target_info)
    print(f"Found {len(duplicates)} duplicates")

    # Create merge plan
    plan = {
        'duplicates': duplicates,
        'source_unique': [],
        'target_files': list(target_info.keys()),
        'stats': {
            'source_total': len(source_info),
            'target_total': len(target_info),
            'duplicates': len(duplicates),
            'unique_source': len(source_info) - len(duplicates)
        }
    }

    # Find unique files in source
    duplicate_hashes = {dup['hash'] for dup in duplicates}
    for path, info in source_info.items():
        if info['hash'] not in duplicate_hashes:
            plan['source_unique'].append(path)

    return plan

def execute_merge(plan, source_lib, target_lib, output_dir):
    """Execute the merge plan"""
    output_path = Path(output_dir)

    print(f"\nMerge Plan Summary:")
    print(f"- Files in source (iTunes): {plan['stats']['source_total']}")
    print(f"- Files in target (existing): {plan['stats']['target_total']}")
    print(f"- Duplicates found: {plan['stats']['duplicates']}")
    print(f"- Unique files to copy: {plan['stats']['unique_source']}")

    response = input("\nProceed with merge? (y/N): ")
    if response.lower() != 'y':
        print("Merge cancelled")
        return

    # Copy existing library first
    print(f"\nCopying existing library to {output_dir}...")
    if not Path(f"{output_dir}/existing").exists():
        shutil.copytree(target_lib, f"{output_dir}/existing")

    # Copy unique files from source
    print(f"\nCopying unique files from iTunes library...")
    itunes_dir = Path(f"{output_dir}/from_itunes")
    itunes_dir.mkdir(exist_ok=True)

    copied = 0
    for source_path in plan['source_unique']:
        source_file = Path(source_path)
        rel_path = source_file.relative_to(source_lib)
        target_file = itunes_dir / rel_path

        # Create directory structure
        target_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            shutil.copy2(source_path, target_file)
            copied += 1
            if copied % 100 == 0:
                print(f"Copied {copied} files...")
        except Exception as e:
            print(f"Error copying {source_path}: {e}")

    print(f"Merge complete! Copied {copied} unique files.")
    print(f"Merged library is in: {output_dir}")
    print(f"Next steps:")
    print(f"1. Run Picard on {output_dir} to clean metadata")
    print(f"2. Use fdupes to find any remaining duplicates")

def main():
    source_lib = "/home/kdresdell/Music/mac-import/iTunes Music"
    target_lib = "/mnt/media/MUSIC"
    output_dir = "/home/kdresdell/Music/merged_library"

    if not Path(source_lib).exists():
        print(f"Source library not found: {source_lib}")
        return

    if not Path(target_lib).exists():
        print(f"Target library not found: {target_lib}")
        return

    # Create merge plan
    plan = create_merge_plan(source_lib, target_lib, output_dir)

    # Save plan for review
    plan_file = Path(output_dir) / "merge_plan.json"
    with open(plan_file, 'w') as f:
        json.dump(plan, f, indent=2)
    print(f"\nMerge plan saved to: {plan_file}")

    # Execute merge
    execute_merge(plan, source_lib, target_lib, output_dir)

if __name__ == "__main__":
    main()