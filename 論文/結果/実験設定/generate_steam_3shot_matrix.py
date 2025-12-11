#!/usr/bin/env python3
"""
Steamデータセット用3-shot実験マトリックス生成スクリプト

Steamデータセットで0-shot, 1-shot, 3-shotの実験を実行する。
- group_size: 100
- use_llm_evaluation: false
- 例題ファイルが存在するもののみ使用
"""

import json
from datetime import datetime
from pathlib import Path

def check_examples_file_exists() -> bool:
    """例題ファイルの存在確認"""
    examples_file = Path("data/analysis-workspace/contrast_examples/steam/steam_examples_v1.json")
    return examples_file.exists()

def generate_experiment_id(
    aspect: str,
    few_shot: int,
    gpt_model: str = "gpt-4o-mini"
) -> str:
    """実験IDを生成"""
    model_short = gpt_model.replace("gpt-", "").replace(".", "")
    return f"steam_{aspect}_{few_shot}_{model_short}_word"

def create_experiment_config(
    aspect: str,
    few_shot: int,
    gpt_model: str = "gpt-4o-mini",
    group_size: int = 100,
    use_llm_evaluation: bool = False
) -> dict:
    """実験設定を作成"""
    experiment_id = generate_experiment_id(aspect, few_shot, gpt_model)
    
    return {
        "experiment_id": experiment_id,
        "dataset": "steam",
        "aspect": aspect,
        "domain": None,
        "few_shot": few_shot,
        "gpt_model": gpt_model,
        "group_size": group_size,
        "split_type": "aspect_vs_others",
        "use_llm_evaluation": use_llm_evaluation,
        "llm_evaluation_model": "gpt-4o-mini",
        "use_aspect_descriptions": False
    }

def main():
    """メイン実行"""
    # 例題ファイルの存在確認
    if not check_examples_file_exists():
        print("エラー: 例題ファイルが見つかりません")
        print("パス: data/analysis-workspace/contrast_examples/steam/steam_examples_v1.json")
        return
    
    print("例題ファイルを確認しました: steam_examples_v1.json")
    
    # Steamアスペクト（既存のマトリックスから確認）
    steam_aspects = ["gameplay", "visual", "story", "audio"]
    
    # 実験設定
    few_shots = [0, 1, 3]
    
    experiments = []
    
    for aspect in steam_aspects:
        for few_shot in few_shots:
            # 0-shotの場合は例題ファイル不要だが、1-shot, 3-shotの場合は必要
            if few_shot > 0:
                if not check_examples_file_exists():
                    print(f"警告: {few_shot}-shot実験をスキップ（例題ファイルなし）")
                    continue
            
            exp = create_experiment_config(
                aspect=aspect,
                few_shot=few_shot,
                group_size=100,
                use_llm_evaluation=False
            )
            experiments.append(exp)
    
    # 実験計画情報
    experiment_plan = {
        "total_experiments": len(experiments),
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "description": "Steamデータセット: 0-shot, 1-shot, 3-shot実験（group_size=100, LLM評価無効）",
        "settings": {
            "dataset": "steam",
            "few_shots": few_shots,
            "group_size": 100,
            "use_llm_evaluation": False,
            "gpt_model": "gpt-4o-mini",
            "examples_file": "data/analysis-workspace/contrast_examples/steam/steam_examples_v1.json"
        }
    }
    
    # マトリックスJSONを生成
    matrix = {
        "experiment_plan": experiment_plan,
        "experiments": experiments
    }
    
    # ファイルに保存
    output_file = Path(__file__).parent / "steam_3shot_experiment_matrix.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(matrix, f, ensure_ascii=False, indent=2)
    
    print(f"\n実験マトリックスを生成しました: {output_file}")
    print(f"総実験数: {len(experiments)}")
    print(f"  - アスペクト数: {len(steam_aspects)}")
    print(f"  - Few-shot設定: {few_shots}")
    print(f"  - 各アスペクト × {len(few_shots)}設定 = {len(experiments)}実験")
    
    print("\n=== 実験一覧 ===")
    for exp in experiments:
        print(f"  {exp['experiment_id']}")

if __name__ == "__main__":
    main()












