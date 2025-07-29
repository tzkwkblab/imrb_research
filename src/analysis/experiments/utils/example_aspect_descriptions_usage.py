#!/usr/bin/env python3
"""
アスペクト説明文機能使用例

新しく実装したアスペクト説明文機能の具体的な使用方法を示す
"""

import sys
from pathlib import Path

# 現在のディレクトリをパスに追加
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from contrast_factor_analyzer import ContrastFactorAnalyzer


def example_basic_usage():
    """基本的な使用例"""
    print("=== 基本的な使用例 ===")
    
    # テストデータ
    group_a = [
        "The gameplay mechanics are intuitive and engaging",
        "Controls are responsive and easy to learn",
        "The combat system is well-designed and balanced"
    ]
    
    group_b = [
        "Beautiful graphics and stunning visuals",
        "The art style is amazing and unique",
        "Visual effects are impressive and realistic"
    ]
    
    correct_answer = "gameplay"
    dataset_path = "data/external/steam-review-aspect-dataset"
    
    # オプション有効で実験実行
    analyzer = ContrastFactorAnalyzer(
        debug=True, 
        use_aspect_descriptions=True
    )
    
    result = analyzer.analyze(
        group_a=group_a,
        group_b=group_b, 
        correct_answer=correct_answer,
        output_dir="example_results",
        experiment_name="gameplay_vs_visual",
        dataset_path=dataset_path
    )
    
    print(f"実験結果:")
    print(f"  BERTスコア: {result['evaluation']['bert_score']:.4f}")
    print(f"  BLEUスコア: {result['evaluation']['bleu_score']:.4f}")
    print(f"  品質評価: {result['evaluation']['quality_assessment']}")
    print()


def example_comparison():
    """説明文使用前後の比較例"""
    print("=== 説明文使用前後の比較 ===")
    
    # テストデータ
    group_a = [
        "The story is compelling and well-written",
        "Character development is excellent",
        "The narrative is engaging from start to finish"
    ]
    
    group_b = [
        "The sound effects are realistic",
        "Music perfectly matches the mood",
        "Voice acting is top-notch"
    ]
    
    correct_answer = "story"
    dataset_path = "data/external/steam-review-aspect-dataset"
    
    # 通常モード（アスペクト名使用）
    analyzer_normal = ContrastFactorAnalyzer(debug=False, use_aspect_descriptions=False)
    result_normal = analyzer_normal.analyze(
        group_a=group_a,
        group_b=group_b,
        correct_answer=correct_answer,
        output_dir="example_results",
        experiment_name="story_vs_audio_normal"
    )
    
    # 説明文モード
    analyzer_desc = ContrastFactorAnalyzer(debug=False, use_aspect_descriptions=True)
    result_desc = analyzer_desc.analyze(
        group_a=group_a,
        group_b=group_b,
        correct_answer=correct_answer,
        output_dir="example_results",
        experiment_name="story_vs_audio_with_descriptions",
        dataset_path=dataset_path
    )
    
    print("比較結果:")
    print(f"  通常モード:")
    print(f"    BERT: {result_normal['evaluation']['bert_score']:.4f}")
    print(f"    BLEU: {result_normal['evaluation']['bleu_score']:.4f}")
    print(f"  説明文モード:")
    print(f"    BERT: {result_desc['evaluation']['bert_score']:.4f}")
    print(f"    BLEU: {result_desc['evaluation']['bleu_score']:.4f}")
    print()


def example_batch_analysis():
    """バッチ分析での使用例"""
    print("=== バッチ分析での使用例 ===")
    
    # 複数の実験設定
    experiments = [
        {
            "group_a": [
                "The gameplay is smooth and responsive",
                "Controls are intuitive and easy to use",
                "The mechanics are well-balanced"
            ],
            "group_b": [
                "The graphics are beautiful and detailed",
                "Visual effects are stunning",
                "The art style is unique and appealing"
            ],
            "correct_answer": "gameplay",
            "experiment_name": "gameplay_vs_visual"
        },
        {
            "group_a": [
                "The story is engaging and well-written",
                "Character development is excellent",
                "The plot is compelling"
            ],
            "group_b": [
                "The sound design is immersive",
                "Music enhances the atmosphere",
                "Audio quality is outstanding"
            ],
            "correct_answer": "story",
            "experiment_name": "story_vs_audio"
        }
    ]
    
    dataset_path = "data/external/steam-review-aspect-dataset"
    
    # バッチ分析実行
    analyzer = ContrastFactorAnalyzer(
        debug=False, 
        use_aspect_descriptions=True
    )
    
    results = analyzer.analyze_batch(
        experiments=experiments,
        output_dir="example_results",
        base_experiment_name="batch_with_descriptions"
    )
    
    print("バッチ分析結果:")
    for i, result in enumerate(results, 1):
        print(f"  実験{i}: {result['experiment_info']['experiment_name']}")
        print(f"    BERT: {result['evaluation']['bert_score']:.4f}")
        print(f"    BLEU: {result['evaluation']['bleu_score']:.4f}")
    print()


def main():
    """メイン関数"""
    print("アスペクト説明文機能使用例\n")
    
    # 各使用例実行
    example_basic_usage()
    example_comparison()
    example_batch_analysis()
    
    print("使用例完了")


if __name__ == "__main__":
    main()