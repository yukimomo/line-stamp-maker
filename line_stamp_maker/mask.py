import numpy as np
import cv2

def smooth_alpha_mask(mask: np.ndarray, feather: int = 3, close_kernel: int = 5, open_kernel: int = 3) -> np.ndarray:
    """
    バイナリマスクから滑らかなアルファマスクを生成する。
    - モルフォロジー閉/開処理
    - 距離変換によるフェザー/ガウスぼかし
    - 0..255のuint8アルファマスクを返す
    """
    mask = mask.astype(np.uint8) * 255
    # モルフォロジー閉処理
    if close_kernel > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_kernel, close_kernel))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    # モルフォロジー開処理
    if open_kernel > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_kernel, open_kernel))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    # 距離変換によるフェザー
    if feather > 0:
        dist_out = cv2.distanceTransform(mask == 0, cv2.DIST_L2, 5)
        dist_in = cv2.distanceTransform(mask == 255, cv2.DIST_L2, 5)
        edge = np.clip((dist_out + dist_in), 0, feather)
        alpha = np.clip((feather - edge) / feather, 0, 1)
        mask = (mask * alpha + 255 * (1 - alpha)).astype(np.uint8)
        mask = cv2.GaussianBlur(mask, (feather * 2 + 1, feather * 2 + 1), 0)
    return mask

# 既存のapply_mask関数をラップまたは置き換え

def apply_mask(image: np.ndarray, mask: np.ndarray, feather: int = 3, close_kernel: int = 5, open_kernel: int = 3) -> np.ndarray:
    """
    マスクを滑らかにしてアルファチャンネルとして適用
    """
    alpha = smooth_alpha_mask(mask, feather, close_kernel, open_kernel)
    if image.shape[-1] == 3:
        image = np.dstack([image, alpha])
    else:
        image[..., -1] = alpha
    return image
