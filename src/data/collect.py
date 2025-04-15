import gzip
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict
import requests
from tqdm import tqdm

class AmazonReviewCollector:
    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_json_gz(self, filepath: str) -> List[Dict]:
        """gzipされたJSONファイルを読み込む"""
        data = []
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            for line in tqdm(f, desc="Loading reviews"):
                data.append(json.loads(line.strip()))
        return data
    
    def download_category_data(self, category: str, url: str):
        """特定カテゴリのデータをダウンロード"""
        output_path = self.data_dir / f"{category}_reviews.json.gz"
        
        if output_path.exists():
            print(f"File already exists: {output_path}")
            return output_path
        
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        return output_path
    
    def process_reviews(self, filepath: str, 
                       min_words: int = 20, 
                       max_reviews: int = 10000) -> pd.DataFrame:
        """レビューデータを前処理"""
        data = self.load_json_gz(filepath)
        
        # DataFrameに変換
        df = pd.DataFrame(data)
        
        # 必要なカラムのみ抽出
        df = df[['reviewText', 'overall', 'summary', 'unixReviewTime']]
        
        # 前処理
        df = df[df['reviewText'].str.split().str.len() >= min_words]  # 短すぎるレビューを除外
        df = df.sort_values('unixReviewTime', ascending=False)  # 新しい順にソート
        df = df.head(max_reviews)  # 最新のn件を抽出
        
        return df

def main():
    # 使用例
    collector = AmazonReviewCollector()
    
    # 例：Electronics カテゴリのデータをダウンロード
    url = "http://snap.stanford.edu/data/amazon/productGraph/categoryFiles/reviews_Electronics_5.json.gz"
    filepath = collector.download_category_data("Electronics", url)
    
    # データの前処理
    df = collector.process_reviews(filepath)
    
    # 保存
    output_path = Path("data/processed/electronics_reviews.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Processed data saved to {output_path}")

if __name__ == "__main__":
    main()
