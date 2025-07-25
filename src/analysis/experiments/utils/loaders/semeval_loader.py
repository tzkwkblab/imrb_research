"""
SemEval ABSA Dataset専用ローダー
"""

import sys
from pathlib import Path
from typing import Dict, List
from .base import BaseDatasetLoader, UnifiedRecord
from ..config import DatasetConfig


class SemEvalDatasetLoader(BaseDatasetLoader):
    """SemEval ABSA Dataset専用ローダー（PyABSA統合データ使用）"""
    
    def __init__(self, base_path: str = None, config: DatasetConfig = None):
        """
        初期化
        
        Args:
            base_path: データセットパス（Noneの場合は設定ファイルから取得）
            config: 設定オブジェクト
        """
        if base_path is None and config is not None:
            dataset_info = config.get_dataset_info("semeval")
            base_path = dataset_info.path
        elif base_path is None:
            base_path = "/Users/seinoshun/imrb_research/data/external/absa-review-dataset"
        
        super().__init__(base_path, "semeval")
        self.config = config
        self.domain_aspects = {
            'restaurant': ['food', 'service', 'atmosphere', 'price'],
            'laptop': ['battery', 'screen', 'keyboard', 'performance']
        }
    
    def load_raw_data(self) -> List[UnifiedRecord]:
        """SemEvalデータを統一フォーマットで読み込み"""
        records = []
        
        try:
            # PyABSADatasetLoaderの動的インポート
            current_dir = Path(__file__).parent.parent.parent / "2025/06/27"
            sys.path.append(str(current_dir))
            from dataset_comparison_framework import PyABSADatasetLoader
            
            loader = PyABSADatasetLoader()
            datasets = loader.list_available_datasets()
            
            for dataset in datasets:
                if self._is_target_dataset(dataset.dataset_id):
                    try:
                        raw_records = loader.load_dataset(dataset.dataset_id)
                        domain = self._extract_domain(dataset.dataset_id)
                        
                        dataset_records = self._convert_raw_records(
                            raw_records, dataset.dataset_id, domain
                        )
                        records.extend(dataset_records)
                        
                    except Exception as e:
                        print(f"SemEval データ読み込みエラー ({dataset.dataset_id}): {e}")
        
        except ImportError as e:
            print(f"PyABSADatasetLoader インポートエラー: {e}")
        except Exception as e:
            print(f"SemEval データ読み込みエラー: {e}")
        
        return records
    
    def _is_target_dataset(self, dataset_id: str) -> bool:
        """対象データセット判定"""
        return 'restaurant14' in dataset_id or 'laptop14' in dataset_id
    
    def _extract_domain(self, dataset_id: str) -> str:
        """データセットIDからドメイン抽出"""
        if 'restaurant' in dataset_id:
            return 'restaurant'
        elif 'laptop' in dataset_id:
            return 'laptop'
        else:
            return 'unknown'
    
    def _convert_raw_records(self, raw_records, dataset_id: str, domain: str) -> List[UnifiedRecord]:
        """生レコードを統一フォーマットに変換"""
        records = []
        
        for record in raw_records:
            try:
                records.append(UnifiedRecord(
                    text=record.text,
                    aspect=record.aspect,
                    label=record.sentiment,
                    domain=domain,
                    dataset_id=dataset_id,
                    metadata={
                        "original_domain": getattr(record, 'domain', ''),
                        "source_dataset": dataset_id
                    }
                ))
            except AttributeError as e:
                print(f"レコード変換エラー: {e}")
                continue
        
        return records
    
    def get_available_aspects(self) -> List[str]:
        """利用可能なアスペクト一覧"""
        all_aspects = []
        for aspects in self.domain_aspects.values():
            all_aspects.extend(aspects)
        return list(set(all_aspects))
    
    def get_domain_info(self) -> Dict:
        """ドメイン情報取得"""
        return {
            "domains": self.domain_aspects,
            "dataset": "semeval_absa",
            "language": "en",
            "data_path": str(self.base_path) if self.base_path else None
        }
    
    def get_domain_aspects(self, domain: str) -> List[str]:
        """ドメイン別アスペクト取得"""
        return self.domain_aspects.get(domain, [])
    
    def filter_by_domain(self, domain: str) -> List[UnifiedRecord]:
        """ドメイン別フィルタリング"""
        records = self.load_with_cache()
        return [r for r in records if r.domain == domain]
    
    def get_domain_statistics(self) -> Dict[str, Dict]:
        """ドメイン別統計情報取得"""
        records = self.load_with_cache()
        stats = {}
        
        for domain in self.domain_aspects.keys():
            domain_records = [r for r in records if r.domain == domain]
            
            aspect_counts = {}
            sentiment_counts = {}
            
            for record in domain_records:
                aspect_counts[record.aspect] = aspect_counts.get(record.aspect, 0) + 1
                sentiment_counts[str(record.label)] = sentiment_counts.get(str(record.label), 0) + 1
            
            stats[domain] = {
                "total_records": len(domain_records),
                "aspects": aspect_counts,
                "sentiments": sentiment_counts
            }
        
        return stats 