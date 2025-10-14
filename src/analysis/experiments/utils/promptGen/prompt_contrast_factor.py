#!/usr/bin/env python3
"""
対比因子生成プロンプト生成器

二つのグループの違いを分析するプロンプトを生成する
# 使用例
prompt = generate_contrast_factor_prompt(
    group_a=["Great battery"], 
    group_b=["Poor screen"], 
    output_language="英語", # 任意
    examples=[  # Few-shot用例題（任意）
        {
            "group_a": ["Fast delivery", "Quick shipping"],
            "group_b": ["Slow response", "Delayed support"], 
            "answer": "Fast delivery and shipping speed"
        }
    ]
)
"""

from typing import List, Dict, Optional
import sys
import os
import yaml

# configディレクトリを追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from experiment_config import get_openai_params


def _load_prompt_config():
    """プロンプト設定をYAMLから読み込み"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'paramaters.yml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config['contrast_factor_prompt']


def _format_examples(examples: List[Dict], example_template: str) -> str:
    """例題セクションを生成"""
    if not examples:
        return ""
    
    examples_text = []
    for i, example in enumerate(examples, 1):
        group_a_text = ", ".join(f'"{text}"' for text in example['group_a'])
        group_b_text = ", ".join(f'"{text}"' for text in example['group_b'])
        
        example_text = example_template.format(
            example_num=i,
            example_group_a=f"[{group_a_text}]",
            example_group_b=f"[{group_b_text}]",
            example_answer=example['answer']
        )
        examples_text.append(example_text)
    
    return "".join(examples_text)


def generate_contrast_factor_prompt(
    group_a: List[str],
    group_b: List[str],
    output_language: Optional[str] = None,
    examples: Optional[List[Dict]] = None
) -> tuple[str, Dict]:
    """
    対比因子生成プロンプトを作成
    
    Args:
        group_a: グループAのテキストリスト
        group_b: グループBのテキストリスト
        output_language: 出力言語（None時は設定ファイルのデフォルト使用）
        examples: Few-shot用例題リスト
                 [{"group_a": [...], "group_b": [...], "answer": "..."}]
    
    Returns:
        (プロンプト文字列, モデル設定辞書)
    """
    # 設定読み込み
    model_config = get_openai_params()
    prompt_config = _load_prompt_config()
    
    # デフォルト言語設定
    if output_language is None:
        output_language = prompt_config['default_language']
    
    # テキスト整形
    group_a_text = "\n".join(f"- {text}" for text in group_a)
    group_b_text = "\n".join(f"- {text}" for text in group_b)
    
    # 例題セクション生成
    examples_section = _format_examples(examples or [], prompt_config['example_template'])
    
    # プロンプト生成（設定ファイルのテンプレート使用）
    prompt = prompt_config['template'].format(
        examples_section=examples_section,
        group_a_text=group_a_text,
        group_b_text=group_b_text,
        output_language=output_language,
        word_count=prompt_config['word_count']
    )
    
    return prompt, model_config


def main():
    """テスト"""
    group_a = ["Great battery life", "Long-lasting battery", "Excellent power management"]
    group_b = ["Poor screen quality", "Uncomfortable keyboard", "Slow performance"]
    
    # 0-shotテスト
    print("=== 0-shot テスト ===")
    prompt0, config = generate_contrast_factor_prompt(group_a, group_b)
    print(prompt0)
    
    # 2-shotテスト
    examples = [
        {
            "group_a": ["Fast delivery", "Quick shipping"],
            "group_b": ["Slow response", "Delayed support"],
            "answer": "Fast delivery and shipping speed"
        },
        {
            "group_a": ["High quality materials", "Durable construction"],
            "group_b": ["Cheap plastic", "Fragile design"],
            "answer": "Material quality and build durability"
        }
    ]
    
    print("\n=== 2-shot テスト ===")
    prompt2, config = generate_contrast_factor_prompt(group_a, group_b, examples=examples)
    print(prompt2)
    
    print("\n=== モデル設定 ===")
    print(f"Model: {config['model']}")
    print(f"Temperature: {config['temperature']}")


if __name__ == "__main__":
    main()