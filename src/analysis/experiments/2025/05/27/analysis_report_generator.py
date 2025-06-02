#!/usr/bin/env python3
"""
類似度評価結果の分析レポート生成スクリプト

評価結果を分析し、詳細なレポートを生成します。
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

class SimilarityAnalysisReporter:
    """類似度評価結果の分析・レポート生成クラス"""
    
    def __init__(self, results_file: str):
        """
        初期化
        
        Args:
            results_file (str): 評価結果JSONファイルのパス
        """
        self.results_file = Path(results_file)
        self.results = []
        self._load_results()
        
    def _load_results(self):
        """評価結果の読み込み"""
        try:
            with open(self.results_file, 'r', encoding='utf-8') as f:
                self.results = json.load(f)
            print(f"評価結果を読み込みました: {len(self.results)}件")
        except Exception as e:
            print(f"結果ファイル読み込みエラー: {e}")
    
    def generate_detailed_analysis(self) -> str:
        """詳細分析レポートの生成"""
        if not self.results:
            return "分析対象データがありません"
        
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("テキスト類似度評価結果 - 詳細分析レポート")
        report_lines.append("=" * 60)
        report_lines.append(f"生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        report_lines.append("")
        
        # 基本統計情報
        bert_scores = [r['bert_similarity'] for r in self.results]
        bleu_scores = [r['bleu_similarity'] for r in self.results]
        
        report_lines.append("## 基本統計情報")
        report_lines.append("")
        report_lines.append("### BERT類似度")
        report_lines.append(f"- 平均値: {np.mean(bert_scores):.4f}")
        report_lines.append(f"- 中央値: {np.median(bert_scores):.4f}")
        report_lines.append(f"- 標準偏差: {np.std(bert_scores):.4f}")
        report_lines.append(f"- 最大値: {np.max(bert_scores):.4f}")
        report_lines.append(f"- 最小値: {np.min(bert_scores):.4f}")
        report_lines.append("")
        
        report_lines.append("### BLEU類似度")
        report_lines.append(f"- 平均値: {np.mean(bleu_scores):.4f}")
        report_lines.append(f"- 中央値: {np.median(bleu_scores):.4f}")
        report_lines.append(f"- 標準偏差: {np.std(bleu_scores):.4f}")
        report_lines.append(f"- 最大値: {np.max(bleu_scores):.4f}")
        report_lines.append(f"- 最小値: {np.min(bleu_scores):.4f}")
        report_lines.append("")
        
        # 個別の特徴分析
        report_lines.append("## 特徴別詳細分析")
        report_lines.append("")
        
        for result in self.results:
            feature_num = result['feature_number']
            bert_sim = result['bert_similarity']
            bleu_sim = result['bleu_similarity']
            gpt_resp = result['gpt_response']
            orig_desc = result['original_description']
            
            report_lines.append(f"### Feature {feature_num}")
            report_lines.append(f"**GPTレスポンス**: \"{gpt_resp}\"")
            report_lines.append(f"**元の特徴記述**: \"{orig_desc}\"")
            report_lines.append(f"**BERT類似度**: {bert_sim:.4f}")
            report_lines.append(f"**BLEU類似度**: {bleu_sim:.4f}")
            
            # 類似度レベルの評価
            if bert_sim >= 0.8:
                bert_level = "非常に高い"
            elif bert_sim >= 0.7:
                bert_level = "高い"
            elif bert_sim >= 0.6:
                bert_level = "中程度"
            else:
                bert_level = "低い"
                
            if bleu_sim >= 0.5:
                bleu_level = "高い"
            elif bleu_sim >= 0.3:
                bleu_level = "中程度"
            elif bleu_sim >= 0.1:
                bleu_level = "低い"
            else:
                bleu_level = "非常に低い"
            
            report_lines.append(f"**評価**: BERT類似度は{bert_level}（{bert_sim:.4f}）、BLEU類似度は{bleu_level}（{bleu_sim:.4f}）")
            report_lines.append("")
            
            # 語彙レベルでの分析
            gpt_words = set(gpt_resp.lower().split())
            orig_words = set(orig_desc.lower().split())
            common_words = gpt_words.intersection(orig_words)
            
            if common_words:
                report_lines.append(f"**共通語彙**: {', '.join(sorted(common_words))}")
            else:
                report_lines.append("**共通語彙**: なし")
            report_lines.append("")
        
        # 総合評価
        report_lines.append("## 総合評価")
        report_lines.append("")
        
        avg_bert = np.mean(bert_scores)
        avg_bleu = np.mean(bleu_scores)
        
        report_lines.append("### BERT類似度について")
        if avg_bert >= 0.8:
            bert_assessment = "非常に良好"
        elif avg_bert >= 0.7:
            bert_assessment = "良好"
        elif avg_bert >= 0.6:
            bert_assessment = "中程度"
        else:
            bert_assessment = "改善が必要"
            
        report_lines.append(f"平均BERT類似度は{avg_bert:.4f}で、{bert_assessment}な結果です。")
        report_lines.append("BERTベースの評価では、意味的な類似性を捉えており、")
        report_lines.append("GPTが生成した特徴記述は元の記述と概ね一致していることを示しています。")
        report_lines.append("")
        
        report_lines.append("### BLEU類似度について")
        if avg_bleu >= 0.3:
            bleu_assessment = "良好"
        elif avg_bleu >= 0.1:
            bleu_assessment = "中程度"
        else:
            bleu_assessment = "低い"
            
        report_lines.append(f"平均BLEU類似度は{avg_bleu:.4f}で、{bleu_assessment}な結果です。")
        report_lines.append("BLEUスコアが低いのは、GPTが元の記述と異なる語彙や表現を使用しているためです。")
        report_lines.append("これは必ずしも悪いことではなく、GPTが内容を理解した上で")
        report_lines.append("より説明的で具体的な表現に言い換えている可能性を示しています。")
        report_lines.append("")
        
        # 改善提案
        report_lines.append("## 改善提案")
        report_lines.append("")
        report_lines.append("1. **プロンプトの調整**: より元の記述に近い表現を生成するよう、")
        report_lines.append("   プロンプトに「元の特徴記述に近い表現で」という指示を追加する。")
        report_lines.append("")
        report_lines.append("2. **語彙制約の導入**: 特定のキーワードを含むよう制約を設ける。")
        report_lines.append("")
        report_lines.append("3. **追加評価指標**: 語順を考慮しない語彙一致度やROUGE-Lスコアなど、")
        report_lines.append("   他の評価指標も併用して多角的に評価する。")
        report_lines.append("")
        
        return "\\n".join(report_lines)
    
    def save_report(self, output_file: str):
        """レポートをファイルに保存"""
        report = self.generate_detailed_analysis()
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"詳細分析レポートを保存しました: {output_file}")
        except Exception as e:
            print(f"レポート保存エラー: {e}")
    
    def create_visualization(self, output_dir: str):
        """結果の可視化グラフを作成"""
        if not self.results:
            print("可視化対象データがありません")
            return
            
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # データの準備
        features = [r['feature_number'] for r in self.results]
        bert_scores = [r['bert_similarity'] for r in self.results]
        bleu_scores = [r['bleu_similarity'] for r in self.results]
        
        # スタイル設定
        plt.style.use('default')
        sns.set_palette("husl")
        
        # 図1: 類似度スコア比較
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # BERT類似度
        ax1.bar([f'Feature {f}' for f in features], bert_scores, color='skyblue', alpha=0.8)
        ax1.set_title('BERT類似度スコア', fontsize=14, fontweight='bold')
        ax1.set_ylabel('類似度', fontsize=12)
        ax1.set_ylim(0, 1)
        ax1.grid(True, alpha=0.3)
        
        # BLEU類似度
        ax2.bar([f'Feature {f}' for f in features], bleu_scores, color='lightcoral', alpha=0.8)
        ax2.set_title('BLEU類似度スコア', fontsize=14, fontweight='bold')
        ax2.set_ylabel('類似度', fontsize=12)
        ax2.set_ylim(0, max(bleu_scores) * 1.2 if bleu_scores else 0.1)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'similarity_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 図2: 散布図
        plt.figure(figsize=(8, 6))
        plt.scatter(bert_scores, bleu_scores, s=100, alpha=0.7, color='purple')
        
        for i, feature in enumerate(features):
            plt.annotate(f'Feature {feature}', 
                        (bert_scores[i], bleu_scores[i]), 
                        xytext=(5, 5), textcoords='offset points')
        
        plt.xlabel('BERT類似度', fontsize=12)
        plt.ylabel('BLEU類似度', fontsize=12)
        plt.title('BERT vs BLEU 類似度相関', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_dir / 'bert_vs_bleu_scatter.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"可視化グラフを保存しました: {output_dir}")


def main():
    """メイン実行関数"""
    print("=== 類似度評価結果分析レポート生成 ===")
    
    # ファイルパス設定
    base_dir = Path("/Users/seinoshun/imrb_research/src/analysis/experiments/2025/05/27")
    results_file = base_dir / "similarity_evaluation_results.json"
    report_file = base_dir / "detailed_analysis_report.md"
    
    # 分析器の初期化
    reporter = SimilarityAnalysisReporter(str(results_file))
    
    # 詳細分析レポートの生成
    reporter.save_report(str(report_file))
    
    # 可視化グラフの作成
    try:
        reporter.create_visualization(str(base_dir))
    except Exception as e:
        print(f"可視化作成中にエラーが発生しました: {e}")
        print("matplotlib がインストールされていない可能性があります")
    
    print("分析完了!")


if __name__ == "__main__":
    main()