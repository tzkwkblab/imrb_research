from typing import Dict, Type
from base_llm import BaseLLM
from gpt.gpt_client import GPTClient


class LLMFactory:
    """LLMクライアントファクトリー"""
    
    # プロバイダー別のクライアントクラス定義
    _providers: Dict[str, Type[BaseLLM]] = {
        'openai': GPTClient,
    }
    
    # GPTモデルのプレフィックス
    _gpt_prefixes = ['gpt-', 'text-', 'davinci', 'curie', 'babbage', 'ada']
    
    @classmethod
    def create_client(cls, model_name: str = None, **kwargs) -> BaseLLM:
        """
        指定されたモデルのクライアントを作成
        Args:
            model_name: モデル名
            **kwargs: クライアント固有の初期化パラメータ
        Returns:
            LLMクライアントインスタンス
        """
        # model_nameがNoneの場合は設定ファイルから取得
        if model_name is None:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../conf'))
            from experiment_config import get_config_manager
            
            config_manager = get_config_manager()
            model_name = config_manager.get_value('model', 'gpt-4')
        
        # プロバイダーを推定してクライアントクラスを取得
        client_class = cls._get_client_class(model_name)
        return client_class(model=model_name, **kwargs)
    
    @classmethod
    def _get_client_class(cls, model_name: str) -> Type[BaseLLM]:
        """モデル名からクライアントクラスを推定"""
        # GPTモデルの場合
        if any(model_name.startswith(prefix) for prefix in cls._gpt_prefixes):
            return cls._providers['openai']
        
        # デフォルトでGPTClientを使用
        return cls._providers['openai']
    
    @classmethod
    def get_supported_models(cls, provider: str = 'openai') -> list:
        """
        API問い合わせによって利用可能なモデル一覧を取得
        Args:
            provider: プロバイダー名（デフォルト: openai）
        Returns:
            利用可能なモデルIDのリスト
        """
        if provider not in cls._providers:
            raise ValueError(f"サポートされていないプロバイダー: {provider}")
        
        # 一時的にクライアントを作成してモデル一覧を取得
        client_class = cls._providers[provider]
        temp_client = client_class()
        return temp_client.get_available_model_ids()
    
    @classmethod
    def get_model_details(cls, provider: str = 'openai') -> list:
        """
        API問い合わせによって利用可能なモデル詳細情報を取得
        Args:
            provider: プロバイダー名（デフォルト: openai）
        Returns:
            モデル詳細情報のリスト
        """
        if provider not in cls._providers:
            raise ValueError(f"サポートされていないプロバイダー: {provider}")
        
        client_class = cls._providers[provider]
        temp_client = client_class()
        return temp_client.list_available_models()