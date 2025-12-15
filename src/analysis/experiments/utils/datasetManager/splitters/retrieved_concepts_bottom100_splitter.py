"""
Retrieved Concepts用: Top-100 vs Bottom-100分割戦略
"""

from typing import List, Dict, Set
from .base import BaseSplitter, BinarySplitResult, SplitOptions
from ..loaders.base import UnifiedRecord
import sys
from pathlib import Path

# URL変換ユーティリティをインポート
utils_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(utils_dir))
from coco_image_url_converter import convert_coco_path_to_url


class RetrievedConceptsBottom100Splitter(BaseSplitter):
    """Top-100 vs Bottom-100分割戦略（retrieved_concepts専用）"""
    
    def __init__(self):
        super().__init__("aspect_vs_bottom100")
    
    def split(
        self, 
        records: List[UnifiedRecord], 
        target_aspect: str,
        options: SplitOptions
    ) -> BinarySplitResult:
        """
        Top-100 vs Bottom-100分割実行
        
        Args:
            records: 分割対象レコード
            target_aspect: 対象アスペクト
            options: 分割オプション
            
        Returns:
            BinarySplitResult: 分割結果
        """
        if not self.validate_records(records):
            raise ValueError("無効なレコードです")
        
        # グループA: 対象アスペクトのTop-100（source_type="top100"）
        group_a_records = [
            r for r in records 
            if target_aspect.lower() == r.aspect.lower() 
            and r.metadata.get("source_type") == "top100"
        ]
        
        # グループB: 対象アスペクトのBottom-100（source_type="bottom100"）
        group_b_records = [
            r for r in records 
            if target_aspect.lower() == r.aspect.lower() 
            and r.metadata.get("source_type") == "bottom100"
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
        
        # Top-5/Bottom-5の画像URLを取得
        group_a_top5_urls = self._get_top5_image_urls(group_a_records)
        group_b_top5_urls = self._get_top5_image_urls(group_b_records)
        
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
                "group_a_source": "top100",
                "group_b_source": "bottom100",
                "group_a_label_distribution": self.get_label_distribution(group_a_records),
                "group_b_label_distribution": self.get_label_distribution(group_b_records),
                "group_a_top5_image_urls": group_a_top5_urls,
                "group_b_top5_image_urls": group_b_top5_urls
            }
        )
        
        return BinarySplitResult(
            group_a=group_a_texts,
            group_b=group_b_texts,
            correct_answer=correct_answer,
            metadata=metadata
        )
    
    def _get_top5_image_urls(self, records: List[UnifiedRecord]) -> List[str]:
        """
        レコードからrank順でTop-5の画像URLを取得
        
        Args:
            records: UnifiedRecordのリスト
        
        Returns:
            Top-5の画像URLリスト
        """
        # 画像パスとrankのペアを作成（重複を除去）
        image_rank_map: Dict[str, int] = {}
        for record in records:
            image_path = record.metadata.get("image_path", "")
            rank = record.metadata.get("rank")
            if image_path and rank is not None:
                # 既に存在する場合は、より小さいrank（上位）を優先
                if image_path not in image_rank_map or rank < image_rank_map[image_path]:
                    image_rank_map[image_path] = rank
        
        # rank順でソートしてTop-5を取得
        sorted_images = sorted(image_rank_map.items(), key=lambda x: x[1])[:5]
        
        # URLに変換
        urls = [convert_coco_path_to_url(image_path) for image_path, _ in sorted_images]
        
        # 空のURLを除外
        return [url for url in urls if url]

