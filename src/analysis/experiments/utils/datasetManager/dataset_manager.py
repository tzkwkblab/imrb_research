#!/usr/bin/env python3
"""
データセット管理クラス（責任特化版）
データの取得・分割・キャッシュのみに責任を限定
"""

from typing import Dict, List
from pathlib import Path

from .loaders import (
    BaseDatasetLoader,
    UnifiedRecord,
    SteamDatasetLoader,
    SemEvalDatasetLoader,
    AmazonDatasetLoader,
    RetrievedConceptsDatasetLoader,
    GoEmotionsDatasetLoader,
)
from .splitters import BaseSplitter, BinarySplitResult, SplitOptions, AspectSplitter, BinarySplitter, RetrievedConceptsBottom100Splitter


class DatasetManager:
    LOADERS = {
        "steam": SteamDatasetLoader,
        "semeval": SemEvalDatasetLoader,
        "amazon": AmazonDatasetLoader,
        "retrieved_concepts": RetrievedConceptsDatasetLoader,
        "goemotions": GoEmotionsDatasetLoader,
    }
    
    SPLITTERS = {
        "aspect_vs_others": AspectSplitter,
        "binary_label": BinarySplitter,
        "aspect_vs_bottom100": RetrievedConceptsBottom100Splitter
    }
    
    def __init__(self, data_root: Path = Path("data/external")):
        self.data_root = data_root
        self._data_cache: Dict[str, List[UnifiedRecord]] = {}
    
    def load_dataset(self, dataset_id: str) -> List[UnifiedRecord]:
        """データセット読み込み"""
        if dataset_id not in self._data_cache:
            if dataset_id not in self.LOADERS:
                raise ValueError(f"未対応のデータセット: {dataset_id}")
            
            loader_class = self.LOADERS[dataset_id]
            
            # データセット固有のパスを構築
            if dataset_id == "steam":
                dataset_path = self.data_root / "steam-review-aspect-dataset" / "current"
            elif dataset_id == "semeval":
                dataset_path = self.data_root / "absa-review-dataset" / "pyabsa-integrated" / "current"
            elif dataset_id == "amazon":
                dataset_path = self.data_root / "amazon-product-reviews" / "kaggle-bittlingmayer" / "current"
            elif dataset_id == "retrieved_concepts":
                dataset_path = self.data_root / "retrieved-concepts" / "farnoosh" / "current"
            elif dataset_id == "goemotions":
                dataset_path = self.data_root / "goemotions" / "kaggle-debarshichanda" / "current"
            else:
                dataset_path = self.data_root
            
            loader = loader_class(str(dataset_path))
            self._data_cache[dataset_id] = loader.load_raw_data()
        
        return self._data_cache[dataset_id]
    
    def split_dataset(
        self,
        dataset_id: str,
        aspect: str,
        group_size: int,
        split_type: str = "aspect_vs_others"
    ) -> BinarySplitResult:
        """データセット分割"""
        if split_type not in self.SPLITTERS:
            raise ValueError(f"未対応の分割タイプ: {split_type}")
        
        records = self.load_dataset(dataset_id)
        
        splitter_class = self.SPLITTERS[split_type]
        splitter = splitter_class()
        
        options = SplitOptions(group_size=group_size, random_seed=42)
        
        return splitter.split(records, aspect, options)
    
    def get_dataset_info(self, dataset_id: str) -> Dict:
        """基本情報取得"""
        if dataset_id not in self.LOADERS:
            raise ValueError(f"未対応のデータセット: {dataset_id}")
        
        loader_class = self.LOADERS[dataset_id]
        loader = loader_class(str(self.data_root))
        
        return {
            "id": dataset_id,
            "domains": loader.get_domain_info(),
            "aspects": loader.get_available_aspects(),
            "total_records": len(self.load_dataset(dataset_id))
        }
    
    def list_datasets(self) -> List[str]:
        """利用可能データセット"""
        return list(self.LOADERS.keys())
    
    def clear_cache(self) -> None:
        """キャッシュクリア"""
        self._data_cache.clear()


# 使用例
def main():
    manager = DatasetManager()
    
    # データセット一覧
    print("利用可能データセット:", manager.list_datasets())
    
    # Steam データセットでゲームプレイアスペクトの分割
    result = manager.split_dataset("steam", "gameplay", 100)
    print(f"分割結果: A={len(result.group_a)}, B={len(result.group_b)}")


if __name__ == "__main__":
    main()
