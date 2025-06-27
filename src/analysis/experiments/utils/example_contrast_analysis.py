#!/usr/bin/env python3
"""
対比因子分析統合ツール使用例

ContrastFactorAnalyzerの基本的な使い方とサンプル実験

# 最小限のコード例
from contrast_factor_analyzer import ContrastFactorAnalyzer

analyzer = ContrastFactorAnalyzer()
result = analyzer.analyze(
    group_a=["Great battery life", "Long-lasting battery"],
    group_b=["Poor screen quality", "Slow performance"],
    correct_answer="Battery performance and power management",
    output_dir="my_results/"
)

print(f"スコア: BERT={result['evaluation']['bert_score']:.3f}")
"""

import os
from dotenv import load_dotenv
from contrast_factor_analyzer import ContrastFactorAnalyzer

# 環境変数読み込み
load_dotenv()


def example_basic_analysis():
    """基本的な対比因子分析の例"""
    print("=== 基本的な対比因子分析 ===")
    
    # データ準備
    group_a = [
        "Great battery life lasting all day",
        "Excellent power management features", 
        "Long-lasting battery performance",
        "Battery lasts through heavy usage"
    ]
    
    group_b = [
        "Poor screen quality and resolution",
        "Uncomfortable keyboard layout",
        "Slow system performance", 
        "Display issues and color problems"
    ]
    
    correct_answer = "Battery performance and power management"
    
    # 分析実行
    analyzer = ContrastFactorAnalyzer(debug=True)
    result = analyzer.analyze(
        group_a=group_a,
        group_b=group_b,
        correct_answer=correct_answer,
        output_dir="results/basic_analysis/",
        experiment_name="battery_vs_display"
    )
    
    # 結果表示
    print("\n--- 分析結果 ---")
    print(f"LLM応答: {result['process']['llm_response']}")
    print(f"BERTスコア: {result['evaluation']['bert_score']:.4f}")
    print(f"BLEUスコア: {result['evaluation']['bleu_score']:.4f}")
    print(f"品質評価: {result['summary']['quality_assessment']['overall_quality']}")
    
    return result


def example_fewshot_analysis():
    """Few-shot学習を使った対比因子分析の例"""
    print("\n=== Few-shot学習を使った分析 ===")
    
    # Few-shot例題
    examples = [
        {
            "group_a": ["Fast delivery", "Quick shipping", "Express service"],
            "group_b": ["Slow response", "Delayed support", "Poor customer service"],
            "answer": "Delivery speed and customer service quality"
        },
        {
            "group_a": ["High quality materials", "Durable construction", "Premium build"],
            "group_b": ["Cheap plastic", "Fragile design", "Poor assembly"],
            "answer": "Material quality and build durability"
        }
    ]
    
    # データ準備
    group_a = [
        "User-friendly interface design",
        "Intuitive navigation system",
        "Easy-to-use features",
        "Simple and clean layout"
    ]
    
    group_b = [
        "Expensive pricing model",
        "High cost for basic features", 
        "Overpriced subscription plans",
        "Poor value for money"
    ]
    
    correct_answer = "User interface design and ease of use"
    
    # 分析実行
    analyzer = ContrastFactorAnalyzer(debug=True)
    result = analyzer.analyze(
        group_a=group_a,
        group_b=group_b,
        correct_answer=correct_answer,
        output_dir="results/fewshot_analysis/",
        examples=examples,
        experiment_name="ui_vs_pricing",
        output_language="英語"
    )
    
    # 結果表示
    print("\n--- Few-shot分析結果 ---")
    print(f"LLM応答: {result['process']['llm_response']}")
    print(f"BERTスコア: {result['evaluation']['bert_score']:.4f}")
    print(f"BLEUスコア: {result['evaluation']['bleu_score']:.4f}")
    
    return result


def example_batch_analysis():
    """バッチ実験の例"""
    print("\n=== バッチ実験 ===")
    
    # 複数の実験設定
    experiments = [
        {
            "group_a": ["Fast performance", "Quick response times", "High speed processing"],
            "group_b": ["Large file size", "Heavy application", "Resource intensive"],
            "correct_answer": "Performance speed and responsiveness"
        },
        {
            "group_a": ["Secure encryption", "Privacy protection", "Data safety features"],
            "group_b": ["Complex setup process", "Difficult configuration", "Hard to install"],
            "correct_answer": "Security and privacy features"
        },
        {
            "group_a": ["Beautiful design", "Attractive appearance", "Elegant styling"],
            "group_b": ["Limited functionality", "Missing features", "Basic capabilities"],
            "correct_answer": "Visual design and aesthetics"
        }
    ]
    
    # バッチ実行
    analyzer = ContrastFactorAnalyzer(debug=False)  # バッチ時はデバッグOFF
    results = analyzer.analyze_batch(
        experiments=experiments,
        output_dir="results/batch_analysis/",
        base_experiment_name="multi_feature_comparison"
    )
    
    # 結果サマリー
    print("\n--- バッチ分析結果サマリー ---")
    successful = sum(1 for r in results if r.get("summary", {}).get("success", False))
    print(f"実行実験数: {len(results)}")
    print(f"成功実験数: {successful}")
    
    for i, result in enumerate(results, 1):
        if result.get("summary", {}).get("success", False):
            eval_data = result["evaluation"]
            quality = result["summary"]["quality_assessment"]["overall_quality"]
            print(f"  実験{i}: BERT={eval_data['bert_score']:.3f}, BLEU={eval_data['bleu_score']:.3f}, 品質={quality}")
        else:
            print(f"  実験{i}: エラー - {result.get('summary', {}).get('error', 'Unknown error')}")
    
    return results


def example_different_languages():
    """異なる出力言語での分析例"""
    print("\n=== 多言語出力分析 ===")
    
    group_a = ["Technical documentation", "Developer guides", "API references"]
    group_b = ["Marketing materials", "Sales brochures", "Promotional content"]
    correct_answer = "Technical content and documentation"
    
    languages = ["英語", "日本語"]
    analyzer = ContrastFactorAnalyzer(debug=False)
    
    for lang in languages:
        print(f"\n--- {lang}での分析 ---")
        result = analyzer.analyze(
            group_a=group_a,
            group_b=group_b,
            correct_answer=correct_answer,
            output_dir=f"results/multilingual_analysis/",
            experiment_name=f"tech_vs_marketing_{lang}",
            output_language=lang
        )
        
        print(f"LLM応答({lang}): {result['process']['llm_response']}")
        print(f"品質評価: {result['summary']['quality_assessment']['overall_quality']}")


def main():
    """全ての使用例を実行"""
    print("対比因子分析統合ツール使用例")
    print("=" * 50)
    
    try:
        # 1. 基本分析
        basic_result = example_basic_analysis()
        
        # 2. Few-shot分析  
        fewshot_result = example_fewshot_analysis()
        
        # 3. バッチ分析
        batch_results = example_batch_analysis()
        
        # 4. 多言語分析
        example_different_languages()
        
        print("\n" + "=" * 50)
        print("全ての使用例が正常に完了しました")
        print(f"結果ファイルは results/ ディレクトリに保存されています")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        print("OpenAI APIキーが設定されているか確認してください")
        print("export OPENAI_API_KEY='your-api-key-here'")


if __name__ == "__main__":
    main() 