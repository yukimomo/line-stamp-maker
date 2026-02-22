import numpy as np
from line_stamp_maker.sticker import add_double_outline, add_shadow

def test_double_outline():
    mask = np.zeros((20, 20), dtype=np.uint8)
    mask[5:15, 5:15] = 255
    img = np.zeros((20, 20, 3), dtype=np.uint8)
    out = add_double_outline(img, mask, outline_outer=4, outline_inner=2)
    # アウトライン領域に白/オフホワイトが存在するか
    assert np.any((out[..., :3] == (255,255,255)).all(axis=-1))
    assert np.any((out[..., :3] == (230,230,240)).all(axis=-1))

def test_shadow():
    mask = np.zeros((20, 20), dtype=np.uint8)
    mask[5:15, 5:15] = 255
    img = np.zeros((20, 20, 3), dtype=np.uint8)
    out = add_shadow(img, mask, offset=(0,2), blur=2, alpha=70)
    # シャドウ領域にalpha>0が存在するか
    assert np.any(out[..., 3] > 0)
