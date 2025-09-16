#!/usr/bin/env python3
"""
Automated Picard Music Library Cleaner
Uses Picard's Python API to clean metadata automatically
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

def create_picard_config():
    """Create a temporary Picard config for automated processing"""
    config_content = """[setting]
enabled_plugins = []
toolbar_layout = []
starting_directory = /home/kdresdell/Music/merged_library

[rename]
windows_compatibility = True
ascii_filenames = False
move_files = True
move_files_to = /home/kdresdell/Music/merged_library_cleaned
file_naming_format = $if2(%albumartist%,%artist%)/%album%/$if($gt(%totaldiscs%,1),%discnumber%-,)$num(%tracknumber%,2) %title%

[metadata]
translate_artist_names = False
standardize_artists = True
standardize_instruments = True
convert_punctuation = True
release_ars = True
track_ars = True
enabled_plugins = []

[advanced]
ignore_file_mbids = False
ignore_track_mbids = False
track_matching_threshold = 0.4
cluster_lookup_threshold = 0.8

[file_renaming]
windows_compatibility = True
ascii_filenames = False
replace_spaces_with_underscores = False

[genres]
use_genres = True
max_genres = 5
min_genre_usage = 90
ignore_genres =
builtin_genres = True
folksonomy_genres = True
only_my_genres = False

[cdlookup]
hostname = musicbrainz.org
port = 80
username =
password =

[musicbrainz]
server_host = musicbrainz.org
server_port = 443
"""
    return config_content

def run_picard_batch_process(music_dir):
    """Run Picard in batch mode to process music files"""
    print(f"Starting Picard automated cleanup of: {music_dir}")

    # Create output directory
    output_dir = f"{music_dir}_cleaned"
    Path(output_dir).mkdir(exist_ok=True)

    print(f"Output directory: {output_dir}")

    # Get list of audio files to process
    audio_extensions = {'.mp3', '.m4a', '.flac', '.wav', '.ogg', '.aac'}
    audio_files = []

    print("Scanning for audio files...")
    for root, dirs, files in os.walk(music_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in audio_extensions):
                audio_files.append(os.path.join(root, file))

    print(f"Found {len(audio_files)} audio files to process")

    if len(audio_files) == 0:
        print("No audio files found!")
        return

    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as config_file:
        config_file.write(create_picard_config())
        config_path = config_file.name

    try:
        # Use Picard's tagger script functionality
        print("Starting Picard processing...")
        print("This will organize files by Artist/Album/Track structure")
        print("and standardize metadata...")

        # Process in smaller batches to avoid memory issues
        batch_size = 100
        total_batches = (len(audio_files) + batch_size - 1) // batch_size

        for i in range(0, len(audio_files), batch_size):
            batch = audio_files[i:i + batch_size]
            batch_num = i // batch_size + 1

            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} files)...")

            # Run picard with configuration
            cmd = [
                'picard',
                '-c', config_path,
                '-s',  # stand-alone instance
                '--no-crash-dialog'
            ] + batch

            try:
                subprocess.run(cmd, timeout=300, check=True)
                print(f"  Batch {batch_num} completed successfully")
            except subprocess.TimeoutExpired:
                print(f"  Batch {batch_num} timed out, skipping...")
            except subprocess.CalledProcessError as e:
                print(f"  Batch {batch_num} failed: {e}")
                continue

    finally:
        # Clean up temp config
        os.unlink(config_path)

    print(f"\nPicard processing completed!")
    print(f"Check the results in: {output_dir}")

def main():
    music_dir = "/home/kdresdell/Music/merged_library"

    if not Path(music_dir).exists():
        print(f"Music directory not found: {music_dir}")
        return 1

    print("=== PICARD AUTOMATED CLEANUP ===")
    print(f"Processing: {music_dir}")

    try:
        run_picard_batch_process(music_dir)
        print("\n=== PICARD CLEANUP COMPLETE ===")
        print("Next step: Run duplicate detection with fdupes")
        return 0
    except Exception as e:
        print(f"Error during Picard processing: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())