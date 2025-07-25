#!/usr/bin/env python3
"""
データセット統一管理ツール

全データセットを統一インターフェースで操作可能にする
使用例: manager.get_binary_splits("steam", aspect="gameplay", group_size=300)
"""

import os
import json
import pandas as pd
import numpy as np
import random
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime

@dataclass
class UnifiedRecord:
    """統一レコード形式"""
    text: str
    aspect: str
    label: Union[str, int, float]  # センチメント/分類ラベル
    domain: str = ""
    dataset_id: str = ""
    metadata: Dict = None

@dataclass
class BinarySplitResult:
    """二項分割結果"""
    group_a: List[str]
    group_b: List[str]
    correct_answer: str
    metadata: Dict

class BaseDatasetLoader(ABC):
    """データセットローダーの基底クラス"""
    
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

class SteamDatasetLoader(BaseDatasetLoader):
    """Steam Review Dataset専用ローダー"""
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = "/Users/seinoshun/imrb_research/data/external/steam-review-aspect-dataset/current"
        self.base_path = Path(base_path)
        self.aspects = ['recommended', 'story', 'gameplay', 'visual', 'audio', 'technical', 'price', 'suggestion']
    
    def load_raw_data(self) -> List[UnifiedRecord]:
        """Steamデータを統一フォーマットで読み込み"""
        train_path = self.base_path / "train.csv"
        test_path = self.base_path / "test.csv"
        
        records = []
        for path in [train_path, test_path]:
            if path.exists():
                df = pd.read_csv(path)
                for _, row in df.iterrows():
                    for aspect in self.aspects:
                        aspect_col = f'label_{aspect}'
                        if aspect_col in df.columns:
                            records.append(UnifiedRecord(
                                text=row['review'],
                                aspect=aspect,
                                label=row[aspect_col],
                                domain="gaming",
                                dataset_id="steam",
                                metadata={"source_file": path.name}
                            ))
        return records
    
    def get_available_aspects(self) -> List[str]:
        return self.aspects
    
    def get_domain_info(self) -> Dict:
        return {"domain": "gaming", "dataset": "steam", "language": "en"}

class SemEvalDatasetLoader(BaseDatasetLoader):
    """SemEval ABSA Dataset専用ローダー（PyABSA統合データ使用）"""
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            # PyABSAの実際のパスに調整
            base_path = "/Users/seinoshun/imrb_research/data/external/absa-review-dataset"
        self.base_path = Path(base_path)
        self.domain_aspects = {
            'restaurant': ['food', 'service', 'atmosphere', 'price'],
            'laptop': ['battery', 'screen', 'keyboard', 'performance']
        }
    
    def load_raw_data(self) -> List[UnifiedRecord]:
        """SemEvalデータを統一フォーマットで読み込み"""
        # PyABSADatasetLoaderの動的インポート
        try:
            import sys
            current_dir = Path(__file__).parent.parent / "2025/06/27"
            sys.path.append(str(current_dir))
            from dataset_comparison_framework import PyABSADatasetLoader
            
            loader = PyABSADatasetLoader()
            datasets = loader.list_available_datasets()
            
            records = []
            for dataset in datasets:
                if 'restaurant14' in dataset.dataset_id or 'laptop14' in dataset.dataset_id:
                    raw_records = loader.load_dataset(dataset.dataset_id)
                    domain = 'restaurant' if 'restaurant' in dataset.dataset_id else 'laptop'
                    
                    for record in raw_records:
                        records.append(UnifiedRecord(
                            text=record.text,
                            aspect=record.aspect,
                            label=record.sentiment,
                            domain=domain,
                            dataset_id=dataset.dataset_id,
                            metadata={"original_domain": getattr(record, 'domain', '')}
                        ))
            return records
        except Exception as e:
            print(f"SemEvalデータ読み込みエラー: {e}")
            return []
    
    def get_available_aspects(self) -> List[str]:
        all_aspects = []
        for aspects in self.domain_aspects.values():
            all_aspects.extend(aspects)
        return list(set(all_aspects))
    
    def get_domain_info(self) -> Dict:
        return {"domains": self.domain_aspects, "dataset": "semeval_absa", "language": "en"}

class AmazonDatasetLoader(BaseDatasetLoader):
    """Amazon Review Dataset専用ローダー"""
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = "/Users/seinoshun/imrb_research/data/external/amazon-product-reviews/kaggle-bittlingmayer/current"
        self.base_path = Path(base_path)
        self.aspects = ['quality', 'price', 'delivery', 'service', 'product']
    
    def load_raw_data(self) -> List[UnifiedRecord]:
        """Amazonデータを統一フォーマットで読み込み"""
        # 実際のファイル構造に応じて実装
        records = []
        try:
            # train.ft.txt, test.ft.txtファイルを想定
            for filename in ['train.ft.txt', 'test.ft.txt']:
                file_path = self.base_path / filename
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                # Amazon fast text形式: __label__1 review text
                                parts = line.strip().split(' ', 1)
                                if len(parts) == 2:
                                    label = int(parts[0].replace('__label__', ''))
                                    text = parts[1]
                                    
                                    # 仮想的にproductアスペクトとして処理
                                    records.append(UnifiedRecord(
                                        text=text,
                                        aspect='product',
                                        label=label,
                                        domain="e-commerce",
                                        dataset_id="amazon",
                                        metadata={"source_file": filename}
                                    ))
        except Exception as e:
            print(f"Amazonデータ読み込みエラー: {e}")
        
        return records
    
    def get_available_aspects(self) -> List[str]:
        return self.aspects
    
    def get_domain_info(self) -> Dict:
        return {"domain": "e-commerce", "dataset": "amazon", "language": "en"}

