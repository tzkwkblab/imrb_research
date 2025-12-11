import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, wilcoxon


ROOT = Path(__file__).resolve().parents[2]  # 論文/結果/追加実験/論文執筆用


def load_json(path: Path) -> Dict:
    with path.open() as f:
        return json.load(f)


def holm_correction(p_values: List[float]) -> List[float]:
    """Holm-Bonferroni 補正."""
    m = len(p_values)
    order = np.argsort(p_values)
    adjusted = np.empty(m)
    for rank, idx in enumerate(order):
        adjusted[idx] = (m - rank) * p_values[idx]
    # 単調性を担保
    for i in range(m - 2, -1, -1):
        adjusted[order[i]] = max(adjusted[order[i]], adjusted[order[i + 1]])
    return [min(1.0, p) for p in adjusted.tolist()]


def load_fewshot() -> pd.DataFrame:
    base = ROOT / "fewshot_llm_eval/steam/実験結果/individual"
    rows = []
    for path in base.glob("steam_*_*_*.json"):
        parts = path.stem.split("_")
        aspect = parts[1]
        few_shot = int(parts[2])
        data = load_json(path)
        rows.append({"aspect": aspect, "few_shot": few_shot, "bert": data["evaluation"]["bert_score"]})
    return pd.DataFrame(rows)


def load_group_size() -> pd.DataFrame:
    path = ROOT / "group_size_comparison/steam/実験結果/batch_results.json"
    data = load_json(path)["results"]
    rows = []
    for item in data:
        info = item["experiment_info"]
        rows.append(
            {
                "aspect": info["aspect"],
                "group_size": int(info["group_size"]),
                "bert": item["evaluation"]["bert_score"],
            }
        )
    return pd.DataFrame(rows)


def load_model_comparison() -> pd.DataFrame:
    base = ROOT / "model_comparison_temperature0/実験結果/individual"
    rows = []
    for path in base.glob("steam_*_*_*.json"):
        parts = path.stem.split("_")
        aspect = parts[1]
        model_tag = parts[3]
        model = "gpt-4o-mini" if model_tag == "4o-mini" else "gpt-5.1"
        data = load_json(path)
        rows.append({"aspect": aspect, "model": model, "bert": data["evaluation"]["bert_score"]})
    return pd.DataFrame(rows)


def load_aspect_desc() -> pd.DataFrame:
    base = ROOT / "aspect_description_comparison/steam/実験結果/individual"
    rows = []
    for path in base.glob("steam_*_*_*.json"):
        parts = path.stem.split("_")
        aspect = parts[1]
        condition = "with_desc" if "with" in parts else "no_desc"
        data = load_json(path)
        rows.append({"aspect": aspect, "condition": condition, "bert": data["evaluation"]["bert_score"]})
    return pd.DataFrame(rows)


def friedman_with_posthoc(df: pd.DataFrame, factor_col: str, value_col: str, block_col: str) -> Tuple[float, pd.DataFrame]:
    pivot = df.pivot(index=block_col, columns=factor_col, values=value_col).sort_index(axis=1)
    if pivot.isnull().any().any():
        raise ValueError(f"Missing data detected in pivot for {factor_col}.")
    stat, p_main = friedmanchisquare(*pivot.to_numpy().T)

    # Post-hoc Wilcoxon
    conditions = list(pivot.columns)
    pairs = []
    p_vals = []
    for i, a in enumerate(conditions):
        for b in conditions[i + 1 :]:
            stat_pair, p_pair = wilcoxon(pivot[a], pivot[b], zero_method="wilcox", correction=False, alternative="two-sided")
            pairs.append((a, b, stat_pair))
            p_vals.append(p_pair)
    p_adj = holm_correction(p_vals)
    post = pd.DataFrame(
        [
            {"cond_a": a, "cond_b": b, "stat": stat_val, "p_raw": p_raw, "p_holm": p_adj_val}
            for (a, b, stat_val), p_raw, p_adj_val in zip(pairs, p_vals, p_adj)
        ]
    )
    return p_main, post.sort_values("p_holm")


