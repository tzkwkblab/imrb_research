"""
COCO画像パスをWeb URLに変換するユーティリティ

MS-COCOデータセットの画像パス（例: data/coco/train2017/000000081860.jpg）
をWeb上で閲覧可能なURL（例: http://images.cocodataset.org/train2017/000000081860.jpg）
に変換する。
"""

import re
from pathlib import Path
from typing import Optional


def convert_coco_path_to_url(path: str) -> str:
    """
    COCO画像パスをWeb URLに変換
    
    Args:
        path: COCO画像パス（例: "data/coco/train2017/000000081860.jpg"）
    
    Returns:
        Web URL（例: "http://images.cocodataset.org/train2017/000000081860.jpg"）
    
    Examples:
        >>> convert_coco_path_to_url("data/coco/train2017/000000081860.jpg")
        'http://images.cocodataset.org/train2017/000000081860.jpg'
        >>> convert_coco_path_to_url("data/coco/val2017/000000397133.jpg")
        'http://images.cocodataset.org/val2017/000000397133.jpg'
    """
    if not path:
        return ""
    
    # パスからファイル名とディレクトリ名を抽出
    # 例: "data/coco/train2017/000000081860.jpg" -> "train2017/000000081860.jpg"
    path_str = str(path).replace("\\", "/")
    
    # data/coco/ の部分を除去
    pattern = r"(?:^|/)data/coco/(.+)$"
    match = re.search(pattern, path_str)
    
    if match:
        relative_path = match.group(1)
        return f"http://images.cocodataset.org/{relative_path}"
    
    # 既にURL形式の場合はそのまま返す
    if path_str.startswith("http://") or path_str.startswith("https://"):
        return path_str
    
    # train2017/ や val2017/ で始まる場合はそのまま使用
    if path_str.startswith("train2017/") or path_str.startswith("val2017/"):
        return f"http://images.cocodataset.org/{path_str}"
    
    # その他の場合は、ファイル名のみから推測を試みる
    # ただし、これは推奨されない
    filename = Path(path_str).name
    if filename:
        # train2017かval2017かを推測できないため、train2017をデフォルトとする
        return f"http://images.cocodataset.org/train2017/{filename}"
    
    return ""


def batch_convert_paths_to_urls(paths: list[str]) -> list[str]:
    """
    複数のパスを一括でURLに変換
    
    Args:
        paths: COCO画像パスのリスト
    
    Returns:
        Web URLのリスト
    """
    return [convert_coco_path_to_url(path) for path in paths if path]


if __name__ == "__main__":
    # テスト
    test_cases = [
        "data/coco/train2017/000000081860.jpg",
        "data/coco/val2017/000000397133.jpg",
        "train2017/000000081860.jpg",
        "http://images.cocodataset.org/train2017/000000081860.jpg",
        "",
    ]
    
    for test_path in test_cases:
        result = convert_coco_path_to_url(test_path)
        print(f"{test_path} -> {result}")

