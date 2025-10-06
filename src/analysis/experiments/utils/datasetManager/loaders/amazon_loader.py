"""
Amazon Review Dataset専用ローダー
"""

from pathlib import Path
from typing import Dict, List
from .base import BaseDatasetLoader, UnifiedRecord
from ..configs.dataset_configs import DatasetConfig


class AmazonDatasetLoader(BaseDatasetLoader):
    """Amazon Review Dataset専用ローダー"""
    
    def __init__(self, base_path: str = None, config: DatasetConfig = None):
        """
        初期化
        
        Args:
            base_path: データセットパス（Noneの場合は設定ファイルから取得）
            config: 設定オブジェクト
        """
        if base_path is None and config is not None:
            dataset_info = config.get_dataset_info("amazon")
            base_path = dataset_info.path
        elif base_path is None:
            base_path = "/Users/seinoshun/imrb_research/data/external/amazon-product-reviews/kaggle-bittlingmayer/current"
        
        super().__init__(base_path, "amazon")
        self.config = config
        self.aspects = ['quality', 'price', 'delivery', 'service', 'product']
    
    def load_raw_data(self) -> List[UnifiedRecord]:
        """Amazonデータを統一フォーマットで読み込み"""
        if not self.validate_data_path():
            raise FileNotFoundError(f"データパスが無効です: {self.base_path}")
        
        records = []
        
        # FastText形式ファイルを処理
        for filename in ['train.ft.txt', 'test.ft.txt']:
            file_path = self.base_path / filename
            if file_path.exists():
                try:
                    file_records = self._load_fasttext_file(file_path, filename)
                    records.extend(file_records)
                except Exception as e:
                    print(f"Amazon データ読み込みエラー ({filename}): {e}")
        
        return records
    
    def _load_fasttext_file(self, file_path: Path, source_file: str) -> List[UnifiedRecord]:
        """FastText形式ファイルを読み込み"""
        records = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # FastText形式: __label__1 review text
                    parts = line.split(' ', 1)
                    if len(parts) != 2:
                        continue
                    
                    label_part = parts[0]
                    text = parts[1]
                    
                    # ラベル抽出
                    if label_part.startswith('__label__'):
                        label = int(label_part.replace('__label__', ''))
                    else:
                        continue
                    
                    # 仮想的にproductアスペクトとして処理
                    records.append(UnifiedRecord(
                        text=text,
                        aspect='product',
                        label=label,
                        domain="e-commerce",
                        dataset_id="amazon",
                        metadata={
                            "source_file": source_file,
                            "line_number": line_num
                        }
                    ))
                
                except (ValueError, IndexError) as e:
                    print(f"行解析エラー ({source_file}:{line_num}): {e}")
                    continue
        
        return records
    
    def get_available_aspects(self) -> List[str]:
        """利用可能なアスペクト一覧"""
        return self.aspects.copy()
    
    def get_domain_info(self) -> Dict:
        """ドメイン情報取得"""
        return {
            "domain": "e-commerce",
            "dataset": "amazon",
            "language": "en",
            "aspects": self.aspects,
            "data_path": str(self.base_path) if self.base_path else None
        }
    
    def get_label_distribution(self) -> Dict:
        """ラベル分布取得"""
        records = self.load_with_cache()
        label_counts = {}
        
        for record in records:
            label = str(record.label)
            label_counts[label] = label_counts.get(label, 0) + 1
        
        return {
            "total_records": len(records),
            "label_distribution": label_counts
        }
    
    def get_text_length_stats(self) -> Dict:
        """テキスト長統計情報取得"""
        records = self.load_with_cache()
        
        if not records:
            return {"error": "データなし"}
        
        text_lengths = [len(record.text.split()) for record in records]
        
        return {
            "total_records": len(records),
            "avg_length": sum(text_lengths) / len(text_lengths),
            "min_length": min(text_lengths),
            "max_length": max(text_lengths),
            "median_length": sorted(text_lengths)[len(text_lengths) // 2]
        } 