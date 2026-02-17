"""Tests for image I/O functions"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from line_stamp_maker.io import open_image, get_supported_formats, is_supported_image


class TestGetSupportedFormats:
    """Test suite for get_supported_formats function"""
    
    def test_includes_common_formats(self):
        """Verify common image formats are supported"""
        formats = get_supported_formats()
        assert ".jpg" in formats
        assert ".png" in formats
        assert ".gif" in formats
        assert ".bmp" in formats
    
    def test_includes_heic_formats(self):
        """Verify HEIC/HEIF formats are in supported list"""
        formats = get_supported_formats()
        assert ".heic" in formats
        assert ".heif" in formats
    
    def test_returns_lowercased_extensions(self):
        """Verify all extensions are lowercase"""
        formats = get_supported_formats()
        assert all(fmt.islower() for fmt in formats)
    
    def test_returns_extensions_with_dots(self):
        """Verify all extensions start with dot"""
        formats = get_supported_formats()
        assert all(fmt.startswith(".") for fmt in formats)


class TestIsSupportedImage:
    """Test suite for is_supported_image function"""
    
    def test_supports_jpg(self):
        """Test JPG support"""
        assert is_supported_image("photo.jpg")
        assert is_supported_image("photo.JPG")
        assert is_supported_image("photo.jpeg")
    
    def test_supports_png(self):
        """Test PNG support"""
        assert is_supported_image("photo.png")
        assert is_supported_image("photo.PNG")
    
    def test_supports_heic(self):
        """Test HEIC support detection"""
        assert is_supported_image("photo.heic")
        assert is_supported_image("photo.HEIC")
    
    def test_supports_heif(self):
        """Test HEIF support detection"""
        assert is_supported_image("photo.heif")
        assert is_supported_image("photo.HEIF")
    
    def test_rejects_unsupported_formats(self):
        """Test that unsupported formats are rejected"""
        assert not is_supported_image("document.txt")
        assert not is_supported_image("image.xyz")
    
    def test_accepts_path_objects(self):
        """Test that Path objects are accepted"""
        assert is_supported_image(Path("photo.png"))
        assert is_supported_image(Path("photo.heic"))


class TestOpenImageHEICWithoutPillowHEIF:
    """Test suite for HEIC/HEIF handling without pillow-heif installed"""
    
    def test_heic_raises_error_without_pillow_heif(self, monkeypatch, tmp_path):
        """
        Test that opening HEIC file raises RuntimeError when pillow_heif is not available.
        
        This test:
        1. Creates a dummy HEIC file
        2. Monkeypatches import to raise ImportError for pillow_heif
        3. Verifies RuntimeError is raised with correct message
        """
        # Create a dummy HEIC file (we won't really open it as HEIC)
        heic_file = tmp_path / "test.heic"
        heic_file.write_bytes(b"dummy heic content")
        
        # Mock sys.modules to simulate pillow_heif not being installed
        def mock_import(name, *args, **kwargs):
            if name == "pillow_heif":
                raise ImportError("No module named 'pillow_heif'")
            return original_import(name, *args, **kwargs)
        
        original_import = __builtins__.__import__
        
        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(RuntimeError) as exc_info:
                open_image(heic_file)
            
            error_msg = str(exc_info.value)
            assert "HEIC/HEIF support requires pillow-heif" in error_msg
            assert "pip install pillow-heif" in error_msg
            assert "pip install -e \".[heic]\"" in error_msg
    
    def test_heif_raises_error_without_pillow_heif(self, monkeypatch, tmp_path):
        """
        Test that opening HEIF file raises RuntimeError when pillow_heif is not available.
        """
        heif_file = tmp_path / "test.heif"
        heif_file.write_bytes(b"dummy heif content")
        
        def mock_import(name, *args, **kwargs):
            if name == "pillow_heif":
                raise ImportError("No module named 'pillow_heif'")
            return original_import(name, *args, **kwargs)
        
        original_import = __builtins__.__import__
        
        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(RuntimeError) as exc_info:
                open_image(heif_file)
            
            error_msg = str(exc_info.value)
            assert "HEIC/HEIF support requires pillow-heif" in error_msg


class TestOpenImageFileNotFound:
    """Test suite for file not found scenarios"""
    
    def test_raises_file_not_found_error(self):
        """Test that FileNotFoundError is raised for non-existent files"""
        with pytest.raises(FileNotFoundError):
            open_image(Path("/nonexistent/path/to/image.png"))
    
    def test_error_message_includes_path(self):
        """Test that error message includes the file path"""
        missing_path = Path("/missing/image.png")
        
        with pytest.raises(FileNotFoundError) as exc_info:
            open_image(missing_path)
        
        assert str(missing_path) in str(exc_info.value)


@pytest.fixture
def sample_png_image(tmp_path):
    """Fixture: Create a sample PNG image for testing"""
    try:
        from PIL import Image as PILImage
        
        img = PILImage.new("RGB", (100, 100), color=(255, 0, 0))
        img_path = tmp_path / "test.png"
        img.save(img_path)
        return img_path
    except ImportError:
        pytest.skip("PIL/Pillow not installed")


class TestOpenImagePNG:
    """Test suite for opening standard PNG files"""
    
    def test_opens_png_successfully(self, sample_png_image):
        """Test that PNG files can be opened successfully"""
        img = open_image(sample_png_image)
        assert img is not None
        assert img.mode == "RGBA"
    
    def test_png_returned_as_rgba(self, sample_png_image):
        """Test that returned image is always in RGBA mode"""
        img = open_image(sample_png_image)
        assert img.mode == "RGBA"
    
    def test_accepts_string_path(self, sample_png_image):
        """Test that string paths are accepted"""
        img = open_image(str(sample_png_image))
        assert img is not None
    
    def test_accepts_path_object(self, sample_png_image):
        """Test that Path objects are accepted"""
        img = open_image(Path(sample_png_image))
        assert img is not None
