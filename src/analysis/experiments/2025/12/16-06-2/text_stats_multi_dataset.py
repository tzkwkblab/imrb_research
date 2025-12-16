#!/usr/bin/env python3
import os, json, csv, logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
import sys

import numpy as np
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# sys.path 用設定（必須パターンに従うが本スクリプトでは直接未使用）
utils_dir = Path(__file__).resolve().parents[2] / "utils"
sys.path.append(str(utils_dir))
sys.path.append(str(utils_dir / "LLM"))


def tokenize(text: str) -> List[str]:
    return text.lower().split()


def compute_text_stats(texts: Iterable[str]) -> Dict[str, Any]:
    clean_texts = [t.strip() for t in texts if isinstance(t, str) and t.strip()]
    token_lists = [tokenize(t) for t in clean_texts]
    word_counts = [len(toks) for toks in token_lists]
    vocab: set[str] = set()
    for toks in token_lists:
        vocab.update(toks)

    total_tokens = sum(word_counts)
    return {
        "n_samples": len(clean_texts),
        "word_count_mean": float(np.mean(word_counts)) if word_counts else 0.0,
        "word_count_median": float(np.median(word_counts)) if word_counts else 0.0,
        "word_count_max": int(max(word_counts)) if word_counts else 0,
        "word_count_min": int(min(word_counts)) if word_counts else 0,
        "vocab_size": len(vocab),
        "ttr": float(len(vocab) / total_tokens) if total_tokens else 0.0,
    }


def compute_label_stats(label_lists: Iterable[List[str]]) -> Dict[str, Any]:
    labels_per_sample = [len(labels) for labels in label_lists]
    label_word_counts = [
        len(tokenize(label))
        for labels in label_lists
        for label in labels
        if isinstance(label, str) and label.strip()
    ]

    return {
        "mean_labels_per_sample": float(np.mean(labels_per_sample)) if labels_per_sample else 0.0,
        "pct_multi_label": float(
            sum(1 for c in labels_per_sample if c >= 2) / len(labels_per_sample)
        )
        if labels_per_sample
        else 0.0,
        "ref_label_mean_words": float(np.mean(label_word_counts)) if label_word_counts else 0.0,
        "ref_label_median_words": float(np.median(label_word_counts))
        if label_word_counts
        else 0.0,
    }


def merge_stats(texts: List[str], label_lists: List[List[str]]) -> Dict[str, Any]:
    text_stats = compute_text_stats(texts)
    label_stats = compute_label_stats(label_lists)
    merged = {**text_stats, **label_stats}
    return merged


