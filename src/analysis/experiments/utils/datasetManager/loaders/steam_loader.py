"""
Steam Review Dataset専用ローダー
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List
from .base import BaseDatasetLoader, UnifiedRecord
from ..config import DatasetConfig


class SteamDatasetLoader(BaseDatasetLoader):
    """Steam Review Dataset専用ローダー"""
    
    def __init__(self, base_path: str = None, config: DatasetConfig = None):
        """
        初期化
        
        Args:
            base_path: データセットパス（Noneの場合は設定ファイルから取得）
            config: 設定オブジェクト
        """
        if base_path is None and config is not None:
            dataset_info = config.get_dataset_info("steam")
            base_path = dataset_info.path
        elif base_path is None:
            base_path = "/Users/seinoshun/imrb_research/data/external/steam-review-aspect-dataset/current"
        
        super().__init__(base_path, "steam")
        self.config = config
        self.aspects = [
            'recommended', 'story', 'gameplay', 'visual', 
            'audio', 'technical', 'price', 'suggestion'
        ]
    
    def load_raw_data(self) -> List[UnifiedRecord]:
        """Steamデータを統一フォーマットで読み込み"""
        if not self.validate_data_path():
            raise FileNotFoundError(f"データパスが無効です: {self.base_path}")
        
        train_path = self.base_path / "train.csv"
        test_path = self.base_path / "test.csv"
        
        records = []
        
        for path in [train_path, test_path]:
            if path.exists():
                try:
                    df = pd.read_csv(path)
                    path_records = self._convert_dataframe_to_records(df, path.name)
                    records.extend(path_records)
                except Exception as e:
                    print(f"Steam データ読み込みエラー ({path.name}): {e}")
        
        return records
    
    def _convert_dataframe_to_records(self, df: pd.DataFrame, source_file: str) -> List[UnifiedRecord]:
        """DataFrameを統一レコード形式に変換"""
        records = []
        
        for _, row in df.iterrows():
            review_text = str(row.get('review', ''))
            if not review_text or review_text == 'nan':
                continue
            
            for aspect in self.aspects:
                aspect_col = f'label_{aspect}'
                if aspect_col in df.columns:
                    label_value = row[aspect_col]
                    
                    # NaN値のスキップ
                    if pd.isna(label_value):
                        continue
                    
                    records.append(UnifiedRecord(
                        text=review_text,
                        aspect=aspect,
                        label=int(label_value),
                        domain="gaming",
                        dataset_id="steam",
                        metadata={
                            "source_file": source_file,
                            "original_index": row.name if hasattr(row, 'name') else None
                        }
                    ))
        
        return records
    
    def get_available_aspects(self) -> List[str]:
        """利用可能なアスペクト一覧"""
        return self.aspects.copy()
    
    def get_domain_info(self) -> Dict:
        """ドメイン情報取得"""
        return {
            "domain": "gaming",
            "dataset": "steam",
            "language": "en",
            "aspects": self.aspects,
            "data_path": str(self.base_path) if self.base_path else None
        }
    
    def get_aspect_distribution(self) -> Dict[str, Dict]:
        """アスペクト別ラベル分布取得"""
        records = self.load_with_cache()
        distribution = {}
        
        for aspect in self.aspects:
            aspect_records = [r for r in records if r.aspect == aspect]
            label_counts = {}
            
            for record in aspect_records:
                label = str(record.label)
                label_counts[label] = label_counts.get(label, 0) + 1
            
            distribution[aspect] = {
                "total": len(aspect_records),
                "labels": label_counts
            }
        
        return distribution 