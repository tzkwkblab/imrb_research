"""
統一実験設定ファイルの使用例
experiment_config.py と experiment_settings.json の活用方法を示す
"""

import json
import sys
import os
from pathlib import Path

# 設定ファイルのパスを追加
config_dir = Path(__file__).parent
sys.path.append(str(config_dir))

from experiment_config import (
    ExperimentConfig, 
    HIGH_PRECISION_CONFIG, 
    BALANCED_CONFIG, 
    HIGH_CREATIVITY_CONFIG,
    PromptTemplates,
    MODEL_CONFIGS,
    TEMPERATURE_CONFIGS
)

def load_json_config(config_path: str = None) -> dict:
    """JSON設定ファイルを読み込む"""
    if config_path is None:
        config_path = config_dir / "experiment_settings.json"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def demonstrate_python_config():
    """Python設定ファイルの使用例"""
    print("=== Python設定ファイル使用例 ===\n")
    
    # 1. デフォルト設定
    print("1. デフォルト設定:")
    config = ExperimentConfig()
    print(f"   モデル: {config.model.name}")
    print(f"   Temperature: {config.model.temperature}")
    print(f"   Few-shot設定: {config.fewshot.shot_counts}")
    print(f"   評価指標: BERT={config.evaluation.use_bert_score}, BLEU={config.evaluation.use_bleu_score}")
    
    # 2. カスタム設定
    print("\n2. カスタム設定:")
    custom_config = ExperimentConfig(
        model_key="gpt-3.5-turbo",
        temperature_key="high_creativity",
        fewshot_key="minimal",
        evaluation_key="bert_only"
    )
    print(f"   モデル: {custom_config.model.name}")
    print(f"   Temperature: {custom_config.model.temperature}")
    print(f"   Few-shot設定: {custom_config.fewshot.shot_counts}")
    
    # 3. プリセット設定
    print("\n3. プリセット設定:")
    print(f"   高精度設定: {HIGH_PRECISION_CONFIG.model.name} (temp: {HIGH_PRECISION_CONFIG.model.temperature})")
    print(f"   バランス設定: {BALANCED_CONFIG.model.name} (temp: {BALANCED_CONFIG.model.temperature})")
    print(f"   高創造性設定: {HIGH_CREATIVITY_CONFIG.model.name} (temp: {HIGH_CREATIVITY_CONFIG.model.temperature})")
    
    # 4. プロンプトテンプレート取得
    print("\n4. プロンプトテンプレート:")
    contrast_prompt = config.get_prompt_template("contrast")
    print(f"   対比因子プロンプト長: {len(contrast_prompt)}文字")
    
    # 5. 設定の辞書出力
    print("\n5. 設定辞書出力 (JSONシリアライズ可能):")
    config_dict = config.to_dict()
    print(f"   設定項目数: {len(config_dict)}個")
    for key in config_dict.keys():
        print(f"   - {key}")

def demonstrate_json_config():
    """JSON設定ファイルの使用例"""
    print("\n=== JSON設定ファイル使用例 ===\n")
    
    # JSON設定を読み込み
    json_config = load_json_config()
    
    # 1. メタデータ確認
    metadata = json_config["metadata"]
    print("1. メタデータ:")
    print(f"   バージョン: {metadata['config_version']}")
    print(f"   作成日: {metadata['created_at']}")
    print(f"   作成者: {metadata['author']}")
    
    # 2. モデル設定一覧
    print("\n2. 利用可能なモデル:")
    for model_name, model_config in json_config["models"].items():
        print(f"   {model_name}: {model_config['description']}")
    
    # 3. Temperature設定一覧
    print("\n3. Temperature設定:")
    for temp_name, temp_config in json_config["temperature_settings"].items():
        print(f"   {temp_name}: {temp_config['value']} - {temp_config['description']}")
    
    # 4. 実験プリセット
    print("\n4. 実験プリセット:")
    for preset_name, preset_config in json_config["experiment_presets"].items():
        print(f"   {preset_name}: {preset_config['description']}")
        print(f"     モデル={preset_config['model']}, temp={preset_config['temperature']}")
    
    # 5. 評価設計思想
    print("\n5. 評価設計思想:")
    eval_philosophy = json_config["evaluation_design_philosophy"]
    print(f"   主要指標: {', '.join(eval_philosophy['primary_metrics'])}")
    print(f"   参考指標: {', '.join(eval_philosophy['reference_metrics'])}")
    print(f"   設計思想: {eval_philosophy['rationale']}")

