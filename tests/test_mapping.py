"""Tests for mapping file handling"""

import csv
import logging
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from line_stamp_maker.mapping import (
    MappingEntry,
    load_mapping,
    get_mapping_dict,
    _resolve_file,
)


class TestMappingEntry:
    """Test suite for MappingEntry class"""
    
    def test_creates_entry_with_all_fields(self):
        """Test creating entry with all fields"""
        path = Path("/tmp/test.png")
        entry = MappingEntry("test.png", "hello", path)
        
        assert entry.filename == "test.png"
        assert entry.text == "hello"
        assert entry.resolved_path == path
    
    def test_strips_text_whitespace(self):
        """Test that text is stripped of whitespace"""
        entry = MappingEntry("test.png", "  hello  ")
        assert entry.text == "hello"
    
    def test_handles_empty_text(self):
        """Test handling of empty text"""
        entry = MappingEntry("test.png", "")
        assert entry.text == ""
    
    def test_handles_none_text(self):
        """Test handling of None text"""
        entry = MappingEntry("test.png", None)
        assert entry.text == ""


class TestResolveFile:
    """Test suite for _resolve_file function"""
    
    def test_exact_match_found(self):
        """Test exact filename match"""
        with TemporaryDirectory() as tmpdir:
            photos_dir = Path(tmpdir)
            
            # Create test file
            test_file = photos_dir / "photo.png"
            test_file.touch()
            
            result = _resolve_file("photo.png", photos_dir, [".png", ".jpg"])
            
            assert result == test_file
    
    def test_no_extension_resolves_with_priority(self):
        """Test base name without extension resolves with priority"""
        with TemporaryDirectory() as tmpdir:
            photos_dir = Path(tmpdir)
            
            # Create files
            jpg_file = photos_dir / "photo.jpg"
            png_file = photos_dir / "photo.png"
            jpg_file.touch()
            png_file.touch()
            
            # With jpg priority first
            result = _resolve_file("photo", photos_dir, [".jpg", ".png"])
            assert result == jpg_file
            
            # With png priority first
            result = _resolve_file("photo", photos_dir, [".png", ".jpg"])
            assert result == png_file
    
    def test_missing_extension_searches_by_basename(self):
        """Test searching by base name when extension is missing"""
        with TemporaryDirectory() as tmpdir:
            photos_dir = Path(tmpdir)
            
            # Create heic file
            heic_file = photos_dir / "photo.heic"
            heic_file.touch()
            
            result = _resolve_file("photo", photos_dir, [".heic", ".png", ".jpg"])
            assert result == heic_file
    
    def test_file_not_found_returns_none(self):
        """Test that None is returned when file not found"""
        with TemporaryDirectory() as tmpdir:
            photos_dir = Path(tmpdir)
            
            result = _resolve_file("nonexistent.png", photos_dir, [".png"])
            assert result is None
    
    def test_extension_case_insensitive(self):
        """Test that search is case-insensitive for extensions"""
        with TemporaryDirectory() as tmpdir:
            photos_dir = Path(tmpdir)
            
            # Create file with uppercase extension
            file_path = photos_dir / "photo.PNG"
            file_path.touch()
            
            result = _resolve_file("photo", photos_dir, [".png"])
            assert result == file_path
    
    def test_multiple_files_same_basename_warns(self, caplog):
        """Test that multiple files with same basename trigger warning"""
        with TemporaryDirectory() as tmpdir:
            photos_dir = Path(tmpdir)
            
            # Create multiple files with same base name
            heic_file = photos_dir / "photo.heic"
            png_file = photos_dir / "photo.png"
            heic_file.touch()
            png_file.touch()
            
            with caplog.at_level(logging.WARNING):
                result = _resolve_file("photo", photos_dir, [".heic", ".png"])
            
            # Should pick first by priority
            assert result == heic_file
            
            # Should have warning about multiple files
            assert any("Multiple files found" in record.message for record in caplog.records)