def analyze_goemotions(repo_root: Path) -> Dict[str, Any]:
    base_dir = repo_root / "data" / "external" / "goemotions" / "kaggle-debarshichanda" / "current" / "data"
    label_path = base_dir / "emotions.txt"
    label_names = [line.strip() for line in label_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    id_to_label = {idx: name for idx, name in enumerate(label_names)}

    def parse_label_cell(cell: Any) -> List[str]:
        raw = str(cell).strip()
        if raw == "" or raw.lower() == "nan":
            return []
        labels: List[str] = []
        for part in raw.split(","):
            part = part.strip()
            if part == "":
                continue
            if part.isdigit() and int(part) in id_to_label:
                labels.append(id_to_label[int(part)])
            else:
                labels.append(part)
        return labels

    split_files = {
        "train": base_dir / "train.tsv",
        "dev": base_dir / "dev.tsv",
        "test": base_dir / "test.tsv",
    }

    texts_by_split: Dict[str, List[str]] = {}
    labels_by_split: Dict[str, List[List[str]]] = {}

    for split, path in split_files.items():
        logger.info("GoEmotions %s file: %s", split, path)
        df = pd.read_csv(
            path,
            sep="\t",
            header=None,
            names=["text", "label_ids", "example_id"],
            quoting=csv.QUOTE_NONE,
            on_bad_lines="skip",
            encoding="utf-8",
        )
        texts = df["text"].astype(str).tolist()
        label_lists = [parse_label_cell(x) for x in df["label_ids"].tolist()]
        texts_by_split[split] = texts
        labels_by_split[split] = label_lists

    all_texts = [t for texts in texts_by_split.values() for t in texts]
    all_labels = [l for labels in labels_by_split.values() for l in labels]

    split_stats = {
        split: merge_stats(texts_by_split[split], labels_by_split[split]) for split in split_files
    }
    agg_stats = merge_stats(all_texts, all_labels)

    return {
        "dataset": "GoEmotions",
        "files": {k: str(v) for k, v in split_files.items()},
        "text_column": "col0 (text)",
        "label_column": "col1 (label_ids comma-separated)",
        "label_mapping": str(label_path),
        "splits": split_stats,
        "aggregate": agg_stats,
    }


def analyze_steam(repo_root: Path) -> Dict[str, Any]:
    base_dir = repo_root / "data" / "external" / "steam-review-aspect-dataset" / "current"
    split_files = {
        "train": base_dir / "train.csv",
        "test": base_dir / "test.csv",
    }
    aspect_cols = [
        "label_recommended",
        "label_story",
        "label_gameplay",
        "label_visual",
        "label_audio",
        "label_technical",
        "label_price",
        "label_suggestion",
    ]

    texts_by_split: Dict[str, List[str]] = {}
    labels_by_split: Dict[str, List[List[str]]] = {}

    for split, path in split_files.items():
        logger.info("Steam %s file: %s", split, path)
        df = pd.read_csv(path, encoding="utf-8", keep_default_na=False)

        texts: List[str] = []
        label_lists: List[List[str]] = []
        for _, row in df.iterrows():
            raw = str(row.get("review", "") or "")
            cleaned = str(row.get("cleaned_review", "") or "")
            text = cleaned.strip() if cleaned.strip() else raw.strip()
            if not text:
                continue

            labels = []
            for col in aspect_cols:
                val = row.get(col, 0)
                try:
                    val_num = float(val)
                except Exception:
                    val_num = 0.0
                if val_num >= 1.0:
                    labels.append(col.replace("label_", ""))

            texts.append(text)
            label_lists.append(labels)

        texts_by_split[split] = texts
        labels_by_split[split] = label_lists

    all_texts = [t for texts in texts_by_split.values() for t in texts]
    all_labels = [l for labels in labels_by_split.values() for l in labels]

    split_stats = {
        split: merge_stats(texts_by_split[split], labels_by_split[split]) for split in split_files
    }
    agg_stats = merge_stats(all_texts, all_labels)

    return {
        "dataset": "Steam Review Aspect",
        "files": {k: str(v) for k, v in split_files.items()},
        "text_column": "cleaned_review (fallback: review)",
        "label_columns": aspect_cols,
        "splits": split_stats,
        "aggregate": agg_stats,
    }


def parse_seg_file(path: Path) -> Tuple[List[str], List[List[str]]]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) % 3 != 0:
        logger.warning("Line count is not divisible by 3 for %s", path)
    texts: List[str] = []
    labels: List[List[str]] = []
    for i in range(0, len(lines) - 2, 3):
        text = lines[i]
        aspect = lines[i + 1]
        texts.append(text)
        labels.append([aspect])
    return texts, labels


