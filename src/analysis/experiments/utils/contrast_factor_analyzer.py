#!/usr/bin/env python3
"""
対比因子分析統合ツール

グループA・B・正解特徴を入力として、以下を自動実行:
1. プロンプト生成 (prompt_contrast_factor.py)
2. LLM問い合わせ (LLM/llm_factory.py)
3. スコア計算 (get_score.py)
4. 結果保存 (JSON形式)

# 最小限のコード例
from contrast_factor_analyzer import ContrastFactorAnalyzer

analyzer = ContrastFactorAnalyzer()
result = analyzer.analyze(
    group_a=["Great battery life", "Long-lasting battery"],
    group_b=["Poor screen quality", "Slow performance"],
    correct_answer="Battery performance and power management",
    output_dir="my_results/",
    examples=None  # Few-shot例題（任意）
)

print(f"スコア: BERT={result['evaluation']['bert_score']:.3f}")

"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# 必要なモジュールをインポート
try:
    from prompt_contrast_factor import generate_contrast_factor_prompt
    from LLM.llm_factory import LLMFactory
    from get_score import calculate_scores, calculate_scores_with_descriptions
    from aspect_description_manager import AspectDescriptionManager
except ImportError:
    # フォールバック: 絶対インポート
    from .prompt_contrast_factor import generate_contrast_factor_prompt
    from .LLM.llm_factory import LLMFactory
    from .get_score import calculate_scores, calculate_scores_with_descriptions
    from .aspect_description_manager import AspectDescriptionManager


class ContrastFactorAnalyzer:
    """対比因子分析統合クラス"""
    
    def __init__(self, debug: bool = False, use_aspect_descriptions: bool = False):
        """
        初期化
        Args:
            debug: デバッグモードの有効/無効
            use_aspect_descriptions: アスペクト説明文を使用するかどうか
        """
        self.debug = debug
        self.use_aspect_descriptions = use_aspect_descriptions
        self.llm_client = None
        self.aspect_manager = None
    
    def _get_llm_client(self):
        """LLMクライアントの遅延初期化"""
        if self.llm_client is None:
            self.llm_client = LLMFactory.create_client(debug=self.debug)
        return self.llm_client
    
    def analyze(
        self,
        group_a: List[str],
        group_b: List[str],
        correct_answer: str,
        output_dir: str,
        examples: Optional[List[Dict]] = None,
        output_language: Optional[str] = None,
        experiment_name: Optional[str] = None,
        dataset_path: Optional[str] = None
    ) -> Dict:
        """
        対比因子分析を実行
        
        Args:
            group_a: グループAのテキストリスト
            group_b: グループBのテキストリスト
            correct_answer: 正解となる特徴のテキスト
            output_dir: 結果保存ディレクトリ
            examples: Few-shot用例題リスト
            output_language: 出力言語
            experiment_name: 実験名（ファイル名用）
            dataset_path: データセットパス（アスペクト説明文使用時）
            
        Returns:
            分析結果辞書
        """
        if self.debug:
            print(f"[DEBUG] 対比因子分析開始")
            print(f"[DEBUG] グループA: {len(group_a)}件")
            print(f"[DEBUG] グループB: {len(group_b)}件")
            print(f"[DEBUG] 正解: {correct_answer}")
            print(f"[DEBUG] アスペクト説明文使用: {self.use_aspect_descriptions}")
        
        # アスペクト説明文管理クラス初期化
        if self.use_aspect_descriptions and dataset_path:
            self.aspect_manager = AspectDescriptionManager(dataset_path)
            if self.debug:
                print(f"[DEBUG] アスペクト説明文読み込み: {self.aspect_manager.has_descriptions()}")
        
        # タイムスタンプ生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. プロンプト生成
        if self.debug:
            print(f"[DEBUG] Step 1: プロンプト生成")
        
        prompt, model_config = generate_contrast_factor_prompt(
            group_a=group_a,
            group_b=group_b,
            output_language=output_language,
            examples=examples
        )
        
        if self.debug:
            print(f"[DEBUG] プロンプト長: {len(prompt)}文字")
            print(f"[DEBUG] モデル設定: {model_config}")
        
        # 2. LLM問い合わせ
        if self.debug:
            print(f"[DEBUG] Step 2: LLM問い合わせ")
        
        client = self._get_llm_client()
        llm_response = client.ask(prompt, **model_config)
        
        if llm_response is None:
            raise RuntimeError("LLMからの応答取得に失敗しました")
        
        if self.debug:
            print(f"[DEBUG] LLM応答: {llm_response}")
        
        # 3. スコア計算
        if self.debug:
            print(f"[DEBUG] Step 3: スコア計算")
        
        if self.use_aspect_descriptions and self.aspect_manager:
            bert_score, bleu_score = calculate_scores_with_descriptions(
                correct_answer, llm_response, self.aspect_manager, True
            )
            if self.debug:
                print(f"[DEBUG] 説明文使用: {self.aspect_manager.get_description(correct_answer)}")
        else:
            bert_score, bleu_score = calculate_scores(correct_answer, llm_response)
        
        if self.debug:
            print(f"[DEBUG] BERTスコア: {bert_score:.4f}")
            print(f"[DEBUG] BLEUスコア: {bleu_score:.4f}")
        
        # 4. 結果構造化
        result = {
            "experiment_info": {
                "timestamp": timestamp,
                "experiment_name": experiment_name or f"contrast_analysis_{timestamp}",
                "model_config": model_config,
                "input_data": {
                    "group_a_count": len(group_a),
                    "group_b_count": len(group_b),
                    "examples_count": len(examples) if examples else 0,
                    "output_language": output_language
                }
            },
            "input": {
                "group_a": group_a,
                "group_b": group_b,
                "correct_answer": correct_answer,
                "examples": examples
            },
            "process": {
                "prompt": prompt,
                "llm_response": llm_response
            },
            "evaluation": {
                "bert_score": bert_score,
                "bleu_score": bleu_score,
                "similarity_scores": {
                    "semantic_similarity": bert_score,
                    "lexical_similarity": bleu_score
                }
            },
            "summary": {
                "success": True,
                "quality_assessment": self._assess_quality(bert_score, bleu_score),
                "processing_time": timestamp
            }
        }
        
        # 5. 結果保存
        if output_dir:
            output_path = self._save_results(result, output_dir, experiment_name, timestamp)
            result["output_file"] = output_path
        
        return result
    
    def _assess_quality(self, bert_score: float, bleu_score: float) -> Dict:
        """品質評価"""
        avg_score = (bert_score + bleu_score) / 2
        
        if avg_score >= 0.8:
            quality = "excellent"
        elif avg_score >= 0.6:
            quality = "good"
        elif avg_score >= 0.4:
            quality = "fair"
        else:
            quality = "poor"
        
        return {
            "overall_quality": quality,
            "average_score": avg_score,
            "bert_quality": "high" if bert_score >= 0.7 else "medium" if bert_score >= 0.5 else "low",
            "bleu_quality": "high" if bleu_score >= 0.3 else "medium" if bleu_score >= 0.1 else "low"
        }
    
    def _save_results(self, result: Dict, output_dir: str, experiment_name: str, timestamp: str) -> str:
        """結果保存"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{experiment_name}_{timestamp}.json"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    def analyze_batch(
        self,
        experiments: List[Dict],
        output_dir: str,
        base_experiment_name: str = "batch_analysis"
    ) -> List[Dict]:
        """
        バッチ分析実行
        
        Args:
            experiments: 実験設定のリスト
            output_dir: 出力ディレクトリ
            base_experiment_name: 基本実験名
            
        Returns:
            分析結果のリスト
        """
        results = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, experiment in enumerate(experiments):
            try:
                experiment_name = f"{base_experiment_name}_{i+1}"
                
                result = self.analyze(
                    group_a=experiment['group_a'],
                    group_b=experiment['group_b'],
                    correct_answer=experiment['correct_answer'],
                    output_dir=output_dir,
                    examples=experiment.get('examples'),
                    output_language=experiment.get('output_language'),
                    experiment_name=experiment_name,
                    dataset_path=experiment.get('dataset_path')
                )
                
                results.append(result)
                
            except Exception as e:
                error_result = {
                    "experiment_info": {
                        "timestamp": timestamp,
                        "experiment_name": experiment_name,
                        "error": str(e)
                    },
                    "summary": {
                        "success": False,
                        "error": str(e)
                    }
                }
                results.append(error_result)
        
        # バッチ結果の統合保存
        batch_result = {
            "batch_info": {
                "timestamp": timestamp,
                "total_experiments": len(experiments),
                "successful_experiments": sum(1 for r in results if r['summary']['success']),
                "base_experiment_name": base_experiment_name
            },
            "results": results
        }
        
        batch_file = Path(output_dir) / f"{base_experiment_name}_batch_{timestamp}.json"
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(batch_result, f, ensure_ascii=False, indent=2)
        
        return results


def main():
    """メイン関数（テスト用）"""
    # テストデータ
    group_a = [
        "Great battery life",
        "Long-lasting battery",
        "Excellent power management"
    ]
    
    group_b = [
        "Poor screen quality",
        "Slow performance",
        "Bad user interface"
    ]
    
    correct_answer = "Battery performance and power management"
    
    # 分析実行
    analyzer = ContrastFactorAnalyzer(debug=True)
    result = analyzer.analyze(
        group_a=group_a,
        group_b=group_b,
        correct_answer=correct_answer,
        output_dir="test_results/"
    )
    
    print(f"分析結果:")
    print(f"BERTスコア: {result['evaluation']['bert_score']:.4f}")
    print(f"BLEUスコア: {result['evaluation']['bleu_score']:.4f}")
    print(f"品質評価: {result['summary']['quality_assessment']}")


if __name__ == "__main__":
    main()