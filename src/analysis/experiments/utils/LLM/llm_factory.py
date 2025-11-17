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
        if debug:
            logger.debug("LLMFactory.create_client() 開始")
            logger.debug("引数 model_name: %s", model_name)
            logger.debug("引数 debug: %s", debug)
            logger.debug("追加パラメータ: %s", kwargs)
        
        # model_nameがNoneの場合は設定ファイルから取得
        if model_name is None:
            if debug:
                logger.debug("モデル名未指定 - 設定ファイルから取得開始")
            
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../conf'))
            from experiment_config import get_config_manager
            
            config_manager = get_config_manager()
            model_name = config_manager.get_value('model', 'gpt-4')
            
            if debug:
                logger.debug("設定ファイルから取得したモデル: %s", model_name)
                try:
                    model_config = config_manager.get_model_config()
                    logger.debug("設定詳細: temperature=%s", getattr(model_config, 'temperature', None))
                    # system_prompt は長いので先頭のみ
                    sp = getattr(model_config, 'system_prompt', '')
                    logger.debug("設定詳細: system_prompt(先頭50)=%s", sp[:50] if isinstance(sp, str) else '')
                except Exception as e:
                    if debug:
                        logger.debug("設定詳細取得エラー: %s", e)
        
        # プロバイダーを推定してクライアントクラスを取得
        if debug:
            logger.debug("クライアントクラス推定開始: %s", model_name)
        
        client_class = cls._get_client_class(model_name, debug=debug)
        
        if debug:
            logger.debug("決定されたクライアントクラス: %s", client_class.__name__)
            logger.debug("クライアントインスタンス作成開始")
        
        # debugパラメータをkwargsに追加
        kwargs['debug'] = debug
        client = client_class(model=model_name, **kwargs)
        
        if debug:
            logger.debug("クライアントインスタンス作成完了")
            logger.debug("作成されたクライアントのモデル: %s", client.get_model_name())
        
        return client
    
    @classmethod
    def _get_client_class(cls, model_name: str, debug: bool = False) -> Type[BaseLLM]:
        """モデル名からクライアントクラスを推定"""
        logger = logging.getLogger(__name__)
        if debug:
            logger.debug("クライアントクラス推定: %s", model_name)
            logger.debug("GPTプレフィックス: %s", cls._gpt_prefixes)
        
        # モデルレジストリからプロバイダーを推定
        provider = get_provider_from_model_id(model_name)
        
        if provider and provider in cls._providers:
            if debug:
                logger.debug("プロバイダー '%s' と判定", provider)
            return cls._providers[provider]
        
        # フォールバック: プレフィックスベースの判定
        model_name_lower = model_name.lower()
        
        # Geminiモデルの場合
        if model_name_lower.startswith('gemini-'):
            if 'google' in cls._providers:
                if debug:
                    logger.debug("Geminiモデルと判定")
                return cls._providers['google']
        
        # Claudeモデルの場合
        if model_name_lower.startswith('claude-'):
            if 'anthropic' in cls._providers:
                if debug:
                    logger.debug("Claudeモデルと判定")
                return cls._providers['anthropic']
        
        # GPTモデルの場合
        for prefix in cls._gpt_prefixes:
            if model_name_lower.startswith(prefix):
                if debug:
                    logger.debug("GPTモデルと判定: プレフィックス '%s' にマッチ", prefix)
                return cls._providers['openai']
        
        # デフォルトでGPTClientを使用
        if debug:
            logger.debug("プレフィックスにマッチしないため、デフォルトでGPTClientを使用")
        
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
        logger = logging.getLogger(__name__)
        if debug:
            logger.debug("get_supported_models() 開始")
            logger.debug("プロバイダー: %s", provider)
        
        if provider not in cls._providers:
            error_msg = f"サポートされていないプロバイダー: {provider}"
            if debug:
                logger.debug("エラー: %s", error_msg)
            raise ValueError(error_msg)
        
        # 一時的にクライアントを作成してモデル一覧を取得
        client_class = cls._providers[provider]
        
        if debug:
            logger.debug("一時クライアント作成: %s", client_class.__name__)
        
        temp_client = client_class(debug=debug)
        models = temp_client.get_available_model_ids()
        
        if debug:
            logger.debug("取得したモデル数: %d", len(models))
            logger.debug("最初の5個: %s", models[:5] if models else [])
        
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
        logger = logging.getLogger(__name__)
        if debug:
            logger.debug("get_model_details() 開始")
            logger.debug("プロバイダー: %s", provider)
        
        if provider not in cls._providers:
            error_msg = f"サポートされていないプロバイダー: {provider}"
            if debug:
                logger.debug("エラー: %s", error_msg)
            raise ValueError(error_msg)
        
        client_class = cls._providers[provider]
        
        if debug:
            logger.debug("一時クライアント作成: %s", client_class.__name__)
        
        temp_client = client_class(debug=debug)
        details = temp_client.list_available_models()
        
        if debug:
            logger.debug("取得したモデル詳細数: %d", len(details))
        
        return details