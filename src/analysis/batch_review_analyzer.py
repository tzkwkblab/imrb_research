import pandas as pd
from review_feature_analyzer import ReviewFeatureAnalyzer
from datetime import datetime
import json
from pathlib import Path
import glob
import re

class BatchReviewAnalyzer:
    def __init__(self, sample_size=300):
        self.sample_size = sample_size
        # 実行開始時の時間を保存
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        # 出力ディレクトリの設定
        self.output_dir = Path(f"src/analysis/results_batch_analysis/{self.timestamp}")
        # ReviewFeatureAnalyzerに出力ディレクトリを指定
        self.analyzer = ReviewFeatureAnalyzer(output_dir=str(self.output_dir))
        
    def analyze_reviews(self, resume_from_dir: str = None):
        """サンプルデータを読み込んで分析を実行"""
        # サンプルデータの読み込み
        df = pd.read_csv("src/data/examples/sample_reviews_300.csv")
        
        # レジューム処理の初期化
        start_index = 0
        all_results = []
        
        if resume_from_dir:
            # 既存の結果を読み込む
            self.output_dir = Path(resume_from_dir)
            start_index, all_results = self._load_existing_results(resume_from_dir)
            print(f"\n=== 既存の結果を読み込みました ===")
            print(f"処理済み件数: {start_index}")
            print(f"再開位置: {start_index + 1}番目のレビューから\n")
        else:
            # 新規実行の場合は出力ディレクトリを作成
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 進捗表示
        total = len(df)
        print(f"\n=== バッチ分析{'再開' if resume_from_dir else '開始'} ===")
        print(f"サンプル数: {total}")
        print(f"出力ディレクトリ: {self.output_dir}\n")
        
        try:
            # 各レビューの分析
            for idx, row in df.iloc[start_index:].iterrows():
                print(f"分析中... {idx + 1}/{total}")
                
                result = self.analyzer.analyze_review(
                    review_text=row['review_text'],
                    review_rating=row['rating'],
                    review_title=row['summary']
                )
                
                if result:
                    # 結果に元のレビュー情報を追加
                    analysis_result = {
                        'review_id': idx,
                        'review_text': row['review_text'],
                        'rating': row['rating'],
                        'product_id': row['product_id'],
                        'summary': row['summary'],
                        'analysis_result': result
                    }
                    all_results.append(analysis_result)
                    
                    # 10件ごとに中間結果を保存
                    if (len(all_results) % 10 == 0) or (idx == total - 1):
                        self._save_intermediate_results(all_results, self.output_dir, idx + 1)
                
        except KeyboardInterrupt:
            print("\n\n=== 処理が中断されました ===")
            print(f"現在の進捗: {idx + 1}/{total}件")
            print(f"再開する場合は以下のディレクトリを指定してください:")
            print(f"resume_from_dir='{self.output_dir}'")
            # 中断時点までの結果を保存
            self._save_intermediate_results(all_results, self.output_dir, idx + 1)
            return
        
        # 最終結果の保存
        self._save_final_results(all_results, self.output_dir)
        
        print(f"\n=== 分析完了 ===")
        print(f"分析結果: {self.output_dir}/all_results.json")
        print(f"サマリーレポート: {self.output_dir}/summary_report.md")
    
    def _load_existing_results(self, resume_dir: str) -> tuple[int, list]:
        """既存の結果を読み込んで、再開位置と結果リストを返す"""
        resume_dir = Path(resume_dir)
        intermediate_dir = resume_dir / "intermediate"
        
        if not intermediate_dir.exists():
            print("警告: 中間結果ディレクトリが見つかりません")
            return 0, []
        
        # 最新の中間結果ファイルを探す
        result_files = glob.glob(str(intermediate_dir / "results_*.json"))
        if not result_files:
            print("警告: 中間結果ファイルが見つかりません")
            return 0, []
        
        # ファイル名から処理件数を抽出してソート
        def extract_number(filename):
            match = re.search(r'results_(\d+)\.json', filename)
            return int(match.group(1)) if match else 0
        
        latest_file = max(result_files, key=extract_number)
        
        # 最新の結果を読み込む
        with open(latest_file, 'r', encoding='utf-8') as f:
            all_results = json.load(f)
        
        # 最後に処理したインデックスを取得
        last_processed = len(all_results) - 1
        
        return last_processed, all_results
    
    def _save_intermediate_results(self, results, output_dir, current_count):
        """中間結果を保存"""
        # 中間結果用のディレクトリ
        intermediate_dir = output_dir / "intermediate"
        intermediate_dir.mkdir(exist_ok=True)
        
        # 結果をJSONファイルとして保存
        with open(intermediate_dir / f"results_{current_count}.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"中間結果を保存しました（{current_count}件）")
    
    def _save_final_results(self, results, output_dir):
        """最終結果を保存"""
        # 全体の結果をJSONファイルとして保存
        with open(output_dir / 'all_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # サマリーレポートの作成
        self._create_summary_report(results, output_dir)
    
    def _create_summary_report(self, results, output_dir):
        """分析結果のサマリーレポートを作成"""
        # 特徴の出現頻度を計算
        feature_counts = {str(i): 0 for i in range(1, 21)}
        stability_sums = {str(i): 0.0 for i in range(1, 21)}
        
        for result in results:
            features = result['analysis_result']['features']
            stability = result['analysis_result']['stability']
            
            for feature_id in feature_counts.keys():
                if features[feature_id] == 1:
                    feature_counts[feature_id] += 1
                stability_sums[feature_id] += stability[feature_id]
        
        # レポート作成
        report = f"""# バッチ分析レポート
実行日時: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## 分析概要
- 分析対象レビュー数: {len(results)}
- レーティング分布:
{self._get_rating_distribution(results)}

## 特徴分析結果

| 特徴ID | 出現数 | 出現率 | 平均安定性 |
|--------|--------|--------|------------|
"""
        
        for feature_id in feature_counts.keys():
            count = feature_counts[feature_id]
            percentage = (count / len(results)) * 100
            avg_stability = stability_sums[feature_id] / len(results)
            
            report += f"| {feature_id} | {count} | {percentage:.1f}% | {avg_stability:.2f} |\n"
        
        # レポートの保存
        with open(output_dir / 'summary_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
    
    def _get_rating_distribution(self, results):
        """レーティングの分布を文字列として返す"""
        ratings = [r['rating'] for r in results]
        distribution = pd.Series(ratings).value_counts().sort_index()
        
        result = ""
        for rating, count in distribution.items():
            percentage = (count / len(results)) * 100
            result += f"  - {rating}星: {count}件 ({percentage:.1f}%)\n"
        
        return result

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='バッチでレビューの特徴分析を実行')
    parser.add_argument('--resume', type=str, help='再開する分析の出力ディレクトリ')
    args = parser.parse_args()
    
    analyzer = BatchReviewAnalyzer(sample_size=300)
    analyzer.analyze_reviews(resume_from_dir=args.resume) 