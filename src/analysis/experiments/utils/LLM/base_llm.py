from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import sys
import os

# 簡易設定（外部依存なし）


class BaseLLM(ABC):
    """LLM抽象基底クラス"""
    
    def __init__(self, model: str = None, max_retries: int = 3):
        """
        基底クラスの初期化
        Args:
            model: モデル名（Noneの場合は設定ファイルから取得）
            max_retries: 最大リトライ回数
        """
        # デフォルト設定（外部依存なし）
        self.model = model or 'gpt-4o-mini'
        self.max_retries = max_retries
        self.default_temperature = 0.0
        self.default_max_tokens = 1000
    
    def get_api_key(self, env_key: str) -> str:
        """APIキーを取得（基底クラスで共通化）"""
        import os
        api_key = os.getenv(env_key)
        if not api_key:
            raise ValueError(f"{env_key}環境変数が設定されていません")
        return api_key
    
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
    
    @abstractmethod
    def list_available_models(self) -> List[Dict[str, str]]:
        """利用可能なモデル一覧を取得"""
        pass
    
    @abstractmethod
    def get_available_model_ids(self) -> List[str]:
        """利用可能なモデルIDのみを取得"""
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