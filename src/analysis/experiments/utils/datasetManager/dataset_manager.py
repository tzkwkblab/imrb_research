#!/usr/bin/env python3
"""
データセット統一管理ツール（リファクタリング版）

全データセットを統一インターフェースで操作可能にする
設定駆動・責任分離・テスト容易性を重視した設計

使用例: 
    # 設定ファイル駆動
    manager = DatasetManager.from_config()
    splits = manager.get_binary_splits("steam", aspect="gameplay", group_size=300)
    
    # 依存性注入対応  
    config = DatasetConfig()
    manager = DatasetManager(config=config)
"""

import random
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime

# 新しいモジュール構成をインポート
try:
    from ..config import DatasetConfig, ConfigValidator, ValidationError
    from ..loaders import (
        BaseDatasetLoader, UnifiedRecord,
        SteamDatasetLoader, SemEvalDatasetLoader, AmazonDatasetLoader
    )
    from ..splitters import (
        BaseSplitter, BinarySplitResult, SplitOptions,
        AspectSplitter, BinarySplitter
    )
    
    # 後方互換性のため元のクラスもエクスポート
    from ..loaders.base import UnifiedRecord
    from ..splitters.base import BinarySplitResult
except ImportError:
    # フォールバック: 絶対インポート
    from config import DatasetConfig, ConfigValidator, ValidationError
    from loaders import (
        BaseDatasetLoader, UnifiedRecord,
        SteamDatasetLoader, SemEvalDatasetLoader, AmazonDatasetLoader
    )
    from splitters import (
        BaseSplitter, BinarySplitResult, SplitOptions,
        AspectSplitter, BinarySplitter
    )
    
    # 後方互換性のため元のクラスもエクスポート
    from loaders.base import UnifiedRecord
    from splitters.base import BinarySplitResult


class LoaderFactory:
    """ローダーファクトリー"""
    
    @staticmethod
    def create_loader(dataset_id: str, config: Optional[DatasetConfig] = None) -> BaseDatasetLoader:
        """ローダーインスタンス作成"""
        loader_mapping = {
            "steam": SteamDatasetLoader,
            "semeval": SemEvalDatasetLoader,
            "amazon": AmazonDatasetLoader
        }
        
        if dataset_id not in loader_mapping:
            raise ValueError(f"未対応のデータセット: {dataset_id}")
        
        loader_class = loader_mapping[dataset_id]
        return loader_class(config=config)


class SplitterFactory:
    """分割戦略ファクトリー"""
    
    @staticmethod
    def create_splitter(split_type: str) -> BaseSplitter:
        """分割戦略インスタンス作成"""
        splitter_mapping = {
            "aspect_vs_others": AspectSplitter,
            "binary_label": BinarySplitter
        }
        
        if split_type not in splitter_mapping:
            raise ValueError(f"未対応の分割タイプ: {split_type}")
        
        splitter_class = splitter_mapping[split_type]
        return splitter_class()


