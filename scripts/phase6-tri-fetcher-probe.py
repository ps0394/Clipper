"""F4.3 input data: tri-fetcher probe across a URL list.

Runs `retrievability.phase5.fetcher.fetch_markdown` against every URL in
an input CSV or text file and writes a JSON + CSV report. Pure HTTP:
no browser, no LLM calls. Safe to re-run; no side effects beyond the
output file.

This is the **pre-experiment evidence** for Session 4 F4.2/F4.3: before
spending LLM budget on paired grading, we want to know (a) which vendors
serve any form of page-level markdown at all and (b) which resolution
path succeeds. Vendors where the answer is "none" are excluded from the
F4.2 paired-grading pass.

Usage:
    # probe the 43 corpus-002 URLs and write alongside other analysis
    python scripts/phase6-tri-fetcher-probe.py `
        --urls evaluation/phase5-results/corpus-002-analysis/per-page.csv `
        --out  evaluation/phase5-results/corpus-002-analysis/tri-fetcher-probe.json `
        --csv-out evaluation/phase5-results/corpus-002-analysis/tri-fetcher-probe.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

# Allow running as a script from the repo root without installation.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from retrievability.phase5.fetcher import fetch_markdown


def _load_urls(path: Path) -> list[dict]:
    """Load URLs from either a per-page.csv (columns: slug,url,...,vendor,...)
    or a plain text file (one URL per line, # comments ignored)."""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".csv":
        rows = list(csv.DictReader(text.splitlines()))
        out = []
        for r in rows:
            url = r.get("url", "").strip()
            if not url:
                continue
            out.append({
                "slug":   r.get("slug") or urlparse(url).netloc,
                "url":    url,
                "vendor": r.get("vendor") or urlparse(url).netloc,
            })
        return out
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append({
            "slug":   urlparse(line).netloc + urlparse(line).path.replace("/", "-"),
            "url":    line,
            "vendor": urlparse(line).netloc,
        })
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--urls", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--csv-out", type=Path, default=None)
    p.add_argument("--limit", type=int, default=0, help="limit number of URLs; 0=all")
    args = p.parse_args()

    urls = _load_urls(args.urls)
    if args.limit:
        urls = urls[: args.limit]
    if not urls:
        print(f"No URLs to probe in {args.urls}")
        return 1

    results: list[dict] = []
    for i, rec in enumerate(urls, 1):
        t0 = time.time()
        print(f"[{i:>3}/{len(urls)}] {rec['url']}", flush=True)
        try:
            body, meta = fetch_markdown(rec["url"])
        except Exception as e:  # defensive; the fetcher should not raise
            results.append({
                **rec,
                "resolved_by": None,
                "error": f"{type(e).__name__}: {e}",
                "elapsed_s": round(time.time() - t0, 3),
                "attempts": [],
            })
            continue
        results.append({
            **rec,
            "resolved_by": meta.get("resolved_by"),
            "resolved_url": meta.get("resolved_url"),
            "bytes": meta.get("bytes"),
            "content_type": meta.get("content_type"),
            "elapsed_s": meta.get("elapsed_s"),
            "attempts": meta.get("attempts", []),
            "has_body": body is not None,
        })
        for a in meta.get("attempts", []):
            print(f"    {a['probe']:<16} ok={a.get('ok')}")

    # Aggregate
    vendors: dict[str, dict] = {}
    resolved_counts: dict[str, int] = {"accept_header": 0, "link_alternate": 0, "sibling_md": 0}
    miss = 0
    for r in results:
        v = r["vendor"]
        vendors.setdefault(v, {"n": 0, "hits": 0, "by_probe": {}})
        vendors[v]["n"] += 1
        rb = r.get("resolved_by")
        if rb:
            vendors[v]["hits"] += 1
            vendors[v]["by_probe"][rb] = vendors[v]["by_probe"].get(rb, 0) + 1
            resolved_counts[rb] = resolved_counts.get(rb, 0) + 1
        else:
            miss += 1

    summary = {
        "n_urls": len(results),
        "hit_count": sum(1 for r in results if r.get("resolved_by")),
        "miss_count": miss,
        "hit_rate": round(
            sum(1 for r in results if r.get("resolved_by")) / len(results), 4
        ),
        "by_probe": resolved_counts,
        "by_vendor": {
            v: {
                **data,
                "hit_rate": round(data["hits"] / data["n"], 4) if data["n"] else 0.0,
            }
            for v, data in sorted(vendors.items())
        },
        "caveats": [
            "Pure HTTP probe: does not run JS, does not evaluate content quality.",
            "A 'hit' means a markdown-like body was returned and passed the "
            "HTML-in-disguise gate. It does not mean the markdown is "
            "complete or semantically equivalent to the rendered HTML.",
            "Some CDNs serve different content to User-Agent Clipper-Phase5 "
            "than to browser UAs. Vendor misses may be UA-gating, not "
            "absence of markdown. Rerun with a browser UA to confirm.",
        ],
        "results": results,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if args.csv_out:
        with args.csv_out.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["slug", "vendor", "url", "resolved_by", "resolved_url",
                        "bytes", "content_type", "elapsed_s"])
            for r in results:
                w.writerow([
                    r.get("slug", ""),
                    r.get("vendor", ""),
                    r.get("url", ""),
                    r.get("resolved_by") or "",
                    r.get("resolved_url") or "",
                    r.get("bytes") or "",
                    r.get("content_type") or "",
                    r.get("elapsed_s") or "",
                ])

    # Console
    print()
    print(f"URLs probed:     {summary['n_urls']}")
    print(f"Markdown hits:   {summary['hit_count']}  ({summary['hit_rate']:.1%})")
    print(f"Misses:          {summary['miss_count']}")
    print(f"By probe path:   {summary['by_probe']}")
    print()
    print(f"{'vendor':<16} {'n':>3} {'hits':>4} {'hit_rate':>8}  probes")
    print("-" * 64)
    for v, data in summary["by_vendor"].items():
        print(f"{v:<16} {data['n']:>3} {data['hits']:>4} {data['hit_rate']:>7.1%}  {data['by_probe']}")
    print()
    print(f"Wrote {args.out}")
    if args.csv_out:
        print(f"Wrote {args.csv_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
