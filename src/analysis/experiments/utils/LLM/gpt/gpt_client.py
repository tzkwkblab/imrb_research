import os
import openai
from typing import Optional, List, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_llm import BaseLLM


class GPTClient(BaseLLM):
    """GPT APIクライアント"""
    
    def __init__(self, model: str = None, max_retries: int = 3):
        # 基底クラスで設定管理
        super().__init__(model, max_retries)
        
        # OpenAIクライアント初期化（環境変数からAPIキー取得）
        api_key = self.get_api_key('OPENAI_API_KEY')
        self.client = openai.OpenAI(api_key=api_key)
    
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
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    **params
                )
                return response.choices[0].message.content.strip()
            
            except Exception as e:
                print(f"GPT API エラー (試行 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    return None
        
        return None
    
    def get_model_name(self) -> str:
        return self.model