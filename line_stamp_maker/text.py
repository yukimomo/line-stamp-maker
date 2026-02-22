import re

def wrap_japanese_text(text, font, max_width, max_lines=2):
    """
    日本語テキストを幅・改行位置・省略でラップ
    - font.getlengthで幅計測
    - 区切り文字や日本語間で改行
    - 最大行数超過時は省略
    Returns: list[str]
    """
    breaks = r'[、,；。.！？・ー\s]'
    lines = []
    buf = ''
    for c in text:
        buf += c
        if font.getlength(buf) > max_width:
            # 区切り文字優先
            m = re.search(breaks, buf[::-1])
            if m:
                idx = len(buf) - m.start()
                lines.append(buf[:idx])
                buf = buf[idx:]
            else:
                lines.append(buf[:-1])
                buf = c
            if len(lines) == max_lines-1:
                break
    if buf:
        lines.append(buf)
    # 行数超過時は省略
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if len(lines[-1]) > 1:
            lines[-1] = lines[-1][:-1] + '…'
        else:
            lines[-1] = '…'
    return lines
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

def render_bubble_caption(caption: str, target_rect, palette, font, bubble_height=50, stroke=3, shadow=True) -> Image.Image:
    """
    バブル型キャプションを描画
    - target_rect: (x, y, w, h)
    - palette: dict (bubble, text, outline)
    - font: PIL.ImageFont
    - bubble_height: バブル高さ
    - stroke: バブル枠線太さ
    - shadow: シャドウ有効
    """
    x, y, w, h = target_rect
    radius = int(bubble_height * 0.3)
    tail_w, tail_h = int(bubble_height * 0.4), int(bubble_height * 0.3)
    canvas = Image.new('RGBA', (w, h+tail_h+8), (0,0,0,0))
    draw = ImageDraw.Draw(canvas)
    # バブル本体
    bubble_rect = [stroke, stroke, w-stroke, h-stroke]
    draw.rounded_rectangle(bubble_rect, radius=radius, fill=palette['bubble'], outline=palette['outline'], width=stroke)
    # バブルの尾
    tail_x = w//2
    tail_poly = [(tail_x-tail_w//2, h), (tail_x+tail_w//2, h), (tail_x, h+tail_h)]
    draw.polygon(tail_poly, fill=palette['bubble'], outline=palette['outline'])
    # シャドウ
    if shadow:
        shadow_img = canvas.copy()
        shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(4))
        shadow_img = Image.new('RGBA', shadow_img.size, (0,0,0,70)).convert('RGBA').paste(shadow_img, (0,2), shadow_img)
        canvas = Image.alpha_composite(shadow_img, canvas)
    # テキスト描画
    # 日本語折り返し
    lines = []
    for line in caption.split('\n'):
        while len(line) > 0:
            lines.append(line[:12])
            line = line[12:]
    lines = lines[:2]
    # フォントサイズ自動調整
    font_size = font.size
    while True:
        font_obj = ImageFont.truetype(font.path, font_size)
        text_h = sum([font_obj.getsize(l)[1] for l in lines])
        if text_h < h - 2*stroke or font_size <= 12:
            break
        font_size -= 2
    # テキストアウトライン
    for i, line in enumerate(lines):
        tx = w//2
        ty = h//2 - text_h//2 + i*font_obj.getsize(line)[1]
        # アウトライン
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            draw.text((tx+dx, ty+dy), line, font=font_obj, fill=palette['outline'], anchor='mm')
        draw.text((tx, ty), line, font=font_obj, fill=palette['text'], anchor='mm')
    return canvas
