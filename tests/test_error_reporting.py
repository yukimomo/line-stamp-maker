import json
import tempfile
import shutil
from pathlib import Path
import pytest
from line_stamp_maker.image_processor import ImageProcessor
from line_stamp_maker.config import ProcessingConfig
from PIL import Image

def test_error_reporting_in_results(tmp_path):
    # ダミー画像とマッピングを作成
    img = Image.new('RGB', (32, 32), color='white')
    img_path = tmp_path / 'dummy.png'
    img.save(img_path)
    # 存在しない画像も追加
    missing_path = tmp_path / 'notfound.png'
    mapping = {img_path: 'テスト', missing_path: 'エラー'}
    # 設定を最小限で作成
    config = ProcessingConfig()
    processor = ImageProcessor(config)
    # 強制的にエラーを起こすため、segmenterをNoneにしてuse_segmentationをTrueに
    processor.segmenter = None
    processor.config.use_segmentation = True
    results = processor.process_batch(mapping)
    # 結果を一時ファイルに保存
    results_path = tmp_path / 'results.json'
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    # 結果を検証
    with open(results_path, encoding='utf-8') as f:
        loaded = json.load(f)
    # 存在しないファイルのエラー
    assert 'notfound.png' in loaded
    err = loaded['notfound.png']
    assert err['status'] == 'error'
    assert err['stage'] == 'load'
    # 強制エラーのファイル
    assert 'dummy.png' in loaded
    derr = loaded['dummy.png']
    assert derr['status'] == 'error'
    assert 'type' in derr and 'message' in derr and 'traceback' in derr and 'stage' in derr
    assert derr['type'] == 'AttributeError' or derr['type'] == 'RuntimeError'
    assert derr['stage'] in ['segment', 'load', 'face']
    assert isinstance(derr['traceback'], list)
    assert len(derr['traceback']) > 0
