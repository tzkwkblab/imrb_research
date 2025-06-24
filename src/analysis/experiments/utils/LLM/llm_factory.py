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
        if debug:
            print(f"[DEBUG] LLMFactory.create_client() 開始")
            print(f"[DEBUG] 引数 model_name: {model_name}")
            print(f"[DEBUG] 引数 debug: {debug}")
            print(f"[DEBUG] 追加パラメータ: {kwargs}")
        
        # model_nameがNoneの場合は設定ファイルから取得
        if model_name is None:
            if debug:
                print(f"[DEBUG] モデル名未指定 - 設定ファイルから取得開始")
            
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../conf'))
            from experiment_config import get_config_manager
            
            config_manager = get_config_manager()
            model_name = config_manager.get_value('model', 'gpt-4')
            
            if debug:
                print(f"[DEBUG] 設定ファイルから取得したモデル: {model_name}")
                # 他の設定も表示
                try:
                    model_config = config_manager.get_model_config()
                    print(f"[DEBUG] 設定詳細:")
                    print(f"[DEBUG]   temperature: {model_config.temperature}")
                    print(f"[DEBUG]   system_prompt: {model_config.system_prompt[:50]}...")
                except Exception as e:
                    if debug:
                        print(f"[DEBUG] 設定詳細取得エラー: {e}")
        
        # プロバイダーを推定してクライアントクラスを取得
        if debug:
            print(f"[DEBUG] クライアントクラス推定開始: {model_name}")
        
        client_class = cls._get_client_class(model_name, debug=debug)
        
        if debug:
            print(f"[DEBUG] 決定されたクライアントクラス: {client_class.__name__}")
            print(f"[DEBUG] クライアントインスタンス作成開始")
        
        # debugパラメータをkwargsに追加
        kwargs['debug'] = debug
        client = client_class(model=model_name, **kwargs)
        
        if debug:
            print(f"[DEBUG] クライアントインスタンス作成完了")
            print(f"[DEBUG] 作成されたクライアントのモデル: {client.get_model_name()}")
        
        return client
    
    @classmethod
    def _get_client_class(cls, model_name: str, debug: bool = False) -> Type[BaseLLM]:
        """モデル名からクライアントクラスを推定"""
        if debug:
            print(f"[DEBUG] クライアントクラス推定: {model_name}")
            print(f"[DEBUG] GPTプレフィックス: {cls._gpt_prefixes}")
        
        # GPTモデルの場合
        for prefix in cls._gpt_prefixes:
            if model_name.startswith(prefix):
                if debug:
                    print(f"[DEBUG] GPTモデルと判定: プレフィックス '{prefix}' にマッチ")
                return cls._providers['openai']
        
        # デフォルトでGPTClientを使用
        if debug:
            print(f"[DEBUG] プレフィックスにマッチしないため、デフォルトでGPTClientを使用")
        
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
        if debug:
            print(f"[DEBUG] get_supported_models() 開始")
            print(f"[DEBUG] プロバイダー: {provider}")
        
        if provider not in cls._providers:
            error_msg = f"サポートされていないプロバイダー: {provider}"
            if debug:
                print(f"[DEBUG] エラー: {error_msg}")
            raise ValueError(error_msg)
        
        # 一時的にクライアントを作成してモデル一覧を取得
        client_class = cls._providers[provider]
        
        if debug:
            print(f"[DEBUG] 一時クライアント作成: {client_class.__name__}")
        
        temp_client = client_class(debug=debug)
        models = temp_client.get_available_model_ids()
        
        if debug:
            print(f"[DEBUG] 取得したモデル数: {len(models)}")
            print(f"[DEBUG] 最初の5個: {models[:5] if models else []}")
        
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
        if debug:
            print(f"[DEBUG] get_model_details() 開始")
            print(f"[DEBUG] プロバイダー: {provider}")
        
        if provider not in cls._providers:
            error_msg = f"サポートされていないプロバイダー: {provider}"
            if debug:
                print(f"[DEBUG] エラー: {error_msg}")
            raise ValueError(error_msg)
        
        client_class = cls._providers[provider]
        
        if debug:
            print(f"[DEBUG] 一時クライアント作成: {client_class.__name__}")
        
        temp_client = client_class(debug=debug)
        details = temp_client.list_available_models()
        
        if debug:
            print(f"[DEBUG] 取得したモデル詳細数: {len(details)}")
        
        return details