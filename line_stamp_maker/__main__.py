"""CLI entry point for line-stamp-maker"""

import json
import shutil
from pathlib import Path
from typing import Optional
import typer
from dotenv import load_dotenv

from .config import ProcessingConfig, ImageConfig, TextConfig
from .image_processor import ImageProcessor
from .utils import load_mapping_csv

# Load environment variables
load_dotenv()

app = typer.Typer(
    name="line-stamp-maker",
    help="Create LINE stickers from photos with person segmentation and text overlay"
)


@app.command()
def process(
    photos_dir: Path = typer.Option(
        Path("photos"),
        "--photos",
        "-p",
        help="Directory containing input photos"
    ),
    mapping_file: Path = typer.Option(
        Path("mapping.csv"),
        "--mapping",
        "-m",
        help="CSV file with filename and text mapping (format: filename,text)"
    ),
    output_dir: Path = typer.Option(
        Path("out"),
        "--output",
        "-o",
        help="Output directory for stickers"
    ),
    sticker_width: int = typer.Option(
        370,
        "--sticker-width",
        help="Maximum sticker width (maintains aspect ratio)"
    ),
    sticker_height: int = typer.Option(
        320,
        "--sticker-height",
        help="Maximum sticker height (maintains aspect ratio)"
    ),
    border_width: int = typer.Option(
        8,
        "--border",
        "-b",
        help="White border width in pixels"
    ),
    font_size: int = typer.Option(
        24,
        "--font-size",
        "-f",
        help="Font size for text overlay"
    ),
    no_segmentation: bool = typer.Option(
        False,
        "--no-segmentation",
        help="Skip person segmentation (use image as-is)"
    ),
    no_face_detection: bool = typer.Option(
        False,
        "--no-face-detection",
        help="Skip face detection for cropping"
    ),
    no_shadow: bool = typer.Option(
        False,
        "--no-shadow",
        help="Disable shadow effect"
    ),
    create_zip: bool = typer.Option(
        True,
        "--zip/--no-zip",
        help="Create upload.zip for LINE Creators Market"
    ),
):
    """
    Process photos to create LINE stickers.
    
    Example:
        python -m line_stamp_maker process --photos photos --mapping mapping.csv --output out
    """
    typer.secho("🎨 LINE Stamp Maker", bold=True, fg=typer.colors.CYAN)
    
    # Validate input files
    if not photos_dir.exists():
        typer.secho(f"❌ Photos directory not found: {photos_dir}", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    if not mapping_file.exists():
        typer.secho(f"❌ Mapping file not found: {mapping_file}", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    # Load mapping
    try:
        mapping = load_mapping_csv(mapping_file)
        typer.secho(f"✓ Loaded {len(mapping)} images from mapping", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"❌ Error loading mapping: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    # Create configuration
    image_config = ImageConfig(
        sticker_max_width=sticker_width,
        sticker_max_height=sticker_height,
        border_width=border_width,
        shadow_enabled=not no_shadow
    )
    
    text_config = TextConfig(font_size=font_size)
    
    config = ProcessingConfig(
        photos_dir=photos_dir,
        mapping_file=mapping_file,
        output_dir=output_dir,
        image_config=image_config,
        text_config=text_config,
        detect_face=not no_face_detection,
        use_segmentation=not no_segmentation,
        create_zip=create_zip
    )
    
    # Create processor
    try:
        processor = ImageProcessor(config)
    except Exception as e:
        typer.secho(f"❌ Error initializing processor: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    # Process batch
    typer.secho("\n📸 Processing images...", fg=typer.colors.CYAN)
    results = processor.process_batch(mapping)
    
    # Summary
    successful = sum(1 for r in results.values() if r["status"] == "success")
    failed = sum(1 for r in results.values() if r["status"] == "error")
    
    typer.secho(f"\n✓ Completed: {successful} successful, {failed} failed", fg=typer.colors.GREEN)
    
    # Create zip if requested
    if create_zip and successful > 0:
        try:
            zip_path = create_upload_zip(config.output_dir)
            typer.secho(f"✓ Created {zip_path}", fg=typer.colors.GREEN)
        except Exception as e:
            typer.secho(f"⚠ Could not create ZIP: {e}", fg=typer.colors.YELLOW)
    
    # Save results summary
    results_file = config.output_dir / "results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    typer.secho(f"✓ Results saved to {results_file}", fg=typer.colors.GREEN)
    typer.secho(f"✓ Output directory: {config.output_dir.absolute()}", fg=typer.colors.GREEN)


@app.command()
def info():
    """Show information about the tool"""
    from . import __version__
    
    typer.secho("LINE Stamp Maker", bold=True, fg=typer.colors.CYAN)
    typer.secho(f"Version: {__version__}", fg=typer.colors.BLUE)
    typer.secho("\nUsage:", bold=True)
    typer.secho("  python -m line_stamp_maker process [OPTIONS]", fg=typer.colors.GREEN)
    typer.secho("\nExample:", bold=True)
    typer.secho("  python -m line_stamp_maker process \\", dim=True)
    typer.secho("    --photos photos \\", dim=True)
    typer.secho("    --mapping mapping.csv \\", dim=True)
    typer.secho("    --output out", dim=True)
    typer.secho("\nMapping CSV Format:", bold=True)
    typer.secho("  filename,text", dim=True)
    typer.secho("  photo1.jpg,\"Hello World\"", dim=True)
    typer.secho("  photo2.jpg,\"Line 1\\nLine 2\"", dim=True)


def create_upload_zip(output_dir: Path) -> Path:
    """
    Create upload.zip for LINE Creators Market.
    
    Structure:
    upload.zip
    ├── stickers/
    │   ├── 01.png
    │   ├── 02.png
    │   └── ...
    ├── main.png (first image as main)
    └── tab.png (first image as tab)
    
    Args:
        output_dir: Output directory
        
    Returns:
        Path to created zip file
    """
    zip_path = output_dir / "upload.zip"
    
    # Create temporary directory structure
    temp_dir = output_dir / ".temp_zip"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Copy stickers
        stickers_src = output_dir / "stickers"
        stickers_dst = temp_dir / "stickers"
        
        if stickers_src.exists():
            if stickers_dst.exists():
                shutil.rmtree(stickers_dst)
            shutil.copytree(stickers_src, stickers_dst)
        
        # Copy main and tab images (use first ones)
        main_files = list(output_dir.glob("main_*.png"))
        tab_files = list(output_dir.glob("tab_*.png"))
        
        if main_files:
            shutil.copy(main_files[0], temp_dir / "main.png")
        
        if tab_files:
            shutil.copy(tab_files[0], temp_dir / "tab.png")
        
        # Create zip
        shutil.make_archive(str(zip_path.with_suffix('')), 'zip', temp_dir)
        
        return zip_path
    
    finally:
        # Clean up temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    app()
