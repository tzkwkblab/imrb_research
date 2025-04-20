"""
レビューデータから300件をランダムにサンプリングするスクリプト

## ストラティファイドサンプリング（層化抽出法）について
ストラティファイドサンプリングとは、母集団をある特性（この場合はレーティング）に基づいて
複数の層（stratum）に分け、各層から元の比率を保持しながらサンプリングを行う手法です。

### なぜレーティング分布を保持するのか
1. 代表性の確保
   - 商品レビューデータでは、レーティングの分布が重要な特性
   - 高評価（5星）が多く、低評価（1-2星）が少ない傾向がある
   - 単純なランダムサンプリングでは、少数の層（低評価）が適切に抽出されない可能性

2. 分析の信頼性
   - 特徴検出の精度評価では、各レーティング層での性能を確認する必要がある
   - 特に低評価レビューでの特徴検出が重要（問題点や改善点の抽出）
   - 分布を保持することで、元データと同様の条件での評価が可能

3. バイアスの防止
   - 単純ランダムサンプリングでは、偶然により特定のレーティングが過多/過少になる可能性
   - 層化抽出により、各レーティング層の比率を保証
   - 評価実験の再現性と一般性を向上

### 実装方法
1. レーティングごとにグループ化
2. 各グループから、元の分布比率に基づいて抽出
3. 合計が目標サンプルサイズになるように調整

主な特徴：
- レーティング分布を保持したストラティファイドサンプリング
- 結果をCSVファイルとして保存
"""

import pandas as pd
from pathlib import Path
import numpy as np

def create_sample_dataset(
    input_file: str = "data/processed/electronics_reviews.csv",
    output_file: str = "src/data/examples/sample_reviews_300.csv",
    sample_size: int = 300,
    random_state: int = 42
) -> None:
    """
    レビューデータからサンプルデータセットを作成
    
    Args:
        input_file: 入力ファイルのパス
        output_file: 出力ファイルのパス
        sample_size: サンプリングするデータ数
        random_state: 乱数シード
    """
    # 入力ファイルの読み込み
    print(f"元データの読み込み中: {input_file}")
    df = pd.read_csv(input_file)
    
    # 元データの情報表示
    print("\n=== 元データの情報 ===")
    print(f"総レビュー数: {len(df)}")
    print("\nレーティング分布:")
    rating_dist = df['rating'].value_counts().sort_index()
    for rating, count in rating_dist.items():
        percentage = (count / len(df)) * 100
        print(f"  {rating}星: {count}件 ({percentage:.1f}%)")
    
    # レーティングごとの比率を保持したストラティファイドサンプリング
    sampled_df = df.groupby('rating', group_keys=False).apply(
        lambda x: x.sample(
            n=max(1, int(sample_size * len(x) / len(df))),
            random_state=random_state
        )
    )
    
    # サンプルサイズを厳密に300件に調整
    if len(sampled_df) > sample_size:
        sampled_df = sampled_df.sample(n=sample_size, random_state=random_state)
    elif len(sampled_df) < sample_size:
        # 不足分を全体からランダムに追加
        additional_samples = df.sample(
            n=sample_size - len(sampled_df),
            random_state=random_state
        )
        sampled_df = pd.concat([sampled_df, additional_samples])
    
    # サンプリング結果の情報表示
    print("\n=== サンプリング結果 ===")
    print(f"サンプル数: {len(sampled_df)}")
    print("\nレーティング分布:")
    sample_dist = sampled_df['rating'].value_counts().sort_index()
    for rating, count in sample_dist.items():
        percentage = (count / len(sampled_df)) * 100
        print(f"  {rating}星: {count}件 ({percentage:.1f}%)")
    
    # 出力ディレクトリの作成
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 結果の保存
    sampled_df.to_csv(output_file, index=False)
    print(f"\nサンプルデータを保存しました: {output_file}")

if __name__ == "__main__":
    create_sample_dataset() 