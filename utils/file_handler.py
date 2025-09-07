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
    
    UPLOAD_DIR = "static/uploads"
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    TARGET_WIDTH = 1920
    TARGET_HEIGHT = 1080
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
    
    def __init__(self):
        """Initialize FileHandler."""
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
    
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
            else:
                # Save video files as-is
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