#!/usr/bin/env python3
"""
LLM評価スコア計算

参照テキストと候補テキストの意味的類似度をLLMで評価
"""

import json
import logging
import asyncio
from typing import Tuple, List, Optional, Dict, Any
import sys
from pathlib import Path
import os

# LLMクライアントのインポート
try:
    from ..LLM.llm_factory import LLMFactory
except ImportError:
    # フォールバック
    sys.path.append(str(Path(__file__).parent.parent))
    from LLM.llm_factory import LLMFactory

logger = logging.getLogger(__name__)


def _create_evaluation_prompt(reference_text: str, candidate_text: str) -> str:
    """
    LLM評価用プロンプト生成
    
    Args:
        reference_text: 参照テキスト
        candidate_text: 候補テキスト
        
    Returns:
        評価プロンプト
    """
    prompt = f"""参照テキストと候補テキストの意味的類似度を5段階（1-5）で評価してください。

参照テキスト: {reference_text}

候補テキスト: {candidate_text}

評価基準:
- 5: 完全に同じ意味
- 4: ほぼ同じ意味（細かい違いのみ）
- 3: 類似しているが一部異なる
- 2: 部分的に類似している
- 1: ほとんど異なる

出力形式（JSON形式）:
{{
    "score": 4,
    "normalized_score": 0.8,
    "reasoning": "評価理由を簡潔に説明"
}}

score: 1-5の整数スコア
normalized_score: 0.0-1.0に正規化したスコア（score/5.0）
reasoning: 評価理由の説明（50文字以内）

JSON形式のみで回答してください。"""
    return prompt


def calculate_llm_score(
    reference_text: str,
    candidate_text: str,
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.0,
    timeout: int = 30,
    max_retries: int = 3
) -> Optional[Dict[str, Any]]:
    """
    LLMでテキストペアの評価スコアを計算
    
    Args:
        reference_text: 参照テキスト
        candidate_text: 候補テキスト
        model_name: 使用するLLMモデル名
        temperature: 温度パラメータ（デフォルト0.0）
        timeout: タイムアウト秒数（デフォルト30秒）
        max_retries: 最大リトライ回数
        
    Returns:
        評価結果辞書 {"score": int, "normalized_score": float, "reasoning": str}
        失敗時はNone
    """
    if not reference_text.strip() or not candidate_text.strip():
        logger.warning("空のテキストが渡されました")
        return None
    
    try:
        # LLMクライアント作成
        client = LLMFactory.create_client(model_name=model_name, debug=False)
        
        # プロンプト生成
        prompt = _create_evaluation_prompt(reference_text, candidate_text)
        
        # LLM問い合わせ
        response = client.ask(
            prompt,
            temperature=temperature,
            max_tokens=200
        )
        
        if response is None:
            logger.warning("LLMからの応答が取得できませんでした")
            return None
        
        # JSON解析
        try:
            # JSON部分を抽出（```json ... ``` や ``` ... ``` を除去）
            response_clean = response.strip()
            if response_clean.startswith("```"):
                # コードブロックを除去
                lines = response_clean.split("\n")
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith("```json") or line.strip().startswith("```"):
                        in_json = True
                        continue
                    if in_json and line.strip().startswith("```"):
                        break
                    if in_json:
                        json_lines.append(line)
                response_clean = "\n".join(json_lines)
            
            result = json.loads(response_clean)
            
            # バリデーション
            if "score" not in result or "normalized_score" not in result:
                # scoreからnormalized_scoreを計算
                if "score" in result:
                    score = int(result["score"])
                    result["normalized_score"] = float(score / 5.0)
                else:
                    logger.warning("評価結果にscoreが含まれていません")
                    return None
            
            # 型変換と検証
            result["score"] = int(result["score"])
            result["normalized_score"] = float(result["normalized_score"])
            result["reasoning"] = str(result.get("reasoning", ""))
            
            # スコア範囲チェック
            if not (1 <= result["score"] <= 5):
                logger.warning(f"スコアが範囲外です: {result['score']}")
                return None
            
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析エラー: {e}, 応答: {response[:200]}")
            return None
            
    except Exception as e:
        logger.error(f"LLM評価エラー: {e}")
        return None


def calculate_llm_score_batch(
    text_pairs: List[Tuple[str, str]],
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.0,
    timeout: int = 30,
    max_retries: int = 3
) -> List[Optional[Dict[str, any]]]:
    """
    複数ペアのLLM評価をバッチ処理（同期版）
    
    Args:
        text_pairs: [(reference_text1, candidate_text1), ...] のリスト
        model_name: 使用するLLMモデル名
        temperature: 温度パラメータ
        timeout: タイムアウト秒数
        max_retries: 最大リトライ回数
        
    Returns:
        評価結果のリスト（失敗時はNone）
    """
    results = []
    for reference_text, candidate_text in text_pairs:
        result = calculate_llm_score(
            reference_text=reference_text,
            candidate_text=candidate_text,
            model_name=model_name,
            temperature=temperature,
            timeout=timeout,
            max_retries=max_retries
        )
        results.append(result)
    return results


