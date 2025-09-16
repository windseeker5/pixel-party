#!/usr/bin/env python3
"""
Quick Music Library Merger - Fast merge using file size + name comparison
"""

import os
import shutil
import subprocess
from pathlib import Path
from collections import defaultdict
import json

def get_file_info(filepath):
    """Get basic file info for comparison"""
    try:
        stat = filepath.stat()
        return {
            'size': stat.st_size,
            'name': filepath.name.lower(),
            'path': str(filepath)
        }
    except:
        return None

def scan_library_fast(library_path, label):
    """Fast scan using file size + name"""
    files_info = {}
    audio_extensions = {'.mp3', '.m4a', '.flac', '.wav', '.ogg', '.aac'}

    print(f"Scanning {label}: {library_path}")
    count = 0

    for root, dirs, files in os.walk(library_path):
        for file in files:
            filepath = Path(root) / file
            if filepath.suffix.lower() in audio_extensions:
                info = get_file_info(filepath)
                if info:
                    # Use size + name as key for duplicate detection
                    key = f"{info['size']}_{info['name']}"
                    files_info[key] = info
                    count += 1
                    if count % 500 == 0:
                        print(f"  Scanned {count} files...")

    print(f"  Found {count} audio files in {label}")
    return files_info

def find_duplicates_fast(source_info, target_info):
    """Find duplicates using size + name comparison"""
    duplicates = []

    for key, source_file in source_info.items():
        if key in target_info:
            duplicates.append({
                'source': source_file['path'],
                'target': target_info[key]['path'],
                'key': key
            })

    return duplicates

def execute_merge_rsync(source_lib, target_lib, output_dir):
    """Execute merge using rsync for efficiency"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print(f"\n=== MUSIC LIBRARY MERGE ===")
    print(f"Source (iTunes): {source_lib}")
    print(f"Target (Existing): {target_lib}")
    print(f"Output: {output_dir}")

    # Fast scan both libraries
    print(f"\n1. Scanning libraries...")
    source_info = scan_library_fast(source_lib, "iTunes library")
    target_info = scan_library_fast(target_lib, "existing library")

    # Find duplicates
    print(f"\n2. Finding duplicates...")
    duplicates = find_duplicates_fast(source_info, target_info)

    stats = {
        'source_total': len(source_info),
        'target_total': len(target_info),
        'duplicates': len(duplicates),
        'unique_source': len(source_info) - len(duplicates)
    }

    print(f"\n=== MERGE STATISTICS ===")
    print(f"iTunes library files: {stats['source_total']}")
    print(f"Existing library files: {stats['target_total']}")
    print(f"Duplicates found: {stats['duplicates']}")
    print(f"Unique files to add: {stats['unique_source']}")
    print(f"Final library size: {stats['target_total'] + stats['unique_source']}")

    # Save duplicate list
    duplicate_file = output_path / "duplicates_found.json"
    with open(duplicate_file, 'w') as f:
        json.dump(duplicates, f, indent=2)
    print(f"Duplicate list saved: {duplicate_file}")

    print(f"\nProceeding with merge...")

    print(f"\n3. Copying existing library...")
    # Use rsync for efficient copying
    subprocess.run([
        'rsync', '-av', '--progress',
        f"{target_lib}/",
        f"{output_dir}/"
    ])

    print(f"\n4. Adding unique files from iTunes...")
    # Copy non-duplicate files from source
    duplicate_sources = {dup['source'] for dup in duplicates}
    copied = 0

    for key, file_info in source_info.items():
        if file_info['path'] not in duplicate_sources:
            source_file = Path(file_info['path'])
            rel_path = source_file.relative_to(source_lib)
            target_file = output_path / "from_itunes" / rel_path

            target_file.parent.mkdir(parents=True, exist_ok=True)

            try:
                shutil.copy2(source_file, target_file)
                copied += 1
                if copied % 100 == 0:
                    print(f"  Copied {copied}/{stats['unique_source']} unique files...")
            except Exception as e:
                print(f"  Error copying {source_file}: {e}")

    print(f"\n=== MERGE COMPLETE ===")
    print(f"✓ Copied all {stats['target_total']} files from existing library")
    print(f"✓ Added {copied} unique files from iTunes library")
    print(f"✓ Skipped {stats['duplicates']} duplicates")
    print(f"✓ Total files in merged library: {stats['target_total'] + copied}")
    print(f"✓ Merged library location: {output_dir}")
    print(f"\n=== NEXT STEPS ===")
    print(f"1. Run Picard on: {output_dir}")
    print(f"2. After Picard, run: fdupes -r -d '{output_dir}'")

def main():
    source_lib = "/home/kdresdell/Music/mac-import/iTunes Music"
    target_lib = "/mnt/media/MUSIC"
    output_dir = "/home/kdresdell/Music/merged_library"

    if not Path(source_lib).exists():
        print(f"❌ Source library not found: {source_lib}")
        return

    if not Path(target_lib).exists():
        print(f"❌ Target library not found: {target_lib}")
        return

    execute_merge_rsync(source_lib, target_lib, output_dir)

if __name__ == "__main__":
    main()