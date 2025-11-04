import json
import sys
from pathlib import Path


DATA_FILE = "/Users/seinoshun/imrb_research/data/external/retrieved-concepts/farnoosh/current/retrieved_dataset_100.json"


def iter_concepts(path: str):
    """Stream concept objects under results[] without loading entire file."""
    with open(path, "r", encoding="utf-8") as f:
        in_results = False
        capturing = False
        brace_depth = 0
        buffer_lines = []

        for raw_line in f:
            line = raw_line.rstrip("\n")

            if not in_results:
                if '"results"' in line and "[" in line:
                    in_results = True
                continue

            # results array end
            if in_results and not capturing and "]" in line:
                break

            # start of an object
            if in_results and not capturing:
                if "{" in line:
                    capturing = True
                    brace_depth = line.count("{") - line.count("}")
                    buffer_lines = [line]
                    if brace_depth == 0:
                        try:
                            obj = json.loads("".join(buffer_lines).strip().rstrip(","))
                            yield obj
                        except Exception:
                            pass
                        capturing = False
                        buffer_lines = []
                continue

            if capturing:
                buffer_lines.append(line)
                brace_depth += line.count("{") - line.count("}")
                if brace_depth == 0:
                    try:
                        obj = json.loads("\n".join(buffer_lines).strip().rstrip(","))
                        yield obj
                    except Exception:
                        pass
                    capturing = False
                    buffer_lines = []


def summarize(scores):
    s_sorted = sorted(scores)
    n = len(s_sorted)
    if n == 0:
        return {"min": None, "p25": None, "median": None, "mean": None, "p75": None, "max": None}
    return {
        "min": float(s_sorted[0]),
        "p25": float(s_sorted[n // 4]),
        "median": float(s_sorted[n // 2]),
        "mean": float(sum(s_sorted) / n),
        "p75": float(s_sorted[(3 * n) // 4]),
        "max": float(s_sorted[-1]),
    }


def main(ids):
    path = DATA_FILE
    want = set(ids) if ids else None
    for concept in iter_concepts(path):
        cid = int(concept.get("concept_id", -1))
        if want is not None and cid not in want:
            continue
        topk = concept.get("topk", [])
        if len(topk) < 100:
            print(f"concept_{cid}: topk size={len(topk)} < 100")
            continue
        # sort by rank asc
        topk_sorted = sorted(topk, key=lambda e: int(e.get("rank", 1_000_000)))
        top10 = topk_sorted[:10]
        bottom10 = topk_sorted[-10:]

        top10_scores = [float(e.get("score", 0.0)) for e in top10]
        bottom10_scores = [float(e.get("score", 0.0)) for e in bottom10]

        s_top = summarize(top10_scores)
        s_bot = summarize(bottom10_scores)

        margin = 0.05
        separable = (max(bottom10_scores) < min(top10_scores) - margin) if bottom10_scores and top10_scores else False

        print(f"concept_{cid}:")
        print(f"  top10   rank range: {top10[0]['rank']}..{top10[-1]['rank']}")
        print(f"  bottom10 rank range: {bottom10[0]['rank']}..{bottom10[-1]['rank']}")
        print(f"  top10   score stats: {s_top}")
        print(f"  bottom10 score stats: {s_bot}")
        print(f"  separable_with_margin_0.05: {separable}")
        print("")

        if want is not None:
            want.remove(cid)
            if not want:
                break


if __name__ == "__main__":
    ids = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else [0]
    main(ids)


