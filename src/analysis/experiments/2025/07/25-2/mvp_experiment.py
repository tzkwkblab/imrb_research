#!/usr/bin/env python3
"""
対比因子生成実験MVP版

新しいutils統合ツールを活用した最小構成実験
- Steam Reviewデータセットのみ
- gameplay vs visual アスペクト
- 0-shot実験のみ
- 基本スコア計算・JSON出力
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# utils統合ツールのパス設定
script_dir = Path(__file__).parent
utils_dir = script_dir / ".." / ".." / ".." / "utils"
utils_dir = utils_dir.resolve()
sys.path.append(str(utils_dir))

# 設定ファイル読み込み
from mvp_config import *

# utils統合ツール
from dataset_manager import DatasetManager
from contrast_factor_analyzer import ContrastFactorAnalyzer

# スコア計算
from scores.bert_score import calculate_bert_score
from scores.bleu_score import calculate_bleu_score

class MVPExperiment:
    """MVP版対比因子生成実験クラス"""
    
    def __init__(self):
        self.setup_logging()
        self.results = {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def setup_logging(self):
        """ログ設定"""
        if DEBUG_MODE:
            logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def print_header(self):
        """実験開始メッセージ"""
        if CONSOLE_OUTPUT:
            print("=== 対比因子生成実験 MVP ===")
            print(f"データセット: {DATASET}")
            print(f"実験バージョン: {EXPERIMENT_VERSION}")
            print()
    
    def load_data(self):
        """データセット読み込み"""
        self.logger.info("DatasetManagerでデータ読み込み開始")
        
        try:
            # DatasetManager初期化
            self.manager = DatasetManager.from_config()
            self.logger.info("DatasetManager初期化完了")
            return True
            
        except Exception as e:
            self.logger.error(f"データ読み込みエラー: {e}")
            return False
    
    def run_aspect_experiment(self, aspect):
        """単一アスペクトでの実験実行"""
        if CONSOLE_OUTPUT:
            print(f"アスペクト: {aspect}")
            print("[実験実行]")
        
        try:
            # データ分割取得
            splits = self.manager.get_binary_splits(
                DATASET, 
                aspect=aspect, 
                group_size=GROUP_SIZE
            )
            
            if CONSOLE_OUTPUT:
                print(f"✅ データ分割取得完了 (グループA: {len(splits.group_a)}件, グループB: {len(splits.group_b)}件)")
            
            # 対比因子分析実行
            analyzer = ContrastFactorAnalyzer(debug=DEBUG_MODE)
            
            result = analyzer.analyze(
                group_a=splits.group_a,
                group_b=splits.group_b,
                correct_answer=splits.correct_answer,
                output_dir=OUTPUT_DIR,
                experiment_name=f"mvp_{aspect}_{self.timestamp}"
            )
            
            if CONSOLE_OUTPUT:
                print("✅ 対比因子分析実行完了")
            
            # スコア計算
            llm_response = result.get('llm_response', '')
            correct_answer = splits.correct_answer
            
            bert_score = calculate_bert_score(llm_response, correct_answer)
            bleu_score = calculate_bleu_score(llm_response, correct_answer)
            
            if CONSOLE_OUTPUT:
                print("✅ スコア計算完了")
                print()
                print("[結果]")
                print(f"BERTスコア: {bert_score:.4f}")
                print(f"BLEUスコア: {bleu_score:.4f}")
            
            # 品質評価
            quality = self.evaluate_quality(bert_score, bleu_score)
            if CONSOLE_OUTPUT:
                print(f"品質評価: {quality}")
            
            # 結果構造化
            experiment_result = {
                "experiment_info": {
                    "timestamp": self.timestamp,
                    "dataset": DATASET,
                    "aspect": aspect,
                    "group_size": GROUP_SIZE,
                    "version": EXPERIMENT_VERSION
                },
                "results": {
                    "bert_score": bert_score,
                    "bleu_score": bleu_score,
                    "llm_response": llm_response,
                    "correct_answer": correct_answer
                },
                "summary": {
                    "success": True,
                    "quality": quality
                }
            }
            
            # 結果保存
            filename = f"mvp_{aspect}_{self.timestamp}.json"
            filepath = Path(OUTPUT_DIR) / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(experiment_result, f, ensure_ascii=False, indent=2)
            
            if CONSOLE_OUTPUT:
                print(f"保存先: {filepath}")
                print("-" * 50)
                print()
            
            return experiment_result
            
        except Exception as e:
            self.logger.error(f"アスペクト実験エラー ({aspect}): {e}")
            return {
                "experiment_info": {
                    "timestamp": self.timestamp,
                    "dataset": DATASET,
                    "aspect": aspect,
                    "error": str(e)
                },
                "summary": {
                    "success": False,
                    "error": str(e)
                }
            }
    
    def evaluate_quality(self, bert_score, bleu_score):
        """品質評価判定"""
        avg_score = (bert_score + bleu_score) / 2
        
        if avg_score >= 0.7:
            return "good"
        elif avg_score >= 0.5:
            return "fair"
        else:
            return "poor"
    
    def run_experiment(self):
        """実験全体実行"""
        self.print_header()
        
        # データ読み込み
        if not self.load_data():
            print("❌ データ読み込みに失敗しました")
            return False
        
        # 各アスペクトで実験実行
        all_results = []
        
        for aspect in ASPECTS:
            result = self.run_aspect_experiment(aspect)
            all_results.append(result)
        
        # 統合結果保存
        summary_result = {
            "experiment_meta": {
                "version": EXPERIMENT_VERSION,
                "timestamp": self.timestamp,
                "dataset": DATASET,
                "aspects": ASPECTS,
                "description": DESCRIPTION
            },
            "results": all_results
        }
        
        summary_file = Path(OUTPUT_DIR) / f"mvp_summary_{self.timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_result, f, ensure_ascii=False, indent=2)
        
        if CONSOLE_OUTPUT:
            print(f"=== 実験完了 ===")
            print(f"統合結果: {summary_file}")
        
        return True

def main():
    """メイン実行関数"""
    experiment = MVPExperiment()
    success = experiment.run_experiment()
    
    if success:
        print("✅ MVP実験が正常に完了しました")
        return 0
    else:
        print("❌ MVP実験でエラーが発生しました")
        return 1

if __name__ == "__main__":
    exit(main()) 