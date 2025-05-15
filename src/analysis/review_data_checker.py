"""
このスクリプトについて

- 元データ（data/processed/electronics_reviews.csv）の
  レビュー情報を確認・要約表示できます。
- また、レーティング分布を維持したまま
  サンプルデータ（例：300件）を抽出し、
  src/data/examples/sample_reviews_300.csv
  に保存します。

主な出力先:
  src/data/examples/sample_reviews_300.csv
"""
import pandas as pd
from pathlib import Path

def create_sample_dataset(sample_size=300):
    """レーティングの分布を保持したまま指定件数のサンプルを抽出してCSVファイルに保存"""
    # CSVファイルを読み込む
    df = pd.read_csv("data/processed/electronics_reviews.csv")
    
    # レーティングの分布を保持したままランダムサンプリング
    sampled_df = df.groupby('rating', group_keys=False).apply(
        lambda x: x.sample(n=int(sample_size * len(x) / len(df)))
    ).reset_index(drop=True)
    
    # 保存先ディレクトリの作成
    output_dir = Path("src/data/examples")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # サンプルデータを保存
    output_file = output_dir / "sample_reviews_300.csv"
    sampled_df.to_csv(output_file, index=False)
    
    print(f"\n=== サンプルデータセット作成完了 ===")
    print(f"保存先: {output_file}")
    print(f"\n=== サンプルデータの内容 ===")
    print(f"レコード数: {len(sampled_df)}")
    print("\n=== レーティング分布 ===")
    print(sampled_df['rating'].value_counts().sort_index())

def check_review_data():
    """元のデータセットの基本情報を表示"""
    # CSVファイルを読み込む
    df = pd.read_csv("data/processed/electronics_reviews.csv")
    
    # データの基本情報を表示
    print("=== データの基本情報 ===")
    print(f"レコード数: {len(df)}")
    print("\n=== カラム一覧 ===")
    print(df.columns.tolist())
    print("\n=== 最初の3件のレビュー ===")
    print(df.head(3))
    
    # レーティングの分布を確認
    print("\n=== レーティングの分布 ===")
    print(df['rating'].value_counts().sort_index())

if __name__ == "__main__":
    # 元のデータセットの情報を表示
    check_review_data()
    
    # サンプルデータセットを作成
    create_sample_dataset() 