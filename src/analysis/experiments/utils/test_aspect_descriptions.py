#!/usr/bin/env python3
"""
アスペクト説明文機能テストスクリプト

新しく実装したアスペクト説明文機能の動作確認を行う
"""

import sys
from pathlib import Path

# 現在のディレクトリをパスに追加
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from aspect_description_manager import AspectDescriptionManager
from get_score import calculate_scores, calculate_scores_with_descriptions
from contrast_factor_analyzer import ContrastFactorAnalyzer


def test_aspect_description_manager():
    """AspectDescriptionManagerのテスト"""
    print("=== AspectDescriptionManager テスト ===")
    
    # Steamデータセットパス（descriptions.csvが存在するディレクトリ）
    dataset_path = "data/external/steam-review-aspect-dataset"
    
    # マネージャー初期化
    manager = AspectDescriptionManager(dataset_path)
    
    print(f"説明文利用可能: {manager.has_descriptions()}")
    print(f"利用可能アスペクト: {manager.get_available_aspects()}")
    
    # テストケース
    test_aspects = ["gameplay", "story", "visual", "unknown_aspect"]
    
    for aspect in test_aspects:
        description = manager.get_description(aspect)
        print(f"{aspect}: {description}")
    
    print()


def test_score_calculation():
    """スコア計算のテスト"""
    print("=== スコア計算テスト ===")
    
    # テストデータ
    llm_response = "The game has excellent controls and mechanics that are easy to learn"
    
    # 通常のスコア計算（アスペクト名使用）
    bert_score1, bleu_score1 = calculate_scores("gameplay", llm_response)
    print(f"アスペクト名使用: BERT={bert_score1:.4f}, BLEU={bleu_score1:.4f}")
    
    # 説明文使用のスコア計算
    dataset_path = "data/external/steam-review-aspect-dataset"
    manager = AspectDescriptionManager(dataset_path)
    
    bert_score2, bleu_score2 = calculate_scores_with_descriptions(
        "gameplay", llm_response, manager, True
    )
    print(f"説明文使用: BERT={bert_score2:.4f}, BLEU={bleu_score2:.4f}")
    
    # 説明文の内容確認
    description = manager.get_description("gameplay")
    print(f"使用された説明文: {description}")
    
    print()


def test_contrast_factor_analyzer():
    """ContrastFactorAnalyzer統合テスト"""
    print("=== ContrastFactorAnalyzer統合テスト ===")
    
    # テストデータ
    group_a = [
        "The gameplay mechanics are intuitive and engaging",
        "Controls are responsive and easy to learn",
        "The combat system is well-designed"
    ]
    
    group_b = [
        "Beautiful graphics and stunning visuals",
        "The art style is amazing",
        "Visual effects are impressive"
    ]
    
    correct_answer = "gameplay"
    dataset_path = "data/external/steam-review-aspect-dataset"
    
    # 通常モードでテスト
    print("--- 通常モード（アスペクト名使用） ---")
    analyzer1 = ContrastFactorAnalyzer(debug=True, use_aspect_descriptions=False)
    
    try:
        result1 = analyzer1.analyze(
            group_a=group_a,
            group_b=group_b,
            correct_answer=correct_answer,
            output_dir="test_results",
            experiment_name="test_normal"
        )
        print(f"結果: BERT={result1['evaluation']['bert_score']:.4f}, BLEU={result1['evaluation']['bleu_score']:.4f}")
    except Exception as e:
        print(f"エラー: {e}")
    
    # 説明文モードでテスト
    print("\n--- 説明文モード ---")
    analyzer2 = ContrastFactorAnalyzer(debug=True, use_aspect_descriptions=True)
    
    try:
        result2 = analyzer2.analyze(
            group_a=group_a,
            group_b=group_b,
            correct_answer=correct_answer,
            output_dir="test_results",
            experiment_name="test_with_descriptions",
            dataset_path=dataset_path
        )
        print(f"結果: BERT={result2['evaluation']['bert_score']:.4f}, BLEU={result2['evaluation']['bleu_score']:.4f}")
    except Exception as e:
        print(f"エラー: {e}")


def main():
    """メイン関数"""
    print("アスペクト説明文機能テスト開始\n")
    
    # 各テスト実行
    test_aspect_description_manager()
    test_score_calculation()
    test_contrast_factor_analyzer()
    
    print("テスト完了")


if __name__ == "__main__":
    main()