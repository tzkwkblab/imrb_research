#!/usr/bin/env python3
"""
アスペクト説明文管理クラス

descriptions.csv もしくは明示指定された CSV からアスペクト名と説明文の
マッピングを読み込み、アスペクト名から説明文への変換を提供する。

# 使用例（ディレクトリ指定: ディレクトリ直下の descriptions.csv を使用）
manager = AspectDescriptionManager(dataset_path="data/external/steam-review-aspect-dataset/current")
description = manager.get_description("gameplay")

# 使用例（CSVファイルを直接指定）
manager = AspectDescriptionManager(csv_path="/path/to/steam_v1.csv")
description = manager.get_description("gameplay")
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class AspectDescriptionManager:
    """アスペクト説明文管理クラス"""
    
    def __init__(self, dataset_path: Optional[str] = None, csv_path: Optional[str] = None):
        """
        初期化
        
        Args:
            dataset_path: データセットのディレクトリパス（直下の descriptions.csv を利用）
            csv_path: 説明文CSVファイルの明示パス（優先）
        """
        self.dataset_path = Path(dataset_path) if dataset_path else None
        self.csv_path = Path(csv_path) if csv_path else None
        self.descriptions: Dict[str, str] = {}
        self.source_file: Optional[Path] = None
        self._load_descriptions()
    
    def _load_descriptions(self):
        """説明文CSVを読み込み（csv_path優先、次にdataset_path/descriptions.csv）"""
        # 優先: 明示CSV
        if self.csv_path is not None:
            if self.csv_path.exists():
                self._read_csv(self.csv_path)
                return
            else:
                logger.warning(f"指定のCSVが見つかりません: {self.csv_path}")
        # 次: ディレクトリの descriptions.csv
        if self.dataset_path is not None:
            desc_file = self.dataset_path / "descriptions.csv"
            if desc_file.exists():
                self._read_csv(desc_file)
                return
            else:
                logger.debug(f"descriptions.csvが見つかりません: {desc_file}")
        # いずれも無ければ空
        self.descriptions = {}
    
    def _load_descriptions_manual(self, desc_file: Path):
        """
        手動でCSVを読み込み（フォールバック用）
        
        最初のカンマで分割することで、descriptionフィールド内のカンマに対応
        """
        self.descriptions = {}
        try:
            with open(desc_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) < 2:
                    logger.warning(f"CSVファイルの行数が不足しています（2行未満）: {desc_file}")
                    return
                
                # ヘッダーをスキップ
                header = lines[0].strip()
                logger.debug(f"CSVヘッダー: {header}")
                
                for line_num, line in enumerate(lines[1:], start=2):
                    line = line.rstrip('\n\r')
                    if not line.strip():
                        continue
                    
                    # 最初のカンマで分割（aspect, description）
                    parts = line.split(',', 1)
                    if len(parts) == 2:
                        aspect = parts[0].strip()
                        description = parts[1].strip()
                        if aspect:
                            self.descriptions[aspect] = description
                        else:
                            logger.warning(f"行{line_num}: aspectが空です")
                    else:
                        logger.warning(f"行{line_num}: カンマが見つかりません（フィールド数: {len(parts)}）")
            
            self.source_file = desc_file
            logger.debug(f"手動読み込み完了: {len(self.descriptions)}件のアスペクトを読み込みました")
            
        except Exception as e:
            logger.error(f"手動読み込み中にエラーが発生しました: {desc_file}, エラー: {e}")
            raise

    def _read_csv(self, file_path: Path) -> None:
        """
        CSVを読み込む（複数の方法を試行）
        
        1. pandas標準読み込み（クォート対応）
        2. 手動読み込み（最初のカンマで分割）- descriptionフィールド内のカンマに対応
        
        注意: descriptionフィールドにカンマが含まれるCSVの場合、
        手動読み込み（方法2）が確実に動作します。
        """
        import csv
        
        # 方法1: 標準のpandas読み込み（クォート対応）
        try:
            df = pd.read_csv(file_path, quoting=csv.QUOTE_ALL)
            if 'aspect' in df.columns and 'description' in df.columns:
                self.descriptions = dict(zip(df['aspect'], df['description']))
                self.source_file = file_path
                logger.debug(f"CSV読み込み成功（pandas標準）: {file_path}, {len(self.descriptions)}件")
                # データが期待通り読み込まれているか確認
                if len(self.descriptions) > 0:
                    return
                else:
                    logger.warning(f"pandas標準読み込みでデータが空でした: {file_path}")
            else:
                logger.warning(f"CSVに必要なカラム（aspect, description）がありません: {file_path}")
        except Exception as e:
            logger.debug(f"pandas標準読み込み失敗: {e}")
        
        # 方法2: 手動読み込み（最初のカンマで分割）
        # descriptionフィールド内のカンマに対応するため、この方法が確実
        try:
            logger.debug(f"手動読み込みを試行します: {file_path}")
            self._load_descriptions_manual(file_path)
            if self.descriptions:
                logger.info(f"手動読み込み成功: {file_path}, {len(self.descriptions)}件")
            else:
                logger.warning(f"手動読み込み後もデータが空です: {file_path}")
        except Exception as e:
            logger.error(f"手動読み込みも失敗しました: {file_path}, エラー: {e}")
            self.descriptions = {}
    
    def get_description(self, aspect: str) -> str:
        """
        アスペクト名から説明文を取得
        
        Args:
            aspect: アスペクト名
            
        Returns:
            説明文（見つからない場合は元のアスペクト名を返す）
        """
        return self.descriptions.get(aspect, aspect)
    
    def has_descriptions(self) -> bool:
        """
        説明文ファイルが存在し、読み込み済みかチェック
        
        Returns:
            説明文が利用可能な場合True
        """
        return len(self.descriptions) > 0
    
    def get_available_aspects(self) -> list:
        """
        利用可能なアスペクト名のリストを取得
        
        Returns:
            アスペクト名のリスト
        """
        return list(self.descriptions.keys())
    
    def get_all_descriptions(self) -> Dict[str, str]:
        """
        全てのアスペクト名と説明文のマッピングを取得
        
        Returns:
            アスペクト名と説明文の辞書
        """
        return self.descriptions.copy()