async def calculate_llm_score_async(
    reference_text: str,
    candidate_text: str,
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.0,
    timeout: int = 30,
    max_retries: int = 3
) -> Optional[Dict[str, Any]]:
    """
    LLMでテキストペアの評価スコアを非同期計算
    
    Args:
        reference_text: 参照テキスト
        candidate_text: 候補テキスト
        model_name: 使用するLLMモデル名
        temperature: 温度パラメータ（デフォルト0.0）
        timeout: タイムアウト秒数（デフォルト30秒）
        max_retries: 最大リトライ回数
        
    Returns:
        評価結果辞書 {"score": int, "normalized_score": float, "reasoning": str}
        失敗時はNone
    """
    if not reference_text.strip() or not candidate_text.strip():
        logger.warning("空のテキストが渡されました")
        return None
    
    try:
        # OpenAI非同期クライアントを使用
        try:
            from openai import AsyncOpenAI
        except ImportError:
            logger.error("openaiパッケージがインストールされていません")
            return None
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY環境変数が設定されていません")
            return None
        
        client = AsyncOpenAI(api_key=api_key)
        
        # プロンプト生成
        prompt = _create_evaluation_prompt(reference_text, candidate_text)
        
        # 非同期LLM問い合わせ
        for attempt in range(max_retries):
            try:
                response = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        max_tokens=200
                    ),
                    timeout=timeout
                )
                
                response_text = response.choices[0].message.content.strip()
                
                # JSON解析
                try:
                    response_clean = response_text.strip()
                    if response_clean.startswith("```"):
                        lines = response_clean.split("\n")
                        json_lines = []
                        in_json = False
                        for line in lines:
                            if line.strip().startswith("```json") or line.strip().startswith("```"):
                                in_json = True
                                continue
                            if in_json and line.strip().startswith("```"):
                                break
                            if in_json:
                                json_lines.append(line)
                        response_clean = "\n".join(json_lines)
                    
                    result = json.loads(response_clean)
                    
                    # バリデーション
                    if "score" not in result:
                        logger.warning("評価結果にscoreが含まれていません")
                        return None
                    
                    if "normalized_score" not in result:
                        score = int(result["score"])
                        result["normalized_score"] = float(score / 5.0)
                    
                    # 型変換と検証
                    result["score"] = int(result["score"])
                    result["normalized_score"] = float(result["normalized_score"])
                    result["reasoning"] = str(result.get("reasoning", ""))
                    
                    # スコア範囲チェック
                    if not (1 <= result["score"] <= 5):
                        logger.warning(f"スコアが範囲外です: {result['score']}")
                        return None
                    
                    return result
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON解析エラー: {e}, 応答: {response_text[:200]}")
                    if attempt == max_retries - 1:
                        return None
                    continue
                    
            except asyncio.TimeoutError:
                logger.warning(f"タイムアウトエラー (試行 {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    return None
                continue
            except Exception as e:
                logger.warning(f"LLM API エラー (試行 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return None
                continue
        
        return None
        
    except Exception as e:
        logger.error(f"LLM評価エラー: {e}")
        return None


async def calculate_llm_score_batch_async(
    text_pairs: List[Tuple[str, str]],
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.0,
    timeout: int = 30,
    max_retries: int = 3,
    max_concurrent: int = 5
) -> List[Optional[Dict[str, any]]]:
    """
    複数ペアのLLM評価を非同期バッチ処理（並列実行）
    
    Args:
        text_pairs: [(reference_text1, candidate_text1), ...] のリスト
        model_name: 使用するLLMモデル名
        temperature: 温度パラメータ
        timeout: タイムアウト秒数
        max_retries: 最大リトライ回数
        max_concurrent: 同時実行数の上限（デフォルト5）
        
    Returns:
        評価結果のリスト（失敗時はNone）
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def evaluate_with_semaphore(reference_text: str, candidate_text: str):
        async with semaphore:
            return await calculate_llm_score_async(
                reference_text=reference_text,
                candidate_text=candidate_text,
                model_name=model_name,
                temperature=temperature,
                timeout=timeout,
                max_retries=max_retries
            )
    
    tasks = [
        evaluate_with_semaphore(ref, cand)
        for ref, cand in text_pairs
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 例外をNoneに変換
    final_results = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"非同期評価エラー: {result}")
            final_results.append(None)
        else:
            final_results.append(result)
    
    return final_results


def main():
    """テスト"""
    print("=== LLM評価スコアテスト ===")
    
    test_pairs = [
        ("技術的な詳細", "Includes technical details"),
        ("競合製品との比較", "Contains comparisons"),
        ("全く関係ない話", "Completely unrelated topic"),
    ]
    
    for reference, candidate in test_pairs:
        print(f"\n参照: {reference}")
        print(f"候補: {candidate}")
        
        result = calculate_llm_score(reference, candidate)
        if result:
            print(f"スコア: {result['score']}/5")
            print(f"正規化スコア: {result['normalized_score']:.4f}")
            print(f"理由: {result['reasoning']}")
        else:
            print("評価失敗")


if __name__ == "__main__":
    main()

