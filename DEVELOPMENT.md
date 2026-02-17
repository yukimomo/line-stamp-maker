# Development Setup Guide

This document provides instructions for setting up the development environment.

## Setup Steps

### 1. Install Python 3.11+

Ensure you have Python 3.11 or higher installed:

```bash
python --version
```

### 2. Create Virtual Environment (Optional but Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python -m line_stamp_maker info
```

You should see the tool version and usage information.

## Quick Start

### 1. Prepare Input Files

- Add photos to `photos/` folder
- Create/update `mapping.csv` with filenames and text

### 2. Run Processing

```bash
python -m line_stamp_maker process
```

### 3. Check Results

- View output in `out/` folder
- Check `out/results.json` for processing results

## Development

### Project Structure

```
line_stamp_maker/
├── __init__.py              # Package initialization
├── __main__.py              # CLI entry point
├── config.py                # Configuration & Pydantic models
├── image_processor.py       # Main processing pipeline
├── face_detection.py        # Face detection module
├── segmentation.py          # Person segmentation (MediaPipe)
├── text_renderer.py         # Text rendering
└── utils.py                 # Utility functions
```

### Adding New Features

1. **New Image Processor**: Add to `image_processor.py`
2. **New CLI Options**: Update `__main__.py` app command
3. **Configuration**: Add fields to relevant Config class in `config.py`

### Testing

```bash
# Manual testing
python -m line_stamp_maker process --help

# Test with sample images (create photos/sample.jpg first)
python -m line_stamp_maker process --photos photos --mapping mapping.csv
```

## Troubleshooting

### Import Errors

If you get import errors, try:

```bash
pip install --upgrade -r requirements.txt
```

### MediaPipe Issues

MediaPipe sometimes requires additional setup:

```bash
# Try reinstalling
pip uninstall mediapipe
pip install mediapipe
```

### Permission Issues (Windows)

If you get permission errors:

```bash
# Run in Administrator mode or use:
pip install --user -r requirements.txt
```

## Performance Tips

1. **Reduce Image Resolution**: Large images take longer to process
2. **Skip Unnecessary Steps**: Use `--no-face-detection` or `--no-segmentation` if not needed
3. **Batch Processing**: Process multiple images in one run (more efficient system resource usage)

## Environment Variables

Optional environment variables (create `.env` file):

```env
# Future configuration options can be added here
DEBUG=false
```

## Running from Different Directories

```bash
# From any directory, specify full paths
python -m line_stamp_maker process \
  -p C:\path\to\photos \
  -m C:\path\to\mapping.csv \
  -o C:\path\to\output
```

