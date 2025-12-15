#!/usr/bin/env python3
import argparse
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests


@dataclass
class CheckResult:
    key: str
    start_line: int
    has_comment: bool
    title: str
    identifier: Optional[str]
    status: str  # OK / FAIL / NO_ID
    status_code: Optional[int]
    final_url: Optional[str]
    error: Optional[str]
    elapsed_sec: Optional[float]


def _extract_bibitem_blocks(tex: str):
    matches = list(re.finditer(r"\\bibitem\{([^}]+)\}", tex))
    blocks = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(tex)
        key = m.group(1).strip()
        start_line = tex.count("\n", 0, start) + 1
        block = tex[start:end]
        blocks.append((key, start_line, block))
    return blocks


def _has_comment(block: str) -> bool:
    for line in block.splitlines()[1:]:
        s = line.lstrip()
        if s.startswith("%") and s[1:].strip():
            return True
    return False


def _extract_title(block: str) -> str:
    # Heuristic: ``Title,'' pattern
    m = re.search(r"``([^`]+?)''", block, flags=re.DOTALL)
    if m:
        return " ".join(m.group(1).split())
    # Fallback: first non-empty line after \bibitem
    for line in block.splitlines()[1:]:
        s = line.strip()
        if s and not s.startswith("%"):
            return " ".join(s.split())[:160]
    return ""


def _extract_urls(block: str):
    return [u.strip() for u in re.findall(r"\\url\{([^}]+)\}", block)]


def _extract_doi(block: str) -> Optional[str]:
    m = re.search(r"\bdoi\s*:\s*([0-9][0-9./A-Za-z_-]+)", block)
    if not m:
        return None
    doi = m.group(1).strip()
    doi = doi.rstrip(").,;")
    return doi


def _extract_arxiv(block: str) -> Optional[str]:
    m = re.search(r"\barXiv\s*:\s*([0-9]{4}\.[0-9]{4,5})(v\d+)?\b", block)
    if not m:
        return None
    return m.group(1)


def _pick_identifier(block: str) -> Optional[str]:
    doi = _extract_doi(block)
    if doi:
        return f"https://doi.org/{doi}"
    arxiv = _extract_arxiv(block)
    if arxiv:
        return f"https://arxiv.org/abs/{arxiv}"
    urls = _extract_urls(block)
    if urls:
        return urls[0]
    return None


def _request_once(method: str, url: str, timeout: float):
    headers = {"User-Agent": "imrb-research-reference-check/1.0"}
    return requests.request(method, url, allow_redirects=True, timeout=timeout, headers=headers, stream=True)


def _check_url(url: str, timeout: float, max_retries: int, sleep_sec: float):
    last_err = None
    for attempt in range(max_retries + 1):
        t0 = time.time()
        try:
            r = _request_once("HEAD", url, timeout)
            status = r.status_code
            final_url = str(r.url) if r.url else None
            r.close()

            if status in (403, 405) or status >= 500:
                r = _request_once("GET", url, timeout)
                status = r.status_code
                final_url = str(r.url) if r.url else final_url
                r.close()

            return status, final_url, None, time.time() - t0
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            if attempt < max_retries:
                time.sleep(sleep_sec * (attempt + 1))
                continue
            return None, None, last_err, time.time() - t0


def _to_markdown_table(rows: list[CheckResult]) -> str:
    header = (
        "| key | 行 | コメント | title(抜粋) | identifier | status | code | final_url | error |\n"
        "|---|---:|:---:|---|---|:---:|---:|---|---|\n"
    )
    lines = []
    for r in rows:
        comment = "Y" if r.has_comment else "N"
        ident = (r.identifier or "").replace("|", "\\|")
        title = (r.title or "").replace("|", "\\|")
        final_url = (r.final_url or "").replace("|", "\\|")
        err = (r.error or "").replace("|", "\\|")
        code = "" if r.status_code is None else str(r.status_code)
        lines.append(
            f"| {r.key} | {r.start_line} | {comment} | {title} | {ident} | {r.status} | {code} | {final_url} | {err} |"
        )
    return header + "\n".join(lines) + "\n"


