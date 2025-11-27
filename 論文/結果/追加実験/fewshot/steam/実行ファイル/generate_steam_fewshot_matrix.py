#!/usr/bin/env python3
"""
Steamデータセット Few-shot実験マトリックス生成スクリプト

Steamデータセットで4アスペクトに対してfew-shotを0, 1, 3で行い、
BERT/BLEUスコアを抽出する実験のマトリックスを生成する。
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
    
    # Steamアスペクト
    steam_aspects = ["gameplay", "visual", "story", "audio"]
    
    # Few-shot設定
    few_shots = [0, 1, 3]
    
    experiments = []
    
    for aspect in steam_aspects:
        for few_shot in few_shots:
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
        "description": "Steamデータセット: 4アスペクト × 3Few-shot(0,1,3) = 12実験",
        "settings": {
            "dataset": "steam",
            "aspects": steam_aspects,
            "few_shots": few_shots,
            "group_size": 100,
            "use_llm_evaluation": False,
            "gpt_model": "gpt-4o-mini",
            "temperature": 0.0,
            "max_tokens": 100,
            "llm_evaluation_temperature": 0.0,
            "examples_file": "data/analysis-workspace/contrast_examples/steam/steam_examples_v1.json",
            "evaluation_metrics": ["bert_score", "bleu_score"]
        }
    }
    
    # マトリックスJSONを生成
    matrix = {
        "experiment_plan": experiment_plan,
        "experiments": experiments
    }
    
    # ファイルに保存
    script_dir = Path(__file__).parent
    output_file = script_dir.parent / "マトリックス" / "steam_fewshot_matrix.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
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

