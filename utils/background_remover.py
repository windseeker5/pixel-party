#!/usr/bin/env python3
"""
Background Removal Utility for PixelParty

A robust Python utility script that removes backgrounds from images using AI-powered models.
Supports both single image files and batch processing of entire folders.

Dependencies:
    pip install rembg pillow tqdm

Usage:
    python background_remover.py /path/to/image.jpg
    python background_remover.py /path/to/folder --output /path/to/output
    python background_remover.py /path/to/folder --model u2net_human_seg
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional, Tuple
import tempfile

try:
    from PIL import Image
    from tqdm import tqdm
    import rembg
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install required packages:")
    print("pip install rembg pillow tqdm")
    sys.exit(1)


class BackgroundRemover:
    """
    A utility class for removing backgrounds from images using AI models.
    """
    
    # Supported image formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
    
    # Available rembg models
    AVAILABLE_MODELS = [
        'u2net',           # General use
        'u2net_human_seg', # Human segmentation
        'u2netp',          # Lightweight general use
        'silueta',         # General use (alternative)
        'isnet-general-use', # Improved general use
    ]
    
    def __init__(self, model_name: str = 'u2net', output_dir: Optional[str] = None):
        """
        Initialize the BackgroundRemover.
        
        Args:
            model_name: Name of the AI model to use
            output_dir: Output directory for processed images
        """
        self.model_name = model_name
        self.output_dir = output_dir
        self.session = None
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Validate model
        if model_name not in self.AVAILABLE_MODELS:
            self.logger.warning(f"Model '{model_name}' not in known models. Proceeding anyway...")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger('background_remover')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_session(self):
        """Initialize the rembg session."""
        if self.session is None:
            try:
                self.logger.info(f"Loading AI model: {self.model_name}")
                self.session = rembg.new_session(self.model_name)
                self.logger.info("Model loaded successfully")
            except Exception as e:
                self.logger.error(f"Failed to load model '{self.model_name}': {e}")
                raise
    
    def _is_supported_format(self, file_path: Path) -> bool:
        """Check if file format is supported."""
        return file_path.suffix.lower() in self.SUPPORTED_FORMATS
    
    def _get_output_path(self, input_path: Path, input_root: Optional[Path] = None) -> Path:
        """
        Generate output path for processed image.
        
        Args:
            input_path: Path to input image
            input_root: Root directory of input (for maintaining folder structure)
            
        Returns:
            Path object for output file
        """
        if self.output_dir:
            output_dir = Path(self.output_dir)
            
            if input_root and input_path.is_relative_to(input_root):
                # Maintain folder structure
                relative_path = input_path.relative_to(input_root)
                output_path = output_dir / relative_path.parent / f"{relative_path.stem}_no_bg.png"
            else:
                # Simple output
                output_path = output_dir / f"{input_path.stem}_no_bg.png"
        else:
            # Output in same directory as input
            output_path = input_path.parent / f"{input_path.stem}_no_bg.png"
        
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        return output_path
    
    def remove_background(self, input_path: Path, output_path: Optional[Path] = None) -> bool:
        """
        Remove background from a single image.
        
        Args:
            input_path: Path to input image
            output_path: Path for output image (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Initialize session if needed
            self._initialize_session()
            
            # Validate input
            if not input_path.exists():
                self.logger.error(f"Input file does not exist: {input_path}")
                return False
            
            if not self._is_supported_format(input_path):
                self.logger.error(f"Unsupported file format: {input_path.suffix}")
                return False
            
            # Generate output path if not provided
            if output_path is None:
                output_path = self._get_output_path(input_path)
            
            self.logger.debug(f"Processing: {input_path} -> {output_path}")
            
            # Load and process image
            with open(input_path, 'rb') as input_file:
                input_data = input_file.read()
            
            # Remove background
            output_data = rembg.remove(input_data, session=self.session)
            
            # Save result
            with open(output_path, 'wb') as output_file:
                output_file.write(output_data)
            
            # Verify output file was created and has content
            if output_path.exists() and output_path.stat().st_size > 0:
                self.logger.debug(f"Successfully processed: {input_path}")
                return True
            else:
                self.logger.error(f"Output file was not created or is empty: {output_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing {input_path}: {e}")
            return False
    
    def find_images(self, directory: Path) -> List[Path]:
        """
        Find all supported image files in a directory recursively.
        
        Args:
            directory: Directory to search
            
        Returns:
            List of image file paths
        """
        images = []
        for file_path in directory.rglob('*'):
            if file_path.is_file() and self._is_supported_format(file_path):
                images.append(file_path)
        return sorted(images)
    
    def process_directory(self, input_dir: Path) -> Tuple[int, int]:
        """
        Process all images in a directory.
        
        Args:
            input_dir: Directory containing images to process
            
        Returns:
            Tuple of (successful_count, total_count)
        """
        if not input_dir.exists() or not input_dir.is_dir():
            self.logger.error(f"Input directory does not exist: {input_dir}")
            return 0, 0
        
        # Find all images
        image_files = self.find_images(input_dir)
        
        if not image_files:
            self.logger.warning(f"No supported image files found in: {input_dir}")
            return 0, 0
        
        self.logger.info(f"Found {len(image_files)} images to process")
        
        # Process images with progress bar
        successful = 0
        
        with tqdm(image_files, desc="Removing backgrounds", unit="image") as pbar:
            for image_path in pbar:
                pbar.set_postfix(file=image_path.name)
                
                output_path = self._get_output_path(image_path, input_dir)
                
                if self.remove_background(image_path, output_path):
                    successful += 1
                
                pbar.set_postfix(
                    file=image_path.name,
                    success_rate=f"{successful}/{pbar.n + 1}"
                )
        
        self.logger.info(f"Processing complete: {successful}/{len(image_files)} successful")
        return successful, len(image_files)
    
    def process_single_file(self, input_file: Path) -> bool:
        """
        Process a single image file.
        
        Args:
            input_file: Path to image file
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Processing single file: {input_file}")
        output_path = self._get_output_path(input_file)
        
        success = self.remove_background(input_file, output_path)
        
        if success:
            self.logger.info(f"Successfully saved: {output_path}")
        else:
            self.logger.error(f"Failed to process: {input_file}")
        
        return success


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Remove backgrounds from images using AI models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single image
  python background_remover.py photo.jpg
  
  # Process folder with custom output directory
  python background_remover.py /path/to/photos --output /path/to/output
  
  # Use different AI model
  python background_remover.py photos/ --model u2net_human_seg
  
  # Enable verbose logging
  python background_remover.py photos/ --verbose

Available Models:
  u2net            - General use (default)
  u2net_human_seg  - Human segmentation
  u2netp           - Lightweight general use
  silueta          - General use (alternative)
  isnet-general-use - Improved general use
        """
    )
    
    parser.add_argument(
        'input',
        type=str,
        help='Input image file or directory'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output directory (default: same as input)'
    )
    
    parser.add_argument(
        '--model', '-m',
        type=str,
        default='u2net',
        choices=BackgroundRemover.AVAILABLE_MODELS,
        help='AI model to use for background removal (default: u2net)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--list-models',
        action='store_true',
        help='List available AI models and exit'
    )
    
    args = parser.parse_args()
    
    # List models and exit
    if args.list_models:
        print("Available AI models:")
        for model in BackgroundRemover.AVAILABLE_MODELS:
            print(f"  - {model}")
        return
    
    # Set logging level
    if args.verbose:
        logging.getLogger('background_remover').setLevel(logging.DEBUG)
    
    # Validate input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        sys.exit(1)
    
    # Create remover instance
    try:
        remover = BackgroundRemover(
            model_name=args.model,
            output_dir=args.output
        )
    except Exception as e:
        print(f"Error initializing background remover: {e}")
        sys.exit(1)
    
    # Process input
    try:
        if input_path.is_file():
            # Single file
            success = remover.process_single_file(input_path)
            sys.exit(0 if success else 1)
        
        elif input_path.is_dir():
            # Directory
            successful, total = remover.process_directory(input_path)
            
            if total == 0:
                print("No images found to process")
                sys.exit(1)
            
            success_rate = (successful / total) * 100
            print(f"\nProcessing summary:")
            print(f"  Total images: {total}")
            print(f"  Successful: {successful}")
            print(f"  Failed: {total - successful}")
            print(f"  Success rate: {success_rate:.1f}%")
            
            sys.exit(0 if successful > 0 else 1)
        
        else:
            print(f"Error: Input is neither a file nor directory: {input_path}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()