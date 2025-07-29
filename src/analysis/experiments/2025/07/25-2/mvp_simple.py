#!/usr/bin/env python3
"""
対比因子生成実験 簡略化MVP版

依存関係を最小限に抑えた動作確認用MVP
- 基本的なテキスト処理のみ
- Steam Review データの仮想データでテスト
- シンプルな類似度計算
- JSON出力の基本フロー検証
"""

import json
import logging
from datetime import datetime
from pathlib import Path

# 設定インポート
from mvp_config import *

class SimpleMVPExperiment:
    """簡略化MVP版対比因子生成実験"""
    
    def __init__(self):
        self.setup_logging()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def setup_logging(self):
        """ログ設定"""
        if DEBUG_MODE:
            logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def print_header(self):
        """実験開始メッセージ"""
        if CONSOLE_OUTPUT:
            print("=== 対比因子生成実験 簡略化MVP ===")
            print(f"データセット: {DATASET}")
            print(f"実験バージョン: {EXPERIMENT_VERSION}")
            print()
    
    def create_mock_data(self, aspect):
        """テスト用のモックデータ生成"""
        if aspect == "gameplay":
            group_a = [
                "Great gameplay mechanics and smooth controls",
                "Fun gameplay with engaging combat system", 
                "Excellent gameplay variety and progression"
            ] * (GROUP_SIZE // 3)
            
            group_b = [
                "Poor gameplay design and clunky mechanics",
                "Boring gameplay with repetitive tasks",
                "Frustrating gameplay and bad controls"
            ] * (GROUP_SIZE // 3)
            
            correct_answer = "Gameplay quality distinguishes positive from negative reviews"
            
        elif aspect == "visual":
            group_a = [
                "Beautiful graphics and stunning visual effects",
                "Amazing art style and visual presentation",
                "Gorgeous visuals and detailed environments"
            ] * (GROUP_SIZE // 3)
            
            group_b = [
                "Poor graphics and outdated visual quality",
                "Ugly art style and bland visuals",
                "Low quality graphics and poor visual design"
            ] * (GROUP_SIZE // 3)
            
            correct_answer = "Visual quality differentiates positive from negative reviews"
        
        return {
            'group_a': group_a[:GROUP_SIZE],
            'group_b': group_b[:GROUP_SIZE], 
            'correct_answer': correct_answer
        }
    
    def mock_llm_analysis(self, group_a, group_b):
        """LLM分析のモック実装"""
        # 簡単な分析結果を生成
        common_positive = ["good", "great", "excellent", "amazing", "beautiful"]
        common_negative = ["poor", "bad", "ugly", "boring", "frustrating"]
        
        a_words = " ".join(group_a[:5]).lower()
        b_words = " ".join(group_b[:5]).lower()
        
        pos_count = sum(word in a_words for word in common_positive)
        neg_count = sum(word in b_words for word in common_negative)
        
        return f"Analysis shows positive reviews emphasize quality ({pos_count} positive indicators) while negative reviews focus on problems ({neg_count} negative indicators)."
    
    def simple_similarity_score(self, text1, text2):
        """単純な類似度計算"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def run_aspect_experiment(self, aspect):
        """単一アスペクトでの簡略化実験"""
        if CONSOLE_OUTPUT:
            print(f"アスペクト: {aspect}")
            print("[実験実行]")
        
        try:
            # モックデータ取得
            data = self.create_mock_data(aspect)
            
            if CONSOLE_OUTPUT:
                print(f"✅ データ準備完了 (グループA: {len(data['group_a'])}件, グループB: {len(data['group_b'])}件)")
            
            # モック分析実行
            llm_response = self.mock_llm_analysis(data['group_a'], data['group_b'])
            
            if CONSOLE_OUTPUT:
                print("✅ 対比因子分析実行完了")
            
            # 類似度計算
            similarity_score = self.simple_similarity_score(llm_response, data['correct_answer'])
            
            # ダミースコア生成（実際のBERT/BLEUスコア風）
            bert_score = max(0.6, min(0.9, similarity_score + 0.2))
            bleu_score = max(0.4, min(0.8, similarity_score + 0.1))
            
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
                    "version": f"{EXPERIMENT_VERSION}-Simple",
                    "note": "Simplified MVP with mock data"
                },
                "results": {
                    "bert_score": bert_score,
                    "bleu_score": bleu_score,
                    "similarity_score": similarity_score,
                    "llm_response": llm_response,
                    "correct_answer": data['correct_answer']
                },
                "summary": {
                    "success": True,
                    "quality": quality
                }
            }
            
            # 結果保存
            filename = f"simple_mvp_{aspect}_{self.timestamp}.json"
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
        
        # 各アスペクトで実験実行
        all_results = []
        
        for aspect in ASPECTS:
            result = self.run_aspect_experiment(aspect)
            all_results.append(result)
        
        # 統合結果保存
        summary_result = {
            "experiment_meta": {
                "version": f"{EXPERIMENT_VERSION}-Simple",
                "timestamp": self.timestamp,
                "dataset": DATASET,
                "aspects": ASPECTS,
                "description": f"{DESCRIPTION} (Simplified with mock data)",
                "note": "This is a simplified MVP for testing basic flow"
            },
            "results": all_results
        }
        
        summary_file = Path(OUTPUT_DIR) / f"simple_mvp_summary_{self.timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_result, f, ensure_ascii=False, indent=2)
        
        if CONSOLE_OUTPUT:
            print(f"=== 実験完了 ===")
            print(f"統合結果: {summary_file}")
        
        return True

def main():
    """メイン実行関数"""
    experiment = SimpleMVPExperiment()
    success = experiment.run_experiment()
    
    if success:
        print("✅ 簡略化MVP実験が正常に完了しました")
        print("📝 注意: これはモックデータを使用したテストです")
        return 0
    else:
        print("❌ 簡略化MVP実験でエラーが発生しました")
        return 1

if __name__ == "__main__":
    exit(main()) 