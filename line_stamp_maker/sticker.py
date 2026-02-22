import numpy as np
import cv2

def add_double_outline(image: np.ndarray, mask: np.ndarray, outline_outer=10, outline_inner=4) -> np.ndarray:
    """
    マスクを膨張させて二重アウトラインを追加
    - 外側: 白, 太さoutline_outer
    - 内側: オフホワイト, 太さoutline_inner
    """
    h, w = mask.shape
    outline_img = np.zeros((h, w, 4), dtype=np.uint8)
    # 外側アウトライン
    kernel_outer = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (outline_outer*2+1, outline_outer*2+1))
    mask_outer = cv2.dilate(mask, kernel_outer)
    mask_outer = mask_outer - mask
    outline_img[mask_outer > 0] = (255, 255, 255, 255)
    # 内側アウトライン
    kernel_inner = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (outline_inner*2+1, outline_inner*2+1))
    mask_inner = cv2.dilate(mask, kernel_inner)
    mask_inner = mask_inner - mask
    outline_img[mask_inner > 0] = (230, 230, 240, 255)
    # 元画像と合成
    img_rgba = image.copy()
    if img_rgba.shape[-1] == 3:
        img_rgba = np.dstack([img_rgba, mask])
    img_rgba = cv2.addWeighted(img_rgba, 1, outline_img, 1, 0)
    return img_rgba

def add_shadow(image: np.ndarray, mask: np.ndarray, offset=(0,2), blur=4, alpha=70) -> np.ndarray:
    """
    ステッカーの後ろにドロップシャドウを追加
    """
    h, w = mask.shape
    shadow = np.zeros((h, w, 4), dtype=np.uint8)
    shadow_mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (blur*2+1, blur*2+1)))
    shadow_mask = cv2.GaussianBlur(shadow_mask, (blur*2+1, blur*2+1), 0)
    shadow[..., :3] = 0
    shadow[..., 3] = (shadow_mask * alpha // 255).astype(np.uint8)
    # オフセット
    M = np.float32([[1,0,offset[0]],[0,1,offset[1]]])
    shadow = cv2.warpAffine(shadow, M, (w, h))
    # 合成
    img_rgba = image.copy()
    if img_rgba.shape[-1] == 3:
        img_rgba = np.dstack([img_rgba, mask])
    img_rgba = cv2.addWeighted(shadow, 1, img_rgba, 1, 0)
    return img_rgba
