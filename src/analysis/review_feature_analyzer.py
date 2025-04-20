"""
1. OpenAI APIを使用してレビューテキストを分析
2. 各特徴について1（当てはまる）または0（当てはまらない）を判定
3. 複数回の分析結果を統計的に処理
"""

import openai
import pandas as pd
import json
from pathlib import Path
from dotenv import load_dotenv
import os
from collections import Counter
from typing import List, Dict
from datetime import datetime
import csv

# 
class ReviewFeatureAnalyzer:
    def __init__(self, output_dir: str = None):
        # .envファイルから環境変数を読み込む
        load_dotenv()
        
        # 環境変数からAPIキーを設定
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        if not self.client.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # 特徴定義の読み込み
        self.features_df = pd.read_csv("src/data/features/definitions/review_features.csv")
        
        # 出力ディレクトリの設定
        self.output_dir = Path(output_dir) if output_dir else Path("src/analysis/results_review_feature_analysis")
        
    def analyze_review(self, review_text: str, review_rating: float, num_trials: int = 5) -> Dict:
        """一つのレビューに対して複数回特徴を分析し、多数決で判定"""
        results = []
        stability_data = {str(i): [] for i in range(1, 21)}  # 各特徴の判定安定性データ
        all_results = []  # 各試行の結果を保存
        
        # 指定回数の分析を実行
        for trial in range(num_trials):
            result = self._single_analysis(review_text, review_rating)
            if result and 'features' in result:
                results.append(result['features'])
                # 各特徴の判定を記録
                for feature_id, value in result['features'].items():
                    stability_data[feature_id].append(value)
                # 試行結果を保存
                all_results.append({
                    'trial': trial + 1,
                    **result['features']
                })
        
        if not results:
            return None
        
        # 多数決による最終判定と安定性の計算
        final_result = {
            'features': self._get_majority_vote(results),
            'stability': self._calculate_stability(stability_data, num_trials),
            'all_trials': all_results  # 各試行の結果を含める
        }
        
        # 結果をCSVファイルに保存
        self._save_results_to_csv(final_result)
        
        return final_result
    
    def _save_results_to_csv(self, results: Dict):
        """分析結果をCSVファイルに保存"""
        # 現在時刻からファイル名を生成
        timestamp = datetime.now().strftime("%H%M")
        output_file = self.output_dir / f"{timestamp}.csv"
        
        # 出力ディレクトリが存在しない場合は作成
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 特徴の説明を取得
        feature_descriptions = {
            str(row['feature_id']): row['feature_description']
            for _, row in self.features_df.iterrows()
        }
        
        # CSVファイルに書き込み
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # ヘッダー行を書き込み
            writer.writerow(['Feature ID', 'Description', 'Final Value', 'Stability'] + 
                          [f'Trial {i+1}' for i in range(len(results['all_trials']))])
            
            # 各特徴の結果を書き込み
            for feature_id in range(1, 21):
                feature_id_str = str(feature_id)
                row = [
                    feature_id,
                    feature_descriptions[feature_id_str],
                    results['features'][feature_id_str],
                    f"{results['stability'][feature_id_str]:.2f}"
                ]
                
                # 各試行の結果を追加
                for trial in results['all_trials']:
                    row.append(trial[feature_id_str])
                
                writer.writerow(row)
        
        print(f"\nDetailed results saved to: {output_file}")
    
    def _single_analysis(self, review_text: str, review_rating: float) -> Dict:
        """単一の分析を実行"""
        prompt = self._create_prompt(review_text, review_rating)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in analyzing product reviews."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            return self._parse_response(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error during API call: {e}")
            return None
        
    def _create_prompt(self, review_text: str, rating: float) -> str:
        """分析用のプロンプトを作成"""
        features_list = "\n".join([
            f"{row['feature_id']}. {row['feature_description']}"
            for _, row in self.features_df.iterrows()
        ])
        
        prompt = f"""
Please evaluate whether each feature applies to the following product review.
Clearly indicate your judgment with 0 (feature not present) or 1 (feature present).

[REVIEW]
{review_text}

[REVIEW RATING]
{rating}

[FEATURE LIST]
{features_list}

Response format:
{{
    "features": {{
        "1": 0 or 1,
        "2": 0 or 1,
        ...
    }}
}}

"""
        return prompt
    
    def _get_majority_vote(self, results: List[Dict]) -> Dict:
        """複数の判定結果から多数決で最終判定を決定"""
        final_result = {}
        for feature_id in range(1, 21):
            feature_id_str = str(feature_id)
            # 各特徴の判定値を集計
            votes = [result[feature_id_str] for result in results]
            # 多数決（同数の場合は1を優先）
            counter = Counter(votes)
            final_result[feature_id_str] = 1 if counter[1] >= counter[0] else 0
            
        return final_result
    
    def _calculate_stability(self, stability_data: Dict, num_trials: int) -> Dict:
        """各特徴の判定安定性を計算"""
        stability_scores = {}
        for feature_id, values in stability_data.items():
            if values:  # データが存在する場合のみ
                # 最頻値の出現回数を数える
                counter = Counter(values)
                most_common_count = counter.most_common(1)[0][1]
                # 安定性スコアを計算（最頻値の出現率）
                stability_scores[feature_id] = most_common_count / num_trials
                
        return stability_scores
    
    def _parse_response(self, response_text: str) -> Dict:
        """APIレスポンスをパース"""
        try:
            # JSON部分を抽出して解析
            json_str = response_text.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            result = json.loads(json_str)
            return result
        except Exception as e:
            print(f"Error parsing response: {e}")
            return None

# 使用例
if __name__ == "__main__":
    analyzer = ReviewFeatureAnalyzer()
    
    # テスト用レビュー
    review = """We got this GPS for my husband who is an (OTR) over the road trucker. Very Impressed with the shipping time, it arrived a few days earlier than expected... within a week of use however it started freezing up... could of just been a glitch in that unit. Worked great when it worked! Will work great for the normal person as well but does have the "trucker" option. (the big truck routes - tells you when a scale is coming up ect...) Love the bigger screen, the ease of use, the ease of putting addresses into memory. Nothing really bad to say about the unit with the exception of it freezing which is probably one in a million and that's just my luck. I contacted the seller and within minutes of my email I received a email back with instructions for an exchange! VERY impressed all the way around!"""
    
    result = analyzer.analyze_review(review, 4.0)
    
    if result:
        print("=== Review Analysis Results ===\n")
        print("\n--- Feature Analysis ---")
        for feature_id, feature_value in result['features'].items():
            feature_desc = analyzer.features_df.loc[
                analyzer.features_df['feature_id'] == int(feature_id), 
                'feature_description'
            ].iloc[0]
            print(f"\nFeature {feature_id}: {feature_desc}")
            print(f"Value: {feature_value}")
            print(f"Stability: {result['stability'][feature_id]:.2f}")