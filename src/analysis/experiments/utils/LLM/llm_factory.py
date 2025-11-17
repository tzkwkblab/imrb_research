from typing import Dict, Type
import logging
from .base_llm import BaseLLM
from .gpt.gpt_client import GPTClient

try:
    from .gemini.gemini_client import GeminiClient
except ImportError:
    GeminiClient = None

try:
    from .claude.claude_client import ClaudeClient
except ImportError:
    ClaudeClient = None

from .model_registry import get_provider_from_model_id


class LLMFactory:
    """LLMクライアントファクトリー"""
    
    # プロバイダー別のクライアントクラス定義
    _providers: Dict[str, Type[BaseLLM]] = {
        'openai': GPTClient,
    }
    
    # 利用可能なプロバイダーを動的に追加
    if GeminiClient is not None:
        _providers['google'] = GeminiClient
    
    if ClaudeClient is not None:
        _providers['anthropic'] = ClaudeClient
    
    # GPTモデルのプレフィックス
    _gpt_prefixes = ['gpt-', 'text-', 'davinci', 'curie', 'babbage', 'ada', 'o']
    
    @classmethod
    def create_client(cls, model_name: str = None, debug: bool = False, **kwargs) -> BaseLLM:
        """
        指定されたモデルのクライアントを作成
        Args:
            model_name: モデル名
            debug: デバッグモードの有効/無効
            **kwargs: クライアント固有の初期化パラメータ
        Returns:
            LLMクライアントインスタンス
        """
        logger = logging.getLogger(__name__)
        
        # model_nameがNoneの場合は設定ファイルから取得
        if model_name is None:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../conf'))
            from experiment_config import get_config_manager
            
            config_manager = get_config_manager()
            model_name = config_manager.get_value('model', 'gpt-4')
        
        # プロバイダーを推定してクライアントクラスを取得
        client_class = cls._get_client_class(model_name, debug=debug)
        
        # debugパラメータをkwargsに追加
        kwargs['debug'] = debug
        client = client_class(model=model_name, **kwargs)
        
        return client
    
    @classmethod
    def _get_client_class(cls, model_name: str, debug: bool = False) -> Type[BaseLLM]:
        """モデル名からクライアントクラスを推定"""
        # モデルレジストリからプロバイダーを推定
        provider = get_provider_from_model_id(model_name)
        
        if provider and provider in cls._providers:
            return cls._providers[provider]
        
        # フォールバック: プレフィックスベースの判定
        model_name_lower = model_name.lower()
        
        # Geminiモデルの場合
        if model_name_lower.startswith('gemini-'):
            if 'google' in cls._providers:
                return cls._providers['google']
        
        # Claudeモデルの場合
        if model_name_lower.startswith('claude-'):
            if 'anthropic' in cls._providers:
                return cls._providers['anthropic']
        
        # GPTモデルの場合
        for prefix in cls._gpt_prefixes:
            if model_name_lower.startswith(prefix):
                return cls._providers['openai']
        
        # デフォルトでGPTClientを使用
        return cls._providers['openai']
    
    @classmethod
    def get_supported_models(cls, provider: str = 'openai', debug: bool = False) -> list:
        """
        API問い合わせによって利用可能なモデル一覧を取得
        Args:
            provider: プロバイダー名（デフォルト: openai）
            debug: デバッグモードの有効/無効
        Returns:
            利用可能なモデルIDのリスト
        """
        if provider not in cls._providers:
            raise ValueError(f"サポートされていないプロバイダー: {provider}")
        
        # 一時的にクライアントを作成してモデル一覧を取得
        client_class = cls._providers[provider]
        temp_client = client_class(debug=debug)
        models = temp_client.get_available_model_ids()
        
        return models
    
    @classmethod
    def get_model_details(cls, provider: str = 'openai', debug: bool = False) -> list:
        """
        API問い合わせによって利用可能なモデル詳細情報を取得
        Args:
            provider: プロバイダー名（デフォルト: openai）
            debug: デバッグモードの有効/無効
        Returns:
            モデル詳細情報のリスト
        """
        if provider not in cls._providers:
            raise ValueError(f"サポートされていないプロバイダー: {provider}")
        
        client_class = cls._providers[provider]
        temp_client = client_class(debug=debug)
        details = temp_client.list_available_models()
        
        return details