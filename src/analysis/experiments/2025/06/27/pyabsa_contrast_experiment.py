#!/usr/bin/env python3
"""
PyABSAデータセット対比因子抽出実験

0-shot、1-shot、3-shotでの対比因子抽出とスコア評価
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

class PyABSAContrastExperiment:
    """PyABSAデータセット対比因子実験クラス"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.dataset_loader = PyABSADatasetLoader()
        self.analyzer = ContrastFactorAnalyzer(debug=debug)
        
        # 実験パラメータ
        self.group_size = 300  # 各グループのサンプル数
        self.random_seed = 42
        random.seed(self.random_seed)
        
        logger.info("PyABSA対比因子実験初期化完了")
    
    def prepare_contrast_groups(
        self, 
        records: List[ABSARecord], 
        primary_aspect: str,
        contrast_aspect: str
    ) -> Tuple[List[str], List[str], str]:
        """
        対比グループの準備
        
        Args:
            records: ABSAレコードリスト
            primary_aspect: 主要アスペクト（グループA）
            contrast_aspect: 対比アスペクト（グループB）
        
        Returns:
            group_a, group_b, correct_answer
        """
        # アスペクトでフィルタリング
        group_a_records = [r for r in records if primary_aspect.lower() in r.aspect.lower()]
        group_b_records = [r for r in records if contrast_aspect.lower() in r.aspect.lower()]
        
        logger.info(f"アスペクトマッチング - {primary_aspect}: {len(group_a_records)}件, {contrast_aspect}: {len(group_b_records)}件")
        
        # サンプル調整
        group_a_texts = self._adjust_sample_size([r.text for r in group_a_records], self.group_size)
        group_b_texts = self._adjust_sample_size([r.text for r in group_b_records], self.group_size)
        
        # 正解作成
        correct_answer = f"{primary_aspect} vs {contrast_aspect} characteristics"
        
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
    
    def create_few_shot_examples(self, dataset_name: str, shot_count: int) -> List[Dict]:
        """Few-shot例題作成"""
        if shot_count == 0:
            return None
        
        examples = []
        
        # 汎用例題パターン
        base_examples = [
            {
                "group_a": ["Fast delivery", "Quick shipping", "Express service"],
                "group_b": ["Slow response", "Delayed support", "Poor customer service"],
                "answer": "Service speed and responsiveness"
            },
            {
                "group_a": ["High quality materials", "Durable construction", "Premium build"],
                "group_b": ["Cheap plastic", "Fragile design", "Poor assembly"],
                "answer": "Build quality and material durability"
            },
            {
                "group_a": ["User-friendly interface", "Intuitive navigation", "Easy to use"],
                "group_b": ["Expensive pricing", "High cost", "Overpriced"],
                "answer": "User experience vs pricing considerations"
            }
        ]
        
        return base_examples[:shot_count]
    
    def run_experiment(
        self,
        dataset_id: str,
        aspect_pairs: List[Tuple[str, str]],
        shot_settings: List[int] = [0, 1, 3]
    ) -> Dict:
        """
        実験実行
        
        Args:
            dataset_id: データセットID
            aspect_pairs: アスペクトペアのリスト [(primary, contrast), ...]
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
                "aspect_pairs": aspect_pairs,
                "shot_settings": shot_settings,
                "group_size": self.group_size,
                "random_seed": self.random_seed
            },
            "results": []
        }
        
        # 実験ループ
        for aspect_pair in aspect_pairs:
            primary_aspect, contrast_aspect = aspect_pair
            
            logger.info(f"アスペクトペア処理: {primary_aspect} vs {contrast_aspect}")
            
            try:
                # 対比グループ準備
                group_a, group_b, correct_answer = self.prepare_contrast_groups(
                    records, primary_aspect, contrast_aspect
                )
                
                if len(group_a) < 10 or len(group_b) < 10:
                    logger.warning(f"サンプル数不足をスキップ: {primary_aspect} vs {contrast_aspect}")
                    continue
                
                # 各Shot設定で実験
                for shot_count in shot_settings:
                    logger.info(f"Shot設定: {shot_count}")
                    
                    # Few-shot例題準備
                    examples = self.create_few_shot_examples(dataset_id, shot_count)
                    
                    # 実験名
                    experiment_name = f"{dataset_id}_{primary_aspect.replace(' ', '_')}_vs_{contrast_aspect.replace(' ', '_')}_{shot_count}shot"
                    
                    # 対比因子分析実行
                    try:
                        result = self.analyzer.analyze(
                            group_a=group_a,
                            group_b=group_b,
                            correct_answer=correct_answer,
                            output_dir=f"results/{dataset_id}/",
                            examples=examples,
                            experiment_name=experiment_name
                        )
                        
                        # 結果記録
                        experiment_record = {
                            "aspect_pair": aspect_pair,
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
                            "aspect_pair": aspect_pair,
                            "shot_count": shot_count,
                            "error": str(e),
                            "success": False
                        })
            
            except Exception as e:
                logger.error(f"アスペクトペア処理エラー: {e}")
        
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
        
        return {
            "total_experiments": len(results),
            "successful_experiments": len(successful_results),
            "bert_score_avg": sum(bert_scores) / len(bert_scores),
            "bleu_score_avg": sum(bleu_scores) / len(bleu_scores),
            "bert_score_range": [min(bert_scores), max(bert_scores)],
            "bleu_score_range": [min(bleu_scores), max(bleu_scores)],
            "shot_statistics": shot_stats
        }


def main():
    """メイン実行"""
    logger.info("PyABSA対比因子抽出実験開始")
    
    # 実験インスタンス作成
    experiment = PyABSAContrastExperiment(debug=True)
    
    # 利用可能データセット確認
    datasets = experiment.dataset_loader.list_available_datasets()
    logger.info(f"利用可能データセット: {len(datasets)}件")
    
    # SemEvalデータセットで実験
    semeval_datasets = [d for d in datasets if 'SemEval' in d.name and d.record_count > 1000]
    
    if not semeval_datasets:
        logger.error("適切なSemEvalデータセットが見つかりません")
        return
    
    # 最初のSemEvalデータセットを使用
    target_dataset = semeval_datasets[0]
    logger.info(f"実験対象データセット: {target_dataset.name} ({target_dataset.record_count}件)")
    
    # アスペクトペア定義（データセットに応じて調整）
    if 'laptop' in target_dataset.name.lower():
        aspect_pairs = [
            ("battery", "screen"),
            ("keyboard", "performance"),
            ("price", "design")
        ]
    elif 'restaurant' in target_dataset.name.lower():
        aspect_pairs = [
            ("food", "service"),
            ("atmosphere", "price"),
            ("staff", "location")
        ]
    else:
        # 汎用アスペクトペア
        aspect_pairs = [
            ("quality", "price"),
            ("performance", "design"),
            ("service", "value")
        ]
    
    # 実験実行
    results = experiment.run_experiment(
        dataset_id=target_dataset.dataset_id,
        aspect_pairs=aspect_pairs,
        shot_settings=[0, 1, 3]
    )
    
    # 結果保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"pyabsa_contrast_experiment_results_{timestamp}.json"
    
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
    
    logger.info(f"\n結果ファイル: {output_file}")


if __name__ == "__main__":
    main() 