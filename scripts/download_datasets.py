#!/usr/bin/env python3
"""
データセットダウンロードスクリプト
Kaggle APIを使用して外部データセットをダウンロードし、適切なディレクトリに配置します。

事前準備:
1. pip install kaggle
2. Kaggle APIトークンを ~/.kaggle/kaggle.json に配置
   (https://www.kaggle.com/settings → API → Create New Token)

使用方法:
    python download_datasets.py --all          # 全データセットをダウンロード
    python download_datasets.py --dataset steam  # 個別ダウンロード
"""

import argparse
import subprocess
import sys
from pathlib import Path


DATASETS = {
    "steam": {
        "kaggle_id": "ilosvigil/steam-review-aspect-dataset",
        "target_dir": "data/external/steam-review-aspect-dataset/current",
        "description": "Steam Review Aspect Dataset (ゲームレビュー)"
    },
    "goemotions": {
        "kaggle_id": "debarshichanda/goemotions",
        "target_dir": "data/external/goemotions/kaggle-debarshichanda/current",
        "description": "GoEmotions Dataset (感情分類)"
    },
    "amazon": {
        "kaggle_id": "bittlingmayer/amazonreviews",
        "target_dir": "data/external/amazon-product-reviews/kaggle-bittlingmayer/current",
        "description": "Amazon Product Reviews"
    }
}


def check_kaggle_cli():
    """Kaggle CLIの存在確認"""
    try:
        subprocess.run(["kaggle", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def download_dataset(dataset_key: str, project_root: Path):
    """個別データセットのダウンロード"""
    if dataset_key not in DATASETS:
        print(f"エラー: 未知のデータセット '{dataset_key}'")
        print(f"利用可能: {list(DATASETS.keys())}")
        return False
    
    info = DATASETS[dataset_key]
    target_path = project_root / info["target_dir"]
    
    print(f"\n{'='*50}")
    print(f"ダウンロード: {info['description']}")
    print(f"Kaggle ID: {info['kaggle_id']}")
    print(f"保存先: {target_path}")
    print(f"{'='*50}")
    
    # ディレクトリ作成
    target_path.mkdir(parents=True, exist_ok=True)
    
    # Kaggle APIでダウンロード
    cmd = [
        "kaggle", "datasets", "download",
        "-d", info["kaggle_id"],
        "-p", str(target_path),
        "--unzip"
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✓ ダウンロード完了: {dataset_key}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ ダウンロード失敗: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="データセットダウンロードツール")
    parser.add_argument("--all", action="store_true", help="全データセットをダウンロード")
    parser.add_argument("--dataset", type=str, help="個別データセット指定 (steam, goemotions, amazon)")
    parser.add_argument("--list", action="store_true", help="利用可能なデータセット一覧")
    args = parser.parse_args()
    
    if args.list:
        print("\n利用可能なデータセット:")
        for key, info in DATASETS.items():
            print(f"  {key}: {info['description']}")
        return
    
    if not check_kaggle_cli():
        print("エラー: Kaggle CLIが見つかりません")
        print("インストール: pip install kaggle")
        print("設定: https://www.kaggle.com/settings → API → Create New Token")
        sys.exit(1)
    
    # プロジェクトルートを特定
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    if not (project_root / "src").exists():
        project_root = Path.cwd()
    
    print(f"プロジェクトルート: {project_root}")
    
    if args.all:
        for key in DATASETS:
            download_dataset(key, project_root)
    elif args.dataset:
        download_dataset(args.dataset, project_root)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