class DatasetManager:
    """データセット統一管理クラス"""
    
    def __init__(self, random_seed: int = 42):
        """
        初期化
        Args:
            random_seed: ランダムシード値
        """
        self.random_seed = random_seed
        random.seed(random_seed)
        np.random.seed(random_seed)
        
        # データセットローダー登録
        self.loaders = {
            "steam": SteamDatasetLoader,
            "semeval": SemEvalDatasetLoader,
            "amazon": AmazonDatasetLoader
        }
        
        self._cache = {}  # データキャッシュ
    
    def list_available_datasets(self) -> Dict[str, Dict]:
        """利用可能なデータセット情報を取得"""
        datasets_info = {}
        
        for dataset_id, loader_class in self.loaders.items():
            try:
                loader = loader_class()
                info = loader.get_domain_info()
                info['aspects'] = loader.get_available_aspects()
                datasets_info[dataset_id] = info
            except Exception as e:
                datasets_info[dataset_id] = {"error": str(e)}
        
        return datasets_info
    
    def get_dataset_records(self, dataset_id: str, use_cache: bool = True) -> List[UnifiedRecord]:
        """データセットのレコードを取得"""
        if use_cache and dataset_id in self._cache:
            return self._cache[dataset_id]
        
        if dataset_id not in self.loaders:
            raise ValueError(f"未対応のデータセット: {dataset_id}")
        
        loader = self.loaders[dataset_id]()
        records = loader.load_raw_data()
        
        if use_cache:
            self._cache[dataset_id] = records
        
        return records
    
    def get_binary_splits(
        self,
        dataset_id: str,
        aspect: str,
        group_size: int = 300,
        split_type: str = "aspect_vs_others"
    ) -> BinarySplitResult:
        """
        二項分割データを取得（メイン機能）
        
        Args:
            dataset_id: データセット名 ("steam", "semeval", "amazon")
            aspect: 対象アスペクト
            group_size: 各グループのサンプル数
            split_type: 分割タイプ ("aspect_vs_others", "binary_label")
        
        Returns:
            BinarySplitResult: 二項分割結果
        """
        records = self.get_dataset_records(dataset_id)
        
        if split_type == "aspect_vs_others":
            return self._create_aspect_vs_others_split(records, aspect, group_size, dataset_id)
        elif split_type == "binary_label":
            return self._create_binary_label_split(records, aspect, group_size, dataset_id)
        else:
            raise ValueError(f"未対応の分割タイプ: {split_type}")
    
    def _create_aspect_vs_others_split(
        self, 
        records: List[UnifiedRecord], 
        target_aspect: str, 
        group_size: int,
        dataset_id: str
    ) -> BinarySplitResult:
        """アスペクト含む vs 含まない分割"""
        
        # グループA: 対象アスペクト含む
        group_a_records = [r for r in records if target_aspect.lower() in r.aspect.lower()]
        
        # グループB: 対象アスペクト含まない
        group_b_records = [r for r in records if target_aspect.lower() not in r.aspect.lower()]
        
        # サンプル調整
        group_a_texts = self._adjust_sample_size([r.text for r in group_a_records], group_size)
        group_b_texts = self._adjust_sample_size([r.text for r in group_b_records], group_size)
        
        # 正解作成
        correct_answer = f"{target_aspect} related characteristics"
        
        return BinarySplitResult(
            group_a=group_a_texts,
            group_b=group_b_texts,
            correct_answer=correct_answer,
            metadata={
                "dataset_id": dataset_id,
                "aspect": target_aspect,
                "split_type": "aspect_vs_others",
                "group_a_size": len(group_a_texts),
                "group_b_size": len(group_b_texts),
                "original_a_size": len(group_a_records),
                "original_b_size": len(group_b_records),
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def _create_binary_label_split(
        self, 
        records: List[UnifiedRecord], 
        target_aspect: str, 
        group_size: int,
        dataset_id: str
    ) -> BinarySplitResult:
        """バイナリラベルによる分割（Steam用）"""
        
        # 対象アスペクトでフィルタ
        aspect_records = [r for r in records if r.aspect == target_aspect]
        
        # ラベル1（ポジティブ）とラベル0（ネガティブ）で分割
        group_a_records = [r for r in aspect_records if r.label == 1]
        group_b_records = [r for r in aspect_records if r.label == 0]
        
        # サンプル調整
        group_a_texts = self._adjust_sample_size([r.text for r in group_a_records], group_size)
        group_b_texts = self._adjust_sample_size([r.text for r in group_b_records], group_size)
        
        # 正解作成
        correct_answer = f"{target_aspect} positive vs negative characteristics"
        
        return BinarySplitResult(
            group_a=group_a_texts,
            group_b=group_b_texts,
            correct_answer=correct_answer,
            metadata={
                "dataset_id": dataset_id,
                "aspect": target_aspect,
                "split_type": "binary_label",
                "group_a_size": len(group_a_texts),
                "group_b_size": len(group_b_texts),
                "original_a_size": len(group_a_records),
                "original_b_size": len(group_b_records),
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def _adjust_sample_size(self, samples: List[str], target_size: int) -> List[str]:
        """サンプル数調整（共通処理）"""
        if len(samples) >= target_size:
            return random.sample(samples, target_size)
        elif len(samples) > 0:
            # 重複サンプリングで補完
            return samples + random.choices(samples, k=target_size - len(samples))
        else:
            return samples
    
    def create_examples(
        self, 
        dataset_id: str, 
        aspect: str, 
        shot_count: int,
        language: str = "en"
    ) -> List[Dict]:
        """Few-shot用例題を作成"""
        
        if shot_count == 0:
            return []
        
        # データセット・アスペクト別例題テンプレート
        example_templates = {
            "steam": {
                "gameplay": [
                    {
                        "group_a": ["The gameplay mechanics are intuitive and engaging"],
                        "group_b": ["Beautiful graphics and stunning visuals"],
                        "answer": "gameplay mechanics and controls"
                    }
                ],
                "story": [
                    {
                        "group_a": ["Compelling storyline with great character development"],
                        "group_b": ["Excellent sound effects and music"],
                        "answer": "narrative and story elements"
                    }
                ],
                "visual": [
                    {
                        "group_a": ["Stunning graphics and beautiful art style"],
                        "group_b": ["Great gameplay but confusing controls"],
                        "answer": "visual presentation and graphics quality"
                    }
                ]
            },
            "semeval": {
                "food": [
                    {
                        "group_a": ["The pasta was perfectly cooked and delicious"],
                        "group_b": ["The service was excellent and attentive"],
                        "answer": "food quality and taste descriptions"
                    }
                ],
                "service": [
                    {
                        "group_a": ["The waiter was very helpful and friendly"],
                        "group_b": ["The atmosphere was cozy and romantic"],
                        "answer": "staff behavior and service quality"
                    }
                ],
                "atmosphere": [
                    {
                        "group_a": ["The ambiance was romantic with soft lighting"],
                        "group_b": ["The food was excellent but overpriced"],
                        "answer": "environmental and mood descriptions"
                    }
                ]
            },
            "amazon": {
                "product": [
                    {
                        "group_a": ["This product exceeded my expectations"],
                        "group_b": ["Poor quality and disappointing purchase"],
                        "answer": "product quality and satisfaction"
                    }
                ]
            }
        }
        
        # テンプレート取得
        templates = example_templates.get(dataset_id, {}).get(aspect, [])
        
        # 指定数まで例題を返す
        return templates[:shot_count] if templates else []
    
    def get_experiment_config(
        self, 
        dataset_id: str, 
        aspects: List[str] = None,
        shot_settings: List[int] = None
    ) -> Dict:
        """実験設定を取得"""
        
        if aspects is None:
            loader = self.loaders[dataset_id]()
            aspects = loader.get_available_aspects()
        
        if shot_settings is None:
            shot_settings = [0, 1, 3]
        
        return {
            "dataset_id": dataset_id,
            "aspects": aspects,
            "shot_settings": shot_settings,
            "estimated_experiments": len(aspects) * len(shot_settings),
            "domain_info": self.loaders[dataset_id]().get_domain_info()
        }


def main():
    """使用例とテスト"""
    print("=" * 60)
    print("データセット統一管理ツール テスト")
    print("=" * 60)
    
    # マネージャー初期化
    manager = DatasetManager()
    
    # 利用可能データセット確認
    print("\n📊 利用可能データセット:")
    datasets = manager.list_available_datasets()
    for dataset_id, info in datasets.items():
        print(f"  - {dataset_id}: {info}")
    
    # Steamデータセットでテスト
    print(f"\n🎮 Steamデータセット二項分割テスト:")
    try:
        splits = manager.get_binary_splits("steam", aspect="gameplay", group_size=50, split_type="binary_label")
        print(f"  ✅ グループA: {len(splits.group_a)}件")
        print(f"  ✅ グループB: {len(splits.group_b)}件")
        print(f"  ✅ 正解: {splits.correct_answer}")
        if splits.group_a:
            print(f"  📝 サンプルA: {splits.group_a[0][:100]}...")
        if splits.group_b:
            print(f"  📝 サンプルB: {splits.group_b[0][:100]}...")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    
    # Few-shot例題生成テスト
    print(f"\n💡 Few-shot例題生成テスト:")
    examples = manager.create_examples("steam", "gameplay", shot_count=1)
    if examples:
        print(f"  ✅ 例題数: {len(examples)}")
        print(f"  📝 例題: {examples[0]}")
    else:
        print(f"  ⚠️ 例題なし")


if __name__ == "__main__":
    main() 