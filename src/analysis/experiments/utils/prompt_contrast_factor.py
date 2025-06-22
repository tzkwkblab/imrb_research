#!/usr/bin/env python3
"""
対比因子生成プロンプト生成器

二つのグループの違いを分析するプロンプトを生成する
# 使用例
prompt = generate_contrast_factor_prompt(
    group_a=["Great battery"], 
    group_b=["Poor screen"], 
    domain="laptop",  # 内部的にドメイン変換は残っているが表示されない
)
"""

from typing import List, Dict
import sys
import os

# confディレクトリを追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'conf'))
from experiment_config import get_openai_params


def generate_contrast_factor_prompt(
    group_a: List[str],
    group_b: List[str],
    output_language: str = "英語"
) -> tuple[str, Dict]:
    """
    対比因子生成プロンプトを作成
    
    Args:
        group_a: グループAのテキストリスト
        group_b: グループBのテキストリスト
        output_language: 出力言語
    
    Returns:
        (プロンプト文字列, モデル設定辞書)
    """
    model_config = get_openai_params()
    
    group_a_text = "\n".join(f"- {text}" for text in group_a)
    group_b_text = "\n".join(f"- {text}" for text in group_b)
    
    prompt = f"""以下の2つのデータグループを比較して、グループAに特徴的でグループBには見られない表現パターンや内容の特徴を特定してください。

【グループA】
{group_a_text}

【グループB】
{group_b_text}

{output_language}で5-10単語程度で、グループAに特徴的でグループBには見られない主要な違いを簡潔に回答してください。

回答："""
    
    return prompt, model_config


def main():
    """テスト"""
    group_a = ["Great battery life", "Long-lasting battery", "Excellent power management"]
    group_b = ["Poor screen quality", "Uncomfortable keyboard", "Slow performance"]
    
    prompt, config = generate_contrast_factor_prompt(group_a, group_b)
    
    print("=== 生成されたプロンプト ===")
    print(prompt)
    print("\n=== モデル設定 ===")
    print(f"Model: {config['model']}")
    print(f"Temperature: {config['temperature']}")


if __name__ == "__main__":
    main()