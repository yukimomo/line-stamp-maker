import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

def pick_accent_palette(img_rgba):
    """
    画像からアクセントカラー抽出
    - 画像を縮小
    - 白/黒近傍除外
    - k-meansで主要色抽出
    - 中程度の彩度・明度をaccent
    - バブル色・枠色・テキスト色を返す
    Returns: (bubble_rgb, bubble_stroke_rgb, text_rgb)
    """
    img = Image.fromarray(img_rgba).convert('RGB').resize((32,32))
    arr = np.array(img).reshape(-1,3)
    # 白/黒除外
    arr = arr[(arr.mean(axis=1) > 30) & (arr.mean(axis=1) < 220)]
    if len(arr) < 10:
        arr = np.array(img).reshape(-1,3)
    # k-means
    k = min(4, len(arr))
    km = KMeans(n_clusters=k, n_init='auto').fit(arr)
    centers = km.cluster_centers_.astype(int)
    # HSVで中程度の彩度・明度
    hsv = np.array([rgb_to_hsv(*c) for c in centers])
    idx = np.argsort(np.abs(hsv[:,1]-0.5) + np.abs(hsv[:,2]-0.5))[0]
    bubble = tuple(centers[idx])
    # 枠色はバブルより暗め
    stroke = tuple(np.clip(np.array(bubble)*0.7,0,255).astype(int))
    # テキスト色はバブルと十分コントラスト
    text = (0,0,0) if contrast_ratio(bubble, (0,0,0)) > 4.5 else (255,255,255)
    return bubble, stroke, text

def rgb_to_hsv(r,g,b):
    arr = np.array([[r/255,g/255,b/255]])
    return tuple(np.squeeze(np.array(Image.fromarray((arr*255).astype(np.uint8)).convert('HSV')))/255)

def contrast_ratio(rgb1, rgb2):
    # WCAGコントラスト比
    def luminance(rgb):
        a = [v/255 for v in rgb]
        return 0.2126*a[0]+0.7152*a[1]+0.0722*a[2]
    l1 = luminance(rgb1)
    l2 = luminance(rgb2)
    return (max(l1,l2)+0.05)/(min(l1,l2)+0.05)
