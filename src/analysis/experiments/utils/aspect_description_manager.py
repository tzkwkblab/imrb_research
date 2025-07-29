#!/usr/bin/env python3
"""
アスペクト説明文管理クラス

descriptions.csvからアスペクト名と説明文のマッピングを読み込み、
アスペクト名から説明文への変換を提供する

# 使用例
manager = AspectDescriptionManager("data/external/steam-review-aspect-dataset/current")
description = manager.get_description("gameplay")
# → "Controls, mechanics, interactivity, difficulty and other gameplay setups."
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Optional


class AspectDescriptionManager:
    """アスペクト説明文管理クラス"""
    
    def __init__(self, dataset_path: str):
        """
        初期化
        
        Args:
            dataset_path: データセットのパス（descriptions.csvを含むディレクトリ）
        """
        self.dataset_path = Path(dataset_path)
        self.descriptions = {}
        self._load_descriptions()
    
    def _load_descriptions(self):
        """descriptions.csvから説明文を読み込み"""
        desc_file = self.dataset_path / "descriptions.csv"
        if desc_file.exists():
            try:
                # カンマを含む説明文を適切に処理するため、quoting=csv.QUOTE_ALLを使用
                import csv
                df = pd.read_csv(desc_file, quoting=csv.QUOTE_ALL)
                self.descriptions = dict(zip(df['aspect'], df['description']))
            except Exception as e:
                print(f"警告: descriptions.csvの読み込みに失敗しました: {e}")
                # フォールバック: 手動でCSVを読み込み
                try:
                    self._load_descriptions_manual(desc_file)
                except Exception as e2:
                    print(f"警告: 手動読み込みも失敗しました: {e2}")
                    self.descriptions = {}
        else:
            print(f"警告: descriptions.csvが見つかりません: {desc_file}")
    
    def _load_descriptions_manual(self, desc_file):
        """手動でCSVを読み込み（フォールバック用）"""
        self.descriptions = {}
        with open(desc_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) < 2:
                return
            
            # ヘッダーをスキップ
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                
                # 最初のカンマで分割
                parts = line.split(',', 1)
                if len(parts) == 2:
                    aspect = parts[0].strip()
                    description = parts[1].strip()
                    self.descriptions[aspect] = description
    
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