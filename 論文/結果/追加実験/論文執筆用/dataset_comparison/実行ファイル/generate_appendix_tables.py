import json
from pathlib import Path


def fmt(x: float) -> str:
    return f"{x:.4f}"

def aspect_display(dataset: str, aspect: str) -> str:
    if dataset == "semeval":
        mapping = {"food": "Food", "service": "Service", "battery": "Battery", "screen": "Screen"}
        return mapping.get(aspect, aspect)
    if dataset == "steam":
        mapping = {"gameplay": "Gameplay", "visual": "Visual", "story": "Story", "audio": "Audio"}
        return mapping.get(aspect, aspect)
    if dataset == "goemotions":
        return aspect[:1].upper() + aspect[1:]
    return aspect


def order_aspects(dataset: str, aspects: list[str]) -> list[str]:
    preferred: list[str] | None = None
    if dataset == "semeval":
        preferred = ["food", "service", "battery", "screen"]
    elif dataset == "steam":
        preferred = ["gameplay", "visual", "story", "audio"]

    if not preferred:
        return aspects

    present = [a for a in preferred if a in aspects]
    rest = [a for a in aspects if a not in present]
    return present + rest


def longtable_block(label: str, caption: str, sections: list[tuple[str, str, list[list[str]]]]) -> str:
    """
    sections: [(dataset_display, dataset_key, rows=[ [aspect, sbert, bleu, llm], ... ])]
    """
    lines: list[str] = []
    lines.append(r"\begin{longtable}{llccc}")
    lines.append(f"\\caption{{{caption}}}\\label{{{label}}} \\\\")
    lines.append(r"\toprule")
    lines.append(r"データセット & アスペクト & SBERT類似度 & BLEU & LLM \\")
    lines.append(r"\midrule")
    lines.append(r"\endfirsthead")
    lines.append(rf"\multicolumn{{5}}{{l}}{{\small 表~\ref{{{label}}}（続き）}} \\")
    lines.append(r"\toprule")
    lines.append(r"データセット & アスペクト & SBERT類似度 & BLEU & LLM \\")
    lines.append(r"\midrule")
    lines.append(r"\endhead")
    lines.append(r"\midrule")
    lines.append(r"\multicolumn{5}{r}{\small 次ページへ続く} \\")
    lines.append(r"\endfoot")
    lines.append(r"\bottomrule")
    lines.append(r"\endlastfoot")

    for dataset_display, _, rows in sections:
        lines.append(r"\midrule")
        lines.append(rf"\multicolumn{{5}}{{l}}{{\textbf{{{dataset_display}}}}} \\")
        for aspect, sbert, bleu, llm in rows:
            lines.append(f" & {aspect} & {sbert} & {bleu} & {llm} \\\\")

    lines.append(r"\end{longtable}")
    return "\n".join(lines)


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]  # .../dataset_comparison
    stats_path = base_dir / "実験設定" / "dataset_comparison_statistics.json"
    out_path = base_dir.parents[3] / "chapters" / "appendix_dataset_comparison_tables.tex"  # .../論文/chapters/

    with stats_path.open("r", encoding="utf-8") as f:
        stats = json.load(f)

    ds = stats["statistics"]["dataset_stats"]

    semeval = ds["semeval"]
    steam = ds["steam"]
    go = ds["goemotions"]

    def rows_for(dataset_key: str, d: dict) -> list[list[str]]:
        aspects = order_aspects(dataset_key, d["aspects"])
        idx = {a: i for i, a in enumerate(d["aspects"])}
        rows: list[list[str]] = []
        for a in aspects:
            i = idx[a]
            rows.append([aspect_display(dataset_key, a), fmt(d["bert_scores"][i]), fmt(d["bleu_scores"][i]), fmt(d["llm_scores"][i])])
        return rows

    blocks: list[str] = []
    blocks.append("% Auto-generated. DO NOT EDIT.")
    blocks.append("% Source: dataset_comparison/実験設定/dataset_comparison_statistics.json")
    blocks.append("")
    blocks.append(
        longtable_block(
            label="tab:appendix_all_aspects_dataset_comparison",
            caption="データセット別比較：本実験で扱った全アスペクトの評価スコア",
            sections=[
                ("SemEval-2014", "semeval", rows_for("semeval", semeval)),
                ("GoEmotions", "goemotions", rows_for("goemotions", go)),
                ("Steam", "steam", rows_for("steam", steam)),
            ],
        )
    )
    blocks.append("")

    out_path.write_text("\n".join(blocks), encoding="utf-8")
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()


