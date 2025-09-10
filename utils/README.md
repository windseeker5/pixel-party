# PixelParty Utilities

This directory contains utility scripts for the PixelParty application.

## Background Remover (`background_remover.py`)

A robust Python utility script that removes backgrounds from images using AI-powered models.

### Installation

Install the required dependencies:

```bash
pip install rembg pillow tqdm
```

Or install all project dependencies:

```bash
pip install -r requirements.txt
```

### Usage

#### Basic Usage

Process a single image:
```bash
python utils/background_remover.py path/to/image.jpg
```

Process all images in a folder:
```bash
python utils/background_remover.py path/to/folder/
```

#### Advanced Options

Specify output directory:
```bash
python utils/background_remover.py photos/ --output processed/
```

Use different AI model:
```bash
python utils/background_remover.py photos/ --model u2net_human_seg
```

Enable verbose logging:
```bash
python utils/background_remover.py photos/ --verbose
```

List available models:
```bash
python utils/background_remover.py --list-models
```

### Available AI Models

- `u2net` (default) - General use
- `u2net_human_seg` - Human segmentation (best for people)
- `u2netp` - Lightweight general use
- `silueta` - General use (alternative)
- `isnet-general-use` - Improved general use

### Features

- **Batch Processing**: Process entire folders of images
- **Progress Tracking**: Visual progress bar with tqdm
- **Flexible Output**: Maintain folder structure or specify custom output
- **Error Handling**: Robust error handling and logging
- **Format Support**: JPG, JPEG, PNG, BMP, TIFF, WebP
- **Transparent Output**: All processed images saved as PNG with transparency

### Output

- Processed images are saved as PNG files with transparent backgrounds
- Original filename + `_no_bg.png` suffix
- When processing folders, the directory structure is preserved in the output

### Examples

```bash
# Process party photos
python utils/background_remover.py media/photos/ --output export/no_bg_photos/

# Process with human segmentation model for better people detection
python utils/background_remover.py media/photos/ --model u2net_human_seg --verbose

# Process single photo
python utils/background_remover.py media/photos/guest_photo.jpg
```

The utility is particularly useful for creating clean profile images or preparing photos for overlay effects in the PixelParty slideshow.