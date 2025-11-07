#!/usr/bin/env python3
"""
実験結果JSONから画像URLを抽出してMarkdown形式で出力するスクリプト

指定数の画像URLを抽出し、Markdown形式で表示する。
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Optional


def load_result_json(json_path: str) -> Dict:
    """実験結果JSONを読み込む"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_image_urls(result: Dict, top_n: int = 5, bottom_n: int = 5) -> Dict[str, List[str]]:
    """
    実験結果から画像URLを抽出
    
    Args:
        result: 実験結果辞書
        top_n: グループAから取得する画像数
        bottom_n: グループBから取得する画像数
    
    Returns:
        {"group_a": [URLリスト], "group_b": [URLリスト]}
    """
    input_data = result.get('input', {})
    group_a_urls = input_data.get('group_a_top5_image_urls', [])[:top_n]
    group_b_urls = input_data.get('group_b_top5_image_urls', [])[:bottom_n]
    
    return {
        "group_a": group_a_urls,
        "group_b": group_b_urls
    }


def generate_markdown_gallery(
    result: Dict,
    top_n: int = 5,
    bottom_n: int = 5,
    include_images: bool = True
) -> str:
    """
    Markdown形式の画像ギャラリーを生成
    
    Args:
        result: 実験結果辞書
        top_n: グループAから取得する画像数
        bottom_n: グループBから取得する画像数
        include_images: 画像タグを含めるか（Falseの場合はリンクのみ）
    
    Returns:
        Markdown形式の文字列
    """
    lines: List[str] = []
    
    # 実験情報
    info = result.get('experiment_info', {})
    experiment_name = info.get('experiment_name', 'Unknown')
    dataset = info.get('dataset', 'Unknown')
    aspect = info.get('aspect', 'Unknown')
    
    lines.append(f"# 画像ギャラリー: {experiment_name}")
    lines.append("")
    lines.append(f"- データセット: {dataset}")
    lines.append(f"- アスペクト: {aspect}")
    lines.append("")
    
    # 画像URLを抽出
    urls = extract_image_urls(result, top_n, bottom_n)
    
    # グループA
    if urls["group_a"]:
        lines.append("## グループA (Top)")
        lines.append("")
        for i, url in enumerate(urls["group_a"], 1):
            if include_images:
                lines.append(f"### 画像 {i}")
                lines.append(f"![Image {i}]({url})")
                lines.append(f"")
                lines.append(f"[リンク]({url})")
            else:
                lines.append(f"{i}. [{url}]({url})")
            lines.append("")
    
    # グループB
    if urls["group_b"]:
        lines.append("## グループB (Bottom)")
        lines.append("")
        for i, url in enumerate(urls["group_b"], 1):
            if include_images:
                lines.append(f"### 画像 {i}")
                lines.append(f"![Image {i}]({url})")
                lines.append(f"")
                lines.append(f"[リンク]({url})")
            else:
                lines.append(f"{i}. [{url}]({url})")
            lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="実験結果JSONから画像URLを抽出してMarkdown形式で出力"
    )
    parser.add_argument(
        "--result-json",
        type=str,
        required=True,
        help="実験結果JSONファイルのパス"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="グループAから取得する画像数（デフォルト: 5）"
    )
    parser.add_argument(
        "--bottom-n",
        type=int,
        default=5,
        help="グループBから取得する画像数（デフォルト: 5）"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="出力ファイルパス（指定しない場合は標準出力）"
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="画像タグを含めず、リンクのみを出力"
    )
    
    args = parser.parse_args()
    
    # JSONファイルを読み込み
    result = load_result_json(args.result_json)
    
    # Markdownを生成
    markdown = generate_markdown_gallery(
        result,
        top_n=args.top_n,
        bottom_n=args.bottom_n,
        include_images=not args.no_images
    )
    
    # 出力
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        print(f"画像ギャラリーを保存しました: {output_path}")
    else:
        print(markdown)


if __name__ == "__main__":
    main()

