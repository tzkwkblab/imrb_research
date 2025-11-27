#!/usr/bin/env python3
"""
3-shot実験マトリックス生成スクリプト

既存の実験マトリックスからfew_shot=1の実験を抽出し、
few_shot=3に変更したマトリックスを生成する。
"""

import json
from datetime import datetime
from pathlib import Path

def generate_3shot_matrix(input_matrix_path: str, output_matrix_path: str):
    """3-shot実験マトリックスを生成"""
    
    # 既存のマトリックスを読み込み
    with open(input_matrix_path, 'r', encoding='utf-8') as f:
        matrix = json.load(f)
    
    # few_shot=1の実験を抽出
    one_shot_experiments = [
        exp for exp in matrix['experiments'] 
        if exp.get('few_shot') == 1
    ]
    
    # few_shot=3に変更
    three_shot_experiments = []
    for exp in one_shot_experiments:
        new_exp = exp.copy()
        new_exp['few_shot'] = 3
        
        # experiment_idを更新（_1_を_3_に変更）
        if 'experiment_id' in new_exp:
            new_exp['experiment_id'] = new_exp['experiment_id'].replace('_1_', '_3_')
        
        three_shot_experiments.append(new_exp)
    
    # 新しいマトリックスを作成
    new_matrix = {
        "experiment_plan": {
            "total_experiments": len(three_shot_experiments),
            "main_experiments": len([e for e in three_shot_experiments if e.get('group_size') == 100]),
            "sub_experiments": len([e for e in three_shot_experiments if e.get('group_size') != 100]),
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "description": "3-shot実験（few_shot=1の実験をfew_shot=3に変更）",
            "llm_evaluation_model": "gpt-4o-mini",
            "main_experiment_settings": {
                "few_shot": 3,
                "gpt_model": "gpt-4o-mini",
                "use_aspect_descriptions": False,
                "use_llm_evaluation": True
            }
        },
        "experiments": three_shot_experiments
    }
    
    # ファイルに保存
    with open(output_matrix_path, 'w', encoding='utf-8') as f:
        json.dump(new_matrix, f, ensure_ascii=False, indent=2)
    
    print(f"3-shot実験マトリックスを生成しました: {output_matrix_path}")
    print(f"総実験数: {len(three_shot_experiments)}")
    
    # データセット別の内訳を表示
    datasets = {}
    for exp in three_shot_experiments:
        dataset = exp['dataset']
        if dataset not in datasets:
            datasets[dataset] = 0
        datasets[dataset] += 1
    
    print("\n=== データセット別実験数 ===")
    for dataset, count in sorted(datasets.items()):
        print(f"  {dataset}: {count}実験")
    
    return new_matrix

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent.parent
    input_matrix = project_root / "実験マトリックス.json"
    output_matrix = Path(__file__).parent / "3shot_experiment_matrix.json"
    
    generate_3shot_matrix(str(input_matrix), str(output_matrix))

