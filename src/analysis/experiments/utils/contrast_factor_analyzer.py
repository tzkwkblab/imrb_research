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
from prompt_contrast_factor import generate_contrast_factor_prompt
from LLM.llm_factory import LLMFactory
from get_score import calculate_scores, calculate_scores_with_descriptions
from aspect_description_manager import AspectDescriptionManager


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
        if self.debug:
            print(f"[DEBUG] Step 4: 結果保存")
        
        output_path = self._save_results(result, output_dir, experiment_name, timestamp)
        result["output_file"] = output_path
        
        if self.debug:
            print(f"[DEBUG] 結果保存完了: {output_path}")
        
        return result
    
    def _assess_quality(self, bert_score: float, bleu_score: float) -> Dict:
        """スコアに基づく品質評価"""
        
        # しきい値設定
        bert_thresholds = {"high": 0.8, "medium": 0.6}
        bleu_thresholds = {"high": 0.6, "medium": 0.3}
        
        # 品質レベル判定
        bert_level = "high" if bert_score >= bert_thresholds["high"] else \
                    "medium" if bert_score >= bert_thresholds["medium"] else "low"
        
        bleu_level = "high" if bleu_score >= bleu_thresholds["high"] else \
                    "medium" if bleu_score >= bleu_thresholds["medium"] else "low"
        
        # 総合評価
        if bert_level == "high" and bleu_level in ["high", "medium"]:
            overall = "excellent"
        elif bert_level in ["high", "medium"] and bleu_level in ["high", "medium"]:
            overall = "good"
        elif bert_level in ["medium", "high"] or bleu_level in ["medium", "high"]:
            overall = "fair"
        else:
            overall = "poor"
        
        return {
            "bert_level": bert_level,
            "bleu_level": bleu_level,
            "overall_quality": overall,
            "comments": f"BERT:{bert_level}, BLEU:{bleu_level} → 総合:{overall}"
        }
    
    def _save_results(self, result: Dict, output_dir: str, experiment_name: str, timestamp: str) -> str:
        """結果をJSONファイルに保存"""
        
        # 出力ディレクトリ作成
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # ファイル名生成
        if experiment_name:
            filename = f"{experiment_name}_{timestamp}.json"
        else:
            filename = f"contrast_analysis_{timestamp}.json"
        
        output_path = os.path.join(output_dir, filename)
        
        # JSON保存
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return output_path
    
    def analyze_batch(
        self,
        experiments: List[Dict],
        output_dir: str,
        base_experiment_name: str = "batch_analysis"
    ) -> List[Dict]:
        """
        複数実験のバッチ実行
        
        Args:
            experiments: 実験設定のリスト
                [{"group_a": [...], "group_b": [...], "correct_answer": "...", ...}, ...]
            output_dir: 結果保存ディレクトリ
            base_experiment_name: 基本実験名
            
        Returns:
            各実験結果のリスト
        """
        if self.debug:
            print(f"[DEBUG] バッチ分析開始: {len(experiments)}件")
        
        results = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, exp in enumerate(experiments, 1):
            if self.debug:
                print(f"[DEBUG] 実験 {i}/{len(experiments)} 実行中")
            
            experiment_name = f"{base_experiment_name}_{i:02d}"
            
            try:
                result = self.analyze(
                    output_dir=output_dir,
                    experiment_name=experiment_name,
                    **exp
                )
                results.append(result)
                
            except Exception as e:
                error_result = {
                    "experiment_info": {"experiment_name": experiment_name, "error": str(e)},
                    "summary": {"success": False, "error": str(e)}
                }
                results.append(error_result)
                
                if self.debug:
                    print(f"[DEBUG] 実験 {i} でエラー: {e}")
        
        # バッチ結果サマリー保存
        batch_summary = {
            "batch_info": {
                "timestamp": timestamp,
                "total_experiments": len(experiments),
                "successful_experiments": sum(1 for r in results if r.get("summary", {}).get("success", False)),
                "base_experiment_name": base_experiment_name
            },
            "results": results
        }
        
        summary_path = os.path.join(output_dir, f"{base_experiment_name}_summary_{timestamp}.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(batch_summary, f, ensure_ascii=False, indent=2)
        
        if self.debug:
            print(f"[DEBUG] バッチ分析完了: {summary_path}")
        
        return results


def main():
    """テスト実行"""
    print("=== 対比因子分析統合ツール テスト ===")
    
    # テストデータ
    group_a = [
        "Great battery life lasting all day",
        "Excellent power management features",
        "Long-lasting battery performance"
    ]
    
    group_b = [
        "Poor screen quality and resolution",
        "Uncomfortable keyboard layout",
        "Slow system performance"
    ]
    
    correct_answer = "Battery performance and power management"
    
    # Few-shot例題
    examples = [
        {
            "group_a": ["Fast delivery", "Quick shipping"],
            "group_b": ["Slow response", "Delayed support"],
            "answer": "Delivery speed and response time"
        }
    ]
    
    # 分析実行
    analyzer = ContrastFactorAnalyzer(debug=True)
    
    print("\n--- 単一実験テスト ---")
    result = analyzer.analyze(
        group_a=group_a,
        group_b=group_b,
        correct_answer=correct_answer,
        output_dir="test_results/",
        examples=examples,
        experiment_name="test_battery_vs_screen"
    )
    
    print(f"\n結果サマリー:")
    print(f"  BERTスコア: {result['evaluation']['bert_score']:.4f}")
    print(f"  BLEUスコア: {result['evaluation']['bleu_score']:.4f}")
    print(f"  品質評価: {result['summary']['quality_assessment']['overall_quality']}")
    print(f"  出力ファイル: {result['output_file']}")
    
    print("\n--- バッチ実験テスト ---")
    batch_experiments = [
        {
            "group_a": group_a,
            "group_b": group_b,
            "correct_answer": correct_answer,
            "examples": examples
        },
        {
            "group_a": ["High quality materials", "Durable construction"],
            "group_b": ["Cheap plastic", "Fragile design"],
            "correct_answer": "Material quality and build durability"
        }
    ]
    
    batch_results = analyzer.analyze_batch(
        experiments=batch_experiments,
        output_dir="test_results/",
        base_experiment_name="batch_test"
    )
    
    print(f"\nバッチ結果: {len(batch_results)}件処理完了")


if __name__ == "__main__":
    main() 