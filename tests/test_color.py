import numpy as np
from line_stamp_maker.color import pick_accent_palette

def test_accent_palette_simple():
    # 赤主体
    img = np.zeros((32,32,4), dtype=np.uint8)
    img[...,0] = 220
    img[...,3] = 255
    bubble, stroke, text = pick_accent_palette(img)
    assert bubble[0] > 200
    assert text in [(0,0,0),(255,255,255)]

def test_accent_palette_dark():
    img = np.zeros((32,32,4), dtype=np.uint8)
    img[...,0] = 10
    img[...,1] = 10
    img[...,2] = 10
    img[...,3] = 255
    bubble, stroke, text = pick_accent_palette(img)
    assert bubble[0] < 50
    assert text == (255,255,255)

def test_accent_palette_light():
    img = np.ones((32,32,4), dtype=np.uint8)*240
    img[...,3] = 255
    bubble, stroke, text = pick_accent_palette(img)
    assert bubble[0] > 200
    assert text == (0,0,0)
