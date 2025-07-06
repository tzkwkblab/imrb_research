#!/usr/bin/env python3
"""
PyABSAデータセット二項対比因子抽出実験

特定アスペクトを含むグループ vs 含まないグループでの対比因子抽出とスコア評価
例: "food"を含むレビュー vs "food"を含まないレビュー → 正解: "food"
"""

import os
import sys
import json
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
import logging

# ディレクトリ設定
current_dir = Path(__file__).parent
experiments_dir = current_dir.parent.parent.parent
utils_dir = experiments_dir / "utils"
sys.path.append(str(utils_dir))
sys.path.append(str(utils_dir / "LLM"))

# 必要なモジュールをインポート
from dataset_comparison_framework import PyABSADatasetLoader, ABSARecord
from contrast_factor_analyzer import ContrastFactorAnalyzer

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境変数設定
from dotenv import load_dotenv
load_dotenv()

class PyABSABinaryContrastExperiment:
    """PyABSAデータセット二項対比因子実験クラス"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.dataset_loader = PyABSADatasetLoader()
        self.analyzer = ContrastFactorAnalyzer(debug=debug)
        
        # 実験パラメータ
        self.group_size = 300  # 各グループのサンプル数
        self.random_seed = 42
        random.seed(self.random_seed)
        
        logger.info("PyABSA二項対比因子実験初期化完了")
    
    def prepare_binary_contrast_groups(
        self, 
        records: List[ABSARecord], 
        target_aspect: str
    ) -> Tuple[List[str], List[str], str]:
        """
        二項対比グループの準備
        
        Args:
            records: ABSAレコードリスト
            target_aspect: 対象アスペクト（例：food）
        
        Returns:
            group_a（対象アスペクトを含む）, group_b（含まない）, correct_answer
        """
        # アスペクトでフィルタリング
        group_a_records = [r for r in records if target_aspect.lower() in r.aspect.lower()]
        group_b_records = [r for r in records if target_aspect.lower() not in r.aspect.lower()]
        
        logger.info(f"アスペクト分割 - {target_aspect}含む: {len(group_a_records)}件, 含まない: {len(group_b_records)}件")
        
        # サンプル調整
        group_a_texts = self._adjust_sample_size([r.text for r in group_a_records], self.group_size)
        group_b_texts = self._adjust_sample_size([r.text for r in group_b_records], self.group_size)
        
        # 正解作成（対象アスペクト名そのもの）
        correct_answer = target_aspect
        
        return group_a_texts, group_b_texts, correct_answer
    
    def _adjust_sample_size(self, texts: List[str], target_size: int) -> List[str]:
        """サンプルサイズ調整"""
        if len(texts) >= target_size:
            return random.sample(texts, target_size)
        else:
            # 不足分は重複サンプリング
            multiplier = (target_size // len(texts)) + 1
            extended = texts * multiplier
            return random.sample(extended, target_size)
    
    def create_few_shot_examples(self, target_aspect: str, shot_count: int) -> List[Dict]:
        """Few-shot例題作成"""
        if shot_count == 0:
            return None
        
        # ドメイン特化例題パターン
        if target_aspect.lower() == "food":
            base_examples = [
                {
                    "group_a": ["Delicious pasta", "Great pizza", "Amazing dessert"],
                    "group_b": ["Slow service", "High prices", "Noisy atmosphere"],
                    "answer": "food"
                },
                {
                    "group_a": ["Fresh ingredients", "Tasty meal", "Excellent cuisine"],
                    "group_b": ["Poor location", "Uncomfortable seating", "Long wait times"],
                    "answer": "food"
                },
                {
                    "group_a": ["Flavorful dishes", "Quality ingredients", "Well-prepared food"],
                    "group_b": ["Rude staff", "Expensive drinks", "Cramped space"],
                    "answer": "food"
                }
            ]
        elif target_aspect.lower() == "service":
            base_examples = [
                {
                    "group_a": ["Attentive staff", "Friendly waiters", "Quick service"],
                    "group_b": ["Bland food", "High prices", "Poor location"],
                    "answer": "service"
                },
                {
                    "group_a": ["Professional service", "Helpful staff", "Excellent waiters"],
                    "group_b": ["Tasteless meals", "Expensive menu", "Bad atmosphere"],
                    "answer": "service"
                }
            ]
        else:
            # 汎用例題
            base_examples = [
                {
                    "group_a": [f"Great {target_aspect}", f"Excellent {target_aspect}", f"Amazing {target_aspect}"],
                    "group_b": ["Other aspects", "Different features", "Unrelated qualities"],
                    "answer": target_aspect
                }
            ]
        
        return base_examples[:shot_count]
    
    def run_experiment(
        self,
        dataset_id: str,
        target_aspects: List[str],
        shot_settings: List[int] = [0, 1, 3]
    ) -> Dict:
        """
        実験実行
        
        Args:
            dataset_id: データセットID
            target_aspects: 対象アスペクトリスト ["food", "service", "atmosphere"]
            shot_settings: Shot設定リスト [0, 1, 3]
        
        Returns:
            実験結果辞書
        """
        logger.info(f"実験開始: {dataset_id}")
        
        # データセット読み込み
        records = self.dataset_loader.load_dataset(dataset_id)
        logger.info(f"データ読み込み完了: {len(records)}件")
        
        # 実験設定
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_results = {
            "experiment_info": {
                "dataset_id": dataset_id,
                "timestamp": timestamp,
                "total_records": len(records),
                "target_aspects": target_aspects,
                "shot_settings": shot_settings,
                "group_size": self.group_size,
                "random_seed": self.random_seed,
                "experiment_type": "binary_contrast"
            },
            "results": []
        }
        
        # 実験ループ
        for target_aspect in target_aspects:
            logger.info(f"対象アスペクト処理: {target_aspect}")
            
            try:
                # 二項対比グループ準備
                group_a, group_b, correct_answer = self.prepare_binary_contrast_groups(
                    records, target_aspect
                )
                
                if len(group_a) < 10 or len(group_b) < 10:
                    logger.warning(f"サンプル数不足をスキップ: {target_aspect}")
                    continue
                
                # 各Shot設定で実験
                for shot_count in shot_settings:
                    logger.info(f"Shot設定: {shot_count}")
                    
                    # Few-shot例題準備
                    examples = self.create_few_shot_examples(target_aspect, shot_count)
                    
                    # 実験名
                    experiment_name = f"{dataset_id}_{target_aspect}_binary_{shot_count}shot"
                    
                    # 対比因子分析実行
                    try:
                        result = self.analyzer.analyze(
                            group_a=group_a,
                            group_b=group_b,
                            correct_answer=correct_answer,
                            output_dir=f"results/{dataset_id}_binary/",
                            examples=examples,
                            experiment_name=experiment_name
                        )
                        
                        # 結果記録
                        experiment_record = {
                            "target_aspect": target_aspect,
                            "shot_count": shot_count,
                            "group_sizes": {"group_a": len(group_a), "group_b": len(group_b)},
                            "bert_score": result["evaluation"]["bert_score"],
                            "bleu_score": result["evaluation"]["bleu_score"],
                            "quality_assessment": result["summary"]["quality_assessment"]["overall_quality"],
                            "llm_response": result["process"]["llm_response"],
                            "correct_answer": correct_answer,
                            "success": True
                        }
                        
                        experiment_results["results"].append(experiment_record)
                        
                        logger.info(f"実験完了 - BERT: {result['evaluation']['bert_score']:.3f}, BLEU: {result['evaluation']['bleu_score']:.3f}")
                        
                    except Exception as e:
                        logger.error(f"実験エラー ({shot_count}shot): {e}")
                        experiment_results["results"].append({
                            "target_aspect": target_aspect,
                            "shot_count": shot_count,
                            "error": str(e),
                            "success": False
                        })
            
            except Exception as e:
                logger.error(f"アスペクト処理エラー: {e}")
        
        # 統計サマリー追加
        experiment_results["summary"] = self._generate_summary(experiment_results["results"])
        
        return experiment_results
    
    def _generate_summary(self, results: List[Dict]) -> Dict:
        """実験結果サマリー生成"""
        successful_results = [r for r in results if r.get("success", False)]
        
        if not successful_results:
            return {"total_experiments": len(results), "successful_experiments": 0}
        
        bert_scores = [r["bert_score"] for r in successful_results]
        bleu_scores = [r["bleu_score"] for r in successful_results]
        
        # Shot別統計
        shot_stats = {}
        for shot in [0, 1, 3]:
            shot_results = [r for r in successful_results if r["shot_count"] == shot]
            if shot_results:
                shot_bert = [r["bert_score"] for r in shot_results]
                shot_bleu = [r["bleu_score"] for r in shot_results]
                shot_stats[f"{shot}shot"] = {
                    "count": len(shot_results),
                    "bert_avg": sum(shot_bert) / len(shot_bert),
                    "bleu_avg": sum(shot_bleu) / len(shot_bleu)
                }
        
        # アスペクト別統計
        aspect_stats = {}
        aspects = list(set(r["target_aspect"] for r in successful_results))
        for aspect in aspects:
            aspect_results = [r for r in successful_results if r["target_aspect"] == aspect]
            if aspect_results:
                aspect_bert = [r["bert_score"] for r in aspect_results]
                aspect_bleu = [r["bleu_score"] for r in aspect_results]
                aspect_stats[aspect] = {
                    "count": len(aspect_results),
                    "bert_avg": sum(aspect_bert) / len(aspect_bert),
                    "bleu_avg": sum(aspect_bleu) / len(aspect_bleu)
                }
        
        return {
            "total_experiments": len(results),
            "successful_experiments": len(successful_results),
            "bert_score_avg": sum(bert_scores) / len(bert_scores),
            "bleu_score_avg": sum(bleu_scores) / len(bleu_scores),
            "bert_score_range": [min(bert_scores), max(bert_scores)],
            "bleu_score_range": [min(bleu_scores), max(bleu_scores)],
            "shot_statistics": shot_stats,
            "aspect_statistics": aspect_stats
        }


def main():
    """メイン実行"""
    logger.info("PyABSA二項対比因子抽出実験開始")
    
    # 実験インスタンス作成
    experiment = PyABSABinaryContrastExperiment(debug=True)
    
    # 利用可能データセット確認
    datasets = experiment.dataset_loader.list_available_datasets()
    logger.info(f"利用可能データセット: {len(datasets)}件")
    
    # SemEvalデータセットで実験
    semeval_datasets = [d for d in datasets if 'SemEval' in d.name and d.record_count > 1000]
    
    if not semeval_datasets:
        logger.error("適切なSemEvalデータセットが見つかりません")
        return
    
    # レストランデータセットを使用
    restaurant_datasets = [d for d in semeval_datasets if 'restaurant' in d.name.lower()]
    if restaurant_datasets:
        target_dataset = restaurant_datasets[0]
    else:
        target_dataset = semeval_datasets[0]
    
    logger.info(f"実験対象データセット: {target_dataset.name} ({target_dataset.record_count}件)")
    
    # 対象アスペクト定義
    target_aspects = ["food", "service", "atmosphere", "price"]
    
    # 実験実行
    results = experiment.run_experiment(
        dataset_id=target_dataset.dataset_id,
        target_aspects=target_aspects,
        shot_settings=[0, 1, 3]
    )
    
    # 結果保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"pyabsa_binary_contrast_experiment_results_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 結果表示
    logger.info("=" * 60)
    logger.info("実験結果サマリー")
    logger.info("=" * 60)
    
    summary = results["summary"]
    logger.info(f"総実験数: {summary['total_experiments']}")
    logger.info(f"成功実験数: {summary['successful_experiments']}")
    
    if summary["successful_experiments"] > 0:
        logger.info(f"平均BERTスコア: {summary['bert_score_avg']:.4f}")
        logger.info(f"平均BLEUスコア: {summary['bleu_score_avg']:.4f}")
        
        logger.info("\nShot別統計:")
        for shot, stats in summary["shot_statistics"].items():
            logger.info(f"  {shot}: BERT={stats['bert_avg']:.3f}, BLEU={stats['bleu_avg']:.3f} ({stats['count']}件)")
        
        logger.info("\nアスペクト別統計:")
        for aspect, stats in summary["aspect_statistics"].items():
            logger.info(f"  {aspect}: BERT={stats['bert_avg']:.3f}, BLEU={stats['bleu_avg']:.3f} ({stats['count']}件)")
    
    logger.info(f"\n結果ファイル: {output_file}")


if __name__ == "__main__":
    main() 