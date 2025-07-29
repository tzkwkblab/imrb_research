#!/usr/bin/env python3
"""
統合対比因子生成実験 - 実験固有設定

DatasetManagerとContrastFactorAnalyzerを活用した
新しいutils統合ツールの包括的活用実験設定
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ExperimentConfig:
    """実験設定クラス"""
    
    # 基本設定
    experiment_name: str = "unified_contrast_experiment_20250725"
    random_seed: int = 42
    debug_mode: bool = True
    
    # データセット・アスペクト設定
    target_datasets: List[str] = None
    aspect_configurations: Dict[str, Dict] = None
    
    # Few-shot設定
    shot_settings: List[int] = None
    group_size: int = 300
    
    # 出力設定
    output_dir: str = "results/"
    save_intermediate: bool = True
    generate_report: bool = True
    
    def __post_init__(self):
        """デフォルト値設定"""
        if self.target_datasets is None:
            self.target_datasets = ["steam", "semeval", "amazon"]
        
        if self.aspect_configurations is None:
            self.aspect_configurations = {
                "steam": {
                    "aspects": ["gameplay", "story"],
                    "split_type": "binary_label"
                },
                "semeval": {
                    "aspects": ["food", "service"],
                    "split_type": "aspect_vs_others",
                    "domains": ["restaurant", "laptop"]
                },
                "amazon": {
                    "aspects": ["quality", "price"],
                    "split_type": "aspect_vs_others"
                }
            }
        
        if self.shot_settings is None:
            self.shot_settings = [0, 1, 3]
    
    def get_experiment_matrix(self) -> List[Dict]:
        """実験マトリックス生成"""
        experiments = []
        
        for dataset_id in self.target_datasets:
            config = self.aspect_configurations.get(dataset_id, {})
            aspects = config.get("aspects", [])
            split_type = config.get("split_type", "aspect_vs_others")
            domains = config.get("domains", [None])
            
            for domain in domains:
                for aspect in aspects:
                    for shot_setting in self.shot_settings:
                        experiment_def = {
                            "dataset_id": dataset_id,
                            "domain": domain,
                            "aspect": aspect,
                            "shot_setting": shot_setting,
                            "split_type": split_type,
                            "group_size": self.group_size,
                            "experiment_id": self._generate_experiment_id(
                                dataset_id, domain, aspect, shot_setting
                            )
                        }
                        experiments.append(experiment_def)
        
        return experiments
    
    def _generate_experiment_id(self, dataset_id: str, domain: Optional[str], 
                               aspect: str, shot_setting: int) -> str:
        """実験ID生成"""
        if domain:
            return f"{dataset_id}_{domain}_{aspect}_{shot_setting}shot"
        else:
            return f"{dataset_id}_{aspect}_{shot_setting}shot"
    
    def get_total_experiments(self) -> int:
        """総実験数計算"""
        return len(self.get_experiment_matrix())
    
    def get_estimated_time(self, seconds_per_experiment: int = 10) -> str:
        """推定実行時間計算"""
        total_seconds = self.get_total_experiments() * seconds_per_experiment
        minutes = total_seconds // 60
        hours = minutes // 60
        
        if hours > 0:
            return f"約{hours}時間{minutes % 60}分"
        else:
            return f"約{minutes}分"

# 実験設定インスタンス
CONFIG = ExperimentConfig()

# デバッグ用設定確認
if __name__ == "__main__":
    print("=== 統合対比因子生成実験設定 ===")
    print(f"実験名: {CONFIG.experiment_name}")
    print(f"対象データセット: {CONFIG.target_datasets}")
    print(f"総実験数: {CONFIG.get_total_experiments()}")
    print(f"推定実行時間: {CONFIG.get_estimated_time()}")
    
    print("\n=== 実験マトリックス例 ===")
    matrix = CONFIG.get_experiment_matrix()
    for i, exp in enumerate(matrix[:6]):  # 最初の6つを表示
        print(f"{i+1:2d}. {exp['experiment_id']}")
    
    if len(matrix) > 6:
        print(f"    ... 他{len(matrix)-6}実験") 