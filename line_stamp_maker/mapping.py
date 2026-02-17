"""Mapping file handling with robust file resolution"""

import csv
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class MappingEntry:
    """Single mapping entry with resolved file path"""
    
    def __init__(self, filename: str, text: str, resolved_path: Optional[Path] = None):
        """
        Initialize mapping entry.
        
        Args:
            filename: Filename from mapping.csv
            text: Text to overlay
            resolved_path: Actual resolved file path
        """
        self.filename = filename
        self.text = text.strip() if text else ""
        self.resolved_path = resolved_path
    
    def __repr__(self) -> str:
        return f"MappingEntry(filename={self.filename!r}, text={self.text[:30]!r}..., resolved={self.resolved_path})"


def load_mapping(csv_path: Path, photos_dir: Path, 
                 ext_priority: list[str] | str = "heic,jpg,jpeg,png,webp") -> list[MappingEntry]:
    """
    Load mapping from CSV file with file resolution.
    
    Args:
        csv_path: Path to mapping.csv file
        photos_dir: Directory containing photos
        ext_priority: Priority list of extensions (comma-separated string or list)
                     Defaults to "heic,jpg,jpeg,png,webp"
    
    Returns:
        List of MappingEntry objects with resolved file paths
        
    Raises:
        FileNotFoundError: If mapping.csv is not found
        ValueError: If CSV format is invalid
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Mapping file not found: {csv_path}")
    
    if not photos_dir.exists():
        raise FileNotFoundError(f"Photos directory not found: {photos_dir}")
    
    # Parse extension priority
    if isinstance(ext_priority, str):
        ext_priority = [ext.strip().lower() for ext in ext_priority.split(",")]
    else:
        ext_priority = [ext.strip().lower() for ext in ext_priority]
    
    # Ensure extensions start with dot
    ext_priority = [f".{ext}" if not ext.startswith(".") else ext for ext in ext_priority]
    
    logger.debug(f"Extension priority: {ext_priority}")
    
    entries = []
    
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            if reader.fieldnames is None or "filename" not in reader.fieldnames:
                raise ValueError("CSV must have 'filename' column")
            
            for row_num, row in enumerate(reader, start=2):  # start=2 because header is row 1
                filename = row.get("filename", "").strip()
                text = row.get("text", "").strip()
                
                if not filename:
                    logger.warning(f"Row {row_num}: Empty filename, skipping")
                    continue
                
                # Resolve file path
                resolved_path = _resolve_file(filename, photos_dir, ext_priority)
                
                if resolved_path is None:
                    logger.warning(f"Row {row_num}: Could not resolve file for '{filename}'")
                
                entry = MappingEntry(filename, text, resolved_path)
                entries.append(entry)
    
    except csv.Error as e:
        raise ValueError(f"Error reading CSV file {csv_path}: {e}")
    except Exception as e:
        raise ValueError(f"Error processing mapping file {csv_path}: {e}")
    
    if not entries:
        raise ValueError(f"No valid entries found in {csv_path}")
    
    logger.info(f"Loaded {len(entries)} entries from {csv_path}")
    return entries


def _resolve_file(filename: str, photos_dir: Path, ext_priority: list[str]) -> Optional[Path]:
    """
    Resolve a file in photos_dir with smart extension handling.
    
    Strategy:
    1. If filename exists exactly -> use it
    2. If filename has no extension:
       - Try to find file with same base name in priority order
       - If multiple found, use priority order and warn
    3. If filename has extension but not found:
       - Try to find by base name, prefer same extension
    
    Args:
        filename: Filename to resolve
        photos_dir: Directory to search in
        ext_priority: Priority list of extensions
        
    Returns:
        Resolved Path object or None if not found
    """
    photos_dir = Path(photos_dir)
    filepath = photos_dir / filename
    
    # Check exact match first
    if filepath.exists():
        logger.debug(f"Exact match found: {filepath}")
        return filepath
    
    # Parse filename
    base_path = Path(filename)
    base_name = base_path.stem
    file_ext = base_path.suffix.lower()
    
    # If no extension or exact not found, search by base name
    logger.debug(f"Searching for base name '{base_name}' with extensions {ext_priority}")
    
    candidates = []
    
    # Check all priority extensions
    for ext in ext_priority:
        candidate = photos_dir / f"{base_name}{ext}"
        if candidate.exists():
            candidates.append(candidate)
    
    # If no priority extensions matched, check all files with same base name
    if not candidates:
        for file_path in photos_dir.iterdir():
            if file_path.is_file() and file_path.stem == base_name:
                candidates.append(file_path)
    
    if not candidates:
        logger.debug(f"No file found for base name '{base_name}'")
        return None
    
    # Pick first candidate (respects priority)
    selected = candidates[0]
    
    # Warn if multiple candidates and different from original
    if len(candidates) > 1:
        logger.warning(
            f"Multiple files found for '{filename}': {[str(c.name) for c in candidates]}. "
            f"Selected: {selected.name}"
        )
    elif selected.name != filename:
        logger.debug(f"Resolved '{filename}' to '{selected.name}'")
    
    return selected


def get_mapping_dict(entries: list[MappingEntry]) -> dict[Path, str]:
    """
    Convert list of MappingEntry to dict of [Path -> text].
    
    Only includes entries with successfully resolved paths.
    
    Args:
        entries: List of MappingEntry objects
        
    Returns:
        Dictionary mapping resolved Path to text
    """
    return {
        entry.resolved_path: entry.text
        for entry in entries
        if entry.resolved_path is not None
    }
