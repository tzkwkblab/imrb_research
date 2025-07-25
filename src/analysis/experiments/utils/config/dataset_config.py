"""
データセット設定管理クラス
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field


@dataclass
class DatasetInfo:
    """個別データセット情報"""
    path: str
    domain: Optional[str] = None
    language: str = "en"
    aspects: Optional[List[str]] = None
    domains: Optional[Dict[str, Dict[str, List[str]]]] = None


@dataclass
class ExperimentDefaults:
    """実験デフォルト設定"""
    group_size: int = 300
    shot_settings: List[int] = field(default_factory=lambda: [0, 1, 3])
    random_seed: int = 42
    split_types: List[str] = field(default_factory=lambda: ["aspect_vs_others", "binary_label"])


@dataclass
class ExampleTemplate:
    """Few-shot例題テンプレート"""
    group_a: List[str]
    group_b: List[str]
    answer: str


class DatasetConfig:
    """YAMLベースの設定管理クラス"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初期化
        
        Args:
            config_path: 設定ファイルパス（Noneの場合はデフォルトパスを使用）
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "dataset_configs.yaml"
        
        self.config_path = Path(config_path)
        self._config_data: Dict = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """設定ファイル読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_data = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"YAML形式エラー: {e}")
    
    @classmethod
    def load(cls, config_path: str) -> 'DatasetConfig':
        """ファクトリーメソッド"""
        return cls(config_path)
    
    def get_dataset_info(self, dataset_id: str) -> DatasetInfo:
        """データセット情報取得"""
        if dataset_id not in self._config_data.get('datasets', {}):
            raise ValueError(f"未定義のデータセット: {dataset_id}")
        
        data = self._config_data['datasets'][dataset_id]
        return DatasetInfo(**data)
    
    def get_experiment_defaults(self) -> ExperimentDefaults:
        """実験デフォルト設定取得"""
        defaults_data = self._config_data.get('experiment_defaults', {})
        return ExperimentDefaults(**defaults_data)
    
    def get_example_templates(self, dataset_id: str, aspect: str) -> List[ExampleTemplate]:
        """Few-shot例題テンプレート取得"""
        templates_data = self._config_data.get('example_templates', {})
        dataset_templates = templates_data.get(dataset_id, {})
        aspect_templates = dataset_templates.get(aspect, [])
        
        return [ExampleTemplate(**template) for template in aspect_templates]
    
    def list_available_datasets(self) -> List[str]:
        """利用可能データセット一覧"""
        return list(self._config_data.get('datasets', {}).keys())
    
    def get_dataset_aspects(self, dataset_id: str) -> List[str]:
        """データセットのアスペクト一覧取得"""
        dataset_info = self.get_dataset_info(dataset_id)
        
        if dataset_info.aspects:
            return dataset_info.aspects
        elif dataset_info.domains:
            # SemEval形式の場合
            all_aspects = []
            for domain_data in dataset_info.domains.values():
                all_aspects.extend(domain_data.get('aspects', []))
            return list(set(all_aspects))
        else:
            return []
    
    def get_loader_config(self, dataset_id: str) -> Dict[str, str]:
        """ローダー設定取得（将来の拡張用）"""
        loaders_config = self._config_data.get('loaders', {})
        return loaders_config.get(dataset_id, {})
    
    def get_splitter_config(self, split_type: str) -> Dict[str, str]:
        """分割戦略設定取得（将来の拡張用）"""
        splitters_config = self._config_data.get('splitters', {})
        return splitters_config.get(split_type, {}) 