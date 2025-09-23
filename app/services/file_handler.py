"""File upload and processing utilities."""

import io
import os
import uuid
import hashlib
from datetime import datetime
from typing import Optional, Tuple
from PIL import Image, ImageOps
import aiofiles


class FileHandler:
    """Handle file uploads and processing."""

    UPLOAD_DIR = "media/photos"
    THUMBNAIL_DIR = "media/thumbnails"
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_VIDEO_DURATION = 120  # seconds (2 minutes)
    TARGET_WIDTH = 1920
    TARGET_HEIGHT = 1080
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}

    def __init__(self):
        """Initialize FileHandler."""
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.THUMBNAIL_DIR, exist_ok=True)
    
    def generate_filename(self, original_filename: str, guest_name: str) -> str:
        """Generate a unique filename for uploaded files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        guest_clean = "".join(c for c in guest_name if c.isalnum() or c in ('-', '_')).strip()
        
        # Get file extension
        _, ext = os.path.splitext(original_filename.lower())
        
        # Generate unique ID
        unique_id = str(uuid.uuid4())[:8]
        
        return f"{timestamp}_{guest_clean}_{unique_id}{ext}"
    
    def validate_file(self, file_data: bytes, filename: str) -> Tuple[bool, str]:
        """Validate uploaded file."""
        if len(file_data) > self.MAX_FILE_SIZE:
            return False, f"File size exceeds maximum limit of {self.MAX_FILE_SIZE // (1024*1024)}MB"

        if len(file_data) == 0:
            return False, "File is empty"

        _, ext = os.path.splitext(filename.lower())

        if ext not in (self.ALLOWED_IMAGE_EXTENSIONS | self.ALLOWED_VIDEO_EXTENSIONS):
            return False, f"File type {ext} not supported"

        return True, "Valid file"

    def validate_video_duration(self, file_path: str) -> Tuple[bool, str, float]:
        """Validate video duration and return duration in seconds."""
        try:
            from moviepy.editor import VideoFileClip

            with VideoFileClip(file_path) as clip:
                duration = clip.duration

            if duration > self.MAX_VIDEO_DURATION:
                return False, f"Video is {duration:.1f} seconds. Maximum allowed is {self.MAX_VIDEO_DURATION} seconds (2 minutes) for smooth party flow!", duration

            return True, f"Video duration: {duration:.1f} seconds", duration

        except Exception as e:
            print(f"Error checking video duration: {e}")
            return False, "Unable to check video duration. Please try a different format.", 0.0

    def generate_video_thumbnail(self, video_path: str) -> str:
        """Generate a thumbnail image from a video file."""
        try:
            from moviepy.editor import VideoFileClip
            import os

            # Generate thumbnail filename
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            thumbnail_name = f"{video_name}_thumb.jpg"
            thumbnail_path = os.path.join(self.THUMBNAIL_DIR, thumbnail_name)

            print(f"Generating thumbnail for {video_path} -> {thumbnail_path}")

            # Extract frame at 1 second (or 10% of duration, whichever is smaller)
            with VideoFileClip(video_path) as clip:
                duration = clip.duration
                timestamp = min(1.0, duration * 0.1)  # 1 second or 10% of video
                print(f"Video duration: {duration}s, extracting frame at {timestamp}s")

                # Save frame as thumbnail
                frame = clip.get_frame(timestamp)
                from PIL import Image

                # Convert to PIL Image and save
                image = Image.fromarray(frame)
                # Resize to reasonable thumbnail size
                image.thumbnail((400, 300), Image.LANCZOS)
                image.save(thumbnail_path, 'JPEG', quality=85)
                print(f"Thumbnail saved successfully: {thumbnail_name}")

            return thumbnail_name

        except Exception as e:
            print(f"Error generating video thumbnail: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def is_image(self, filename: str) -> bool:
        """Check if file is an image."""
        _, ext = os.path.splitext(filename.lower())
        return ext in self.ALLOWED_IMAGE_EXTENSIONS
    
    def is_video(self, filename: str) -> bool:
        """Check if file is a video."""
        _, ext = os.path.splitext(filename.lower())
        return ext in self.ALLOWED_VIDEO_EXTENSIONS
    
    async def process_image(self, file_data: bytes, output_path: str) -> bool:
        """Process and resize image to target dimensions."""
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(file_data))
            
            # Convert to RGB if necessary (handles RGBA, P mode, etc.)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparent images
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                if image.mode in ('RGBA', 'LA'):
                    background.paste(image, mask=image.split()[-1])
                    image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Auto-rotate based on EXIF data
            image = ImageOps.exif_transpose(image)
            
            # Resize maintaining aspect ratio
            image.thumbnail((self.TARGET_WIDTH, self.TARGET_HEIGHT), Image.LANCZOS)
            
            # Save processed image
            image.save(output_path, 'JPEG', quality=85, optimize=True)
            
            return True
            
        except Exception as e:
            print(f"Error processing image: {e}")
            return False
    
    async def save_file(self, file_data: bytes, filename: str, guest_name: str) -> Tuple[bool, str, Optional[str]]:
        """Save uploaded file to disk."""
        try:
            # Validate file
            is_valid, message = self.validate_file(file_data, filename)
            if not is_valid:
                return False, message, None

            # Generate unique filename
            new_filename = self.generate_filename(filename, guest_name)
            file_path = os.path.join(self.UPLOAD_DIR, new_filename)

            # Process image if it's an image file
            if self.is_image(filename):
                success = await self.process_image(file_data, file_path)
                if not success:
                    return False, "Failed to process image", None
            elif self.is_video(filename):
                # Save video file first
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(file_data)

                # Validate video duration
                is_valid_duration, duration_message, duration = self.validate_video_duration(file_path)
                if not is_valid_duration:
                    # Remove the saved file if duration is invalid
                    try:
                        os.remove(file_path)
                    except:
                        pass
                    return False, duration_message, None

                # Generate thumbnail for video
                thumbnail_name = self.generate_video_thumbnail(file_path)
                if thumbnail_name:
                    print(f"Generated video thumbnail: {thumbnail_name}")
                else:
                    print("Failed to generate video thumbnail")
            else:
                # Save other files as-is
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(file_data)

            return True, "File saved successfully", new_filename

        except Exception as e:
            return False, f"Error saving file: {str(e)}", None
    
    def get_file_info(self, filename: str) -> dict:
        """Get information about an uploaded file."""
        file_path = os.path.join(self.UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            return {}
        
        stat = os.stat(file_path)
        file_type = "image" if self.is_image(filename) else "video"
        
        info = {
            'filename': filename,
            'file_path': file_path,
            'file_size': stat.st_size,
            'file_type': file_type,
            'created_at': datetime.fromtimestamp(stat.st_ctime),
            'modified_at': datetime.fromtimestamp(stat.st_mtime),
        }
        
        # Get image dimensions if it's an image
        if file_type == "image":
            try:
                with Image.open(file_path) as img:
                    info['width'] = img.width
                    info['height'] = img.height
            except:
                pass
        
        return info
    
    def delete_file(self, filename: str) -> bool:
        """Delete an uploaded file."""
        try:
            file_path = os.path.join(self.UPLOAD_DIR, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {filename}: {e}")
            return False
    
    def get_file_hash(self, file_data: bytes) -> str:
        """Generate hash for file deduplication."""
        return hashlib.md5(file_data).hexdigest()


# Create global instance
file_handler = FileHandler()