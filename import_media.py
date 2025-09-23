#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PixelParty Media Import Script

Imports all photos and videos from the import/ folder into the PixelParty database.
Supports full emoji support for submitter names and wishes.

Usage: python import_media.py
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
import uuid
import asyncio
from typing import Optional

# Add the app directory to Python path so we can import app modules
sys.path.append(str(Path(__file__).parent))

# Import PixelParty modules
from app import create_app, db
from app.models import Guest, Photo
from app.services.file_handler import FileHandler

# Ensure UTF-8 encoding for terminal output
if sys.stdout.encoding != 'utf-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stdin = codecs.getreader('utf-8')(sys.stdin.buffer, 'strict')


class MediaImporter:
    """Import media files from import/ folder into PixelParty."""

    IMPORT_DIR = Path("import")
    SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    SUPPORTED_VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}

    def __init__(self):
        """Initialize the importer."""
        self.app = create_app()
        self.file_handler = FileHandler()

    def get_media_files(self):
        """Get all supported media files from import directory."""
        if not self.IMPORT_DIR.exists():
            print(f"❌ Import directory '{self.IMPORT_DIR}' not found!")
            return [], []

        images = []
        videos = []

        for file_path in self.IMPORT_DIR.iterdir():
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext in self.SUPPORTED_IMAGE_EXTENSIONS:
                    images.append(file_path)
                elif ext in self.SUPPORTED_VIDEO_EXTENSIONS:
                    videos.append(file_path)

        # Sort by name for consistent ordering
        images.sort(key=lambda x: x.name)
        videos.sort(key=lambda x: x.name)

        return images, videos

    def get_user_input(self):
        """Get submitter name and wish from user."""
        print("\n🎉 PixelParty Media Import Tool")
        print("=" * 50)

        # Get submitter name (required)
        while True:
            submitter = input("\n📝 Enter submitter name (supports emojis like 'John 🎉'): ").strip()
            if submitter:
                break
            print("❌ Submitter name is required!")

        # Get wish/comment (optional)
        print("\n💭 Enter a wish/comment for all media files")
        print("   (supports emojis like 'Happy Birthday! 🥳🎊')")
        print("   (press Enter to leave empty):")
        wish = input("Wish: ").strip()

        if not wish:
            wish = ""  # Empty wish is allowed

        return submitter, wish

    def sanitize_filename(self, name: str) -> str:
        """Sanitize name for use in filename (remove emojis and special chars)."""
        # Keep only alphanumeric, dash, underscore, and space
        sanitized = ''.join(c for c in name if c.isalnum() or c in ('-', '_', ' ')).strip()
        # Replace spaces with underscores and limit length
        sanitized = sanitized.replace(' ', '_')[:20]
        return sanitized or "guest"

    def generate_filename(self, original_file: Path, guest_name: str) -> str:
        """Generate unique filename following app conventions."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        guest_clean = self.sanitize_filename(guest_name)
        unique_id = str(uuid.uuid4())[:8]
        ext = original_file.suffix.lower()

        return f"{timestamp}_{guest_clean}_{unique_id}{ext}"

    def create_or_get_guest(self, name: str) -> Guest:
        """Create or retrieve guest record."""
        # Look for existing guest by name
        guest = Guest.query.filter_by(name=name).first()
        if guest:
            return guest

        # Create new guest
        session_id = f"import_{uuid.uuid4().hex[:16]}"
        guest = Guest(
            name=name,
            session_id=session_id,
            total_submissions=0
        )
        db.session.add(guest)
        db.session.flush()  # Get the ID without committing
        return guest

    async def process_file(self, file_path: Path, guest: Guest, wish: str) -> bool:
        """Process a single media file."""
        try:
            # Read file data
            with open(file_path, 'rb') as f:
                file_data = f.read()

            # Validate file
            is_valid, message = self.file_handler.validate_file(file_data, file_path.name)
            if not is_valid:
                print(f"  ❌ {file_path.name}: {message}")
                return False

            # Generate new filename
            new_filename = self.generate_filename(file_path, guest.name)

            # Save file using the app's file handler
            success, save_message, saved_filename = await self.file_handler.save_file(
                file_data, file_path.name, guest.name
            )

            if not success:
                print(f"  ❌ {file_path.name}: {save_message}")
                return False

            # Determine file type and get additional info
            file_type = "image" if self.file_handler.is_image(file_path.name) else "video"
            file_size = len(file_data)

            # For videos, get duration and thumbnail filename
            duration = None
            thumbnail = None
            if file_type == "video":
                video_path = os.path.join(self.file_handler.UPLOAD_DIR, saved_filename)
                try:
                    _, _, duration = self.file_handler.validate_video_duration(video_path)
                    # Get thumbnail filename (generated during save_file)
                    video_name = os.path.splitext(saved_filename)[0]
                    thumbnail = f"{video_name}_thumb.jpg"
                except:
                    duration = None
                    thumbnail = None

            # Create photo record in database
            photo = Photo(
                guest_id=guest.id,
                guest_name=guest.name,
                filename=saved_filename,
                original_filename=file_path.name,
                wish_message=wish,
                file_size=file_size,
                file_type=file_type,
                duration=duration,
                thumbnail=thumbnail
            )

            db.session.add(photo)

            print(f"  ✅ {file_path.name} -> {saved_filename}")
            return True

        except Exception as e:
            print(f"  ❌ {file_path.name}: Error processing file: {e}")
            return False

    async def import_media(self):
        """Main import process."""
        with self.app.app_context():
            # Get media files
            images, videos = self.get_media_files()
            total_files = len(images) + len(videos)

            if total_files == 0:
                print(f"❌ No supported media files found in '{self.IMPORT_DIR}/'")
                return

            print(f"\n📊 Found {len(images)} images and {len(videos)} videos ({total_files} total)")

            # Get user input
            submitter, wish = self.get_user_input()

            # Show summary
            print(f"\n📋 Import Summary:")
            print(f"   Submitter: {submitter}")
            print(f"   Wish: {'(empty)' if not wish else wish}")
            print(f"   Files: {total_files}")

            # Confirm before proceeding
            confirm = input(f"\n❓ Import all {total_files} files? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("❌ Import cancelled.")
                return

            # Create or get guest record
            guest = self.create_or_get_guest(submitter)

            print(f"\n🚀 Starting import...")
            print("-" * 50)

            successful = 0
            failed = 0

            # Process all files
            all_files = list(images) + list(videos)
            for i, file_path in enumerate(all_files, 1):
                print(f"[{i:2d}/{total_files}] Processing {file_path.name}...")

                success = await self.process_file(file_path, guest, wish)
                if success:
                    successful += 1
                else:
                    failed += 1

            # Update guest submission count
            guest.total_submissions = successful

            # Commit all changes
            try:
                db.session.commit()
                print("-" * 50)
                print(f"🎉 Import completed!")
                print(f"   ✅ Successful: {successful}")
                print(f"   ❌ Failed: {failed}")
                print(f"   👤 Submitter: {guest.name} (ID: {guest.id})")

                if successful > 0:
                    print(f"\n💡 Files are now available in the PixelParty slideshow!")

            except Exception as e:
                db.session.rollback()
                print(f"❌ Database error: {e}")
                return


async def main():
    """Main entry point."""
    importer = MediaImporter()
    await importer.import_media()


if __name__ == "__main__":
    print("🎬 PixelParty Media Import Tool")
    print("Supports full emoji support! 🎉📸🎬")

    # Run the async import process
    asyncio.run(main())