class DatasetManager:
    """データセット統一管理クラス（リファクタリング版）"""
    
    def __init__(self, config: Optional[DatasetConfig] = None, random_seed: int = 42):
        """
        初期化
        
        Args:
            config: 設定オブジェクト（Noneの場合はデフォルト設定）
            random_seed: ランダムシード値
        """
        self.config = config or DatasetConfig()
        self.random_seed = random_seed
        self._setup_random_seed()
        
        # ファクトリー初期化
        self.loader_factory = LoaderFactory()
        self.splitter_factory = SplitterFactory()
        
        # キャッシュ
        self._loader_cache: Dict[str, BaseDatasetLoader] = {}
        self._data_cache: Dict[str, List[UnifiedRecord]] = {}
        
        # 設定検証
        self.validator = ConfigValidator(self.config)
    
    @classmethod
    def from_config(cls, config_path: Optional[str] = None) -> 'DatasetManager':
        """設定ファイルからインスタンス作成"""
        config = DatasetConfig(config_path)
        defaults = config.get_experiment_defaults()
        return cls(config=config, random_seed=defaults.random_seed)
    
    def _setup_random_seed(self) -> None:
        """ランダムシード設定"""
        random.seed(self.random_seed)
        np.random.seed(self.random_seed)
    
    def get_loader(self, dataset_id: str, use_cache: bool = True) -> BaseDatasetLoader:
        """ローダー取得"""
        if use_cache and dataset_id in self._loader_cache:
            return self._loader_cache[dataset_id]
        
        loader = self.loader_factory.create_loader(dataset_id, self.config)
        
        if use_cache:
            self._loader_cache[dataset_id] = loader
        
        return loader
    
    def list_available_datasets(self) -> Dict[str, Dict]:
        """利用可能なデータセット情報を取得"""
        datasets_info = {}
        
        for dataset_id in self.config.list_available_datasets():
            try:
                loader = self.get_loader(dataset_id)
                info = loader.get_domain_info()
                info['aspects'] = loader.get_available_aspects()
                
                # アクセス可能性チェック
                info['accessible'] = self.validator.check_dataset_accessibility(dataset_id)
                
                # 設定検証結果
                warnings = self.validator.validate_dataset(dataset_id)
                if warnings:
                    info['warnings'] = warnings
                
                datasets_info[dataset_id] = info
                
            except Exception as e:
                datasets_info[dataset_id] = {"error": str(e)}
        
        return datasets_info
    
    def get_dataset_records(self, dataset_id: str, use_cache: bool = True) -> List[UnifiedRecord]:
        """データセットのレコードを取得"""
        if use_cache and dataset_id in self._data_cache:
            return self._data_cache[dataset_id]
        
        loader = self.get_loader(dataset_id)
        records = loader.load_with_cache(use_cache)
        
        if use_cache:
            self._data_cache[dataset_id] = records
        
        return records
    
    def get_binary_splits(
        self,
        dataset_id: str,
        aspect: str,
        group_size: int = 300,
        split_type: str = "aspect_vs_others",
        **kwargs
    ) -> BinarySplitResult:
        """
        二項分割データを取得（メイン機能）
        
        Args:
            dataset_id: データセット名 ("steam", "semeval", "amazon")
            aspect: 対象アスペクト
            group_size: 各グループのサンプル数
            split_type: 分割タイプ ("aspect_vs_others", "binary_label")
            **kwargs: 追加の分割オプション
        
        Returns:
            BinarySplitResult: 二項分割結果
        """
        # レコード取得
        records = self.get_dataset_records(dataset_id)
        
        # 分割オプション作成
        options = SplitOptions(
            group_size=group_size,
            random_seed=self.random_seed,
            **kwargs
        )
        
        # 分割戦略取得・実行
        splitter = self.splitter_factory.create_splitter(split_type)
        return splitter.split(records, aspect, options)
    
    def create_examples(
        self, 
        dataset_id: str, 
        aspect: str, 
        shot_count: int,
        language: str = "en"
    ) -> List[Dict]:
        """Few-shot用例題を作成"""
        if shot_count == 0:
            return []
        
        templates = self.config.get_example_templates(dataset_id, aspect)
        
        # 指定数まで例題を返す（循環使用）
        if templates:
            examples = []
            for i in range(shot_count):
                template = templates[i % len(templates)]
                examples.append({
                    "group_a": template.group_a,
                    "group_b": template.group_b,
                    "answer": template.answer
                })
            return examples
        
        return []
    
    def get_experiment_config(
        self, 
        dataset_id: str, 
        aspects: List[str] = None,
        shot_settings: List[int] = None
    ) -> Dict:
        """実験設定を取得"""
        defaults = self.config.get_experiment_defaults()
        
        if aspects is None:
            aspects = self.config.get_dataset_aspects(dataset_id)
        
        if shot_settings is None:
            shot_settings = defaults.shot_settings
        
        loader = self.get_loader(dataset_id)
        
        return {
            "dataset_id": dataset_id,
            "aspects": aspects,
            "shot_settings": shot_settings,
            "estimated_experiments": len(aspects) * len(shot_settings),
            "domain_info": loader.get_domain_info(),
            "default_group_size": defaults.group_size,
            "supported_split_types": defaults.split_types
        }
    
    def validate_configuration(self) -> Dict[str, List[str]]:
        """設定検証実行"""
        all_warnings = self.validator.validate_all()
        
        result = {
            "status": "valid" if not all_warnings else "warnings",
            "warnings": all_warnings,
            "datasets_checked": len(self.config.list_available_datasets()),
            "timestamp": datetime.now().isoformat()
        }
        
        return result
    
    def get_data_statistics(self, dataset_id: str) -> Dict:
        """データ統計情報取得"""
        loader = self.get_loader(dataset_id)
        return loader.get_data_stats()
    
    def clear_cache(self) -> None:
        """全キャッシュクリア"""
        self._loader_cache.clear()
        self._data_cache.clear()
        
        # ローダー内キャッシュもクリア
        for loader in self._loader_cache.values():
            loader.clear_cache()


def main():
    """メイン関数（テスト用）"""
    manager = DatasetManager()
    
    # 利用可能データセット一覧
    datasets = manager.list_available_datasets()
    print("利用可能データセット:")
    for dataset_id, info in datasets.items():
        print(f"  {dataset_id}: {info}")
    
    # 設定検証
    validation = manager.validate_configuration()
    print(f"\n設定検証結果: {validation}")


if __name__ == "__main__":
    main()