def analyze_semeval(repo_root: Path) -> Dict[str, Any]:
    base_dir = (
        repo_root
        / "data"
        / "external"
        / "absa-review-dataset"
        / "pyabsa-integrated"
        / "current"
        / "ABSADatasets"
        / "datasets"
        / "apc_datasets"
        / "110.SemEval"
    )

    targets = {
        "laptop14": {
            "train": base_dir / "113.laptop14" / "Laptops_Train.xml.seg",
            "test": base_dir / "113.laptop14" / "Laptops_Test_Gold.xml.seg",
        },
        "restaurant14": {
            "train": base_dir / "114.restaurant14" / "Restaurants_Train.xml.seg",
            "test": base_dir / "114.restaurant14" / "Restaurants_Test_Gold.xml.seg",
        },
    }

    dataset_entries = []
    for name, split_files in targets.items():
        texts_by_split: Dict[str, List[str]] = {}
        labels_by_split: Dict[str, List[List[str]]] = {}

        for split, path in split_files.items():
            logger.info("SemEval %s %s file: %s", name, split, path)
            texts, labels = parse_seg_file(path)
            texts_by_split[split] = texts
            labels_by_split[split] = labels

        all_texts = [t for texts in texts_by_split.values() for t in texts]
        all_labels = [l for labels in labels_by_split.values() for l in labels]

        split_stats = {split: merge_stats(texts, labels) for split, texts, labels in [
            (s, texts_by_split[s], labels_by_split[s]) for s in split_files
        ]}
        agg_stats = merge_stats(all_texts, all_labels)

        dataset_entries.append(
            {
                "dataset": f"SemEval-2014 {name}",
                "files": {k: str(v) for k, v in split_files.items()},
                "text_column": "line0 in 3-line block ($T$ placeholder)",
                "label_column": "line1 in 3-line block (aspect term)",
                "splits": split_stats,
                "aggregate": agg_stats,
            }
        )

    return dataset_entries


def build_markdown_table(entries: List[Dict[str, Any]]) -> str:
    headers = [
        "dataset",
        "n_samples",
        "mean_words",
        "median_words",
        "max_words",
        "vocab_types",
        "ttr",
        "mean_labels_per_sample",
        "pct_multi_label",
        "ref_label_median_words",
    ]
    lines = ["|" + "|".join(headers) + "|", "|" + "|".join(["---"] * len(headers)) + "|"]
    for entry in entries:
        stats = entry["aggregate"]
        row = [
            entry["dataset"],
            f"{stats['n_samples']}",
            f"{stats['word_count_mean']:.2f}",
            f"{stats['word_count_median']:.2f}",
            f"{stats['word_count_max']}",
            f"{stats['vocab_size']}",
            f"{stats['ttr']:.4f}",
            f"{stats['mean_labels_per_sample']:.2f}",
            f"{stats['pct_multi_label']*100:.2f}%",
            f"{stats['ref_label_median_words']:.2f}",
        ]
        lines.append("|" + "|".join(row) + "|")
    return "\n".join(lines)


def main():
    repo_root = Path(__file__).resolve().parents[6]
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    goemotions = analyze_goemotions(repo_root)
    steam = analyze_steam(repo_root)
    semeval_entries = analyze_semeval(repo_root)

    all_entries = [goemotions, steam] + semeval_entries

    markdown_table = build_markdown_table(all_entries)
    print(markdown_table)

    llm_eval_settings = {
        "models": ["GPT-4o-mini (main)", "GPT-5.1 (model comparison)", "GPT-4o (aspect explanation comparison)"],
        "temperature": 0.0,
        "rating_scale": "1-5, normalized via (score-1)/4",
        "prompt_source": "論文/chapters/04_experiment.tex",
        "evaluation_runs": "single pass per pair",
    }

    summary = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "definitions": {
            "tokenization": "text.lower().split() (no punctuation removal)",
            "vocab": "unique tokens aggregated over all samples",
            "ttr": "types/tokens over aggregated texts",
            "label_count_per_sample": "number of labels linked to each sample (>=2 -> multi-label)",
            "ref_label_word_count": "len(label.lower().split()) per label string",
        },
        "datasets": all_entries,
        "llm_eval_settings": llm_eval_settings,
    }

    out_path = results_dir / f"text_stats_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Saved summary JSON: %s", out_path)


if __name__ == "__main__":
    main()

