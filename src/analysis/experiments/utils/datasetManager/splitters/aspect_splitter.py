"""
アスペクト含む vs 含まない分割戦略
"""

from typing import List
from .base import BaseSplitter, BinarySplitResult, SplitOptions
from ..loaders.base import UnifiedRecord


class AspectSplitter(BaseSplitter):
    """アスペクト含む vs 含まない分割戦略"""
    
    def __init__(self):
        super().__init__("aspect_vs_others")
    
    def split(
        self, 
        records: List[UnifiedRecord], 
        target_aspect: str,
        options: SplitOptions
    ) -> BinarySplitResult:
        """
        アスペクト含む vs 含まない分割実行
        
        Args:
            records: 分割対象レコード
            target_aspect: 対象アスペクト
            options: 分割オプション
            
        Returns:
            BinarySplitResult: 分割結果
        """
        if not self.validate_records(records):
            raise ValueError("無効なレコードです")
        
        # グループA: 対象アスペクト含む
        group_a_records = [
            r for r in records 
            if target_aspect.lower() in r.aspect.lower()
        ]
        
        # グループB: 対象アスペクト含まない  
        group_b_records = [
            r for r in records 
            if target_aspect.lower() not in r.aspect.lower()
        ]
        
        # 最小サンプル数フィルタリング
        if options.balance_labels:
            group_a_records = self.filter_by_min_samples(
                group_a_records, options.min_samples_per_label
            )
            group_b_records = self.filter_by_min_samples(
                group_b_records, options.min_samples_per_label
            )
        
        # 元のサイズを記録
        original_a_size = len(group_a_records)
        original_b_size = len(group_b_records)
        
        # サンプル調整
        group_a_texts = self.adjust_sample_size(
            [r.text for r in group_a_records], options.group_size
        )
        group_b_texts = self.adjust_sample_size(
            [r.text for r in group_b_records], options.group_size
        )
        
        # 正解作成
        correct_answer = f"{target_aspect} related characteristics"
        
        # メタデータ作成
        metadata = self.create_metadata(
            dataset_id=records[0].dataset_id if records else "unknown",
            aspect=target_aspect,
            options=options,
            original_a_size=original_a_size,
            original_b_size=original_b_size,
            actual_a_size=len(group_a_texts),
            actual_b_size=len(group_b_texts),
            additional_metadata={
                "group_a_label_distribution": self.get_label_distribution(group_a_records),
                "group_b_label_distribution": self.get_label_distribution(group_b_records)
            }
        )
        
        return BinarySplitResult(
            group_a=group_a_texts,
            group_b=group_b_texts,
            correct_answer=correct_answer,
            metadata=metadata
        )
    
    def get_aspect_similarity_score(self, aspect1: str, aspect2: str) -> float:
        """アスペクト類似度スコア計算"""
        aspect1_lower = aspect1.lower()
        aspect2_lower = aspect2.lower()
        
        # 完全一致
        if aspect1_lower == aspect2_lower:
            return 1.0
        
        # 部分一致
        if aspect1_lower in aspect2_lower or aspect2_lower in aspect1_lower:
            return 0.7
        
        # 単語レベル一致
        words1 = set(aspect1_lower.split())
        words2 = set(aspect2_lower.split())
        
        if words1 & words2:
            return 0.3
        
        return 0.0
    
    def get_related_aspects(
        self, 
        target_aspect: str, 
        all_aspects: List[str], 
        threshold: float = 0.3
    ) -> List[str]:
        """関連アスペクト取得"""
        related = []
        
        for aspect in all_aspects:
            if aspect != target_aspect:
                score = self.get_aspect_similarity_score(target_aspect, aspect)
                if score >= threshold:
                    related.append(aspect)
        
        return related 