#!/usr/bin/env python3
"""
一連の流れの統合テスト

1. 対比因子抽出プロンプト作成 (prompt_contrast_factor.py)
2. GPTに問い合わせ (LLM/example_usage.py)
3. BERTとBLEUスコア計算 (get_score.py)
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# パス設定
current_dir = Path(__file__).parent
# 2025/06/22 -> 2025 -> experiments -> utils
experiments_dir = current_dir.parent.parent.parent
utils_dir = experiments_dir / "utils"
sys.path.append(str(utils_dir))
sys.path.append(str(utils_dir / "LLM"))



# 環境変数読み込み
load_dotenv()

# モジュールインポート
from prompt_contrast_factor import generate_contrast_factor_prompt
from llm_factory import LLMFactory
from get_score import calculate_scores


def run_integration_test():
    """統合テスト実行"""
    print("🚀 一連の流れ統合テスト開始")
    print("=" * 60)
    
    # ステップ1: テストデータ準備
    print("\n📊 ステップ1: テストデータ準備")
    group_a = [
        "Great battery life lasting all day",
        "Excellent power management features", 
        "Long-lasting battery performance"
    ]
    
    group_b = [
        "Poor screen quality and resolution",
        "Uncomfortable keyboard layout",
        "Slow system performance issues"
    ]
    
    # 正解例（評価用）
    expected_answer = "Battery life and power management"
    
    print(f"グループA（{len(group_a)}件）:")
    for text in group_a:
        print(f"  - {text}")
    
    print(f"\nグループB（{len(group_b)}件）:")
    for text in group_b:
        print(f"  - {text}")
    
    print(f"\n期待する回答: {expected_answer}")
    
    # ステップ2: プロンプト生成
    print("\n🔧 ステップ2: 対比因子抽出プロンプト生成")
    prompt, model_config = generate_contrast_factor_prompt(
        group_a=group_a,
        group_b=group_b,
        output_language="英語"
    )
    
    print(f"モデル設定: {model_config}")
    print(f"プロンプト長: {len(prompt)}文字")
    print(f"\n生成プロンプト:")
    print("-" * 40)
    print(prompt)
    print("-" * 40)
    
    # ステップ3: GPT問い合わせ
    print("\n🤖 ステップ3: GPT問い合わせ")
    llm_client = LLMFactory.create_client()
    print(f"使用モデル: {llm_client.get_model_name()}")
    
    # プロンプトからmessagesを構築
    messages = [
        {"role": "user", "content": prompt}
    ]
    
    gpt_response = llm_client.query(
        messages=messages,
        temperature=model_config.get('temperature', 0.7),
        max_tokens=model_config.get('max_tokens', 100)
    )
    
    print(f"GPT応答: {gpt_response}")
    
    # ステップ4: スコア計算
    print("\n📊 ステップ4: BERTとBLEUスコア計算")
    bert_score, bleu_score = calculate_scores(expected_answer, gpt_response)
    
    print(f"期待する回答: {expected_answer}")
    print(f"GPT実際回答: {gpt_response}")
    print(f"BERTスコア: {bert_score:.4f}")
    print(f"BLEUスコア: {bleu_score:.4f}")
    
    # ステップ5: 結果サマリー
    print("\n📋 ステップ5: 結果サマリー")
    print("=" * 60)
    print(f"✅ プロンプト生成: 成功 ({len(prompt)}文字)")
    print(f"✅ GPT問い合わせ: 成功 (モデル: {llm_client.get_model_name()})")
    print(f"✅ スコア計算: 成功 (BERT: {bert_score:.4f}, BLEU: {bleu_score:.4f})")
    
    # 結果辞書
    result = {
        "test_data": {
            "group_a": group_a,
            "group_b": group_b,
            "expected_answer": expected_answer
        },
        "prompt": {
            "content": prompt,
            "length": len(prompt),
            "model_config": model_config
        },
        "gpt_response": gpt_response,
        "evaluation": {
            "bert_score": bert_score,
            "bleu_score": bleu_score
        },
        "model_info": {
            "model_name": llm_client.get_model_name(),
            "temperature": model_config.get('temperature'),
            "max_tokens": model_config.get('max_tokens')
        }
    }
    
    print(f"\n🎉 統合テスト完了!")
    return result


def test_few_shot():
    """Few-shotテスト"""
    print("\n\n🎯 Few-shotテスト")
    print("=" * 60)
    
    # Few-shot例題
    examples = [
        {
            "group_a": ["Fast delivery", "Quick shipping"],
            "group_b": ["Slow response", "Delayed support"],
            "answer": "Delivery and shipping speed"
        }
    ]
    
    group_a = ["High-quality materials", "Durable construction"]
    group_b = ["Cheap plastic", "Fragile design"]
    expected_answer = "Material quality and durability"
    
    # プロンプト生成（Few-shot付き）
    prompt, model_config = generate_contrast_factor_prompt(
        group_a=group_a,
        group_b=group_b,
        output_language="英語",
        examples=examples
    )
    
    # GPT問い合わせ
    llm_client = LLMFactory.create_client()
    messages = [{"role": "user", "content": prompt}]
    gpt_response = llm_client.query(messages=messages, temperature=0.3, max_tokens=50)
    
    # スコア計算
    bert_score, bleu_score = calculate_scores(expected_answer, gpt_response)
    
    print(f"Few-shot例題数: {len(examples)}")
    print(f"期待する回答: {expected_answer}")
    print(f"GPT応答: {gpt_response}")
    print(f"BERTスコア: {bert_score:.4f}")
    print(f"BLEUスコア: {bleu_score:.4f}")
    
    return {
        "few_shot_examples": len(examples),
        "expected_answer": expected_answer,
        "gpt_response": gpt_response,
        "bert_score": bert_score,
        "bleu_score": bleu_score
    }


def main():
    """メイン関数"""
    try:
        # 0-shotテスト
        zero_shot_result = run_integration_test()
        
        # Few-shotテスト
        few_shot_result = test_few_shot()
        
        # 比較結果
        print(f"\n📊 0-shot vs Few-shot 比較")
        print("=" * 60)
        print(f"0-shot  - BERT: {zero_shot_result['evaluation']['bert_score']:.4f}, BLEU: {zero_shot_result['evaluation']['bleu_score']:.4f}")
        print(f"Few-shot- BERT: {few_shot_result['bert_score']:.4f}, BLEU: {few_shot_result['bleu_score']:.4f}")
        
        return {
            "zero_shot": zero_shot_result,
            "few_shot": few_shot_result
        }
        
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()