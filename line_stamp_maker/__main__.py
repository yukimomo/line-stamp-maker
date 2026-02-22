def _preflight_check():
    missing = []
    try:
        import numpy as np
    except ImportError:
        missing.append(("numpy", "pip install numpy"))
    try:
        import mediapipe
    except ImportError:
        missing.append(("mediapipe", "pip install mediapipe"))
    try:
        import pillow_heif
    except ImportError:
        # pillow-heifはHEIC/HEIF入力時のみ必須
        pass
    if missing:
        for name, cmd in missing:
            print(f"[ERR] Missing dependency: {name}\n  Install with: {cmd}")
        sys.exit(1)

"""CLI entry point for line-stamp-maker"""

import json
import shutil
import logging
import sys
from pathlib import Path
from typing import Optional
import typer
from dotenv import load_dotenv

from .config import ProcessingConfig, ImageConfig, TextConfig
from .image_processor import ImageProcessor
from .mapping import load_mapping, get_mapping_dict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def _safe_print(text: str, color=None, bold=False) -> None:
    """Print text safely, handling emoji encoding issues on Windows"""
    # Replace common emojis with text equivalents for Windows compatibility
    replacements = {
        "🎨": "[ART]",
        "✓": "[OK]",
        "✗": "[X]",
        "❌": "[ERR]",
        "📸": "[PHOTO]",
        "📦": "[PKG]",
        "⚠": "[WARN]",
        "ℹ": "[INFO]",
    }
    
    for emoji, replacement in replacements.items():
        text = text.replace(emoji, replacement)
    
    try:
        typer.secho(text, fg=color, bold=bold)
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Fallback: print without color
        print(text)
    
    # Ensure output is flushed immediately
    sys.stdout.flush()


_preflight_check()
app = typer.Typer(
    name="line-stamp-maker",
    help="Create LINE stickers from photos with person segmentation and text overlay"
)


