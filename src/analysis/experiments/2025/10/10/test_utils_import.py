#!/usr/bin/env python3
"""
utilsモジュールの動作確認とインポートテスト
"""

import sys
from pathlib import Path

# utilsディレクトリのパス設定
utils_dir = Path(__file__).parent.parent.parent.parent / "utils"
sys.path.insert(0, str(utils_dir))

def test_imports():
    """各モジュールのインポートテスト"""
    print("=== utilsモジュール インポートテスト ===\n")
    
    tests = []
    
    # 1. DatasetManager
    try:
        from datasetManager.dataset_manager import DatasetManager
        print("✅ DatasetManager インポート成功")
        tests.append(("DatasetManager", True, None))
    except Exception as e:
        print(f"❌ DatasetManager インポート失敗: {e}")
        tests.append(("DatasetManager", False, str(e)))
    
    # 2. ContrastFactorAnalyzer
    try:
        from cfGenerator.contrast_factor_analyzer import ContrastFactorAnalyzer
        print("✅ ContrastFactorAnalyzer インポート成功")
        tests.append(("ContrastFactorAnalyzer", True, None))
    except Exception as e:
        print(f"❌ ContrastFactorAnalyzer インポート失敗: {e}")
        tests.append(("ContrastFactorAnalyzer", False, str(e)))
    
    # 3. スコア計算
    try:
        from scores.get_score import calculate_scores
        print("✅ calculate_scores インポート成功")
        tests.append(("calculate_scores", True, None))
    except Exception as e:
        print(f"❌ calculate_scores インポート失敗: {e}")
        tests.append(("calculate_scores", False, str(e)))
    
    # 4. LLMFactory
    try:
        from LLM.llm_factory import LLMFactory
        print("✅ LLMFactory インポート成功")
        tests.append(("LLMFactory", True, None))
    except Exception as e:
        print(f"❌ LLMFactory インポート失敗: {e}")
        tests.append(("LLMFactory", False, str(e)))
    
    # 5. プロンプト生成
    try:
        from promptGen.prompt_contrast_factor import generate_contrast_factor_prompt
        print("✅ generate_contrast_factor_prompt インポート成功")
        tests.append(("generate_contrast_factor_prompt", True, None))
    except Exception as e:
        print(f"❌ generate_contrast_factor_prompt インポート失敗: {e}")
        tests.append(("generate_contrast_factor_prompt", False, str(e)))
    
    print("\n=== テスト結果サマリー ===")
    success_count = sum(1 for _, success, _ in tests if success)
    total_count = len(tests)
    print(f"成功: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("✅ 全てのインポートが成功しました")
        return True
    else:
        print("❌ 一部のインポートが失敗しました")
        return False

def test_basic_functionality():
    """基本機能のテスト"""
    print("\n=== 基本機能テスト ===\n")
    
    try:
        from datasetManager.dataset_manager import DatasetManager
        
        # DatasetManagerの基本動作確認
        print("[1] DatasetManager初期化テスト")
        manager = DatasetManager()
        print("✅ DatasetManager初期化成功")
        
        # 利用可能データセット確認
        print("\n[2] 利用可能データセット確認")
        datasets = manager.list_datasets()
        print(f"✅ 利用可能データセット: {datasets}")
        
        return True
        
    except Exception as e:
        print(f"❌ 基本機能テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン実行"""
    print("utilsモジュール動作確認開始\n")
    
    # インポートテスト
    import_success = test_imports()
    
    if import_success:
        # 基本機能テスト
        func_success = test_basic_functionality()
        
        if func_success:
            print("\n✅ 全てのテストが成功しました")
            return 0
    
    print("\n❌ テストに失敗しました")
    return 1

if __name__ == "__main__":
    exit(main())

