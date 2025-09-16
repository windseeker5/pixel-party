#!/usr/bin/env python3
"""
Example script demonstrating how to use the background remover utility
in the context of the PixelParty application.

This script shows how to:
1. Process uploaded party photos to remove backgrounds
2. Integrate background removal into the photo processing workflow
3. Handle the processed images for slideshow display

Usage:
    python example_background_removal.py
"""

import os
import sys
from pathlib import Path

# Add utils to path so we can import our background remover
sys.path.append(str(Path(__file__).parent / 'utils'))

try:
    from background_remover import BackgroundRemover
except ImportError:
    print("Background remover not available. Install dependencies with:")
    print("pip install rembg pillow tqdm")
    sys.exit(1)


def process_party_photos():
    """
    Example: Process all uploaded party photos to remove backgrounds.
    
    This could be integrated into the PixelParty app to automatically
    create clean versions of guest photos for special slideshow effects.
    """
    # Paths based on PixelParty directory structure
    photos_dir = Path("media/photos")
    output_dir = Path("media/photos_no_bg")
    
    if not photos_dir.exists():
        print(f"Photos directory doesn't exist: {photos_dir}")
        print("This example requires the PixelParty media/photos directory.")
        return
    
    # Initialize background remover with human segmentation model
    # (best for party photos with people)
    remover = BackgroundRemover(
        model_name='u2net_human_seg',
        output_dir=str(output_dir)
    )
    
    print("Processing party photos to remove backgrounds...")
    print(f"Input: {photos_dir}")
    print(f"Output: {output_dir}")
    
    # Process all photos
    successful, total = remover.process_directory(photos_dir)
    
    if total > 0:
        success_rate = (successful / total) * 100
        print(f"\n✅ Processing complete!")
        print(f"   Processed: {successful}/{total} photos ({success_rate:.1f}% success)")
        print(f"   Output saved to: {output_dir}")
    else:
        print("❌ No photos found to process")


def process_single_photo_example():
    """
    Example: Process a single photo with error handling.
    
    This shows how to integrate background removal into the photo
    upload workflow in the PixelParty app.
    """
    # Example photo path
    photo_path = Path("media/photos/example_guest_photo.jpg")
    
    if not photo_path.exists():
        print(f"Example photo not found: {photo_path}")
        print("Create a test photo to see this example in action.")
        return
    
    # Initialize background remover
    remover = BackgroundRemover(model_name='u2net_human_seg')
    
    print(f"Processing single photo: {photo_path}")
    
    # Process the photo
    success = remover.process_single_file(photo_path)
    
    if success:
        output_path = photo_path.parent / f"{photo_path.stem}_no_bg.png"
        print(f"✅ Success! Background removed photo saved: {output_path}")
    else:
        print("❌ Failed to process photo")


def integration_example():
    """
    Example showing how to integrate background removal into
    the PixelParty photo processing pipeline.
    """
    print("Background Removal Integration Example")
    print("=" * 50)
    
    # This could be called from app/services/file_handler.py
    # after a photo is uploaded and resized
    
    def process_uploaded_photo(uploaded_file_path: Path) -> tuple[bool, Path]:
        """
        Process an uploaded photo to create a background-removed version.
        
        Returns:
            (success: bool, processed_path: Path)
        """
        try:
            # Initialize remover (could be a singleton in the app)
            remover = BackgroundRemover(model_name='u2net_human_seg')
            
            # Generate output path
            no_bg_path = uploaded_file_path.parent / f"{uploaded_file_path.stem}_no_bg.png"
            
            # Remove background
            success = remover.remove_background(uploaded_file_path, no_bg_path)
            
            return success, no_bg_path
            
        except Exception as e:
            print(f"Background removal failed: {e}")
            return False, uploaded_file_path
    
    # Example usage in photo upload handler
    example_photo = Path("media/photos/guest_upload.jpg")
    
    if example_photo.exists():
        success, processed_path = process_uploaded_photo(example_photo)
        
        if success:
            print(f"✅ Photo processed successfully: {processed_path}")
            # Could now use both original and background-removed versions
            # in the slideshow for different visual effects
        else:
            print("❌ Background removal failed, using original photo")
    else:
        print(f"Example photo not found: {example_photo}")
        print("This would work with actual uploaded photos in the app.")


def main():
    """Main example runner."""
    print("PixelParty Background Removal Examples")
    print("=" * 40)
    
    print("\n1. Batch Processing Example:")
    print("-" * 30)
    process_party_photos()
    
    print("\n2. Single Photo Example:")
    print("-" * 25)
    process_single_photo_example()
    
    print("\n3. Integration Example:")
    print("-" * 22)
    integration_example()
    
    print("\n💡 Tips for PixelParty Integration:")
    print("   - Use 'u2net_human_seg' model for party photos with people")
    print("   - Process photos after upload but before slideshow display")
    print("   - Keep both original and background-removed versions")
    print("   - Use background-removed photos for special overlay effects")
    print("   - Consider processing in background thread to avoid blocking uploads")


if __name__ == "__main__":
    main()