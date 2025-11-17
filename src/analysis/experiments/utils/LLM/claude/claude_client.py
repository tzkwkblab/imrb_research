import os
from typing import Optional, List, Dict
from datetime import datetime
from ..base_llm import BaseLLM
import logging

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


class ClaudeClient(BaseLLM):
    """Claude APIクライアント"""
    
    def __init__(self, model: str = None, max_retries: int = 3, debug: bool = False):
        if Anthropic is None:
            raise ImportError("anthropicパッケージがインストールされていません。pip install anthropic を実行してください。")
        
        self.debug = debug
        self.logger = logging.getLogger(__name__)
        
        if self.debug:
            self.logger.debug("ClaudeClient初期化開始")
            self.logger.debug("引数 model: %s", model)
            self.logger.debug("引数 max_retries: %s", max_retries)
        
        super().__init__(model, max_retries)
        
        if self.debug:
            self.logger.debug("基底クラス初期化後のモデル: %s", self.model)
        
        api_key = self.get_api_key('ANTHROPIC_API_KEY')
        self.client = Anthropic(api_key=api_key)
        
        if self.debug:
            self.logger.debug("Anthropicクライアント初期化完了")
        
        self._validate_model()
        
        if self.debug:
            self.logger.debug("ClaudeClient初期化完了 - 最終モデル: %s", self.model)
    
    def _validate_model(self):
        """指定されたモデル名が利用可能かを検証"""
        if self.debug:
            self.logger.debug("モデル検証開始: %s", self.model)
        
        available_models = self.get_available_model_ids()
        
        if self.debug:
            self.logger.debug("利用可能モデル数: %d", len(available_models))
            if available_models:
                self.logger.debug("利用可能モデル（最初の5個）: %s", available_models[:5])
        
        if not available_models:
            self.logger.warning("利用可能なモデル一覧を取得できませんでした。モデル名の検証をスキップします。")
            return
        
        if self.model not in available_models:
            self.logger.warning("モデル '%s' が利用可能モデル一覧に見つかりません", self.model)
            self.logger.warning("利用可能なモデル（最初の10個）: %s", available_models[:10])
    
    def query(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """
        Claude APIにクエリを送信
        
        Args:
            messages: メッセージリスト [{'role': 'user', 'content': '...'}, ...]
            **kwargs: temperature, max_tokens等
        
        Returns:
            応答文字列（失敗時はNone）
        """
        params = self.get_default_params(**kwargs)
        params.pop('model', None)
        
        if self.debug:
            safe_params = {k: v for k, v in params.items() if k not in ('api_key', 'headers')}
            self.logger.debug("API呼び出し開始")
            self.logger.debug("使用モデル: %s", self.model)
            self.logger.debug("パラメータ: %s", safe_params)
            self.logger.debug("メッセージ数: %d", len(messages))
        
        # Claude API用にメッセージを変換
        # Claudeはsystemメッセージをサポートしている
        system_message = None
        claude_messages = []
        
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'system':
                system_message = content
            elif role in ('user', 'assistant'):
                claude_messages.append({
                    'role': role,
                    'content': content
                })
        
        for attempt in range(self.max_retries):
            try:
                request_params = {
                    'model': self.model,
                    'messages': claude_messages,
                    'temperature': params.get('temperature', 0.7),
                    'max_tokens': params.get('max_tokens', 1000),
                }
                
                if system_message:
                    request_params['system'] = system_message
                
                response = self.client.messages.create(**request_params)
                
                if self.debug:
                    self.logger.debug("API呼び出し成功 (試行 %d)", attempt + 1)
                
                # Claude APIの応答からテキストを取得
                if response.content and len(response.content) > 0:
                    result_text = response.content[0].text
                else:
                    result_text = ""
                
                if self.debug:
                    self.logger.debug("応答長: %d 文字", len(result_text))
                
                return result_text.strip()
            
            except Exception as e:
                error_msg = f"Claude API エラー (試行 {attempt + 1}/{self.max_retries}): {e}"
                print(error_msg)
                if self.debug:
                    self.logger.debug("エラー詳細: %s: %s", type(e).__name__, e)
                if attempt == self.max_retries - 1:
                    return None
        
        return None
    
    def get_model_name(self) -> str:
        return self.model
    
    def list_available_models(self) -> List[Dict[str, str]]:
        """
        Claude APIから利用可能なモデル一覧を取得
        
        Returns:
            モデル情報のリスト [{'id': 'claude-3-haiku-20240307', ...}, ...]
        """
        try:
            if self.debug:
                self.logger.debug("モデル一覧取得開始")
            
            # Anthropic APIはモデル一覧を直接取得するAPIがないため、
            # 一般的なモデル名のリストを返す
            # 実際の利用可能性はAPI呼び出し時に検証される
            common_models = [
                'claude-3-haiku-20240307',
                'claude-3-sonnet-20240229',
                'claude-3-opus-20240229',
                'claude-3-5-sonnet-20240620',
                'claude-3-5-haiku-20241022',
                'claude-3-5-sonnet-20241022',
                'claude-sonnet-4-5-20250929',
                'claude-opus-4-1-20250805',
            ]
            
            model_data = []
            for model_id in common_models:
                model_data.append({
                    'id': model_id,
                    'display_name': model_id,
                })
            
            if self.debug:
                self.logger.debug("モデル一覧取得完了: %d個", len(model_data))
            
            return model_data
            
        except Exception as e:
            error_msg = f"モデル一覧取得エラー: {e}"
            print(error_msg)
            if self.debug:
                self.logger.debug("モデル一覧取得エラー詳細: %s: %s", type(e).__name__, e)
            return []
    
    def get_available_model_ids(self) -> List[str]:
        """
        利用可能なモデルIDのみを取得
        
        Returns:
            モデルIDのリスト ['claude-3-haiku-20240307', ...]
        """
        models = self.list_available_models()
        return [model['id'] for model in models]

