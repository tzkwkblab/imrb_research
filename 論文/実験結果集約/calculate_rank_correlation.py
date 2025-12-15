#!/usr/bin/env python3
"""
順位一致の定量根拠（Spearman順位相関）計算スクリプト

入力: 論文/結果/追加実験/main_experiment_rerun_temperature0/main_experiment_statistics.json
出力: 論文/結果/追加実験/論文執筆用/dataset_comparison/統計/rank_correlation_analysis.json
"""

import json
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr
from typing import Dict, List, Any
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
INPUT_FILE = PROJECT_ROOT / "論文" / "結果" / "追加実験" / "main_experiment_rerun_temperature0" / "main_experiment_statistics.json"
OUTPUT_DIR = PROJECT_ROOT / "論文" / "結果" / "追加実験" / "論文執筆用" / "dataset_comparison" / "統計"
OUTPUT_FILE = OUTPUT_DIR / "rank_correlation_analysis.json"


def load_statistics(file_path: Path) -> Dict[str, Any]:
    """統計JSONファイルを読み込み"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_rank_correlation(bert_scores: List[float], llm_scores: List[float]) -> Dict[str, Any]:
    """Spearman順位相関を計算"""
    if len(bert_scores) != len(llm_scores):
        raise ValueError(f"スコアの長さが一致しません: bert={len(bert_scores)}, llm={len(llm_scores)}")
    
    if len(bert_scores) < 2:
        return {
            "correlation": None,
            "p_value": None,
            "n": len(bert_scores)
        }
    
    correlation, p_value = spearmanr(bert_scores, llm_scores)
    
    return {
        "correlation": float(correlation) if not np.isnan(correlation) else None,
        "p_value": float(p_value) if not np.isnan(p_value) else None,
        "n": len(bert_scores)
    }


def extract_aspect_scores(statistics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """アスペクト別のスコアを抽出"""
    aspect_stats = statistics.get("statistics", {}).get("aspect_stats", {})
    
    results = []
    for aspect, stats in aspect_stats.items():
        bert_scores = stats.get("bert_scores", [])
        llm_scores = stats.get("llm_scores", [])
        
        if bert_scores and llm_scores:
            avg_bert = stats.get("avg_bert_score", 0)
            avg_llm = stats.get("avg_llm_score", 0)
            
            dataset = determine_dataset(aspect)
            
            results.append({
                "aspect": aspect,
                "dataset": dataset,
                "bert_score": avg_bert,
                "llm_score": avg_llm,
                "bert_scores": bert_scores,
                "llm_scores": llm_scores
            })
    
    return results


def determine_dataset(aspect: str) -> str:
    """アスペクト名からデータセットを判定"""
    semeval_aspects = ["food", "service", "battery", "screen"]
    steam_aspects = ["gameplay", "visual", "story", "audio"]
    
    if aspect in semeval_aspects:
        return "semeval"
    elif aspect in steam_aspects:
        return "steam"
    else:
        return "goemotions"


def calculate_rankings(scores: List[float], reverse: bool = True) -> List[int]:
    """スコアから順位を計算（高い順）"""
    sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=reverse)
    ranks = [0] * len(scores)
    for rank, idx in enumerate(sorted_indices, start=1):
        ranks[idx] = rank
    return ranks


def analyze_rank_correlation(statistics: Dict[str, Any]) -> Dict[str, Any]:
    """順位相関分析を実行"""
    aspect_scores = extract_aspect_scores(statistics)
    
    all_bert_scores = [item["bert_score"] for item in aspect_scores]
    all_llm_scores = [item["llm_score"] for item in aspect_scores]
    
    overall_correlation = calculate_rank_correlation(all_bert_scores, all_llm_scores)
    
    dataset_correlations = {}
    for dataset in ["semeval", "goemotions", "steam"]:
        dataset_items = [item for item in aspect_scores if item["dataset"] == dataset]
        if len(dataset_items) >= 2:
            dataset_bert = [item["bert_score"] for item in dataset_items]
            dataset_llm = [item["llm_score"] for item in dataset_items]
            dataset_correlations[dataset] = calculate_rank_correlation(dataset_bert, dataset_llm)
        else:
            dataset_correlations[dataset] = {
                "correlation": None,
                "p_value": None,
                "n": len(dataset_items)
            }
    
    bert_ranks = calculate_rankings(all_bert_scores)
    llm_ranks = calculate_rankings(all_llm_scores)
    
    rank_matches = {
        "top3_match": 0,
        "bottom3_match": 0,
        "top3_aspects_bert": [],
        "top3_aspects_llm": [],
        "bottom3_aspects_bert": [],
        "bottom3_aspects_llm": []
    }
    
    if len(aspect_scores) >= 3:
        bert_top3_indices = sorted(range(len(all_bert_scores)), key=lambda i: all_bert_scores[i], reverse=True)[:3]
        llm_top3_indices = sorted(range(len(all_llm_scores)), key=lambda i: all_llm_scores[i], reverse=True)[:3]
        bert_bottom3_indices = sorted(range(len(all_bert_scores)), key=lambda i: all_bert_scores[i], reverse=False)[:3]
        llm_bottom3_indices = sorted(range(len(all_llm_scores)), key=lambda i: all_llm_scores[i], reverse=False)[:3]
        
        rank_matches["top3_aspects_bert"] = [aspect_scores[i]["aspect"] for i in bert_top3_indices]
        rank_matches["top3_aspects_llm"] = [aspect_scores[i]["aspect"] for i in llm_top3_indices]
        rank_matches["bottom3_aspects_bert"] = [aspect_scores[i]["aspect"] for i in bert_bottom3_indices]
        rank_matches["bottom3_aspects_llm"] = [aspect_scores[i]["aspect"] for i in llm_bottom3_indices]
        
        rank_matches["top3_match"] = len(set(bert_top3_indices) & set(llm_top3_indices))
        rank_matches["bottom3_match"] = len(set(bert_bottom3_indices) & set(llm_bottom3_indices))
    
    scatter_data = [
        {
            "aspect": item["aspect"],
            "dataset": item["dataset"],
            "bert_score": item["bert_score"],
            "llm_score": item["llm_score"],
            "bert_rank": bert_ranks[i],
            "llm_rank": llm_ranks[i]
        }
        for i, item in enumerate(aspect_scores)
    ]
    
    return {
        "overall": overall_correlation,
        "by_dataset": dataset_correlations,
        "rank_matches": rank_matches,
        "scatter_data": scatter_data,
        "aspect_details": aspect_scores
    }


def main():
    """メイン処理"""
    print(f"統計ファイルを読み込み: {INPUT_FILE}")
    statistics = load_statistics(INPUT_FILE)
    
    print("順位相関分析を実行中...")
    results = analyze_rank_correlation(statistics)
    
    output_data = {
        "metadata": {
            "calculated_at": datetime.now().isoformat(),
            "source_data": str(INPUT_FILE.relative_to(PROJECT_ROOT)),
            "description": "SBERT類似度とLLM評価の順位相関分析"
        },
        "results": results
    }
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"結果を保存: {OUTPUT_FILE}")
    print(f"\n全体のSpearman順位相関: {results['overall']['correlation']:.4f} (p={results['overall']['p_value']:.4f})")
    
    semeval_corr = results['by_dataset']['semeval']['correlation']
    semeval_str = f"{semeval_corr:.4f}" if semeval_corr is not None else "N/A"
    print(f"SemEval: {semeval_str}")
    
    goemotions_corr = results['by_dataset']['goemotions']['correlation']
    goemotions_str = f"{goemotions_corr:.4f}" if goemotions_corr is not None else "N/A"
    print(f"GoEmotions: {goemotions_str}")
    
    steam_corr = results['by_dataset']['steam']['correlation']
    steam_str = f"{steam_corr:.4f}" if steam_corr is not None else "N/A"
    print(f"Steam: {steam_str}")


if __name__ == "__main__":
    main()

