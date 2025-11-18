"""
GoEmotions Dataset専用ローダー
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List
from .base import BaseDatasetLoader, UnifiedRecord
from ..configs.dataset_config import DatasetConfig


class GoEmotionsDatasetLoader(BaseDatasetLoader):
    """GoEmotions Dataset専用ローダー"""
    
    def __init__(self, base_path: str = None, config: DatasetConfig = None):
        """
        初期化
        
        Args:
            base_path: データセットパス（Noneの場合は設定ファイルから取得）
            config: 設定オブジェクト
        """
        if base_path is None and config is not None:
            dataset_info = config.get_dataset_info("goemotions")
            base_path = dataset_info.path
        elif base_path is None:
            base_path = "/Users/seinoshun/imrb_research/data/external/goemotions/kaggle-debarshichanda/current"
        
        super().__init__(base_path, "goemotions")
        self.config = config
        
        # GoEmotionsの28感情カテゴリ
        self.emotions = [
            'admiration', 'amusement', 'anger', 'annoyance', 'approval',
            'caring', 'confusion', 'curiosity', 'desire', 'disappointment',
            'disapproval', 'disgust', 'embarrassment', 'excitement', 'fear',
            'gratitude', 'grief', 'joy', 'love', 'nervousness',
            'optimism', 'pride', 'realization', 'relief', 'remorse',
            'sadness', 'surprise', 'neutral'
        ]
    
    def load_raw_data(self) -> List[UnifiedRecord]:
        """GoEmotionsデータを統一フォーマットで読み込み"""
        if not self.validate_data_path():
            raise FileNotFoundError(f"データパスが無効です: {self.base_path}")
        
        records = []
        
        # データディレクトリのパス
        data_dir = self.base_path / "data"
        if not data_dir.exists():
            raise FileNotFoundError(f"データディレクトリが見つかりません: {data_dir}")
        
        # 感情IDと感情名のマッピングを読み込み
        emotions_file = data_dir / "emotions.txt"
        if emotions_file.exists():
            with open(emotions_file, 'r', encoding='utf-8') as f:
                emotion_list = [line.strip() for line in f.readlines()]
            # 感情ID（0-27）と感情名のマッピングを作成
            self.emotion_id_to_name = {i: name for i, name in enumerate(emotion_list)}
        else:
            # フォールバック: デフォルトのマッピング
            self.emotion_id_to_name = {i: emotion for i, emotion in enumerate(self.emotions)}
        
        # TSVファイルを読み込み（train.tsv, test.tsv, dev.tsv）
        file_mapping = {
            'train.tsv': 'train.tsv',
            'test.tsv': 'test.tsv',
            'dev.tsv': 'val.tsv'  # dev.tsvをvalとして扱う
        }
        
        for filename, source_name in file_mapping.items():
            file_path = data_dir / filename
            if file_path.exists():
                try:
                    # TSVファイルを読み込み（ヘッダーなし、タブ区切り）
                    df = pd.read_csv(file_path, sep='\t', header=None, names=['text', 'emotion_id', 'comment_id'])
                    file_records = self._convert_dataframe_to_records(df, source_name)
                    records.extend(file_records)
                except Exception as e:
                    print(f"GoEmotions データ読み込みエラー ({filename}): {e}")
        
        return records
    
    def _convert_dataframe_to_records(self, df: pd.DataFrame, source_file: str) -> List[UnifiedRecord]:
        """DataFrameを統一レコード形式に変換"""
        records = []
        
        # GoEmotionsデータセットの構造: text, emotion_id, comment_id
        # 感情IDは単一のIDまたはカンマ区切りの複数ID（マルチラベル）
        for _, row in df.iterrows():
            text = str(row.get('text', ''))
            if not text or text == 'nan':
                continue
            
            # 感情IDを取得（カンマ区切りの可能性がある）
            emotion_id_str = str(row.get('emotion_id', ''))
            if pd.isna(emotion_id_str) or emotion_id_str == 'nan':
                continue
            
            # カンマ区切りの感情IDを分割
            emotion_ids = [eid.strip() for eid in emotion_id_str.split(',')]
            
            # 各感情IDに対してレコードを作成
            for emotion_id_str_part in emotion_ids:
                try:
                    emotion_id = int(emotion_id_str_part)
                    # 感情IDを感情名に変換
                    emotion_name = self.emotion_id_to_name.get(emotion_id)
                    
                    if emotion_name:
                        records.append(UnifiedRecord(
                            text=text,
                            aspect=emotion_name,
                            label=1,
                            domain="emotions",
                            dataset_id="goemotions",
                            metadata={
                                "source_file": source_file,
                                "emotion_id": emotion_id,
                                "emotion": emotion_name,
                                "comment_id": row.get('comment_id', ''),
                                "original_index": row.name if hasattr(row, 'name') else None,
                                "is_multi_label": len(emotion_ids) > 1
                            }
                        ))
                except (ValueError, TypeError):
                    # 無効な感情IDはスキップ
                    continue
        
        return records
    
    def get_available_aspects(self) -> List[str]:
        """利用可能なアスペクト一覧（感情ラベル一覧）"""
        return self.emotions.copy()
    
    def get_domain_info(self) -> Dict:
        """ドメイン情報取得"""
        return {
            "domain": "emotions",
            "dataset": "goemotions",
            "language": "en",
            "aspects": self.emotions,
            "data_path": str(self.base_path) if self.base_path else None
        }
    
    def get_emotion_distribution(self) -> Dict[str, int]:
        """感情別ラベル分布取得"""
        records = self.load_with_cache()
        distribution = {}
        
        for emotion in self.emotions:
            emotion_records = [r for r in records if r.aspect == emotion]
            distribution[emotion] = len(emotion_records)
        
        return distribution

