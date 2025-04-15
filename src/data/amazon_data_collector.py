import gzip
import json
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
import os
import shutil

class AmazonDataCollector:
    def __init__(self, category="Electronics", sample_size=10000, min_words=20):
        self.category = category
        self.sample_size = sample_size
        self.min_words = min_words
        self.base_dir = Path("data")
        self.raw_dir = self.base_dir / "raw"
        self.processed_dir = self.base_dir / "processed"
        
        # ディレクトリの作成
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # データファイルのパス
        self.raw_file = self.raw_dir / f"reviews_{category}_5.json.gz"
        self.processed_file = self.processed_dir / f"{category.lower()}_reviews.csv"

    def download_data(self):
        """データのダウンロード"""
        url = f"http://snap.stanford.edu/data/amazon/productGraph/categoryFiles/reviews_{self.category}_5.json.gz"
        print(f"Downloading {self.category} reviews...")
        
        if self.raw_file.exists():
            print("File already exists. Skipping download.")
            return
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            
            with open(self.raw_file, 'wb') as f:
                for data in tqdm(response.iter_content(block_size), 
                               total=total_size//block_size, 
                               unit='KB', unit_scale=True):
                    f.write(data)
            
            print("\nDownload completed!")
        except Exception as e:
            print(f"Error downloading data: {e}")
            raise

    def process_data(self):
        """データの処理"""
        print("\nProcessing data...")
        data = []
        
        try:
            with gzip.open(self.raw_file, 'rt', encoding='utf-8') as f:
                for i, line in enumerate(tqdm(f)):
                    if i >= self.sample_size * 2:  # 必要数の2倍まで読み込み（フィルタリング後のため）
                        break
                    
                    review = json.loads(line.strip())
                    
                    # 必要なフィールドの抽出
                    processed_review = {
                        'review_text': review.get('reviewText', ''),
                        'rating': review.get('overall', 0),
                        'product_id': review.get('asin', ''),
                        'time': review.get('unixReviewTime', 0),
                        'summary': review.get('summary', '')
                    }
                    
                    # 最小単語数でフィルタリング
                    if len(processed_review['review_text'].split()) >= self.min_words:
                        data.append(processed_review)
                        
                    if len(data) >= self.sample_size:
                        break
            
            # DataFrameに変換
            df = pd.DataFrame(data)
            
            # データの保存
            df.to_csv(self.processed_file, index=False)
            print(f"\nProcessed data saved to {self.processed_file}")
            
            return df
            
        except Exception as e:
            print(f"Error processing data: {e}")
            raise

    def check_data_quality(self, df):
        """データ品質のチェックと基本統計の表示"""
        print("\n=== Data Quality Report ===")
        print(f"総レビュー数: {len(df)}")
        print(f"\n評価の分布:")
        print(df['rating'].value_counts().sort_index())
        
        review_lengths = df['review_text'].str.split().str.len()
        print(f"\nレビュー長の統計:")
        print(f"平均: {review_lengths.mean():.1f}")
        print(f"中央値: {review_lengths.median():.1f}")
        print(f"最小: {review_lengths.min()}")
        print(f"最大: {review_lengths.max()}")
        
        print(f"\n欠損値の数:")
        print(df.isnull().sum())

    def cleanup(self):
        """一時ファイルのクリーンアップ"""
        if self.raw_file.exists():
            os.remove(self.raw_file)
            print(f"\nRemoved raw data file: {self.raw_file}")

    def run(self):
        """メインの実行関数"""
        try:
            print(f"Starting data collection for {self.category} category...")
            self.download_data()
            df = self.process_data()
            self.check_data_quality(df)
            
            cleanup = input("\nClean up raw data file? (y/n): ").lower()
            if cleanup == 'y':
                self.cleanup()
            
            return df
            
        except Exception as e:
            print(f"Error in data collection process: {e}")
            return None

def main():
    # 設定
    CATEGORY = "Electronics"
    SAMPLE_SIZE = 10000
    MIN_WORDS = 20
    
    # データ収集の実行
    collector = AmazonDataCollector(
        category=CATEGORY,
        sample_size=SAMPLE_SIZE,
        min_words=MIN_WORDS
    )
    
    df = collector.run()
    
    if df is not None:
        print("\nデータ収集が完了しました！")
        print(f"処理済みデータの保存先: {collector.processed_file}")

if __name__ == "__main__":
    main()
