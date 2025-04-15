import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
import re

def analyze_reviews():
    # データの読み込み
    file_path = Path('data/processed/electronics_reviews.csv')
    df = pd.read_csv(file_path)
    
    # 基本情報の出力
    print("=== データセット基本情報 ===")
    print(f"データ件数: {len(df)}")
    print(f"\nカラム一覧:")
    print(df.columns.tolist())
    
    # レビューテキストの基本統計
    df['review_length'] = df['review_text'].str.split().str.len()
    
    print("\n=== レビュー長の統計 ===")
    length_stats = df['review_length'].describe()
    print(f"平均: {length_stats['mean']:.1f}")
    print(f"標準偏差: {length_stats['std']:.1f}")
    print(f"最小: {length_stats['min']:.0f}")
    print(f"最大: {length_stats['max']:.0f}")
    
    # 評価の分布
    print("\n=== 評価の分布 ===")
    rating_dist = df['rating'].value_counts().sort_index()
    for rating, count in rating_dist.items():
        percentage = (count / len(df)) * 100
        print(f"{rating}星: {count}件 ({percentage:.1f}%)")

def analyze_review_patterns(df, n_samples=10000):
    """
    レビューの特徴的なパターンを分析する関数
    
    Parameters:
    -----------
    df : DataFrame
        レビューデータ
    n_samples : int
        分析するサンプル数
    """
    patterns = {
        '価格関連': r'\b(price|cost|cheap|expensive|worth|value|money|affordable|budget)\b',
        '比較表現': r'\b(compared to|better than|worse than|previous|other|similar|than|before)\b',
        '感情表現': r'\b(happy|satisfied|disappointed|great|terrible|excellent|amazing|poor|love|hate)\b',
        '品質関連': r'\b(quality|performance|durability|reliable|broke|sturdy|solid|well made|build)\b',
    }
    
    pattern_stats = defaultdict(lambda: {'count': 0, 'samples': [], 'matches': []})
    sample_df = df.sample(n=min(n_samples, len(df)), random_state=42)
    
    for text in sample_df['review_text']:
        for pattern_name, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            found = False
            for match in matches:
                if not found:
                    pattern_stats[pattern_name]['count'] += 1
                    found = True
                if len(pattern_stats[pattern_name]['samples']) < 3:
                    # マッチした部分の前後100文字を取得
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    sample = f"...{text[start:end]}..."
                    pattern_stats[pattern_name]['samples'].append(sample)
                    pattern_stats[pattern_name]['matches'].append(match.group())
    
    return pattern_stats

def display_reviews(n_samples=10, analyze_patterns=True):
    """
    レビューデータを表示し、パターンを分析する関数
    
    Parameters:
    -----------
    n_samples : int
        表示するレビューの数（デフォルト: 10件）
    analyze_patterns : bool
        パターン分析を行うかどうか
    """
    # データファイルのパス
    file_path = Path("data/processed/electronics_reviews.csv")
    
    try:
        # CSVファイルの読み込み
        df = pd.read_csv(file_path)
        
        # 基本情報の表示
        print(f"\n=== レビューデータの基本情報 ===")
        print(f"総レビュー数: {len(df)}")
        print(f"平均評価: {df['rating'].mean():.2f}")
        
        # 評価の分布を表示
        print("\n=== 評価の分布 ===")
        rating_dist = df['rating'].value_counts().sort_index()
        for rating, count in rating_dist.items():
            print(f"{rating}星: {count}件 ({count/len(df)*100:.1f}%)")
        
        # サンプルレビューの表示
        print(f"\n=== サンプルレビュー（{n_samples}件） ===")
        samples = df.sample(n=n_samples, random_state=42)
        for i, (text, rating) in enumerate(zip(samples['review_text'], samples['rating']), 1):
            print(f"\n[レビュー {i}] {rating}星")
            print(f"テキスト: {text[:200]}..." if len(text) > 200 else f"テキスト: {text}")
            print("-" * 80)
        
        # パターン分析の実行と表示
        if analyze_patterns:
            print("\n=== 特徴的なパターンの分析 ===")
            pattern_stats = analyze_review_patterns(df)
            
            for pattern_name, stats in pattern_stats.items():
                percentage = (stats['count'] / len(df)) * 100
                print(f"\n【{pattern_name}】")
                print(f"出現率: {percentage:.1f}%（{stats['count']}件）")
                print("例：")
                for i, sample in enumerate(stats['samples'], 1):
                    print(f"{i}. {sample}")
        
        # 評価ごとの特徴語分析
        print("\n=== 評価ごとの特徴的な表現 ===")
        for rating in sorted(df['rating'].unique()):
            rating_reviews = df[df['rating'] == rating]['review_text'].str.cat(sep=' ')
            # ここに評価ごとの特徴語抽出ロジックを追加予定
            
    except FileNotFoundError:
        print(f"エラー: ファイル {file_path} が見つかりません。")
    except Exception as e:
        print(f"エラー: {str(e)}")

def suggest_features(df, n_features=15):
    """
    特徴定義の候補を提案する関数
    
    Parameters:
    -----------
    df : DataFrame
        レビューデータ
    n_features : int
        提案する特徴の数
    """
    # 基本的な特徴カテゴリ
    feature_categories = [
        "価格関連",
        "品質・性能",
        "比較表現",
        "感情表現",
        "使用経験",
        "デザイン",
        "サービス",
        "機能性",
        "信頼性",
        "推奨度"
    ]
    
    print("\n=== 特徴定義の候補 ===")
    for i, category in enumerate(feature_categories, 1):
        print(f"\n{i}. {category}に関する特徴:")
        # ここに各カテゴリの具体的な特徴候補を追加予定

def display_reviews_for_feature_definition(n_samples=20):
    """
    特徴定義のためにレビューを表示する関数
    
    Parameters:
    -----------
    n_samples : int
        表示するレビューの数（デフォルト: 20件）
    """
    file_path = Path("data/processed/electronics_reviews.csv")
    
    try:
        df = pd.read_csv(file_path)
        
        print(f"\n=== 特徴定義用レビューサンプル（{n_samples}件） ===")
        samples = df.sample(n=n_samples, random_state=42)
        
        for i, (text, rating) in enumerate(zip(samples['review_text'], samples['rating']), 1):
            print(f"\n[レビュー {i}] {rating}星")
            print(f"テキスト: {text}")
            print("-" * 80)
            
    except FileNotFoundError:
        print(f"エラー: ファイル {file_path} が見つかりません。")
    except Exception as e:
        print(f"エラー: {str(e)}")

if __name__ == "__main__":
    display_reviews_for_feature_definition()