def paired_wilcoxon(df: pd.DataFrame, value_col: str, factor_a: str, factor_b: str, block_col: str) -> Dict:
    pivot = df.pivot(index=block_col, columns="condition", values=value_col)
    a, b = pivot[factor_a], pivot[factor_b]
    stat, p = wilcoxon(a, b, zero_method="wilcox", correction=False, alternative="two-sided")
    diff = (b - a).median()
    return {"n": len(a), "stat": stat, "p": p, "median_diff_b_minus_a": diff}


def main() -> None:
    out_dir = ROOT / "stat_tests/results"
    out_dir.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []
    lines.append("# 追加実験の有意差検定\n")
    lines.append("p値は Holm 補正済み（対応のある Wilcoxon）/Friedman です。\n")

    # Few-shot
    fewshot_df = load_fewshot()
    p_main, post = friedman_with_posthoc(fewshot_df, "few_shot", "bert", "aspect")
    lines.append("## Few-shot (0/1/3-shot, Steam 4アスペクト)\n")
    lines.append(f"- Friedman: p = {p_main:.4f}\n")
    lines.append("\n平均BERTScore (アスペクト平均):\n")
    mean_table = fewshot_df.groupby("few_shot")["bert"].mean().rename("mean_bert").to_frame()
    lines.append(mean_table.to_markdown() + "\n")
    lines.append("Post-hoc (Holm補正):\n")
    lines.append(post.to_markdown(index=False) + "\n")

    # Group size
    gs_df = load_group_size()
    p_main, post = friedman_with_posthoc(gs_df, "group_size", "bert", "aspect")
    lines.append("## グループサイズ比較 (50/100/150/200/300)\n")
    lines.append(f"- Friedman: p = {p_main:.4f}\n")
    lines.append("\n平均BERTScore (アスペクト平均):\n")
    mean_table = gs_df.groupby("group_size")["bert"].mean().rename("mean_bert").to_frame()
    lines.append(mean_table.to_markdown() + "\n")
    lines.append("Post-hoc (Holm補正):\n")
    lines.append(post.to_markdown(index=False) + "\n")

    # Model comparison
    model_df = load_model_comparison()
    pivot = model_df.pivot(index="aspect", columns="model", values="bert")
    stat, p_raw = wilcoxon(pivot["gpt-4o-mini"], pivot["gpt-5.1"], zero_method="wilcox", correction=False)
    lines.append("## モデル比較 (GPT-4o-mini vs GPT-5.1)\n")
    lines.append(f"- Wilcoxon (paired): n={len(pivot)}, stat={stat:.3f}, p={p_raw:.4f}\n")
    diff = (pivot["gpt-5.1"] - pivot["gpt-4o-mini"]).median()
    lines.append(f"- 中央差 (5.1 - 4o-mini): {diff:.4f}\n")
    lines.append("\nアスペクト別:\n")
    lines.append(pivot.reset_index().to_markdown(index=False) + "\n")

    # Aspect description
    desc_df = load_aspect_desc()
    pivot = desc_df.pivot(index="aspect", columns="condition", values="bert")
    stat, p_raw = wilcoxon(pivot["with_desc"], pivot["no_desc"], zero_method="wilcox", correction=False)
    lines.append("## アスペクト説明文あり/なし\n")
    lines.append(f"- Wilcoxon (paired): n={len(pivot)}, stat={stat:.3f}, p={p_raw:.4f}\n")
    diff = (pivot["with_desc"] - pivot["no_desc"]).median()
    lines.append(f"- 中央差 (with_desc - no_desc): {diff:.4f}\n")
    lines.append("\nアスペクト別:\n")
    lines.append(pivot.reset_index().to_markdown(index=False) + "\n")

    out_path = out_dir / "stat_tests.md"
    out_path.write_text("\n".join(lines))
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()

