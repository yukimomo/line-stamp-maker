import numpy as np
import cv2
import pytest
from line_stamp_maker.mask import smooth_alpha_mask

def test_smooth_alpha_mask_feather():
    # 10x10 mask, center 4x4 is foreground
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[3:7, 3:7] = 1
    alpha = smooth_alpha_mask(mask, feather=3, close_kernel=0, open_kernel=0)
    # 端は0, 中央は255, 中間値が存在するか
    assert alpha.max() == 255
    assert alpha.min() == 0
    # 中間値（0でも255でもない）が存在するか
    assert np.any((alpha > 0) & (alpha < 255))

def test_smooth_alpha_mask_morph():
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[2:8, 2:8] = 1
    # ノイズ追加
    mask[1,1] = 1
    mask[8,8] = 1
    alpha = smooth_alpha_mask(mask, feather=0, close_kernel=3, open_kernel=3)
    # ノイズ除去されているか
    assert alpha[1,1] == 0
    assert alpha[8,8] == 0
    assert alpha[5,5] == 255

def test_smooth_alpha_mask_combined():
    mask = np.zeros((20, 20), dtype=np.uint8)
    mask[5:15, 5:15] = 1
    alpha = smooth_alpha_mask(mask, feather=5, close_kernel=5, open_kernel=3)
    # 中間値が広範囲に存在するか
    mid = ((alpha > 0) & (alpha < 255)).sum()
    assert mid > 10
