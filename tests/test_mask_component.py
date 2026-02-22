import numpy as np
from line_stamp_maker.mask import select_best_component

def test_select_best_component_face():
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[2:4, 2:4] = 255  # blob1
    mask[6:8, 6:8] = 255  # blob2
    # 顔中心がblob2近く
    out = select_best_component(mask, face_center=(7,7))
    assert out[7,7] == 255
    assert out[3,3] == 0

def test_select_best_component_area():
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[2:4, 2:4] = 255  # blob1
    mask[6:9, 6:9] = 255  # blob2（大きい）
    out = select_best_component(mask)
    assert out[7,7] == 255
    assert out[3,3] == 0

def test_select_best_component_single():
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[2:8, 2:8] = 255
    out = select_best_component(mask)
    assert np.all(out == mask)
