#!/usr/bin/env python3
"""
データセット設定管理クラス
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ExperimentDefaults:
    """実験デフォルト設定"""
    group_size: int = 300
    shot_settings: List[int] = None
    random_seed: int = 42
    split_types: List[str] = None
    use_aspect_descriptions: bool = False
    
    def __post_init__(self):
        if self.shot_settings is None:
            self.shot_settings = [0, 1, 3]
        if self.split_types is None:
            self.split_types = ["aspect_vs_others", "binary_label"]


class DatasetConfig:
    """データセット設定管理クラス"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初期化
        
        Args:
            config_path: 設定ファイルパス（Noneの場合はデフォルト設定）
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "dataset_configs.yaml"
        
        self.config_path = Path(config_path)
        self.config_data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            # デフォルト設定
            return {
                "datasets": {
                    "steam": {
                        "path": "data/external/steam-review-aspect-dataset/current",
                        "domain": "gaming",
                        "language": "en",
                        "aspects": ["recommended", "story", "gameplay", "visual", "audio", "technical", "price", "suggestion"]
                    }
                },
                "experiment_defaults": {
                    "group_size": 300,
                    "shot_settings": [0, 1, 3],
                    "random_seed": 42,
                    "split_types": ["aspect_vs_others", "binary_label"],
                    "use_aspect_descriptions": False
                }
            }
    
    def list_available_datasets(self) -> List[str]:
        """利用可能なデータセット一覧"""
        return list(self.config_data.get("datasets", {}).keys())
    
    def get_dataset_config(self, dataset_id: str) -> Dict[str, Any]:
        """データセット設定取得"""
        return self.config_data.get("datasets", {}).get(dataset_id, {})
    
    def get_dataset_aspects(self, dataset_id: str) -> List[str]:
        """データセットのアスペクト一覧"""
        config = self.get_dataset_config(dataset_id)
        return config.get("aspects", [])
    
    def get_experiment_defaults(self) -> ExperimentDefaults:
        """実験デフォルト設定取得"""
        defaults = self.config_data.get("experiment_defaults", {})
        return ExperimentDefaults(**defaults)
    
    def get_example_templates(self, dataset_id: str, aspect: str) -> List[Dict]:
        """Few-shot例題テンプレート取得"""
        templates = self.config_data.get("example_templates", {})
        dataset_templates = templates.get(dataset_id, {})
        return dataset_templates.get(aspect, [])


class ConfigValidator:
    """設定検証クラス"""
    
    def __init__(self, config: DatasetConfig):
        self.config = config
    
    def validate_dataset(self, dataset_id: str) -> List[str]:
        """データセット設定検証"""
        warnings = []
        config = self.config.get_dataset_config(dataset_id)
        
        if not config:
            warnings.append(f"データセット '{dataset_id}' の設定が見つかりません")
            return warnings
        
        # パス存在チェック
        path = config.get("path")
        if path and not Path(path).exists():
            warnings.append(f"データセットパスが存在しません: {path}")
        
        # アスペクト存在チェック
        aspects = config.get("aspects", [])
        if not aspects:
            warnings.append(f"データセット '{dataset_id}' にアスペクトが定義されていません")
        
        return warnings
    
    def check_dataset_accessibility(self, dataset_id: str) -> bool:
        """データセットアクセス可能性チェック"""
        config = self.config.get_dataset_config(dataset_id)
        if not config:
            return False
        
        path = config.get("path")
        if path:
            return Path(path).exists()
        
        return False
    
    def validate_all(self) -> Dict[str, List[str]]:
        """全設定検証"""
        all_warnings = {}
        
        for dataset_id in self.config.list_available_datasets():
            warnings = self.validate_dataset(dataset_id)
            if warnings:
                all_warnings[dataset_id] = warnings
        
        return all_warnings


class ValidationError(Exception):
    """設定検証エラー"""
    pass