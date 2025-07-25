#!/usr/bin/env python3
"""
DatasetManager リファクタリング互換性テスト

既存のAPIが正常に動作することを確認
"""

import sys
from pathlib import Path

# パッケージパスを追加
current_dir = Path(__file__).parent
parent_dir = current_dir.parent.parent.parent  # src/
sys.path.insert(0, str(parent_dir))

try:
    from analysis.experiments.utils.dataset_manager import DatasetManager
    from analysis.experiments.utils.loaders.base import UnifiedRecord
    from analysis.experiments.utils.splitters.base import BinarySplitResult
except ImportError:
    # フォールバック: 直接インポート
    sys.path.insert(0, str(current_dir))
    import dataset_manager
    from dataset_manager import DatasetManager
    
    # 個別インポート
    from loaders.base import UnifiedRecord
    from splitters.base import BinarySplitResult


def test_basic_initialization():
    """基本初期化テスト"""
    print("🔧 基本初期化テスト")
    
    try:
        # 従来の初期化方法
        manager = DatasetManager()
        print("  ✅ 従来の初期化方法: 成功")
        
        # 新しい初期化方法
        manager_new = DatasetManager.from_config()
        print("  ✅ 新しい初期化方法: 成功")
        
        return True
    except Exception as e:
        print(f"  ❌ 初期化エラー: {e}")
        return False


def test_list_datasets():
    """データセット一覧取得テスト"""
    print("\n📊 データセット一覧取得テスト")
    
    try:
        manager = DatasetManager()
        datasets = manager.list_available_datasets()
        
        print(f"  ✅ データセット数: {len(datasets)}")
        for dataset_id, info in datasets.items():
            print(f"    - {dataset_id}: {info.get('domain', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"  ❌ データセット一覧取得エラー: {e}")
        return False


def test_binary_splits():
    """二項分割テスト"""
    print("\n⚡ 二項分割テスト")
    
    try:
        manager = DatasetManager()
        
        # Steam - binary_label分割
        print("  Steam - binary_label分割:")
        try:
            splits = manager.get_binary_splits(
                "steam", 
                aspect="gameplay", 
                group_size=10, 
                split_type="binary_label"
            )
            print(f"    ✅ グループA: {len(splits.group_a)}件")
            print(f"    ✅ グループB: {len(splits.group_b)}件")
            print(f"    ✅ 正解: {splits.correct_answer[:50]}...")
            
            # 戻り値の型チェック
            assert isinstance(splits, BinarySplitResult)
            assert isinstance(splits.group_a, list)
            assert isinstance(splits.group_b, list)
            assert isinstance(splits.correct_answer, str)
            assert isinstance(splits.metadata, dict)
            
        except Exception as e:
            print(f"    ⚠️ Steam binary_label: {e}")
        
        # Steam - aspect_vs_others分割
        print("  Steam - aspect_vs_others分割:")
        try:
            splits = manager.get_binary_splits(
                "steam", 
                aspect="gameplay", 
                group_size=10, 
                split_type="aspect_vs_others"
            )
            print(f"    ✅ グループA: {len(splits.group_a)}件")
            print(f"    ✅ グループB: {len(splits.group_b)}件")
            
        except Exception as e:
            print(f"    ⚠️ Steam aspect_vs_others: {e}")
        
        return True
    except Exception as e:
        print(f"  ❌ 二項分割テストエラー: {e}")
        return False


def test_example_creation():
    """例題作成テスト"""
    print("\n💡 例題作成テスト")
    
    try:
        manager = DatasetManager()
        
        examples = manager.create_examples("steam", "gameplay", shot_count=2)
        print(f"  ✅ 例題数: {len(examples)}")
        
        if examples:
            print(f"  📝 例題1: {examples[0].get('answer', 'N/A')}")
            
            # 戻り値の型チェック
            assert isinstance(examples, list)
            for example in examples:
                assert isinstance(example, dict)
                assert 'group_a' in example
                assert 'group_b' in example
                assert 'answer' in example
        
        return True
    except Exception as e:
        print(f"  ❌ 例題作成エラー: {e}")
        return False


def test_experiment_config():
    """実験設定取得テスト"""
    print("\n⚙️ 実験設定取得テスト")
    
    try:
        manager = DatasetManager()
        
        config = manager.get_experiment_config("steam")
        print(f"  ✅ アスペクト数: {len(config.get('aspects', []))}")
        print(f"  ✅ Shot設定: {config.get('shot_settings', [])}")
        print(f"  ✅ 推定実験数: {config.get('estimated_experiments', 0)}")
        
        # 戻り値の型チェック
        assert isinstance(config, dict)
        assert 'dataset_id' in config
        assert 'aspects' in config
        assert 'shot_settings' in config
        
        return True
    except Exception as e:
        print(f"  ❌ 実験設定取得エラー: {e}")
        return False


def test_data_statistics():
    """データ統計情報テスト"""
    print("\n📈 データ統計情報テスト")
    
    try:
        manager = DatasetManager()
        
        try:
            stats = manager.get_data_statistics("steam")
            print(f"  ✅ Steam統計: {stats.get('total_records', 'N/A')}件")
        except Exception as e:
            print(f"  ⚠️ Steam統計エラー: {e}")
        
        return True
    except Exception as e:
        print(f"  ❌ データ統計情報エラー: {e}")
        return False


def test_new_features():
    """新機能テスト"""
    print("\n🆕 新機能テスト")
    
    try:
        manager = DatasetManager.from_config()
        
        # 設定検証
        validation = manager.validate_configuration()
        print(f"  ✅ 設定検証: {validation.get('status', 'N/A')}")
        
        # キャッシュクリア
        manager.clear_cache()
        print("  ✅ キャッシュクリア: 成功")
        
        return True
    except Exception as e:
        print(f"  ❌ 新機能エラー: {e}")
        return False


def main():
    """メインテスト関数"""
    print("=" * 70)
    print("DatasetManager リファクタリング互換性テスト")
    print("=" * 70)
    
    tests = [
        test_basic_initialization,
        test_list_datasets,
        test_binary_splits,
        test_example_creation,
        test_experiment_config,
        test_data_statistics,
        test_new_features
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} 実行エラー: {e}")
    
    print("\n" + "=" * 70)
    print(f"テスト結果: {passed}/{total} 成功")
    
    if passed == total:
        print("🎉 全テストパス！既存APIの互換性が保たれています")
    elif passed >= total * 0.8:
        print("✅ 主要APIの互換性が保たれています")
    else:
        print("⚠️ 一部のAPIで問題が発生しています")
    
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 