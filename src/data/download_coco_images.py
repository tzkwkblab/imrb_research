#!/usr/bin/env python3
"""
COCO画像をWeb URLからダウンロードするスクリプト

必要に応じて画像をダウンロードしてローカルに保存する。
"""

import argparse
import requests
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm
import sys

# URL変換ユーティリティをインポート
utils_dir = Path(__file__).parent.parent / "analysis" / "experiments" / "utils"
sys.path.insert(0, str(utils_dir))
from coco_image_url_converter import convert_coco_path_to_url


def download_image(url: str, output_path: Path) -> bool:
    """
    画像をダウンロード
    
    Args:
        url: 画像URL
        output_path: 保存先パス
    
    Returns:
        成功した場合True
    """
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return True
    except Exception as e:
        print(f"エラー: {url} のダウンロードに失敗: {e}")
        return False


def download_images_from_urls(
    urls: List[str],
    output_dir: Path,
    base_url: str = "http://images.cocodataset.org/"
) -> int:
    """
    複数の画像URLから画像をダウンロード
    
    Args:
        urls: 画像URLのリスト
        output_dir: 出力ディレクトリ
        base_url: ベースURL（相対パスから完全URLを構築する際に使用）
    
    Returns:
        成功したダウンロード数
    """
    success_count = 0
    
    for url in tqdm(urls, desc="ダウンロード中"):
        # URLからファイル名を抽出
        # 例: http://images.cocodataset.org/train2017/000000081860.jpg
        # -> train2017/000000081860.jpg
        if url.startswith(base_url):
            relative_path = url[len(base_url):]
        else:
            # 完全URLの場合はそのまま使用
            relative_path = url.split("/")[-1]
            # train2017かval2017かを推測できないため、train2017をデフォルトとする
            relative_path = f"train2017/{relative_path}"
        
        output_path = output_dir / relative_path
        
        # 既に存在する場合はスキップ
        if output_path.exists():
            continue
        
        if download_image(url, output_path):
            success_count += 1
    
    return success_count


def load_urls_from_json(json_path: Path) -> List[str]:
    """
    JSONファイルから画像URLリストを読み込む
    
    実験結果JSONまたは参照用データJSONから画像URLを抽出
    """
    import json
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    urls: List[str] = []
    
    # 実験結果JSON形式の場合
    if 'input' in data:
        input_data = data.get('input', {})
        urls.extend(input_data.get('group_a_top5_image_urls', []))
        urls.extend(input_data.get('group_b_top5_image_urls', []))
    
    # 参照用データJSON形式の場合
    elif isinstance(data, dict) and any('top100' in v or 'bottom100' in v for v in data.values() if isinstance(v, dict)):
        for concept_data in data.values():
            if isinstance(concept_data, dict):
                urls.extend(concept_data.get('top100', []))
                urls.extend(concept_data.get('bottom100', []))
    
    return urls


def main():
    parser = argparse.ArgumentParser(
        description="COCO画像をWeb URLからダウンロード"
    )
    parser.add_argument(
        "--urls",
        type=str,
        nargs="+",
        help="ダウンロードする画像URLのリスト"
    )
    parser.add_argument(
        "--json",
        type=str,
        help="画像URLを含むJSONファイルのパス（実験結果JSONまたは参照用データJSON）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/external/coco-images",
        help="出力ディレクトリ（デフォルト: data/external/coco-images）"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="既に存在するファイルをスキップ"
    )
    
    args = parser.parse_args()
    
    # URLリストを取得
    urls: List[str] = []
    
    if args.urls:
        urls = args.urls
    elif args.json:
        json_path = Path(args.json)
        if not json_path.exists():
            print(f"エラー: ファイルが見つかりません: {json_path}")
            sys.exit(1)
        urls = load_urls_from_json(json_path)
    else:
        parser.print_help()
        print("\nエラー: --urls または --json のいずれかを指定してください")
        sys.exit(1)
    
    if not urls:
        print("警告: 画像URLが見つかりませんでした")
        sys.exit(0)
    
    # 出力ディレクトリ
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"ダウンロード先: {output_dir}")
    print(f"画像数: {len(urls)}件")
    print("")
    
    # ダウンロード実行
    success_count = download_images_from_urls(urls, output_dir)
    
    print(f"\n完了: {success_count}/{len(urls)}件のダウンロードに成功しました")


if __name__ == "__main__":
    main()

