#!/usr/bin/env python3
"""
Steamデータセット モデル比較実験マトリックス生成スクリプト（temperature=0版）

Steamデータセットで4アスペクトに対してgpt-4o-miniとgpt-5.1を比較する実験のマトリックスを生成する。
- temperature=0（生成モデル）
- group_size=100
- few_shot=1
- LLM評価有効（gpt-4o、temperature=0）
"""

import json
from datetime import datetime
from pathlib import Path

def generate_experiment_id(
    aspect: str,
    gpt_model: str,
    few_shot: int = 0
) -> str:
    """実験IDを生成"""
    model_short = gpt_model.replace("gpt-", "").replace(".", "")
    return f"steam_{aspect}_{few_shot}_{model_short}_word"

def create_experiment_config(
    aspect: str,
    gpt_model: str,
    group_size: int = 100,
    few_shot: int = 0,
    use_llm_evaluation: bool = True
) -> dict:
    """実験設定を作成"""
    experiment_id = generate_experiment_id(aspect, gpt_model, few_shot)
    
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
        "llm_evaluation_model": "gpt-4o",
        "use_aspect_descriptions": False
    }

def main():
    """メイン実行"""
    # Steamアスペクト
    steam_aspects = ["gameplay", "visual", "story", "audio"]
    
    # GPTモデル
    gpt_models = ["gpt-4o-mini", "gpt-5.1"]
    
    experiments = []
    
    for aspect in steam_aspects:
        for gpt_model in gpt_models:
            exp = create_experiment_config(
                aspect=aspect,
                gpt_model=gpt_model,
                group_size=100,
                few_shot=0,
                use_llm_evaluation=True
            )
            experiments.append(exp)
    
    # 実験計画情報
    experiment_plan = {
        "total_experiments": len(experiments),
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "description": "Steamデータセット: 4アスペクト × 2モデル(gpt-4o-mini, gpt-5.1) = 8実験。temperature=0、group_size=100、few_shot=0、LLM評価有効(gpt-4o, temperature=0)",
        "settings": {
            "dataset": "steam",
            "aspects": steam_aspects,
            "gpt_models": gpt_models,
            "group_size": 100,
            "few_shot": 0,
            "temperature": 0.0,
            "max_tokens": 100,
            "use_llm_evaluation": True,
            "llm_evaluation_model": "gpt-4o",
            "llm_evaluation_temperature": 0.0,
            "evaluation_metrics": ["bert_score", "bleu_score", "llm_evaluation"]
        }
    }
    
    # マトリックスJSONを生成
    matrix = {
        "experiment_plan": experiment_plan,
        "experiments": experiments
    }
    
    # ファイルに保存
    script_dir = Path(__file__).parent
    output_file = script_dir.parent / "マトリックス" / "steam_model_comparison_temperature0_matrix.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(matrix, f, ensure_ascii=False, indent=2)
    
    print(f"\n実験マトリックスを生成しました: {output_file}")
    print(f"総実験数: {len(experiments)}")
    print(f"  - アスペクト数: {len(steam_aspects)}")
    print(f"  - GPTモデル数: {len(gpt_models)}")
    print(f"  - 各アスペクト × {len(gpt_models)}モデル = {len(experiments)}実験")
    
    print("\n=== 実験パラメータ ===")
    print(f"  データセット: steam")
    print(f"  アスペクト: {', '.join(steam_aspects)}")
    print(f"  group_size: 100 (固定)")
    print(f"  few_shot: 0 (固定)")
    print(f"  temperature: 0.0 (生成モデル)")
    print(f"  max_tokens: 100")
    print(f"  use_llm_evaluation: True")
    print(f"  llm_evaluation_model: gpt-4o")
    print(f"  llm_evaluation_temperature: 0.0")
    print(f"  GPTモデル: {', '.join(gpt_models)}")
    
    print("\n=== 実験一覧 ===")
    for exp in experiments:
        print(f"  {exp['experiment_id']}")

if __name__ == "__main__":
    main()

