#!/usr/bin/env python3
"""
Steamデータセット Group Size実験マトリックス生成スクリプト

Steamデータセットで4アスペクトに対してgroup_sizeを50/100/150/200/300で変化させる実験のマトリックスを生成する。
gpt-4o-miniのみ、few-shot=0で実行。
"""

import json
from datetime import datetime
from pathlib import Path

def generate_experiment_id(
    aspect: str,
    group_size: int,
    gpt_model: str = "gpt-4o-mini"
) -> str:
    """実験IDを生成"""
    model_short = gpt_model.replace("gpt-", "").replace(".", "")
    return f"steam_{aspect}_group_size_{group_size}_0_{model_short}_word"

def create_experiment_config(
    aspect: str,
    group_size: int,
    gpt_model: str = "gpt-4o-mini",
    few_shot: int = 0,
    use_llm_evaluation: bool = True
) -> dict:
    """実験設定を作成"""
    experiment_id = generate_experiment_id(aspect, group_size, gpt_model)
    
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
    # Steamアスペクト
    steam_aspects = ["gameplay", "visual", "story", "audio"]
    
    # Group Size設定
    group_sizes = [50, 100, 150, 200, 300]
    
    # GPTモデル（gpt-4o-miniのみ）
    gpt_model = "gpt-4o-mini"
    
    experiments = []
    
    for aspect in steam_aspects:
        for group_size in group_sizes:
            exp = create_experiment_config(
                aspect=aspect,
                group_size=group_size,
                gpt_model=gpt_model,
                few_shot=0,
                use_llm_evaluation=True
            )
            experiments.append(exp)
    
    # 実験計画情報
    experiment_plan = {
        "total_experiments": len(experiments),
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "description": "Steamデータセット: 4アスペクト × 5group_size(50/100/150/200/300) = 20実験",
        "settings": {
            "dataset": "steam",
            "aspects": steam_aspects,
            "group_sizes": group_sizes,
            "few_shot": 0,
            "use_llm_evaluation": True,
            "gpt_model": gpt_model,
            "temperature": 0.0,
            "max_tokens": 100,
            "llm_evaluation_temperature": 0.0,
            "evaluation_metrics": ["bert_score", "bleu_score", "llm_score"]
        }
    }
    
    # マトリックスJSONを生成
    matrix = {
        "experiment_plan": experiment_plan,
        "experiments": experiments
    }
    
    # ファイルに保存
    script_dir = Path(__file__).parent
    output_file = script_dir.parent / "マトリックス" / "steam_group_size_matrix.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(matrix, f, ensure_ascii=False, indent=2)
    
    print(f"\n実験マトリックスを生成しました: {output_file}")
    print(f"総実験数: {len(experiments)}")
    print(f"  - アスペクト数: {len(steam_aspects)}")
    print(f"  - Group Size設定: {group_sizes}")
    print(f"  - 各アスペクト × {len(group_sizes)}設定 = {len(experiments)}実験")
    
    print("\n=== 実験パラメータ ===")
    print(f"  データセット: steam")
    print(f"  アスペクト: {', '.join(steam_aspects)}")
    print(f"  group_size: {group_sizes}")
    print(f"  few_shot: 0 (固定)")
    print(f"  use_llm_evaluation: True")
    print(f"  GPTモデル: {gpt_model}")
    
    print("\n=== 実験一覧 ===")
    for exp in experiments:
        print(f"  {exp['experiment_id']}")

if __name__ == "__main__":
    main()