@app.command()
def process(
    photos_dir: Path = typer.Option(
        Path("photos"),
        "--photos", "-p",
        help="入力画像フォルダ [default: photos]"
    ),
    mapping_file: Path = typer.Option(
        Path("mapping.csv"),
        "--mapping", "-m",
        help="マッピング CSV ファイル [default: mapping.csv]"
    ),
    output_dir: Path = typer.Option(
        Path("out"),
        "--output", "-o",
        help="出力フォルダ [default: out]"
    ),
    sticker_width: int = typer.Option(
        370,
        "--sticker-width",
        help="ステッカー最大幅 [default: 370]"
    ),
    sticker_height: int = typer.Option(
        320,
        "--sticker-height",
        help="ステッカー最大高さ [default: 320]"
    ),
    border_width: int = typer.Option(
        8,
        "--border", "-b",
        help="白ふち幅（ピクセル） [default: 8]"
    ),
    font_size: int = typer.Option(
        24,
        "--font-size", "-f",
        help="フォントサイズ [default: 24]"
    ),
    font_preset: str = typer.Option(
        "rounded",
        "--font-preset",
        help="フォントプリセット (rounded|maru|kiwi|noto|indie-flower|kalam|cabin-sketch) [default: rounded]"
    ),
    font_path: Optional[Path] = typer.Option(
        None,
        "--font-path",
        help="カスタムフォントファイルパス [optional]"
    ),
    caption_style: str = typer.Option(
        "bubble",
        "--caption-style",
        help="キャプションスタイル (band, bubble, none) [default: bubble]"
    ),
    caption_outline_px: int = typer.Option(
        6,
        "--caption-outline-px",
        help="キャプション文字の縁取り幅 [default: 6]"
    ),
    caption_padding_ratio: float = typer.Option(
        0.06,
        "--caption-padding-ratio",
        help="キャプション余白比率 [default: 0.06]"
    ),
    caption_max_lines: int = typer.Option(
        2,
        "--caption-max-lines",
        help="キャプション最大行数 [default: 2]"
    ),
    caption_text_color: str = typer.Option(
        "255,255,255",
        "--caption-text-color",
        help="キャプション文字色 R,G,B [default: 255,255,255]"
    ),
    caption_outline_color: str = typer.Option(
        "0,0,0",
        "--caption-outline-color",
        help="キャプション縁取り色 R,G,B [default: 0,0,0]"
    ),
    ext_priority: str = typer.Option(
        "heic,jpg,jpeg,png,webp",
        "--ext-priority",
        help="ファイル拡張子優先度 [default: heic,jpg,jpeg,png,webp]"
    ),
    no_segmentation: bool = typer.Option(
        False,
        "--no-segmentation",
        help="人物セグメンテーションをスキップ"
    ),
    no_face_detection: bool = typer.Option(
        True,
        "--no-face-detection/--enable-face-detection",
        help="顔検出をスキップ [default: --no-face-detection]"
    ),
    no_shadow: bool = typer.Option(
        False,
        "--no-shadow",
        help="影効果を無効化"
    ),
    create_zip: bool = typer.Option(
        True,
        "--zip/--no-zip",
        help="ZIP ファイルの作成 [default: --zip]"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="詳細なログを表示"
    ),
):
    """
    Process photos to create LINE stickers.
    
    Example:
        python -m line_stamp_maker process --photos photos --mapping mapping.csv --output out
    """
    # Set logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    _safe_print("🎨 LINE Stamp Maker", color=typer.colors.CYAN, bold=True)
    
    # Validate input files
    if not photos_dir.exists():
        _safe_print(f"❌ Photos directory not found: {photos_dir}", color=typer.colors.RED)
        raise typer.Exit(1)
    
    if not mapping_file.exists():
        _safe_print(f"❌ Mapping file not found: {mapping_file}", color=typer.colors.RED)
        raise typer.Exit(1)
    
    # Load mapping with file resolution
    try:
        entries = load_mapping(mapping_file, photos_dir, ext_priority=ext_priority)
        mapping = get_mapping_dict(entries)
        
        resolved = sum(1 for entry in entries if entry.resolved_path is not None)
        _safe_print(f"✓ Loaded {len(entries)} entries, {resolved} files resolved", color=typer.colors.GREEN)
        
        if resolved == 0:
            _safe_print(f"❌ No files were resolved from mapping", color=typer.colors.RED)
            raise typer.Exit(1)
    
    except Exception as e:
        _safe_print(f"❌ Error loading mapping: {e}", color=typer.colors.RED)
        raise typer.Exit(1)
    
    # Parse color strings
    def parse_color(color_str: str) -> tuple[int, int, int]:
        """Parse color string like '255,255,255' to (R, G, B) tuple"""
        try:
            parts = [int(x.strip()) for x in color_str.split(',')]
            if len(parts) != 3 or any(not 0 <= p <= 255 for p in parts):
                raise ValueError()
            return tuple(parts)  # type: ignore
        except (ValueError, IndexError):
            _safe_print(f"❌ Invalid color format: {color_str} (use R,G,B like 255,255,255)", color=typer.colors.RED)
            raise typer.Exit(1)
    
    caption_text_rgb = parse_color(caption_text_color)
    caption_outline_rgb = parse_color(caption_outline_color)
    
    # Create configuration
    image_config = ImageConfig(
        sticker_max_width=sticker_width,
        sticker_max_height=sticker_height,
        border_width=border_width,
        shadow_enabled=not no_shadow
    )
    
    text_config = TextConfig(
        font_size=font_size,
        font_preset=font_preset,
        font_path=font_path,
        caption_style=caption_style,
        caption_text_color=caption_text_rgb,
        caption_outline_color=caption_outline_rgb,
        caption_outline_px=caption_outline_px,
        caption_padding_ratio=caption_padding_ratio,
        caption_max_lines=caption_max_lines
    )
    
    config = ProcessingConfig(
        photos_dir=photos_dir,
        mapping_file=mapping_file,
        output_dir=output_dir,
        image_config=image_config,
        text_config=text_config,
        detect_face=not no_face_detection,
        use_segmentation=not no_segmentation,
        create_zip=create_zip,
        verbose=verbose
    )
    
    # Create processor
    try:
        processor = ImageProcessor(config)
    except Exception as e:
        _safe_print(f"❌ Error initializing processor: {e}", color=typer.colors.RED)
        raise typer.Exit(1)
    
    # Process batch
    _safe_print("\n📸 Processing images...", color=typer.colors.CYAN)
    try:
        results = processor.process_batch(mapping)
    except Exception as e:
        _safe_print(f"❌ Error during processing: {e}", color=typer.colors.RED)
        import traceback
        _safe_print(traceback.format_exc(), color=typer.colors.RED)
        raise typer.Exit(1)
    
    # Summary
    successful = sum(1 for r in results.values() if r["status"] == "success")
    failed = sum(1 for r in results.values() if r["status"] == "error")
    
    _safe_print(f"\n✓ Completed: {successful} successful, {failed} failed", color=typer.colors.GREEN)
    
    # Create zip if requested
    if create_zip and successful > 0:
        try:
            zip_path = create_upload_zip(config.output_dir)
            _safe_print(f"✓ Created {zip_path}", color=typer.colors.GREEN)
        except Exception as e:
            _safe_print(f"⚠ Could not create ZIP: {e}", color=typer.colors.YELLOW)
    
    # Save results summary
    try:
        results_file = config.output_dir / "results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        _safe_print(f"✓ Results saved to {results_file}", color=typer.colors.GREEN)
    except Exception as e:
        _safe_print(f"⚠ Could not save results: {e}", color=typer.colors.YELLOW)
    
    _safe_print(f"✓ Output directory: {config.output_dir.absolute()}", color=typer.colors.GREEN)


