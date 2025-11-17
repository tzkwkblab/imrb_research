import os
from typing import Optional, List, Dict
from datetime import datetime
from ..base_llm import BaseLLM
import logging

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class GeminiClient(BaseLLM):
    """Gemini APIクライアント"""
    
    def __init__(self, model: str = None, max_retries: int = 3, debug: bool = False):
        if genai is None:
            raise ImportError("google-generativeaiパッケージがインストールされていません。pip install google-generativeai を実行してください。")
        
        self.debug = debug
        self.logger = logging.getLogger(__name__)
        
        if self.debug:
            self.logger.debug("GeminiClient初期化開始")
            self.logger.debug("引数 model: %s", model)
            self.logger.debug("引数 max_retries: %s", max_retries)
        
        super().__init__(model, max_retries)
        
        if self.debug:
            self.logger.debug("基底クラス初期化後のモデル: %s", self.model)
        
        api_key = self.get_api_key('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        
        if self.debug:
            self.logger.debug("Gemini API設定完了")
        
        self._validate_model()
        
        if self.debug:
            self.logger.debug("GeminiClient初期化完了 - 最終モデル: %s", self.model)
    
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
        Gemini APIにクエリを送信
        
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
        
        # Gemini API用にメッセージを変換
        # Geminiはsystemメッセージを直接サポートしていないため、最初のuserメッセージに統合
        prompt_parts = []
        system_message = None
        
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'system':
                system_message = content
            elif role == 'user':
                if system_message:
                    prompt_parts.append(f"{system_message}\n\n{content}")
                    system_message = None
                else:
                    prompt_parts.append(content)
            elif role == 'assistant':
                prompt_parts.append(content)
        
        # モデルを取得
        try:
            model_instance = genai.GenerativeModel(self.model)
        except Exception as e:
            self.logger.error("モデルインスタンス作成エラー: %s", e)
            return None
        
        for attempt in range(self.max_retries):
            try:
                generation_config = {
                    'temperature': params.get('temperature', 0.7),
                    'max_output_tokens': params.get('max_tokens', 1000),
                }
                
                response = model_instance.generate_content(
                    prompt_parts,
                    generation_config=generation_config
                )
                
                if self.debug:
                    self.logger.debug("API呼び出し成功 (試行 %d)", attempt + 1)
                
                result_text = response.text if hasattr(response, 'text') else str(response)
                
                if self.debug:
                    self.logger.debug("応答長: %d 文字", len(result_text))
                
                return result_text.strip()
            
            except Exception as e:
                error_msg = f"Gemini API エラー (試行 {attempt + 1}/{self.max_retries}): {e}"
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
        Gemini APIから利用可能なモデル一覧を取得
        
        Returns:
            モデル情報のリスト [{'id': 'gemini-1.5-flash', ...}, ...]
        """
        try:
            if self.debug:
                self.logger.debug("モデル一覧取得開始")
            
            models = genai.list_models()
            model_data = []
            
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    model_data.append({
                        'id': model.name.split('/')[-1],
                        'display_name': model.display_name,
                        'description': model.description or '',
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
            モデルIDのリスト ['gemini-1.5-flash', ...]
        """
        models = self.list_available_models()
        return [model['id'] for model in models]