def main():
    repo_root = Path(__file__).resolve().parents[1]
    default_tex = repo_root / "論文" / "chapters" / "09_references.tex"
    default_out = repo_root / "data" / "analysis-workspace" / "reference_checks" / datetime.now().strftime("%Y%m%d_%H%M%S")

    p = argparse.ArgumentParser()
    p.add_argument("--tex-file", type=str, default=str(default_tex))
    p.add_argument("--output-dir", type=str, default=str(default_out))
    p.add_argument("--only-missing-comments", action="store_true")
    p.add_argument("--timeout", type=float, default=10.0)
    p.add_argument("--max-retries", type=int, default=2)
    p.add_argument("--sleep-sec", type=float, default=0.2)
    args = p.parse_args()

    tex_path = Path(args.tex_file)
    if not tex_path.is_absolute():
        tex_path = (repo_root / tex_path).resolve()
    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = (repo_root / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    tex = tex_path.read_text(encoding="utf-8")
    blocks = _extract_bibitem_blocks(tex)

    results: list[CheckResult] = []
    for key, start_line, block in blocks:
        has_c = _has_comment(block)
        if args.only_missing_comments and has_c:
            continue
        title = _extract_title(block)
        identifier = _pick_identifier(block)
        if not identifier:
            results.append(
                CheckResult(
                    key=key,
                    start_line=start_line,
                    has_comment=has_c,
                    title=title,
                    identifier=None,
                    status="NO_ID",
                    status_code=None,
                    final_url=None,
                    error=None,
                    elapsed_sec=None,
                )
            )
            continue

        code, final_url, err, elapsed = _check_url(
            identifier, timeout=args.timeout, max_retries=args.max_retries, sleep_sec=args.sleep_sec
        )
        ok = code is not None and 200 <= code < 400
        results.append(
            CheckResult(
                key=key,
                start_line=start_line,
                has_comment=has_c,
                title=title,
                identifier=identifier,
                status="OK" if ok else "FAIL",
                status_code=code,
                final_url=final_url,
                error=err,
                elapsed_sec=elapsed,
            )
        )
        time.sleep(args.sleep_sec)

    # Sort: missing comment first, then FAIL, then NO_ID, then key
    status_order = {"FAIL": 0, "NO_ID": 1, "OK": 2}
    results_sorted = sorted(
        results,
        key=lambda r: (0 if not r.has_comment else 1, status_order.get(r.status, 9), r.key),
    )

    payload = {
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "tex_file": str(tex_path),
        "only_missing_comments": bool(args.only_missing_comments),
        "timeout": args.timeout,
        "max_retries": args.max_retries,
        "total_bibitems": len(blocks),
        "checked_items": len(results),
        "missing_comment_items": sum(1 for r in results if not r.has_comment),
        "ok": sum(1 for r in results if r.status == "OK"),
        "fail": sum(1 for r in results if r.status == "FAIL"),
        "no_id": sum(1 for r in results if r.status == "NO_ID"),
        "results": [asdict(r) for r in results_sorted],
    }

    (out_dir / "reference_check_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    md = []
    md.append(f"# reference check\n")
    md.append(f"- checked_at: {payload['checked_at']}\n")
    md.append(f"- tex_file: {payload['tex_file']}\n")
    md.append(f"- only_missing_comments: {payload['only_missing_comments']}\n")
    md.append(f"- total_bibitems: {payload['total_bibitems']}\n")
    md.append(f"- checked_items: {payload['checked_items']}\n")
    md.append(f"- missing_comment_items: {payload['missing_comment_items']}\n")
    md.append(f"- ok / fail / no_id: {payload['ok']} / {payload['fail']} / {payload['no_id']}\n\n")
    md.append(_to_markdown_table(results_sorted))
    (out_dir / "reference_check_report.md").write_text("".join(md), encoding="utf-8")

    print(f"Saved:\n- {out_dir / 'reference_check_report.md'}\n- {out_dir / 'reference_check_results.json'}")


if __name__ == "__main__":
    main()