def demonstrate_experiment_execution():
    """実際の実験実行での使用例"""
    print("\n=== 実験実行での使用例 ===\n")
    
    # 研究標準設定を使用
    config = ExperimentConfig(
        model_key="gpt-4",
        temperature_key="low_creativity",
        fewshot_key="standard",
        evaluation_key="primary"
    )
    
    print("研究標準設定での実験:")
    print(f"使用モデル: {config.model.name}")
    print(f"Temperature: {config.model.temperature}")
    print(f"Few-shot試行: {config.fewshot.shot_counts}")
    print(f"主要評価指標: BERT={config.evaluation.use_bert_score}, BLEU={config.evaluation.use_bleu_score}")
    
    # プロンプト生成例
    prompt_template = config.get_prompt_template("contrast")
    
    # 実際のプロンプト生成（例）
    sample_prompt = prompt_template.format(
        domain_context="レストラン",
        feature="food",
        group_a_size=100,
        group_b_size=100,
        few_shot_examples="",
        group_a_reviews="グループAのサンプルレビュー...",
        group_b_reviews="グループBのサンプルレビュー..."
    )
    
    print(f"\n生成されたプロンプト長: {len(sample_prompt)}文字")
    print("プロンプト冒頭:")
    print(sample_prompt[:200] + "...")

def demonstrate_config_comparison():
    """異なる設定の比較例"""
    print("\n=== 設定比較例 ===\n")
    
    configs = {
        "高精度": HIGH_PRECISION_CONFIG,
        "バランス": BALANCED_CONFIG,
        "高創造性": HIGH_CREATIVITY_CONFIG
    }
    
    print("設定名 | モデル | Temperature | Few-shot | 評価指標")
    print("-" * 60)
    
    for name, config in configs.items():
        model_name = config.model.name
        temperature = config.model.temperature
        shot_counts = len(config.fewshot.shot_counts)
        bert_score = "○" if config.evaluation.use_bert_score else "×"
        bleu_score = "○" if config.evaluation.use_bleu_score else "×"
        
        print(f"{name:<8} | {model_name:<15} | {temperature:<11} | {shot_counts}種類 | BERT:{bert_score} BLEU:{bleu_score}")

def save_custom_experiment_config():
    """カスタム実験設定の保存例"""
    print("\n=== カスタム設定保存例 ===\n")
    
    # カスタム設定作成
    custom_config = ExperimentConfig(
        model_key="gpt-4",
        temperature_key="deterministic",
        fewshot_key="comprehensive",
        evaluation_key="primary"
    )
    
    # 辞書形式で出力
    config_dict = custom_config.to_dict()
    
    # 実験用メタデータ追加
    config_dict["experiment_metadata"] = {
        "experiment_name": "高精度対比因子抽出実験",
        "researcher": "清野駿",
        "purpose": "SemEval ABSAデータセットでの最高精度実験",
        "expected_duration": "2-3時間"
    }
    
    # ファイル保存（例）
    output_path = config_dir / "custom_experiment_config.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, ensure_ascii=False, indent=2)
    
    print(f"カスタム設定を保存しました: {output_path}")
    print("設定内容:")
    print(f"  モデル: {config_dict['model']['name']}")
    print(f"  Temperature: {config_dict['model']['temperature']}")
    print(f"  実験名: {config_dict['experiment_metadata']['experiment_name']}")

def main():
    """メイン関数：すべての使用例を実行"""
    print("統一実験設定ファイル使用例\n")
    print("=" * 60)
    
    try:
        demonstrate_python_config()
        demonstrate_json_config()
        demonstrate_experiment_execution()
        demonstrate_config_comparison()
        save_custom_experiment_config()
        
        print("\n" + "=" * 60)
        print("✅ すべての使用例が正常に実行されました")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 