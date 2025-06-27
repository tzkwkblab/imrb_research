#!/usr/bin/env python3
"""
PyABSA統合データセット読み込みフレームワーク

PyABSA統合データセットを読み込み、対比因子実験用のデータを準備する
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ABSARecord:
    """ABSA レコード"""
    text: str
    aspect: str
    sentiment: str
    domain: str = ""
    dataset_id: str = ""


@dataclass
class DatasetInfo:
    """データセット情報"""
    dataset_id: str
    name: str
    path: Path
    record_count: int
    domains: List[str]
    aspects: List[str]
    sentiments: List[str]


class PyABSADatasetLoader:
    """PyABSA統合データセットローダー"""
    
    def __init__(self, base_path: str = None):
        """
        初期化
        
        Args:
            base_path: データセットのベースパス（デフォルト: current symlink）
        """
        if base_path is None:
            # 絶対パスで指定
            base_path = "/Users/seinoshun/imrb_research/data/external/absa-review-dataset/pyabsa-integrated/current"
        
        self.base_path = Path(base_path)
        self.absa_datasets_path = self.base_path / "ABSADatasets"
        self.apc_datasets_path = self.absa_datasets_path / "datasets" / "apc_datasets"
        
        # データセット情報読み込み
        self.dataset_info = self._load_dataset_info()
        
        logger.info(f"PyABSAデータセットローダー初期化完了: {self.base_path}")
        logger.info(f"APCデータセットパス: {self.apc_datasets_path}")
        logger.info(f"パス存在確認: {self.apc_datasets_path.exists()}")
    
    def _load_dataset_info(self) -> Dict:
        """データセット情報を読み込み"""
        info_path = self.base_path / "dataset_info.json"
        if info_path.exists():
            with open(info_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def list_available_datasets(self) -> List[DatasetInfo]:
        """利用可能なデータセット一覧を取得"""
        datasets = []
        
        if not self.apc_datasets_path.exists():
            logger.warning(f"APCデータセットパスが存在しません: {self.apc_datasets_path}")
            return datasets
        
        for dataset_dir in self.apc_datasets_path.iterdir():
            if not dataset_dir.is_dir():
                continue
            
            # データセットID抽出（例: "110.SemEval" -> "110", "SemEval"）
            dir_name = dataset_dir.name
            if '.' in dir_name:
                dataset_id, name = dir_name.split('.', 1)
            else:
                dataset_id, name = dir_name, dir_name
            
            # サブディレクトリをチェック
            subdirs = [d for d in dataset_dir.iterdir() if d.is_dir()]
            if subdirs:
                # サブディレクトリがある場合（例: SemEval）
                for subdir in subdirs:
                    sub_info = self._analyze_dataset_directory(subdir)
                    if sub_info:
                        datasets.append(DatasetInfo(
                            dataset_id=f"{dataset_id}.{subdir.name}",
                            name=f"{name}_{subdir.name}",
                            path=subdir,
                            **sub_info
                        ))
            else:
                # 直接ファイルがある場合
                info = self._analyze_dataset_directory(dataset_dir)
                if info:
                    datasets.append(DatasetInfo(
                        dataset_id=dataset_id,
                        name=name,
                        path=dataset_dir,
                        **info
                    ))
        
        return sorted(datasets, key=lambda x: x.dataset_id)
    
    def _analyze_dataset_directory(self, dataset_path: Path) -> Optional[Dict]:
        """データセットディレクトリを分析"""
        # .apc, .xml.seg, .dat.apc ファイルを検索
        data_files = []
        for ext in ['*.apc', '*.xml.seg', '*.dat.apc']:
            data_files.extend(dataset_path.glob(ext))
        
        if not data_files:
            return None
        
        # 最初のファイルでサンプル分析
        sample_file = data_files[0]
        try:
            records = self._load_dataset_file(sample_file)
            if not records:
                return None
            
            # 統計情報計算
            aspects = list(set(r.aspect for r in records))
            sentiments = list(set(r.sentiment for r in records))
            domains = list(set(r.domain for r in records if r.domain))
            
            return {
                'record_count': len(records),
                'domains': domains or ['unknown'],
                'aspects': aspects,
                'sentiments': sentiments
            }
        except Exception as e:
            logger.warning(f"データセット分析エラー {sample_file}: {e}")
            return None
    
    def load_dataset(self, dataset_id: str) -> List[ABSARecord]:
        """指定されたデータセットを読み込み"""
        datasets = self.list_available_datasets()
        target_dataset = None
        
        for dataset in datasets:
            if dataset.dataset_id == dataset_id or dataset.name == dataset_id:
                target_dataset = dataset
                break
        
        if not target_dataset:
            raise ValueError(f"データセットが見つかりません: {dataset_id}")
        
        logger.info(f"データセット読み込み開始: {target_dataset.name}")
        
        # データファイルを検索
        data_files = []
        for ext in ['*.apc', '*.xml.seg', '*.dat.apc']:
            data_files.extend(target_dataset.path.glob(ext))
        
        all_records = []
        for file_path in data_files:
            try:
                records = self._load_dataset_file(file_path)
                for record in records:
                    record.dataset_id = dataset_id
                    record.domain = target_dataset.name
                all_records.extend(records)
            except Exception as e:
                logger.warning(f"ファイル読み込みエラー {file_path}: {e}")
        
        logger.info(f"読み込み完了: {len(all_records)}件")
        return all_records
    
    def _load_dataset_file(self, file_path: Path) -> List[ABSARecord]:
        """データファイルを読み込み"""
        records = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 3行セットで処理（text, aspect, sentiment）
            for i in range(0, len(lines), 3):
                if i + 2 >= len(lines):
                    break
                
                text = lines[i].strip()
                aspect = lines[i + 1].strip()
                sentiment = lines[i + 2].strip()
                
                if text and aspect and sentiment:
                    records.append(ABSARecord(
                        text=text,
                        aspect=aspect,
                        sentiment=sentiment
                    ))
        
        except Exception as e:
            logger.error(f"ファイル読み込みエラー {file_path}: {e}")
        
        return records
    
    def create_dataframe(self, records: List[ABSARecord]) -> pd.DataFrame:
        """ABSAレコードをDataFrameに変換"""
        data = []
        for record in records:
            data.append({
                'text': record.text,
                'aspect': record.aspect,
                'sentiment': record.sentiment,
                'domain': record.domain,
                'dataset_id': record.dataset_id
            })
        
        return pd.DataFrame(data)
    
    def get_dataset_statistics(self, records: List[ABSARecord]) -> Dict:
        """データセット統計情報を取得"""
        df = self.create_dataframe(records)
        
        stats = {
            'total_records': len(df),
            'unique_aspects': df['aspect'].nunique(),
            'unique_domains': df['domain'].nunique(),
            'sentiment_distribution': df['sentiment'].value_counts().to_dict(),
            'aspect_distribution': df['aspect'].value_counts().head(10).to_dict(),
            'domain_distribution': df['domain'].value_counts().to_dict(),
            'text_length_stats': {
                'mean': df['text'].str.len().mean(),
                'median': df['text'].str.len().median(),
                'min': df['text'].str.len().min(),
                'max': df['text'].str.len().max()
            }
        }
        
        return stats


def main():
    """テスト実行"""
    loader = PyABSADatasetLoader()
    
    print("=== 利用可能データセット一覧 ===")
    datasets = loader.list_available_datasets()
    
    for dataset in datasets[:10]:  # 最初の10個表示
        print(f"ID: {dataset.dataset_id}")
        print(f"名前: {dataset.name}")
        print(f"レコード数: {dataset.record_count}")
        print(f"アスペクト数: {len(dataset.aspects)}")
        print(f"感情: {dataset.sentiments}")
        print(f"パス: {dataset.path}")
        print("-" * 50)
    
    if datasets:
        # 最初のデータセットを詳細テスト
        test_dataset = datasets[0]
        print(f"\n=== {test_dataset.name} 詳細テスト ===")
        
        try:
            records = loader.load_dataset(test_dataset.dataset_id)
            stats = loader.get_dataset_statistics(records)
            
            print(f"総レコード数: {stats['total_records']}")
            print(f"ユニークアスペクト数: {stats['unique_aspects']}")
            print(f"感情分布: {stats['sentiment_distribution']}")
            print(f"テキスト長統計: {stats['text_length_stats']}")
            
            # サンプルレコード表示
            print("\n=== サンプルレコード ===")
            for i, record in enumerate(records[:5]):
                print(f"{i+1}. テキスト: {record.text[:100]}...")
                print(f"   アスペクト: {record.aspect}")
                print(f"   感情: {record.sentiment}")
                print()
        
        except Exception as e:
            print(f"エラー: {e}")


if __name__ == "__main__":
    main()
