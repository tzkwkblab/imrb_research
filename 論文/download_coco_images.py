#!/usr/bin/env python3
"""
COCO実験の画像をダウンロードして保存するスクリプト
"""
import os
import requests
from pathlib import Path

# 画像URLの定義（各コンセプトの代表画像を1枚ずつ）
COCO_IMAGES = {
    'concept_0': {
        'group_a': 'http://images.cocodataset.org/train2017/000000105396.jpg',
        'group_b': 'http://images.cocodataset.org/train2017/000000081860.jpg'
    },
    'concept_1': {
        'group_a': 'http://images.cocodataset.org/train2017/000000433452.jpg',
        'group_b': 'http://images.cocodataset.org/train2017/000000095812.jpg'
    },
    'concept_2': {
        'group_a': 'http://images.cocodataset.org/train2017/000000105396.jpg',
        'group_b': 'http://images.cocodataset.org/train2017/000000433472.jpg'
    },
    'concept_10': {
        'group_a': 'http://images.cocodataset.org/train2017/000000269090.jpg',
        'group_b': 'http://images.cocodataset.org/train2017/000000389681.jpg'
    },
    'concept_50': {
        'group_a': 'http://images.cocodataset.org/train2017/000000397613.jpg',
        'group_b': 'http://images.cocodataset.org/train2017/000000487741.jpg'
    }
}

def download_image(url, save_path):
    """画像をダウンロードして保存"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {save_path}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def main():
    # 保存先ディレクトリ
    base_dir = Path(__file__).parent / 'image' / 'coco'
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # 各コンセプトの画像をダウンロード
    for concept, urls in COCO_IMAGES.items():
        for group, url in urls.items():
            filename = f"{concept}_{group}.jpg"
            save_path = base_dir / filename
            download_image(url, save_path)
    
    print(f"\nAll images saved to: {base_dir}")

if __name__ == '__main__':
    main()