class TestLoadMapping:
    """Test suite for load_mapping function"""
    
    def test_loads_valid_csv(self):
        """Test loading valid CSV file"""
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            photos_dir = tmpdir / "photos"
            photos_dir.mkdir()
            
            # Create CSV
            csv_file = tmpdir / "mapping.csv"
            with open(csv_file, "w", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["filename", "text"])
                writer.writerow(["photo1.png", "Hello"])
                writer.writerow(["photo2.png", "World"])
            
            # Create dummy files
            (photos_dir / "photo1.png").touch()
            (photos_dir / "photo2.png").touch()
            
            entries = load_mapping(csv_file, photos_dir)
            
            assert len(entries) == 2
            assert entries[0].filename == "photo1.png"
            assert entries[0].text == "Hello"
            assert entries[1].filename == "photo2.png"
            assert entries[1].text == "World"
    
    def test_csv_not_found(self):
        """Test that FileNotFoundError is raised for missing CSV"""
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            with pytest.raises(FileNotFoundError):
                load_mapping(tmpdir / "missing.csv", tmpdir)
    
    def test_photos_dir_not_found(self):
        """Test that FileNotFoundError is raised for missing photos dir"""
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            csv_file = tmpdir / "mapping.csv"
            csv_file.write_text("filename,text\n")
            
            with pytest.raises(FileNotFoundError):
                load_mapping(csv_file, tmpdir / "missing_photos")
    
    def test_missing_filename_column(self):
        """Test that ValueError is raised for missing filename column"""
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            photos_dir = tmpdir / "photos"
            photos_dir.mkdir()
            
            csv_file = tmpdir / "mapping.csv"
            csv_file.write_text("image,text\nphoto.png,Hello\n")
            
            with pytest.raises(ValueError, match="'filename' column"):
                load_mapping(csv_file, photos_dir)
    
    def test_empty_csv_raises_error(self):
        """Test that empty CSV raises ValueError"""
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            photos_dir = tmpdir / "photos"
            photos_dir.mkdir()
            
            csv_file = tmpdir / "mapping.csv"
            csv_file.write_text("filename,text\n")  # Header only
            
            with pytest.raises(ValueError, match="No valid entries"):
                load_mapping(csv_file, photos_dir)
    
    def test_preserves_order(self):
        """Test that entry order is preserved from CSV"""
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            photos_dir = tmpdir / "photos"
            photos_dir.mkdir()
            
            csv_file = tmpdir / "mapping.csv"
            with open(csv_file, "w", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["filename", "text"])
                for i in range(1, 6):
                    writer.writerow([f"photo{i}.png", f"Text {i}"])
                    (photos_dir / f"photo{i}.png").touch()
            
            entries = load_mapping(csv_file, photos_dir)
            
            assert len(entries) == 5
            for i, entry in enumerate(entries, start=1):
                assert entry.filename == f"photo{i}.png"
                assert entry.text == f"Text {i}"
    
    def test_resolution_with_extension_priority(self):
        """Test file resolution respects extension priority"""
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            photos_dir = tmpdir / "photos"
            photos_dir.mkdir()
            
            # Create CSV with base names only
            csv_file = tmpdir / "mapping.csv"
            with open(csv_file, "w", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["filename", "text"])
                writer.writerow(["photo", "Hello"])
            
            # Create files with different extensions
            heic_file = photos_dir / "photo.heic"
            jpg_file = photos_dir / "photo.jpg"
            heic_file.touch()
            jpg_file.touch()
            
            # Load with heic priority
            entries = load_mapping(csv_file, photos_dir, ext_priority="heic,jpg,png")
            
            assert len(entries) == 1
            assert entries[0].resolved_path == heic_file
    
    def test_skips_empty_filename(self):
        """Test that rows with empty filename are skipped"""
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            photos_dir = tmpdir / "photos"
            photos_dir.mkdir()
            
            csv_file = tmpdir / "mapping.csv"
            with open(csv_file, "w", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["filename", "text"])
                writer.writerow(["", "Skip this"])
                writer.writerow(["photo.png", "Keep this"])
                (photos_dir / "photo.png").touch()
            
            entries = load_mapping(csv_file, photos_dir)
            
            # Should skip the empty filename row
            assert len(entries) == 1
            assert entries[0].filename == "photo.png"
    
    def test_extension_priority_string_parameter(self):
        """Test extension priority can be passed as string"""
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            photos_dir = tmpdir / "photos"
            photos_dir.mkdir()
            
            csv_file = tmpdir / "mapping.csv"
            with open(csv_file, "w", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["filename", "text"])
                writer.writerow(["photo", "Hello"])
            
            jpg_file = photos_dir / "photo.jpg"
            jpg_file.touch()
            
            # Pass as string with spaces
            entries = load_mapping(csv_file, photos_dir, ext_priority="jpg, png, heic")
            
            assert entries[0].resolved_path == jpg_file
    
    def test_extension_priority_list_parameter(self):
        """Test extension priority can be passed as list"""
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            photos_dir = tmpdir / "photos"
            photos_dir.mkdir()
            
            csv_file = tmpdir / "mapping.csv"
            with open(csv_file, "w", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["filename", "text"])
                writer.writerow(["photo", "Hello"])
            
            png_file = photos_dir / "photo.png"
            png_file.touch()
            
            # Pass as list
            entries = load_mapping(csv_file, photos_dir, ext_priority=[".png", ".jpg"])
            
            assert entries[0].resolved_path == png_file


class TestGetMappingDict:
    """Test suite for get_mapping_dict function"""
    
    def test_converts_to_dict(self):
        """Test conversion of entries to dict"""
        path1 = Path("/tmp/photo1.png")
        path2 = Path("/tmp/photo2.png")
        
        entries = [
            MappingEntry("photo1.png", "Hello", path1),
            MappingEntry("photo2.png", "World", path2),
        ]
        
        result = get_mapping_dict(entries)
        
        assert result == {path1: "Hello", path2: "World"}
    
    def test_excludes_unresolved_entries(self):
        """Test that entries without resolved path are excluded"""
        path1 = Path("/tmp/photo1.png")
        
        entries = [
            MappingEntry("photo1.png", "Hello", path1),
            MappingEntry("photo2.png", "World", None),  # No resolved path
        ]
        
        result = get_mapping_dict(entries)
        
        assert len(result) == 1
        assert result == {path1: "Hello"}
    
    def test_empty_entries_returns_empty_dict(self):
        """Test that empty entries return empty dict"""
        entries = []
        result = get_mapping_dict(entries)
        
        assert result == {}
