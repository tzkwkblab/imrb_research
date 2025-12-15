"""
バイナリラベルによる分割戦略（Steam用）
"""

from typing import List, Union
from .base import BaseSplitter, BinarySplitResult, SplitOptions
from ..loaders.base import UnifiedRecord


class BinarySplitter(BaseSplitter):
    """バイナリラベルによる分割戦略"""
    
    def __init__(self):
        super().__init__("binary_label")
    
    def split(
        self, 
        records: List[UnifiedRecord], 
        target_aspect: str,
        options: SplitOptions
    ) -> BinarySplitResult:
        """
        バイナリラベルによる分割実行
        
        Args:
            records: 分割対象レコード
            target_aspect: 対象アスペクト
            options: 分割オプション
            
        Returns:
            BinarySplitResult: 分割結果
        """
        if not self.validate_records(records):
            raise ValueError("無効なレコードです")
        
        # 対象アスペクトでフィルタ
        aspect_records = [r for r in records if r.aspect == target_aspect]
        
        if not aspect_records:
            raise ValueError(f"アスペクト '{target_aspect}' のレコードが見つかりません")
        
        # ラベル1（ポジティブ）とラベル0（ネガティブ）で分割
        positive_records = [r for r in aspect_records if self._is_positive_label(r.label)]
        negative_records = [r for r in aspect_records if self._is_negative_label(r.label)]
        
        # 最小サンプル数チェック
        if len(positive_records) < options.min_samples_per_label:
            raise ValueError(f"ポジティブサンプルが不足: {len(positive_records)} < {options.min_samples_per_label}")
        
        if len(negative_records) < options.min_samples_per_label:
            raise ValueError(f"ネガティブサンプルが不足: {len(negative_records)} < {options.min_samples_per_label}")
        
        # 元のサイズを記録
        original_a_size = len(positive_records)
        original_b_size = len(negative_records)
        
        # サンプル調整
        group_a_texts = self.adjust_sample_size(
            [r.text for r in positive_records], options.group_size
        )
        group_b_texts = self.adjust_sample_size(
            [r.text for r in negative_records], options.group_size
        )
        
        # 正解作成
        correct_answer = f"{target_aspect} positive vs negative characteristics"
        
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
                "positive_label_count": len(positive_records),
                "negative_label_count": len(negative_records),
                "total_aspect_records": len(aspect_records),
                "label_mapping": self._get_label_mapping()
            }
        )
        
        return BinarySplitResult(
            group_a=group_a_texts,
            group_b=group_b_texts,
            correct_answer=correct_answer,
            metadata=metadata
        )
    
    def _is_positive_label(self, label: Union[str, int, float]) -> bool:
        """ポジティブラベル判定"""
        if isinstance(label, (int, float)):
            return label == 1
        elif isinstance(label, str):
            positive_strings = ['1', '1.0', 'positive', 'pos', 'good', 'true']
            return label.lower() in positive_strings
        return False
    
    def _is_negative_label(self, label: Union[str, int, float]) -> bool:
        """ネガティブラベル判定"""
        if isinstance(label, (int, float)):
            return label == 0
        elif isinstance(label, str):
            negative_strings = ['0', '0.0', 'negative', 'neg', 'bad', 'false']
            return label.lower() in negative_strings
        return False
    
    def _get_label_mapping(self) -> dict:
        """ラベルマッピング取得"""
        return {
            "positive": ["1", 1, 1.0, "positive", "pos", "good", "true"],
            "negative": ["0", 0, 0.0, "negative", "neg", "bad", "false"]
        }
    
    def get_label_balance_info(self, records: List[UnifiedRecord], aspect: str) -> dict:
        """ラベルバランス情報取得"""
        aspect_records = [r for r in records if r.aspect == aspect]
        
        positive_count = len([r for r in aspect_records if self._is_positive_label(r.label)])
        negative_count = len([r for r in aspect_records if self._is_negative_label(r.label)])
        other_count = len(aspect_records) - positive_count - negative_count
        
        total = len(aspect_records)
        
        return {
            "total_records": total,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "other_count": other_count,
            "positive_ratio": positive_count / total if total > 0 else 0,
            "negative_ratio": negative_count / total if total > 0 else 0,
            "is_balanced": abs(positive_count - negative_count) / total < 0.3 if total > 0 else False
        }
    
    def suggest_group_size(self, records: List[UnifiedRecord], aspect: str) -> int:
        """推奨グループサイズ算出"""
        balance_info = self.get_label_balance_info(records, aspect)
        
        min_label_count = min(balance_info["positive_count"], balance_info["negative_count"])
        
        # 利用可能な最小ラベル数の80%を推奨
        suggested_size = int(min_label_count * 0.8)
        
        # 最小値と最大値の制限
        return max(10, min(suggested_size, 500)) 