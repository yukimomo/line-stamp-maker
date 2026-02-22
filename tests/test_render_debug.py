import os
import numpy as np
from PIL import Image
from line_stamp_maker.render import save_debug_outputs

def test_save_debug_outputs(tmp_path):
    crop = np.zeros((10,10,3), dtype=np.uint8)
    mask_raw = np.ones((10,10), dtype=np.uint8)*255
    mask_smooth = np.ones((10,10), dtype=np.uint8)*128
    cutout = np.ones((10,10,4), dtype=np.uint8)*200
    outline = np.ones((10,10,4), dtype=np.uint8)*220
    bubble = np.ones((10,10,4), dtype=np.uint8)*240
    final = np.ones((10,10,4), dtype=np.uint8)*255
    save_debug_outputs(1, tmp_path, crop, mask_raw, mask_smooth, cutout, outline, bubble, final)
    files = ["_crop.png","_mask_raw.png","_mask_smooth.png","_cutout.png","_outline.png","_bubble.png","_final.png"]
    for f in files:
        assert os.path.exists(os.path.join(tmp_path,"01",f))
