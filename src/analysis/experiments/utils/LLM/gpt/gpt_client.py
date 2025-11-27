import os
import sys
import openai
import base64
from typing import Optional, List, Dict, Tuple, Union
from datetime import datetime
from pathlib import Path
from ..base_llm import BaseLLM
import logging

# .envファイルを読み込む
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class GPTClient(BaseLLM):
    """GPT APIクライアント"""
    
    def __init__(self, model: str = None, max_retries: int = 3, debug: bool = False):
        # デバッグモード設定
        self.debug = debug
        self.logger = logging.getLogger(__name__)
        
        # OpenAIライブラリのHTTPログを無効化
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)
        
        # 基底クラスで設定管理
        super().__init__(model, max_retries)
        
        # OpenAIクライアント初期化（環境変数からAPIキー取得）
        api_key = self.get_api_key('OPENAI_API_KEY')
        self.client = openai.OpenAI(api_key=api_key)
        
        # モデル名の検証
        self._validate_model()
        
        if self.debug:
            self.logger.debug("GPTClient初期化完了 - モデル: %s", self.model)
    
    def _validate_model(self):
        """
        指定されたモデル名が利用可能かを検証
        不正な場合は利用可能なモデル一覧を表示してエラー終了
        """
        available_models = self.get_available_model_ids()
        
        if not available_models:
            print("エラー: 利用可能なモデル一覧を取得できませんでした")
            sys.exit(1)
        
        if self.model not in available_models:
            print(f"エラー: モデル '{self.model}' は利用できません")
            print("\n利用可能なモデル:")
            for model_id in available_models:
                print(f"  - {model_id}")
            sys.exit(1)
    
    def _is_reasoning_model(self) -> bool:
        """
        推論系モデル（O1/O3/GPT-5系）かどうかを判定
        
        Returns:
            推論系モデルの場合True
        """
        model_lower = self.model.lower()
        return (model_lower.startswith('o1') or 
                model_lower.startswith('o3') or 
                model_lower.startswith('gpt-5'))
    
    def _get_token_param_name(self) -> Tuple[str, bool]:
        """
        モデル名に応じたトークン制限パラメータ名を取得
        
        Returns:
            (パラメータ名, max_tokensを削除するか) のタプル
        """
        model_lower = self.model.lower()
        
        # D. 推論系 O1/O3/GPT-5: max_completion_tokens（必須）
        if self._is_reasoning_model():
            return ('max_completion_tokens', True)
        
        # A. 通常チャット（GPT-4o/Mini、GPT-4.1系含む）: max_tokens（そのまま）
        return ('max_tokens', False)
    
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
        # モデル名をparamsから除外（別途指定するため）
        params.pop('model', None)
        
        # モデル名に応じてパラメータ名を変換
        token_param_name, remove_max_tokens = self._get_token_param_name()
        
        # max_tokensが指定されている場合、適切なパラメータ名に変換
        if 'max_tokens' in params:
            token_value = params.pop('max_tokens')
            # 既に適切なパラメータ名が指定されていない場合のみ設定
            if token_param_name not in params:
                params[token_param_name] = token_value
        
        # 削除が必要な場合は、max_tokensが残っていないか確認
        if remove_max_tokens and 'max_tokens' in params:
            params.pop('max_tokens')
        
        # 推論系モデル（O1/O3/GPT-5系）ではtemperatureパラメータを削除
        # これらのモデルはtemperatureをサポートせず、デフォルト値（1）のみが使用可能
        if self._is_reasoning_model() and 'temperature' in params:
            params.pop('temperature')
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    **params
                )
                
                # choicesが空でないか確認
                if not response.choices or len(response.choices) == 0:
                    error_msg = "応答にchoicesが含まれていません"
                    if self.debug:
                        self.logger.debug("エラー: %s", error_msg)
                    print(f"GPT API エラー: {error_msg}")
                    if attempt == self.max_retries - 1:
                        return None
                    continue
                
                # messageが存在するか確認
                message = response.choices[0].message
                if not message:
                    error_msg = "応答にmessageが含まれていません"
                    if self.debug:
                        self.logger.debug("エラー: %s", error_msg)
                    print(f"GPT API エラー: {error_msg}")
                    if attempt == self.max_retries - 1:
                        return None
                    continue
                
                # finish_reasonを確認
                finish_reason = getattr(response.choices[0], 'finish_reason', None)
                
                # contentがNoneでないか確認
                content = message.content
                if content is None:
                    error_msg = f"応答のcontentがNoneです（finish_reason: {finish_reason}）"
                    print(f"GPT API エラー: {error_msg}")
                    if attempt == self.max_retries - 1:
                        return None
                    continue
                
                # contentが空文字列でないか確認
                content_str = content.strip()
                if not content_str:
                    # finish_reasonがlengthの場合、max_completion_tokensが小さすぎる可能性
                    if finish_reason == 'length':
                        error_msg = f"応答のcontentが空です（finish_reason: length - max_completion_tokensが小さすぎる可能性）"
                    else:
                        error_msg = f"応答のcontentが空です（finish_reason: {finish_reason}）"
                    
                    if self.debug and hasattr(response, 'usage'):
                        self.logger.debug("エラー: %s, usage: %s", error_msg, response.usage)
                    print(f"GPT API エラー: {error_msg}")
                    if attempt == self.max_retries - 1:
                        return None
                    continue
                
                return content_str
            
            except Exception as e:
                error_str = str(e)
                # コンテキスト長超過エラーの場合、リトライしても意味がないので即座にNoneを返す
                if 'context_length_exceeded' in error_str or 'maximum context length' in error_str.lower():
                    print(f"GPT API エラー（コンテキスト長超過）: {e}")
                    if self.debug:
                        self.logger.error("コンテキスト長超過エラー: プロンプトが長すぎます")
                    return None
                
                print(f"GPT API エラー (試行 {attempt + 1}/{self.max_retries}): {e}")
                if self.debug:
                    import traceback
                    self.logger.debug("エラー詳細: %s", traceback.format_exc())
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
            
            return model_data
            
        except Exception as e:
            print(f"モデル一覧取得エラー: {e}")
            return []
    
    def get_available_model_ids(self) -> List[str]:
        """
        利用可能なモデルIDのみを取得
        Returns:
            モデルIDのリスト ['gpt-4', 'gpt-3.5-turbo', ...]
        """
        models = self.list_available_models()
        return [model['id'] for model in models]
    
    def query_with_images(
        self, 
        messages: List[Dict], 
        image_urls: List[str] = None,
        image_paths: List[Union[str, Path]] = None,
        **kwargs
    ) -> Optional[str]:
        """
        画像を含むクエリをGPT-5.1に送信
        
        Args:
            messages: メッセージリスト
            image_urls: 画像URLのリスト（http://またはhttps://）
            image_paths: ローカル画像ファイルパスのリスト
            **kwargs: その他のパラメータ（max_completion_tokens等）
        
        Returns:
            応答文字列
        """
        if not self._supports_vision():
            raise ValueError(f"モデル {self.model} は画像入力に対応していません。GPT-4oまたはGPT-5（画像対応版）を使用してください。")
        
        messages_with_images = []
        
        for msg in messages:
            if msg['role'] == 'user' and (image_urls or image_paths):
                content = []
                
                # テキスト部分を追加
                if isinstance(msg['content'], str):
                    content.append({"type": "text", "text": msg['content']})
                elif isinstance(msg['content'], list):
                    for item in msg['content']:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            content.append(item)
                        elif isinstance(item, str):
                            content.append({"type": "text", "text": item})
                
                # 画像URLを追加
                if image_urls:
                    for url in image_urls:
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": url}
                        })
                
                # ローカル画像をbase64エンコードして追加
                if image_paths:
                    for img_path in image_paths:
                        base64_image = self._encode_image(img_path)
                        if base64_image:
                            image_format = self._detect_image_format(img_path)
                            content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_format};base64,{base64_image}"
                                }
                            })
                
                messages_with_images.append({
                    "role": msg['role'],
                    "content": content
                })
            else:
                messages_with_images.append(msg)
        
        # 推論モデルの場合はmax_completion_tokensを設定（GPT-5.1の場合は100000）
        if self._is_reasoning_model():
            if 'max_completion_tokens' not in kwargs and 'max_tokens' not in kwargs:
                model_lower = self.model.lower()
                if model_lower.startswith('gpt-5'):
                    kwargs['max_completion_tokens'] = 100000
                else:
                    kwargs['max_completion_tokens'] = 8000
        
        return self.query(messages_with_images, **kwargs)
    
    def _supports_vision(self) -> bool:
        """画像入力に対応するモデルかどうかを判定"""
        model_lower = self.model.lower()
        
        # 推論モデル（o1/o3）は画像入力に対応していない
        if model_lower.startswith('o1') or model_lower.startswith('o3'):
            return False
        
        # GPT-4o系は画像入力に対応
        vision_models = ['gpt-4o', 'gpt-4-turbo', 'gpt-4-vision']
        if any(model_lower.startswith(m) for m in vision_models):
            return True
        
        # GPT-5系の場合、推論モデルでなければ画像入力に対応している可能性
        if model_lower.startswith('gpt-5'):
            return True
        
        return False
    
    def _encode_image(self, image_path: Union[str, Path]) -> Optional[str]:
        """画像ファイルをbase64エンコード"""
        try:
            image_path = Path(image_path)
            if not image_path.exists():
                self.logger.error(f"画像ファイルが見つかりません: {image_path}")
                return None
            
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            self.logger.error(f"画像エンコードエラー: {e}")
            return None
    
    def _detect_image_format(self, image_path: Union[str, Path]) -> str:
        """画像ファイルの形式を検出"""
        image_path = Path(image_path)
        suffix = image_path.suffix.lower()
        
        format_map = {
            '.jpg': 'jpeg',
            '.jpeg': 'jpeg',
            '.png': 'png',
            '.gif': 'gif',
            '.webp': 'webp'
        }
        
        return format_map.get(suffix, 'jpeg')