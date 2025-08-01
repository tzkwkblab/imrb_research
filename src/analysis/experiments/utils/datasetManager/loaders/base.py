"""
データセットローダーの基底クラス
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Union
from pathlib import Path


@dataclass
class UnifiedRecord:
    """統一レコード形式"""
    text: str
    aspect: str
    label: Union[str, int, float]
    domain: str = ""
    dataset_id: str = ""
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseDatasetLoader(ABC):
    """データセットローダーの基底クラス"""
    
    def __init__(self, base_path: Optional[str] = None, dataset_id: str = ""):
        """
        初期化
        
        Args:
            base_path: データセットの基本パス
            dataset_id: データセットID
        """
        self.base_path = Path(base_path) if base_path else None
        self.dataset_id = dataset_id
        self._cache: Optional[List[UnifiedRecord]] = None
    
    @abstractmethod
    def load_raw_data(self) -> List[UnifiedRecord]:
        """生データを統一フォーマットで読み込み"""
        pass
    
    @abstractmethod
    def get_available_aspects(self) -> List[str]:
        """利用可能なアスペクト一覧"""
        pass
    
    @abstractmethod
    def get_domain_info(self) -> Dict:
        """ドメイン情報取得"""
        pass
    
    def load_with_cache(self, use_cache: bool = True) -> List[UnifiedRecord]:
        """キャッシュ対応データ読み込み"""
        if use_cache and self._cache is not None:
            return self._cache
        
        data = self.load_raw_data()
        
        if use_cache:
            self._cache = data
        
        return data
    
    def clear_cache(self) -> None:
        """キャッシュクリア"""
        self._cache = None
    
    def validate_data_path(self) -> bool:
        """データパス検証"""
        if not self.base_path:
            return False
        
        return self.base_path.exists() and self.base_path.is_dir()
    
    def get_data_stats(self) -> Dict:
        """データ統計情報取得"""
        try:
            records = self.load_with_cache()
            
            aspect_counts = {}
            label_counts = {}
            
            for record in records:
                aspect_counts[record.aspect] = aspect_counts.get(record.aspect, 0) + 1
                label_counts[str(record.label)] = label_counts.get(str(record.label), 0) + 1
            
            return {
                "total_records": len(records),
                "aspects": aspect_counts,
                "labels": label_counts,
                "dataset_id": self.dataset_id,
                "domain_info": self.get_domain_info()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def filter_by_aspect(self, aspect: str) -> List[UnifiedRecord]:
        """アスペクト別フィルタリング"""
        records = self.load_with_cache()
        return [r for r in records if r.aspect == aspect]
    
    def filter_by_label(self, label: Union[str, int, float]) -> List[UnifiedRecord]:
        """ラベル別フィルタリング"""
        records = self.load_with_cache()
        return [r for r in records if r.label == label] 