#!/usr/bin/env python3
"""
concept_0 ~ concept_9の参照用画像URLリストを生成

元のデータセットJSONから画像パスを読み取り、Web URLに変換して
固定データとして保存する。
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

# URL変換ユーティリティをインポート
utils_dir = Path(__file__).parent.parent / "analysis" / "experiments" / "utils"
sys.path.insert(0, str(utils_dir))
from coco_image_url_converter import convert_coco_path_to_url


def load_dataset_json(json_path: Path) -> Dict:
    """データセットJSONを読み込む"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_concept_images(
    dataset_data: Dict,
    concept_ids: List[int]
) -> Dict[str, Dict[str, List[str]]]:
    """
    指定されたコンセプトの画像URLリストを抽出
    
    Args:
        dataset_data: データセットJSONのデータ
        concept_ids: 抽出するコンセプトIDのリスト
    
    Returns:
        {
            "concept_0": {
                "top100": [URLリスト],
                "bottom100": [URLリスト]
            },
            ...
        }
    """
    result: Dict[str, Dict[str, List[str]]] = {}
    
    results = dataset_data.get('results', [])
    
    for concept_obj in results:
        concept_id = concept_obj.get('concept_id')
        if concept_id is None or concept_id not in concept_ids:
            continue
        
        concept_name = f"concept_{int(concept_id)}"
        result[concept_name] = {
            "top100": [],
            "bottom100": []
        }
        
        # Top-100から画像URLを抽出
        topk = concept_obj.get('topk', [])
        for item in topk:
            image_path = item.get('path', '')
            if image_path:
                url = convert_coco_path_to_url(image_path)
                if url:
                    result[concept_name]["top100"].append(url)
        
        # Bottom-100から画像URLを抽出
        bottomk = concept_obj.get('bottomk', [])
        for item in bottomk:
            image_path = item.get('path', '')
            if image_path:
                url = convert_coco_path_to_url(image_path)
                if url:
                    result[concept_name]["bottom100"].append(url)
    
    return result


def main():
    # データセットパス
    dataset_dir = Path("data/external/retrieved-concepts/farnoosh/current")
    top100_file = dataset_dir / "retrieved_dataset_100.json"
    bottom100_file = dataset_dir / "retrieved_dataset_bottom_100.json"
    
    if not top100_file.exists():
        print(f"エラー: ファイルが見つかりません: {top100_file}")
        sys.exit(1)
    
    if not bottom100_file.exists():
        print(f"エラー: ファイルが見つかりません: {bottom100_file}")
        sys.exit(1)
    
    # コンセプトIDリスト（0~9）
    concept_ids = list(range(10))
    
    # Top-100データを読み込み
    print(f"読み込み中: {top100_file}")
    top100_data = load_dataset_json(top100_file)
    
    # Bottom-100データを読み込み
    print(f"読み込み中: {bottom100_file}")
    bottom100_data = load_dataset_json(bottom100_file)
    
    # 画像URLを抽出
    print("画像URLを抽出中...")
    result: Dict[str, Dict[str, List[str]]] = {}
    
    # Top-100から抽出
    top100_result = extract_concept_images(top100_data, concept_ids)
    for concept_name, urls in top100_result.items():
        if concept_name not in result:
            result[concept_name] = {"top100": [], "bottom100": []}
        result[concept_name]["top100"] = urls["top100"]
    
    # Bottom-100から抽出
    bottom100_result = extract_concept_images(bottom100_data, concept_ids)
    for concept_name, urls in bottom100_result.items():
        if concept_name not in result:
            result[concept_name] = {"top100": [], "bottom100": []}
        result[concept_name]["bottom100"] = urls["bottom100"]
    
    # 出力先
    output_dir = Path("data/processed/retrieved-concepts")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "concept_image_reference.json"
    
    # JSONとして保存
    print(f"保存中: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 統計情報を表示
    print("\n生成完了:")
    for concept_name in sorted(result.keys()):
        top_count = len(result[concept_name]["top100"])
        bottom_count = len(result[concept_name]["bottom100"])
        print(f"  {concept_name}: Top-100={top_count}件, Bottom-100={bottom_count}件")


if __name__ == "__main__":
    main()

