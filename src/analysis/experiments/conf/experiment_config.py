#!/usr/bin/env python3
"""
実験設定管理

設定ファイルを読み込み、実験で使用する各種パラメータを提供する
"""

import yaml
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """モデル設定"""
    model: str
    temperature: float
    system_prompt: str = ""
    output_format: str = "json"


@dataclass
class ExperimentConfig:
    """実験設定"""
    model_config: ModelConfig
    evaluation_metrics: list
    raw_config: Dict[str, Any]


class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config_path: str = None):
        """
        初期化
        
        Args:
            config_path: 設定ファイルのパス（未指定時はデフォルト）
        """
        if config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, "paramaters.yml")
        
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # デフォルト設定
            return {
                'model': 'gpt-4o-mini',
                'temperature': 0.7,
                'system_prompt': 'You are a helpful assistant.',
                'output_format': 'json',
                'evaluation_metrics': ['bert_score', 'bleu_score']
            }
    
    def get_model_config(self) -> ModelConfig:
        """モデル設定を取得"""
        return ModelConfig(
            model=self._config.get('model', 'gpt-4o-mini'),
            temperature=self._config.get('temperature', 0.7),
            system_prompt=self._config.get('system_prompt', 'You are a helpful assistant.'),
            output_format=self._config.get('output_format', 'json')
        )
    
    def get_experiment_config(self) -> ExperimentConfig:
        """実験設定を取得"""
        return ExperimentConfig(
            model_config=self.get_model_config(),
            evaluation_metrics=self._config.get('evaluation_metrics', ['bert_score', 'bleu_score']),
            raw_config=self._config.copy()
        )
    
    def get_openai_params(self) -> Dict[str, Any]:
        """OpenAI API用のパラメータを取得"""
        model_config = self.get_model_config()
        return {
            'model': model_config.model,
            'temperature': model_config.temperature
        }
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """任意の設定値を取得"""
        return self._config.get(key, default)


# グローバルインスタンス（シングルトン的な使用）
_config_manager = None


def get_config_manager(config_path: str = None) -> ConfigManager:
    """設定管理インスタンスを取得"""
    global _config_manager
    if _config_manager is None or config_path is not None:
        _config_manager = ConfigManager(config_path)
    return _config_manager


def get_model_config() -> ModelConfig:
    """モデル設定を取得（便利関数）"""
    return get_config_manager().get_model_config()


def get_openai_params() -> Dict[str, Any]:
    """OpenAI API用パラメータを取得（便利関数）"""
    return get_config_manager().get_openai_params()


def main():
    """テスト"""
    config_manager = get_config_manager()
    
    print("=== モデル設定 ===")
    model_config = config_manager.get_model_config()
    print(f"Model: {model_config.model}")
    print(f"Temperature: {model_config.temperature}")
    print(f"System Prompt: {model_config.system_prompt}")
    
    print("\n=== OpenAI API用パラメータ ===")
    openai_params = config_manager.get_openai_params()
    print(openai_params)
    
    print("\n=== 実験設定 ===")
    exp_config = config_manager.get_experiment_config()
    print(f"Evaluation Metrics: {exp_config.evaluation_metrics}")


if __name__ == "__main__":
    main() 