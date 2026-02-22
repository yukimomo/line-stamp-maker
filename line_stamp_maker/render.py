import os
from pathlib import Path
from PIL import Image
import numpy as np

def save_debug_outputs(sticker_id, debug_dir, crop, mask_raw, mask_smooth, cutout, outline, bubble, final):
    """
    各ステップ画像をdebug_dir/sticker_id/に保存
    """
    outdir = Path(debug_dir) / f"{sticker_id:02d}"
    outdir.mkdir(parents=True, exist_ok=True)
    Image.fromarray(crop).save(outdir / "_crop.png")
    Image.fromarray(mask_raw).save(outdir / "_mask_raw.png")
    Image.fromarray(mask_smooth).save(outdir / "_mask_smooth.png")
    Image.fromarray(cutout).save(outdir / "_cutout.png")
    Image.fromarray(outline).save(outdir / "_outline.png")
    Image.fromarray(bubble).save(outdir / "_bubble.png")
    Image.fromarray(final).save(outdir / "_final.png")
