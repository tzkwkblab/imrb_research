import os
import openai
from typing import Optional, List, Dict
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_llm import BaseLLM


class GPTClient(BaseLLM):
    """GPT APIクライアント"""
    
    def __init__(self, model: str = None, max_retries: int = 3, debug: bool = False):
        # デバッグモード設定
        self.debug = debug
        
        if self.debug:
            print(f"[DEBUG] GPTClient初期化開始")
            print(f"[DEBUG] 引数 model: {model}")
            print(f"[DEBUG] 引数 max_retries: {max_retries}")
        
        # 基底クラスで設定管理
        super().__init__(model, max_retries)
        
        if self.debug:
            print(f"[DEBUG] 基底クラス初期化後のモデル: {self.model}")
        
        # OpenAIクライアント初期化（環境変数からAPIキー取得）
        api_key = self.get_api_key('OPENAI_API_KEY')
        self.client = openai.OpenAI(api_key=api_key)
        
        if self.debug:
            print(f"[DEBUG] OpenAIクライアント初期化完了")
        
        # モデル名の検証
        self._validate_model()
        
        if self.debug:
            print(f"[DEBUG] GPTClient初期化完了 - 最終モデル: {self.model}")
    
    def _validate_model(self):
        """
        指定されたモデル名が利用可能かを検証
        不正な場合は利用可能なモデル一覧を表示してエラー終了
        """
        if self.debug:
            print(f"[DEBUG] モデル検証開始: {self.model}")
        
        available_models = self.get_available_model_ids()
        
        if self.debug:
            print(f"[DEBUG] 利用可能モデル数: {len(available_models)}")
            print(f"[DEBUG] 利用可能モデル（最初の5個）: {available_models[:5]}")
        
        if not available_models:
            print("エラー: 利用可能なモデル一覧を取得できませんでした")
            sys.exit(1)
        
        if self.model not in available_models:
            print(f"エラー: モデル '{self.model}' は利用できません")
            print("\n利用可能なモデル:")
            for model_id in available_models:
                print(f"  - {model_id}")
            sys.exit(1)
        
        if self.debug:
            print(f"[DEBUG] モデル検証成功: {self.model}")
    
    def query(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """
        GPT APIにクエリを送信
        Args:
            messages: メッセージリスト [{'role': 'user', 'content': '...'}, ...]
            **kwargs: temperature, max_tokens等
        Returns:
            応答文字列（失敗時はNone）
        """
        # 基底クラスからデフォルトパラメータを取得
        params = self.get_default_params(**kwargs)
        
        if self.debug:
            print(f"[DEBUG] API呼び出し開始")
            print(f"[DEBUG] 使用モデル: {self.model}")
            print(f"[DEBUG] パラメータ: {params}")
            print(f"[DEBUG] メッセージ数: {len(messages)}")
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    **params
                )
                
                if self.debug:
                    print(f"[DEBUG] API呼び出し成功 (試行 {attempt + 1})")
                    print(f"[DEBUG] 応答長: {len(response.choices[0].message.content)} 文字")
                
                return response.choices[0].message.content.strip()
            
            except Exception as e:
                print(f"GPT API エラー (試行 {attempt + 1}/{self.max_retries}): {e}")
                if self.debug:
                    print(f"[DEBUG] エラー詳細: {type(e).__name__}: {e}")
                if attempt == self.max_retries - 1:
                    return None
        
        return None
    
    def get_model_name(self) -> str:
        return self.model
    
    def list_available_models(self) -> List[Dict[str, str]]:
        """
        OpenAI APIから利用可能なモデル一覧を取得
        Returns:
            モデル情報のリスト [{'id': 'gpt-4', 'created': '2023-03-14', 'owned_by': 'openai'}, ...]
        """
        try:
            if self.debug:
                print(f"[DEBUG] モデル一覧取得開始")
            
            models = self.client.models.list()
            model_data = []
            
            for model in models.data:
                model_data.append({
                    'id': model.id,
                    'created': datetime.fromtimestamp(model.created).strftime('%Y-%m-%d'),
                    'object': model.object,
                    'owned_by': model.owned_by
                })
            
            # 作成日時で降順ソート（新しい順）
            model_data.sort(key=lambda x: x['created'], reverse=True)
            
            if self.debug:
                print(f"[DEBUG] モデル一覧取得完了: {len(model_data)}個")
            
            return model_data
            
        except Exception as e:
            print(f"モデル一覧取得エラー: {e}")
            if self.debug:
                print(f"[DEBUG] モデル一覧取得エラー詳細: {type(e).__name__}: {e}")
            return []
    
    def get_available_model_ids(self) -> List[str]:
        """
        利用可能なモデルIDのみを取得
        Returns:
            モデルIDのリスト ['gpt-4', 'gpt-3.5-turbo', ...]
        """
        models = self.list_available_models()
        return [model['id'] for model in models]