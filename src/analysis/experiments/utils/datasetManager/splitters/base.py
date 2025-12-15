"""
データ分割戦略の基底クラス
"""

import random
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Union
from ..loaders.base import UnifiedRecord

logger = logging.getLogger(__name__)


@dataclass
class SplitOptions:
    """分割オプション"""
    group_size: int = 300
    random_seed: Optional[int] = 42
    balance_labels: bool = False
    min_samples_per_label: int = 10
    
    def __post_init__(self):
        if self.random_seed is not None:
            random.seed(self.random_seed)


@dataclass 
class BinarySplitResult:
    """二項分割結果"""
    group_a: List[str]
    group_b: List[str]
    correct_answer: str
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.metadata:
            self.metadata = {}
        
        # 基本メタデータを自動設定
        self.metadata.setdefault("timestamp", datetime.now().isoformat())
        self.metadata.setdefault("group_a_size", len(self.group_a))
        self.metadata.setdefault("group_b_size", len(self.group_b))


class BaseSplitter(ABC):
    """データ分割戦略の基底クラス"""
    
    def __init__(self, split_type: str = "unknown"):
        """
        初期化
        
        Args:
            split_type: 分割戦略タイプ
        """
        self.split_type = split_type
    
    @abstractmethod
    def split(
        self, 
        records: List[UnifiedRecord], 
        target_aspect: str,
        options: SplitOptions
    ) -> BinarySplitResult:
        """
        データ分割実行
        
        Args:
            records: 分割対象レコード
            target_aspect: 対象アスペクト
            options: 分割オプション
            
        Returns:
            BinarySplitResult: 分割結果
        """
        pass
    
    def adjust_sample_size(self, samples: List[str], target_size: int) -> List[str]:
        """
        サンプル数調整（共通処理）
        
        データが目標数より少ない場合は補完せず、そのまま返す。
        データ不足の情報はメタデータに記録される。
        """
        if len(samples) >= target_size:
            return random.sample(samples, target_size)
        elif len(samples) > 0:
            # データ不足の場合は補完せず、そのまま返す
            logger.warning(
                f"データ不足: 目標数={target_size}, 実際の数={len(samples)}. "
                f"補完せずに少ない数のまま実行します。"
            )
            return samples
        else:
            return samples
    
    def create_metadata(
        self, 
        dataset_id: str, 
        aspect: str, 
        options: SplitOptions,
        original_a_size: int,
        original_b_size: int,
        actual_a_size: Optional[int] = None,
        actual_b_size: Optional[int] = None,
        additional_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        メタデータ作成
        
        Args:
            actual_a_size: 調整後のグループAの実際のサイズ（Noneの場合はoriginal_a_sizeを使用）
            actual_b_size: 調整後のグループBの実際のサイズ（Noneの場合はoriginal_b_sizeを使用）
        """
        actual_a = actual_a_size if actual_a_size is not None else original_a_size
        actual_b = actual_b_size if actual_b_size is not None else original_b_size
        
        # データ不足フラグを判定
        insufficient_a = actual_a < options.group_size
        insufficient_b = actual_b < options.group_size
        
        metadata = {
            "dataset_id": dataset_id,
            "aspect": aspect,
            "split_type": self.split_type,
            "original_a_size": original_a_size,
            "original_b_size": original_b_size,
            "actual_a_size": actual_a,
            "actual_b_size": actual_b,
            "requested_group_size": options.group_size,
            "insufficient_data_a": insufficient_a,
            "insufficient_data_b": insufficient_b,
            "insufficient_data": insufficient_a or insufficient_b,
            "random_seed": options.random_seed,
            "timestamp": datetime.now().isoformat()
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        return metadata
    
    def validate_records(self, records: List[UnifiedRecord]) -> bool:
        """レコード検証"""
        if not records:
            return False
        
        # 基本的な検証
        for record in records[:10]:  # サンプル検証
            if not record.text or not record.aspect:
                return False
        
        return True
    
    def get_label_distribution(self, records: List[UnifiedRecord]) -> Dict[str, int]:
        """ラベル分布取得"""
        label_counts = {}
        for record in records:
            label = str(record.label)
            label_counts[label] = label_counts.get(label, 0) + 1
        return label_counts
    
    def filter_by_min_samples(
        self, 
        records: List[UnifiedRecord], 
        min_samples: int
    ) -> List[UnifiedRecord]:
        """最小サンプル数フィルタリング"""
        label_counts = self.get_label_distribution(records)
        valid_labels = {label for label, count in label_counts.items() if count >= min_samples}
        
        return [r for r in records if str(r.label) in valid_labels] 