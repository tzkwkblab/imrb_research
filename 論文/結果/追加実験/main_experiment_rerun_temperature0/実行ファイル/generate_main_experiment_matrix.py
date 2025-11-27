#!/usr/bin/env python3
"""
メイン実験再実行用マトリックス生成スクリプト

理想パラメータでメイン実験を再実行するための実験マトリックスを生成する。
- SemEval: 4アスペクト
- GoEmotions: 28アスペクト
- Steam: 4アスペクト
合計36実験

パラメータ設定:
- few_shot: 0
- temperature: 0.0
- max_tokens: 2000
- group_size: 100
- use_llm_evaluation: true
"""

import json
from datetime import datetime
from pathlib import Path

def generate_experiment_id(
    dataset: str,
    aspect: str,
    domain: str = None
) -> str:
    """実験IDを生成"""
    if dataset == "semeval" and domain:
        return f"semeval_{domain}_{aspect}_0_4o-mini_word"
    elif dataset == "goemotions":
        return f"goemotions_{aspect}_0_4o-mini_word"
    elif dataset == "steam":
        return f"steam_{aspect}_0_4o-mini_word"
    else:
        return f"{dataset}_{aspect}_0_4o-mini_word"

def create_experiment_config(
    dataset: str,
    aspect: str,
    domain: str = None,
    group_size: int = 100,
    few_shot: int = 0,
    use_llm_evaluation: bool = True
) -> dict:
    """実験設定を作成"""
    experiment_id = generate_experiment_id(dataset, aspect, domain)
    
    return {
        "experiment_id": experiment_id,
        "dataset": dataset,
        "aspect": aspect,
        "domain": domain,
        "few_shot": few_shot,
        "gpt_model": "gpt-4o-mini",
        "group_size": group_size,
        "split_type": "aspect_vs_others",
        "use_llm_evaluation": use_llm_evaluation,
        "llm_evaluation_model": "gpt-4o-mini",
        "use_aspect_descriptions": False
    }

def main():
    """メイン実行"""
    experiments = []
    
    # SemEval: 4アスペクト
    semeval_configs = [
        ("restaurant", "food"),
        ("restaurant", "service"),
        ("laptop", "battery"),
        ("laptop", "screen")
    ]
    for domain, aspect in semeval_configs:
        exp = create_experiment_config(
            dataset="semeval",
            aspect=aspect,
            domain=domain,
            group_size=100,
            few_shot=0,
            use_llm_evaluation=True
        )
        experiments.append(exp)
    
    # GoEmotions: 28アスペクト
    goemotions_aspects = [
        "admiration", "amusement", "anger", "annoyance", "approval",
        "caring", "confusion", "curiosity", "desire", "disappointment",
        "disapproval", "disgust", "embarrassment", "excitement", "fear",
        "gratitude", "grief", "joy", "love", "nervousness",
        "optimism", "pride", "realization", "relief", "remorse",
        "sadness", "surprise", "neutral"
    ]
    for aspect in goemotions_aspects:
        exp = create_experiment_config(
            dataset="goemotions",
            aspect=aspect,
            domain=None,
            group_size=100,
            few_shot=0,
            use_llm_evaluation=True
        )
        experiments.append(exp)
    
    # Steam: 4アスペクト
    steam_aspects = ["gameplay", "visual", "story", "audio"]
    for aspect in steam_aspects:
        exp = create_experiment_config(
            dataset="steam",
            aspect=aspect,
            domain=None,
            group_size=100,
            few_shot=0,
            use_llm_evaluation=True
        )
        experiments.append(exp)
    
    # 実験計画情報
    experiment_plan = {
        "total_experiments": len(experiments),
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "description": "メイン実験再実行: SemEval(4) + GoEmotions(28) + Steam(4) = 36実験",
        "settings": {
            "temperature": 0.0,
            "max_tokens": 2000,
            "few_shot": 0,
            "group_size": 100,
            "use_llm_evaluation": True,
            "llm_evaluation_model": "gpt-4o-mini",
            "llm_evaluation_temperature": 0.0,
            "gpt_model": "gpt-4o-mini",
            "use_aspect_descriptions": False,
            "evaluation_metrics": ["bert_score", "bleu_score", "llm_score"]
        },
        "datasets": {
            "semeval": {
                "count": 4,
                "aspects": ["food", "service", "battery", "screen"],
                "domains": ["restaurant", "laptop"]
            },
            "goemotions": {
                "count": 28,
                "aspects": goemotions_aspects
            },
            "steam": {
                "count": 4,
                "aspects": steam_aspects
            }
        }
    }
    
    # マトリックスJSONを生成
    matrix = {
        "experiment_plan": experiment_plan,
        "experiments": experiments
    }
    
    # ファイルに保存
    script_dir = Path(__file__).parent
    output_file = script_dir.parent / "マトリックス" / "main_experiment_matrix.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(matrix, f, ensure_ascii=False, indent=2)
    
    print(f"\n実験マトリックスを生成しました: {output_file}")
    print(f"総実験数: {len(experiments)}")
    print(f"  - SemEval: 4実験")
    print(f"  - GoEmotions: 28実験")
    print(f"  - Steam: 4実験")
    
    print("\n=== 実験パラメータ ===")
    print(f"  few_shot: 0")
    print(f"  temperature: 0.0")
    print(f"  max_tokens: 2000")
    print(f"  group_size: 100")
    print(f"  use_llm_evaluation: True")
    print(f"  GPTモデル: gpt-4o-mini")
    
    print("\n=== データセット別実験数 ===")
    semeval_count = sum(1 for exp in experiments if exp['dataset'] == 'semeval')
    goemotions_count = sum(1 for exp in experiments if exp['dataset'] == 'goemotions')
    steam_count = sum(1 for exp in experiments if exp['dataset'] == 'steam')
    print(f"  SemEval: {semeval_count}実験")
    print(f"  GoEmotions: {goemotions_count}実験")
    print(f"  Steam: {steam_count}実験")
    
    print("\n=== 実験一覧（最初の10件） ===")
    for i, exp in enumerate(experiments[:10]):
        print(f"  {i+1}. {exp['experiment_id']}")
    if len(experiments) > 10:
        print(f"  ... (残り{len(experiments)-10}件)")

if __name__ == "__main__":
    main()

