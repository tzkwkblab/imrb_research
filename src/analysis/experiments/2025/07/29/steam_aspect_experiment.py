#!/usr/bin/env python3
"""
Steam 8アスペクト対比因子生成実験

READMEの仕様に基づく実験実行スクリプト
utilsライブラリを使用した統合実験フレームワーク
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import json
from tqdm import tqdm

# utilsパスを追加
utils_path = Path(__file__).parent.parent / "utils"
sys.path.append(str(utils_path))

# 直接インポート（既存の動作確認済み方式）
from contrast_factor_analyzer import ContrastFactorAnalyzer
from dataset_manager import DatasetManager

# 実験設定インポート
from experiment_config import (
    EXPERIMENT_NAME,
    TARGET_ASPECTS,
    SHOT_SETTINGS,
    DATASET_ID,
    GROUP_SIZE,
    USE_ASPECT_DESCRIPTION,
    MODEL_CONFIG,
    OUTPUT_DIR
)

class SteamAspectExperiment:
    """Steam 8アスペクト対比因子生成実験クラス"""
    
    def __init__(self):
        self.analyzer = ContrastFactorAnalyzer(debug=True)
        self.dataset_manager = DatasetManager.from_config()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 出力ディレクトリ作成
        self.output_dir = Path(OUTPUT_DIR)
        self.output_dir.mkdir(exist_ok=True)
    
    def run_experiment(self):
        """メイン実験実行"""
        print(f"Steam 8アスペクト対比因子生成実験開始")
        print(f"対象アスペクト: {len(TARGET_ASPECTS)}個")
        print(f"Shot設定: {SHOT_SETTINGS}")
        print(f"各グループサイズ: {GROUP_SIZE}件")
        
        # 実験結果格納
        all_results = []
        summary_data = {}
        
        # アスペクト × Shot設定の全組み合わせ実行
        total_experiments = len(TARGET_ASPECTS) * len(SHOT_SETTINGS)
        
        with tqdm(total=total_experiments, desc="実験進行") as pbar:
            for aspect in TARGET_ASPECTS:
                aspect_results = {}
                
                for shot_count in SHOT_SETTINGS:
                    pbar.set_description(f"実験中: {aspect} ({shot_count}-shot)")
                    
                    try:
                        # データ分割取得
                        splits = self.dataset_manager.get_binary_splits(
                            DATASET_ID,
                            aspect=aspect,
                            group_size=GROUP_SIZE
                        )
                        
                        # 正解答えとしてアスペクト名を使用
                        correct_answer = splits.correct_answer
                        
                        # Few-shot例題準備
                        examples = self._prepare_examples(shot_count) if shot_count > 0 else None
                        
                        # 対比因子分析実行
                        result = self.analyzer.analyze(
                            group_a=splits.group_a,
                            group_b=splits.group_b,
                            correct_answer=correct_answer,
                            output_dir=str(self.output_dir),
                            experiment_name=f"{aspect}_{shot_count}shot",
                            examples=examples
                        )
                        
                        # 結果記録
                        all_results.append({
                            "aspect": aspect,
                            "shot_count": shot_count,
                            "result": result,
                            "metadata": {
                                "group_a_size": len(splits.group_a),
                                "group_b_size": len(splits.group_b),
                                "aspect_description_used": USE_ASPECT_DESCRIPTION
                            }
                        })
                        
                        # サマリーデータ更新
                        aspect_results[f"{shot_count}shot"] = {
                            "bert_score": result["evaluation"]["bert_score"],
                            "bleu_score": result["evaluation"]["bleu_score"]
                        }
                        
                    except Exception as e:
                        print(f"エラー: {aspect} {shot_count}-shot - {str(e)}")
                        aspect_results[f"{shot_count}shot"] = {
                            "bert_score": 0.0,
                            "bleu_score": 0.0,
                            "error": str(e)
                        }
                    
                    pbar.update(1)
                
                summary_data[aspect] = aspect_results
        
        # 結果保存
        self._save_results(all_results, summary_data)
        
        # 結果表示
        self._display_results(summary_data)
        
        return all_results, summary_data
    
    def _prepare_examples(self, shot_count):
        """Few-shot例題準備"""
        if shot_count == 0:
            return None
        
        # 簡単な例題セット
        examples = [
            {
                "group_a": ["Great graphics", "Beautiful visuals"],
                "group_b": ["Poor sound", "Audio issues"],
                "answer": "Visual quality and audio performance"
            }
        ]
        
        return examples[:shot_count]
    
    def _save_results(self, all_results, summary_data):
        """結果保存"""
        # JSON詳細結果保存
        json_filename = f"steam_8aspect_experiment_{self.timestamp}.json"
        json_path = self.output_dir / json_filename
        
        result_data = {
            "experiment_info": {
                "name": EXPERIMENT_NAME,
                "timestamp": self.timestamp,
                "aspects": TARGET_ASPECTS,
                "shot_settings": SHOT_SETTINGS,
                "group_size": GROUP_SIZE,
                "aspect_description_used": USE_ASPECT_DESCRIPTION,
                "model_config": MODEL_CONFIG
            },
            "results": all_results,
            "summary": summary_data
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f"詳細結果保存: {json_path}")
        
        # Markdown表保存
        md_filename = f"summary_table_{self.timestamp}.md"
        md_path = self.output_dir / md_filename
        
        self._save_markdown_table(summary_data, md_path)
        print(f"表形式結果保存: {md_path}")
    
    def _save_markdown_table(self, summary_data, output_path):
        """Markdown表形式で結果保存"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Steam 8アスペクト実験結果 ({self.timestamp})\n\n")
            
            # BERTスコア表
            f.write("## BERTスコア結果\n\n")
            f.write("| アスペクト | 0-shot | 1-shot | 3-shot |\n")
            f.write("|-----------|--------|--------|--------|\n")
            
            for aspect in TARGET_ASPECTS:
                if aspect in summary_data:
                    scores = []
                    for shot in SHOT_SETTINGS:
                        key = f"{shot}shot"
                        score = summary_data[aspect].get(key, {}).get("bert_score", 0.0)
                        scores.append(f"{score:.4f}")
                    f.write(f"| {aspect} | {' | '.join(scores)} |\n")
            
            # BLEUスコア表
            f.write("\n## BLEUスコア結果\n\n")
            f.write("| アスペクト | 0-shot | 1-shot | 3-shot |\n")
            f.write("|-----------|--------|--------|--------|\n")
            
            for aspect in TARGET_ASPECTS:
                if aspect in summary_data:
                    scores = []
                    for shot in SHOT_SETTINGS:
                        key = f"{shot}shot"
                        score = summary_data[aspect].get(key, {}).get("bleu_score", 0.0)
                        scores.append(f"{score:.4f}")
                    f.write(f"| {aspect} | {' | '.join(scores)} |\n")
    
    def _display_results(self, summary_data):
        """結果コンソール表示"""
        print("\n実験結果サマリー")
        print("=" * 60)
        
        # BERTスコア表示
        print("\nBERTスコア:")
        print("| アスペクト    | 0-shot | 1-shot | 3-shot |")
        print("|--------------|--------|--------|--------|")
        
        for aspect in TARGET_ASPECTS:
            if aspect in summary_data:
                scores = []
                for shot in SHOT_SETTINGS:
                    key = f"{shot}shot"
                    score = summary_data[aspect].get(key, {}).get("bert_score", 0.0)
                    scores.append(f"{score:.4f}")
                print(f"| {aspect:12} | {' | '.join(scores)} |")
        
        print("\nBLEUスコア:")
        print("| アスペクト    | 0-shot | 1-shot | 3-shot |")
        print("|--------------|--------|--------|--------|")
        
        for aspect in TARGET_ASPECTS:
            if aspect in summary_data:
                scores = []
                for shot in SHOT_SETTINGS:
                    key = f"{shot}shot"
                    score = summary_data[aspect].get(key, {}).get("bleu_score", 0.0)
                    scores.append(f"{score:.4f}")
                print(f"| {aspect:12} | {' | '.join(scores)} |")


def main():
    """メイン実行関数"""
    experiment = SteamAspectExperiment()
    results, summary = experiment.run_experiment()
    
    print("\n実験完了!")
    print(f"結果保存先: {experiment.output_dir}")


if __name__ == "__main__":
    main()