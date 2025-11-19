#!/usr/bin/env python3
"""
実験マトリックス生成スクリプト

要求仕様:
1. メイン実験（データセット別性能比較）:
   - 全データセット（steam, semeval, amazon, goemotions）
   - 例題1問（few_shot: 1）
   - 単語比較（use_aspect_descriptions: false）
   - LLM評価あり（use_llm_evaluation: true）
   - モデルは4ominiで固定（gpt_model: gpt-4o-mini）
   - LLM評価モデルは4omini（llm_evaluation_model: gpt-4o-mini）

2. サブ実験:
   - Steamデータセット:
     - モデル比較：gpt-4o-mini vs gpt-5.1（few_shot: 1, use_aspect_descriptions: false）
     - 例題比較：0-shot, 1-shot, 3-shot（gpt_model: gpt-4o-mini, use_aspect_descriptions: false）
     - センテンスVS単語比較：use_aspect_descriptions: true vs false（gpt_model: gpt-4o-mini, few_shot: 1）
     - 全てLLM評価あり
   - Retrieved Concepts (COCO) - 別枠実験:
     - 目的：正解のないデータセットに対する対比因子生成の考察
     - 例題なし（few_shot: 0）
     - モデル：gpt-4o-mini と gpt-5.1 の両方
     - LLM評価なし（use_llm_evaluation: false）
     - 単語比較（use_aspect_descriptions: false）
     - スコアは参考値、出力された対比因子と画像を見比べて考察
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional

def generate_experiment_id(
    dataset: str,
    aspect: str,
    few_shot: int,
    gpt_model: str,
    use_aspect_descriptions: bool,
    domain: Optional[str] = None
) -> str:
    """実験IDを生成"""
    comparison_type = "sentence" if use_aspect_descriptions else "word"
    model_short = gpt_model.replace("gpt-", "").replace(".", "")
    
    if domain:
        return f"{dataset}_{domain}_{aspect}_{few_shot}_{model_short}_{comparison_type}"
    else:
        return f"{dataset}_{aspect}_{few_shot}_{model_short}_{comparison_type}"


def create_experiment_config(
    dataset: str,
    aspect: str,
    few_shot: int,
    gpt_model: str,
    use_aspect_descriptions: bool,
    group_size: int,
    split_type: str,
    use_llm_evaluation: bool,
    llm_evaluation_model: str,
    domain: Optional[str] = None
) -> Dict[str, Any]:
    """実験設定を作成"""
    experiment_id = generate_experiment_id(
        dataset, aspect, few_shot, gpt_model, use_aspect_descriptions, domain
    )
    
    config = {
        "experiment_id": experiment_id,
        "dataset": dataset,
        "aspect": aspect,
        "domain": domain,
        "few_shot": few_shot,
        "gpt_model": gpt_model,
        "group_size": group_size,
        "split_type": split_type,
        "use_llm_evaluation": use_llm_evaluation,
        "llm_evaluation_model": llm_evaluation_model,
        "use_aspect_descriptions": use_aspect_descriptions
    }
    
    return config


def generate_main_experiments() -> List[Dict[str, Any]]:
    """メイン実験（データセット別性能比較）を生成"""
    experiments = []
    
    # Steam - 全アスペクト
    steam_aspects = ["gameplay", "visual", "story", "audio", "technical", "price", "suggestion", "recommended"]
    for aspect in steam_aspects:
        exp = create_experiment_config(
            dataset="steam",
            aspect=aspect,
            few_shot=1,
            gpt_model="gpt-4o-mini",
            use_aspect_descriptions=False,
            group_size=300,
            split_type="aspect_vs_others",
            use_llm_evaluation=True,
            llm_evaluation_model="gpt-4o-mini"
        )
        experiments.append(exp)
    
    # SemEval
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
            few_shot=1,
            gpt_model="gpt-4o-mini",
            use_aspect_descriptions=False,
            group_size=300,
            split_type="aspect_vs_others",
            use_llm_evaluation=True,
            llm_evaluation_model="gpt-4o-mini",
            domain=domain
        )
        experiments.append(exp)
    
    # Amazon - 全アスペクト
    amazon_aspects = ["quality", "price", "delivery", "service", "product"]
    for aspect in amazon_aspects:
        exp = create_experiment_config(
            dataset="amazon",
            aspect=aspect,
            few_shot=1,
            gpt_model="gpt-4o-mini",
            use_aspect_descriptions=False,
            group_size=300,
            split_type="aspect_vs_others",
            use_llm_evaluation=True,
            llm_evaluation_model="gpt-4o-mini"
        )
        experiments.append(exp)
    
    # GoEmotions - 全アスペクト（28個）
    goemotions_aspects = [
        "admiration", "amusement", "anger", "annoyance", "approval", "caring",
        "confusion", "curiosity", "desire", "disappointment", "disapproval",
        "disgust", "embarrassment", "excitement", "fear", "gratitude", "grief",
        "joy", "love", "nervousness", "optimism", "pride", "realization",
        "relief", "remorse", "sadness", "surprise", "neutral"
    ]
    for aspect in goemotions_aspects:
        exp = create_experiment_config(
            dataset="goemotions",
            aspect=aspect,
            few_shot=1,
            gpt_model="gpt-4o-mini",
            use_aspect_descriptions=False,
            group_size=300,
            split_type="aspect_vs_others",
            use_llm_evaluation=True,
            llm_evaluation_model="gpt-4o-mini"
        )
        experiments.append(exp)
    
    return experiments


def generate_sub_experiments() -> List[Dict[str, Any]]:
    """サブ実験を生成"""
    experiments = []
    
    # Steam - 全アスペクト
    steam_aspects = ["gameplay", "visual", "story", "audio", "technical", "price", "suggestion", "recommended"]
    
    # 1. モデル比較（gpt-4o-mini vs gpt-5.1）
    for aspect in steam_aspects:
        for gpt_model in ["gpt-4o-mini", "gpt-5.1"]:
            exp = create_experiment_config(
                dataset="steam",
                aspect=aspect,
                few_shot=1,
                gpt_model=gpt_model,
                use_aspect_descriptions=False,
                group_size=300,
                split_type="aspect_vs_others",
                use_llm_evaluation=True,
                llm_evaluation_model="gpt-4o-mini"
            )
            experiments.append(exp)
    
    # 2. 例題比較（0-shot, 1-shot, 3-shot）
    for aspect in steam_aspects:
        for few_shot in [0, 1, 3]:
            exp = create_experiment_config(
                dataset="steam",
                aspect=aspect,
                few_shot=few_shot,
                gpt_model="gpt-4o-mini",
                use_aspect_descriptions=False,
                group_size=300,
                split_type="aspect_vs_others",
                use_llm_evaluation=True,
                llm_evaluation_model="gpt-4o-mini"
            )
            experiments.append(exp)
    
    # 3. センテンスVS単語比較（use_aspect_descriptions: true vs false）
    for aspect in steam_aspects:
        for use_aspect_descriptions in [False, True]:
            exp = create_experiment_config(
                dataset="steam",
                aspect=aspect,
                few_shot=1,
                gpt_model="gpt-4o-mini",
                use_aspect_descriptions=use_aspect_descriptions,
                group_size=300,
                split_type="aspect_vs_others",
                use_llm_evaluation=True,
                llm_evaluation_model="gpt-4o-mini"
            )
            experiments.append(exp)
    
    # Retrieved Concepts (COCO) - 別枠実験
    # 目的：正解のないデータセットに対する対比因子生成の考察
    coco_concepts = ["concept_0", "concept_1", "concept_2", "concept_10", "concept_50"]
    for concept in coco_concepts:
        for gpt_model in ["gpt-4o-mini", "gpt-5.1"]:
            exp = create_experiment_config(
                dataset="retrieved_concepts",
                aspect=concept,
                few_shot=0,
                gpt_model=gpt_model,
                use_aspect_descriptions=False,
                group_size=50,
                split_type="aspect_vs_bottom100",
                use_llm_evaluation=False,
                llm_evaluation_model="gpt-4o-mini"
            )
            experiments.append(exp)
    
    return experiments


def main():
    """メイン実行"""
    main_experiments = generate_main_experiments()
    sub_experiments = generate_sub_experiments()
    
    all_experiments = main_experiments + sub_experiments
    
    # 実験計画情報
    experiment_plan = {
        "total_experiments": len(all_experiments),
        "main_experiments": len(main_experiments),
        "sub_experiments": len(sub_experiments),
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "description": "データセット別性能比較（メイン）+ Steamサブ実験（モデル比較・例題比較・センテンスVS単語比較）+ COCO別枠実験（正解なしデータセット考察）",
        "llm_evaluation_model": "gpt-4o-mini",
        "main_experiment_settings": {
            "few_shot": 1,
            "gpt_model": "gpt-4o-mini",
            "use_aspect_descriptions": False,
            "use_llm_evaluation": True
        },
        "sub_experiment_settings": {
            "steam": {
                "use_llm_evaluation": True,
                "llm_evaluation_model": "gpt-4o-mini"
            },
            "retrieved_concepts": {
                "purpose": "正解のないデータセットに対する対比因子生成の考察",
                "few_shot": 0,
                "use_llm_evaluation": False,
                "models": ["gpt-4o-mini", "gpt-5.1"],
                "note": "スコアは参考値、出力された対比因子と画像を見比べて考察"
            }
        }
    }
    
    # マトリクスJSONを生成
    matrix = {
        "experiment_plan": experiment_plan,
        "experiments": all_experiments
    }
    
    # ファイルに保存
    output_file = "実験マトリックス.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(matrix, f, ensure_ascii=False, indent=2)
    
    print(f"実験マトリックスを生成しました: {output_file}")
    print(f"総実験数: {len(all_experiments)}")
    print(f"  - メイン実験: {len(main_experiments)}")
    print(f"  - サブ実験: {len(sub_experiments)}")
    
    # サマリー表示
    print("\n=== メイン実験サマリー ===")
    datasets = {}
    for exp in main_experiments:
        dataset = exp['dataset']
        if dataset not in datasets:
            datasets[dataset] = 0
        datasets[dataset] += 1
    
    for dataset, count in sorted(datasets.items()):
        print(f"  {dataset}: {count}実験")
    
    print("\n=== サブ実験サマリー ===")
    steam_exps = [e for e in sub_experiments if e['dataset'] == 'steam']
    coco_exps = [e for e in sub_experiments if e['dataset'] == 'retrieved_concepts']
    
    print(f"  Steamデータセット: {len(steam_exps)}実験")
    steam_aspect_count = 8
    print(f"    - モデル比較: {steam_aspect_count * 2}実験 ({steam_aspect_count}アスペクト × 2モデル)")
    print(f"    - 例題比較: {steam_aspect_count * 3}実験 ({steam_aspect_count}アスペクト × 3例題数)")
    print(f"    - センテンスVS単語比較: {steam_aspect_count * 2}実験 ({steam_aspect_count}アスペクト × 2比較タイプ)")
    
    print(f"\n  Retrieved Concepts (COCO) - 別枠実験: {len(coco_exps)}実験")
    print(f"    - 目的: 正解のないデータセットに対する対比因子生成の考察")
    print(f"    - 設定: 例題なし、モデル比較（gpt-4o-mini vs gpt-5.1）、LLM評価なし")
    print(f"    - コンセプト数: {len(coco_exps) // 2}個 × 2モデル")


if __name__ == "__main__":
    main()