@app.command()
def info():
    """Show information about the tool"""
    from . import __version__
    
    _safe_print("LINE Stamp Maker", bold=True, color=typer.colors.CYAN)
    _safe_print(f"Version: {__version__}", color=typer.colors.BLUE)
    _safe_print("\nUsage:", bold=True)
    _safe_print("  python -m line_stamp_maker process [OPTIONS]", color=typer.colors.GREEN)
    _safe_print("\nExample:", bold=True)
    _safe_print("  python -m line_stamp_maker process \\")
    _safe_print("    --photos photos \\")
    _safe_print("    --mapping mapping.csv \\")
    _safe_print("    --output out")
    _safe_print("\nMapping CSV Format:", bold=True)
    _safe_print("  filename,text")
    _safe_print("  photo1.jpg,\"Hello World\"")
    _safe_print("  photo2.jpg,\"Line 1\\nLine 2\"")


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


@app.command()
def fonts_download(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force re-download of all fonts"
    )
):
    """Download and install font presets for text rendering.
    
    Supported presets:
      - rounded: Rounded serif font
      - maru: Maru Gothic (Japanese rounded gothic)
      - kiwi: Kiwi Maru (Japanese rounded font)
      - noto: Noto Sans JP (Japanese sans-serif)
    
    This command downloads fonts from Google Fonts and other sources
    into line_stamp_maker/assets/fonts/
    
    Example:
        python -m line_stamp_maker fonts-download
    """
    import subprocess
    from pathlib import Path
    
    _safe_print("📦 Downloading fonts for LINE Stamp Maker...", color=typer.colors.CYAN, bold=True)
    
    # Determine OS and run appropriate script
    script_dir = Path(__file__).parent.parent / "scripts"
    
    # Try Python script first (cross-platform)
    python_script = script_dir / "download_fonts.py"
    
    try:
        cmd = [sys.executable, str(python_script)]
        if force:
            cmd.append("--force")
        
        result = subprocess.run(cmd, check=False, capture_output=False)
        
        if result.returncode == 0:
            _safe_print("\n[OK] Fonts downloaded successfully!", color=typer.colors.GREEN, bold=True)
        else:
            _safe_print("\n[WARN] Font download completed with warnings", color=typer.colors.YELLOW)
            _safe_print("Please check the output above for details")
    
    except Exception as e:
        _safe_print(f"\n[ERR] Error running font download script: {e}", color=typer.colors.RED)
        _safe_print("You can manually download fonts from Google Fonts and place them in:", color=typer.colors.YELLOW)
        fonts_dir = Path(__file__).parent / "assets" / "fonts"
        _safe_print(f"  {fonts_dir}", color=typer.colors.YELLOW)
        raise typer.Exit(1)


# Entry point
app()




# Entry point for python -m line_stamp_maker
app()
