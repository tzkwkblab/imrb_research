from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import sys
import os

# 設定管理をインポート
sys.path.append(os.path.join(os.path.dirname(__file__), '../../conf'))
from experiment_config import get_config_manager


class BaseLLM(ABC):
    """LLM抽象基底クラス"""
    
    def __init__(self, model: str = None, max_retries: int = 3):
        """
        基底クラスの初期化
        Args:
            model: モデル名（Noneの場合は設定ファイルから取得）
            max_retries: 最大リトライ回数
        """
        # 設定ファイルからデフォルト値を取得
        self.config_manager = get_config_manager()
        self.model_config = self.config_manager.get_model_config()
        
        self.model = model or self.model_config.model
        self.max_retries = max_retries
        self.default_temperature = self.model_config.temperature
        self.default_max_tokens = self.config_manager.get_value('max_tokens', 100)
    
    def get_api_key(self, env_key: str) -> str:
        """APIキーを取得（基底クラスで共通化）"""
        return self.config_manager.get_api_key(env_key)
    
    @abstractmethod
    def query(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """
        LLMにクエリを送信
        Args:
            messages: メッセージリスト [{'role': 'user', 'content': '...'}, ...]
            **kwargs: モデル固有のパラメータ
        Returns:
            応答文字列（失敗時はNone）
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """モデル名を取得"""
        pass
    
    def get_default_params(self, **kwargs) -> Dict[str, Any]:
        """
        デフォルトパラメータを取得（設定ファイル + オーバーライド）
        Args:
            **kwargs: オーバーライドするパラメータ
        Returns:
            マージされたパラメータ辞書
        """
        params = {
            'temperature': self.default_temperature,
            'max_tokens': self.default_max_tokens
        }
        params.update(kwargs)
        return params
    
    def ask(self, question: str, system_message: str = None, **kwargs) -> Optional[str]:
        """
        シンプルな質問用の便利メソッド
        Args:
            question: 質問文字列
            system_message: システムメッセージ（省略可）
            **kwargs: モデル固有のパラメータ
        Returns:
            応答文字列（失敗時はNone）
        """
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": question})
        
        return self.query(messages, **kwargs)