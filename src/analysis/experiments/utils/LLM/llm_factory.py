from typing import Dict, Type
from base_llm import BaseLLM
from gpt.gpt_client import GPTClient


class LLMFactory:
    """LLMクライアントファクトリー"""
    
    _clients: Dict[str, Type[BaseLLM]] = {
        'gpt-4': GPTClient,
        'gpt-4o-mini': GPTClient,
        'gpt-3.5-turbo': GPTClient,
    }
    
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
            # 一時的にダミークライアントで設定を取得
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../conf'))
            from experiment_config import get_config_manager
            
            config_manager = get_config_manager()
            model_name = config_manager.get_value('model', 'gpt-4')  # デフォルトはgpt-4
        
        if model_name not in cls._clients:
            raise ValueError(f"サポートされていないモデル: {model_name}")
        
        client_class = cls._clients[model_name]
        return client_class(model=model_name, **kwargs)
    
    @classmethod
    def get_supported_models(cls) -> list:
        """サポートされているモデル一覧を取得"""
        return list(cls._clients.keys())