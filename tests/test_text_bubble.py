from PIL import Image, ImageFont
from line_stamp_maker.text import render_bubble_caption

def test_render_bubble_caption():
    w, h = 200, 60
    palette = {'bubble': (255,255,255,230), 'text': (50,50,50,255), 'outline': (180,180,180,255)}
    font = ImageFont.truetype("./line_stamp_maker/assets/fonts/kiwi.ttf", 32)
    img = render_bubble_caption("テストバブル\n改行もOK", (0,0,w,h), palette, font, bubble_height=60, stroke=4, shadow=True)
    # バブル領域に白が存在するか
    assert img.getpixel((w//2, h//2))[0] > 200
    # テキスト領域に黒系が存在するか
    assert img.getpixel((w//2, h//2))[1] < 100
