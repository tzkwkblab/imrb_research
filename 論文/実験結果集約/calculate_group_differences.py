#!/usr/bin/env python3
"""
データセット間の統計的差分計算スクリプト

入力: データセットファイル（Steam, SemEval, GoEmotions）
出力: 論文/結果/追加実験/論文執筆用/dataset_comparison/統計/group_differences.json
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
from collections import Counter
import re
from scipy.stats import entropy

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "論文" / "結果" / "追加実験" / "論文執筆用" / "dataset_comparison" / "統計"
OUTPUT_FILE = OUTPUT_DIR / "group_differences.json"

STEAM_DATA_DIR = PROJECT_ROOT / "data" / "external" / "steam-review-aspect-dataset" / "current"
SEMEVAL_DATA_DIR = PROJECT_ROOT / "data" / "external" / "absa-review-dataset" / "pyabsa-integrated" / "current"
GOEMOTIONS_DATA_DIR = PROJECT_ROOT / "data" / "external" / "goemotions" / "kaggle-debarshichanda" / "current"


def load_steam_data() -> pd.DataFrame:
    """Steamデータセットを読み込み"""
    train_path = STEAM_DATA_DIR / "train.csv"
    test_path = STEAM_DATA_DIR / "test.csv"
    
    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError(f"Steamデータセットが見つかりません: {STEAM_DATA_DIR}")
    
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    return pd.concat([train_df, test_df], ignore_index=True)


def extract_words(text: str) -> List[str]:
    """テキストから単語を抽出"""
    if pd.isna(text) or text == "":
        return []
    return re.findall(r'\b\w+\b', str(text).lower())


def calculate_word_distribution(texts: List[str]) -> Dict[str, float]:
    """語彙分布を計算"""
    all_words = []
    for text in texts:
        words = extract_words(text)
        all_words.extend(words)
    
    word_counter = Counter(all_words)
    total = sum(word_counter.values())
    
    if total == 0:
        return {}
    
    return {word: count / total for word, count in word_counter.items()}


def calculate_kl_divergence(p: Dict[str, float], q: Dict[str, float]) -> float:
    """KLダイバージェンスを計算"""
    all_words = set(p.keys()) | set(q.keys())
    
    kl_sum = 0.0
    for word in all_words:
        p_val = p.get(word, 1e-10)
        q_val = q.get(word, 1e-10)
        
        if p_val > 0:
            kl_sum += p_val * np.log(p_val / q_val)
    
    return float(kl_sum)


def calculate_vocabulary_overlap(vocab_a: set, vocab_b: set) -> Dict[str, float]:
    """語彙の重複率を計算"""
    intersection = vocab_a & vocab_b
    union = vocab_a | vocab_b
    
    if len(union) == 0:
        return {
            "overlap_ratio": 0.0,
            "intersection_size": 0,
            "union_size": 0
        }
    
    return {
        "overlap_ratio": float(len(intersection) / len(union)),
        "intersection_size": len(intersection),
        "union_size": len(union)
    }


def split_by_aspect(df: pd.DataFrame, aspect: str, dataset: str) -> Tuple[List[str], List[str]]:
    """アスペクトでグループA/Bに分割"""
    group_a_texts = []
    group_b_texts = []
    
    if dataset == "steam":
        if "labels" not in df.columns:
            return [], []
        
        text_column = "review"
        if "cleaned_review" in df.columns:
            text_column = "cleaned_review"
        
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
                if aspect in labels:
                    group_a_texts.append(str(row[text_column]))
                else:
                    group_b_texts.append(str(row[text_column]))
    
    elif dataset == "semeval":
        if "aspect" not in df.columns:
            return [], []
        
        text_column = "text"
        if "review" in df.columns:
            text_column = "review"
        
        for idx, row in df.iterrows():
            row_aspect = str(row.get("aspect", "")).lower()
            if row_aspect == aspect.lower():
                group_a_texts.append(str(row[text_column]))
            else:
                group_b_texts.append(str(row[text_column]))
    
    elif dataset == "goemotions":
        if "emotions" not in df.columns:
            return [], []
        
        text_column = "text"
        if "comment" in df.columns:
            text_column = "comment"
        
        for idx, row in df.iterrows():
            emotions = row["emotions"]
            if pd.isna(emotions):
                continue
            
            if isinstance(emotions, str):
                if emotions.startswith('[') and emotions.endswith(']'):
                    emotions = eval(emotions)
                else:
                    emotions = [emotions]
            
            if isinstance(emotions, list):
                if aspect in [str(e).lower() for e in emotions]:
                    group_a_texts.append(str(row[text_column]))
                else:
                    group_b_texts.append(str(row[text_column]))
    
    return group_a_texts, group_b_texts


def analyze_group_differences(dataset: str, aspect: str, df: pd.DataFrame) -> Dict[str, Any]:
    """グループA/B間の統計的差分を分析"""
    group_a_texts, group_b_texts = split_by_aspect(df, aspect, dataset)
    
    if len(group_a_texts) == 0 or len(group_b_texts) == 0:
        return {
            "error": "グループAまたはBが空です",
            "group_a_size": len(group_a_texts),
            "group_b_size": len(group_b_texts)
        }
    
    group_a_dist = calculate_word_distribution(group_a_texts)
    group_b_dist = calculate_word_distribution(group_b_texts)
    
    kl_div = calculate_kl_divergence(group_a_dist, group_b_dist)
    
    vocab_a = set(group_a_dist.keys())
    vocab_b = set(group_b_dist.keys())
    vocab_overlap = calculate_vocabulary_overlap(vocab_a, vocab_b)
    
    top10_a = dict(Counter(group_a_dist).most_common(10))
    top10_b = dict(Counter(group_b_dist).most_common(10))
    
    return {
        "group_a_size": len(group_a_texts),
        "group_b_size": len(group_b_texts),
        "kl_divergence": kl_div,
        "vocabulary_overlap": vocab_overlap,
        "top_10_words_group_a": top10_a,
        "top_10_words_group_b": top10_b
    }


def calculate_all_group_differences() -> Dict[str, Any]:
    """全データセットのグループ差分を計算"""
    results = {}
    
    steam_aspects = ["gameplay", "visual", "story", "audio"]
    semeval_aspects = ["food", "service", "battery", "screen"]
    goemotions_aspects = ["admiration", "amusement", "anger", "joy", "sadness"]
    
    if STEAM_DATA_DIR.exists():
        print("Steamデータセットを読み込み中...")
        steam_df = load_steam_data()
        results["steam"] = {}
        
        for aspect in steam_aspects:
            print(f"  Steam - {aspect} を分析中...")
            results["steam"][aspect] = analyze_group_differences("steam", aspect, steam_df)
    
    if SEMEVAL_DATA_DIR.exists():
        print("SemEvalデータセットを読み込み中...")
        try:
            semeval_train = SEMEVAL_DATA_DIR / "train.raw" / "train.raw"
            if semeval_train.exists():
                semeval_df = pd.read_csv(semeval_train, sep='\t', header=None, 
                                        names=['text', 'aspect', 'sentiment'], 
                                        encoding='utf-8', on_bad_lines='skip')
                results["semeval"] = {}
                
                for aspect in semeval_aspects:
                    print(f"  SemEval - {aspect} を分析中...")
                    results["semeval"][aspect] = analyze_group_differences("semeval", aspect, semeval_df)
        except Exception as e:
            print(f"  SemEvalデータの読み込みに失敗: {e}")
            results["semeval"] = {"error": str(e)}
    
    if GOEMOTIONS_DATA_DIR.exists():
        print("GoEmotionsデータセットを読み込み中...")
        try:
            goemotions_data_dir = GOEMOTIONS_DATA_DIR / "data"
            if goemotions_data_dir.exists():
                train_file = goemotions_data_dir / "train.tsv"
                if train_file.exists():
                    goemotions_df = pd.read_csv(train_file, sep='\t', header=None,
                                               names=['text', 'emotions', 'sentiment'],
                                               encoding='utf-8', on_bad_lines='skip')
                    results["goemotions"] = {}
                    
                    for aspect in goemotions_aspects:
                        print(f"  GoEmotions - {aspect} を分析中...")
                        results["goemotions"][aspect] = analyze_group_differences("goemotions", aspect, goemotions_df)
        except Exception as e:
            print(f"  GoEmotionsデータの読み込みに失敗: {e}")
            results["goemotions"] = {"error": str(e)}
    
    return results


def main():
    """メイン処理"""
    print("データセット間の統計的差分を計算中...")
    results = calculate_all_group_differences()
    
    output_data = {
        "metadata": {
            "calculated_at": datetime.now().isoformat(),
            "description": "グループA/B間の統計的差分（KL divergence、語彙重複率など）"
        },
        "results": results
    }
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"結果を保存: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

