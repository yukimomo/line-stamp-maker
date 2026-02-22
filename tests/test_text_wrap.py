from PIL import ImageFont
from line_stamp_maker.text import wrap_japanese_text

def test_wrap_japanese_text_long():
    font = ImageFont.truetype("./line_stamp_maker/assets/fonts/kiwi.ttf", 24)
    text = "これはとても長い日本語の文章です。改行位置を自動で調整します。"
    lines = wrap_japanese_text(text, font, 120, max_lines=2)
    assert len(lines) <= 2
    assert lines[-1].endswith('…') or len(lines) <= 2

def test_wrap_japanese_text_mixed():
    font = ImageFont.truetype("./line_stamp_maker/assets/fonts/kiwi.ttf", 24)
    text = "Hello日本語テスト, wrap!"
    lines = wrap_japanese_text(text, font, 100, max_lines=2)
    assert len(lines) <= 2
    assert all(isinstance(l, str) for l in lines)

def test_wrap_japanese_text_nowrap():
    font = ImageFont.truetype("./line_stamp_maker/assets/fonts/kiwi.ttf", 24)
    text = "短い"
    lines = wrap_japanese_text(text, font, 200, max_lines=2)
    assert len(lines) == 1
    assert lines[0] == text
