#!/usr/bin/env python3
"""
Steamデータセットの定量統計計算スクリプト

入力: data/external/steam-review-aspect-dataset/current/train.csv, test.csv
出力: 論文/結果/追加実験/論文執筆用/dataset_comparison/統計/steam_dataset_statistics.json
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from collections import Counter
import re

PROJECT_ROOT = Path(__file__).parent.parent.parent
STEAM_DATA_DIR = PROJECT_ROOT / "data" / "external" / "steam-review-aspect-dataset" / "current"
OUTPUT_DIR = PROJECT_ROOT / "論文" / "結果" / "追加実験" / "論文執筆用" / "dataset_comparison" / "統計"
OUTPUT_FILE = OUTPUT_DIR / "steam_dataset_statistics.json"


def load_steam_data() -> pd.DataFrame:
    """Steamデータセットを読み込み"""
    train_path = STEAM_DATA_DIR / "train.csv"
    test_path = STEAM_DATA_DIR / "test.csv"
    
    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError(f"Steamデータセットが見つかりません: {STEAM_DATA_DIR}")
    
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    
    full_df = pd.concat([train_df, test_df], ignore_index=True)
    return full_df


def count_words(text: str) -> int:
    """テキストの語数をカウント"""
    if pd.isna(text) or text == "":
        return 0
    words = re.findall(r'\b\w+\b', str(text).lower())
    return len(words)


def count_sentences(text: str) -> int:
    """テキストの文数をカウント"""
    if pd.isna(text) or text == "":
        return 0
    sentences = re.split(r'[.!?]+', str(text))
    return len([s for s in sentences if s.strip()])


def calculate_review_length_stats(df: pd.DataFrame, text_column: str = "review") -> Dict[str, Any]:
    """レビュー長統計を計算"""
    texts = df[text_column].dropna().astype(str)
    
    char_lengths = texts.str.len()
    word_counts = texts.apply(count_words)
    sentence_counts = texts.apply(count_sentences)
    
    return {
        "character_length": {
            "mean": float(char_lengths.mean()),
            "median": float(char_lengths.median()),
            "q1": float(char_lengths.quantile(0.25)),
            "q3": float(char_lengths.quantile(0.75)),
            "min": int(char_lengths.min()),
            "max": int(char_lengths.max()),
            "std": float(char_lengths.std())
        },
        "word_count": {
            "mean": float(word_counts.mean()),
            "median": float(word_counts.median()),
            "q1": float(word_counts.quantile(0.25)),
            "q3": float(word_counts.quantile(0.75)),
            "min": int(word_counts.min()),
            "max": int(word_counts.max()),
            "std": float(word_counts.std())
        },
        "sentence_count": {
            "mean": float(sentence_counts.mean()),
            "median": float(sentence_counts.median()),
            "q1": float(sentence_counts.quantile(0.25)),
            "q3": float(sentence_counts.quantile(0.75)),
            "min": int(sentence_counts.min()),
            "max": int(sentence_counts.max()),
            "std": float(sentence_counts.std())
        }
    }


def calculate_vocabulary_diversity(df: pd.DataFrame, text_column: str = "review") -> Dict[str, Any]:
    """語彙多様性を計算"""
    texts = df[text_column].dropna().astype(str)
    
    all_words = []
    for text in texts:
        words = re.findall(r'\b\w+\b', text.lower())
        all_words.extend(words)
    
    word_counter = Counter(all_words)
    total_tokens = len(all_words)
    unique_types = len(word_counter)
    
    ttr = unique_types / total_tokens if total_tokens > 0 else 0
    
    return {
        "total_tokens": total_tokens,
        "unique_types": unique_types,
        "type_token_ratio": float(ttr),
        "top_10_words": dict(word_counter.most_common(10))
    }


def calculate_aspect_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """アスペクト統計を計算"""
    if "labels" not in df.columns:
        return {}
    
    aspect_counts = []
    multi_aspect_counts = {2: 0, 3: 0, 4: 0}
    
    for idx, row in df.iterrows():
        labels = row["labels"]
        if pd.isna(labels):
            continue
        
        if isinstance(labels, str):
            if labels.startswith('[') and labels.endswith(']'):
                labels = eval(labels)
            else:
                labels = [labels]
        
        if isinstance(labels, list):
            aspect_count = len(labels)
            aspect_counts.append(aspect_count)
            
            if aspect_count >= 2:
                multi_aspect_counts[2] += 1
            if aspect_count >= 3:
                multi_aspect_counts[3] += 1
            if aspect_count >= 4:
                multi_aspect_counts[4] += 1
    
    if not aspect_counts:
        return {}
    
    aspect_counts = np.array(aspect_counts)
    total_reviews = len(aspect_counts)
    
    return {
        "mean_aspects_per_review": float(aspect_counts.mean()),
        "median_aspects_per_review": float(np.median(aspect_counts)),
        "max_aspects_per_review": int(aspect_counts.max()),
        "min_aspects_per_review": int(aspect_counts.min()),
        "multi_aspect_rate": {
            "2_or_more": float(multi_aspect_counts[2] / total_reviews) if total_reviews > 0 else 0,
            "3_or_more": float(multi_aspect_counts[3] / total_reviews) if total_reviews > 0 else 0,
            "4_or_more": float(multi_aspect_counts[4] / total_reviews) if total_reviews > 0 else 0
        }
    }


def calculate_steam_statistics() -> Dict[str, Any]:
    """Steamデータセットの統計を計算"""
    print(f"Steamデータセットを読み込み: {STEAM_DATA_DIR}")
    df = load_steam_data()
    
    print(f"総レビュー数: {len(df)}")
    
    text_column = "review"
    if "cleaned_review" in df.columns:
        text_column = "cleaned_review"
    
    print("レビュー長統計を計算中...")
    length_stats = calculate_review_length_stats(df, text_column)
    
    print("語彙多様性を計算中...")
    vocab_stats = calculate_vocabulary_diversity(df, text_column)
    
    print("アスペクト統計を計算中...")
    aspect_stats = calculate_aspect_statistics(df)
    
    return {
        "total_reviews": int(len(df)),
        "review_length": length_stats,
        "vocabulary_diversity": vocab_stats,
        "aspect_statistics": aspect_stats
    }


def main():
    """メイン処理"""
    print("Steamデータセットの統計を計算中...")
    results = calculate_steam_statistics()
    
    output_data = {
        "metadata": {
            "calculated_at": datetime.now().isoformat(),
            "source_data": str(STEAM_DATA_DIR.relative_to(PROJECT_ROOT)),
            "description": "Steamデータセットの定量統計（レビュー長、語彙多様性、アスペクト統計）"
        },
        "results": results
    }
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"結果を保存: {OUTPUT_FILE}")
    print(f"\n平均文字数: {results['review_length']['character_length']['mean']:.1f}")
    print(f"平均語数: {results['review_length']['word_count']['mean']:.1f}")
    print(f"平均文数: {results['review_length']['sentence_count']['mean']:.1f}")
    print(f"語彙タイプ数: {results['vocabulary_diversity']['unique_types']}")
    print(f"TTR: {results['vocabulary_diversity']['type_token_ratio']:.4f}")


if __name__ == "__main__":
    main()

