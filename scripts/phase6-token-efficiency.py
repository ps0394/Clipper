"""Token / char efficiency comparison across rendered HTML, readability
extract, and served markdown for corpus-002.

For each page that has all three artifacts, report:
- Raw rendered HTML size
- Readability extract size (re-extracted live from page.rendered.html so
  it is NOT clamped by the runner's MIN_DOCUMENT_CHARS=40k limit)
- Served markdown size (taken from fetch.markdown.json's bytes field so
  it is also NOT clamped)
- Compression ratios

Reports cl100k_base token counts via tiktoken.

Reads only on-disk artifacts and re-runs readability locally; no network,
no LLM cost.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from readability import Document

try:
    import tiktoken  # type: ignore
    _ENC = tiktoken.get_encoding("cl100k_base")
    _TOKENS_AVAILABLE = True
except ImportError:
    _ENC = None
    _TOKENS_AVAILABLE = False


def _readability_extract(html: str) -> str:
    """Replicate retrievability.phase5.runner._extract_readability_text
    without the 40k clamp so we measure the publisher's true output size.
    """
    try:
        doc = Document(html)
        summary_html = doc.summary(html_partial=True)
        soup = BeautifulSoup(summary_html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
    # Collapse runs of blank lines, mirroring runner behavior.
    lines = [ln.strip() for ln in text.splitlines()]
    out_lines: list[str] = []
    blank = False
    for ln in lines:
        if ln:
            out_lines.append(ln)
            blank = False
        elif not blank:
            out_lines.append("")
            blank = True
    return "\n".join(out_lines).strip()


# Clamp constant from retrievability/phase5/runner.py — pages whose
# extract or markdown hit this length were truncated, so their reported
# "size" is a floor not a true measure. We override via --clamp so the
# token-efficiency analysis can use the unclamped page.markdown.txt /
# page.rendered.txt files (these are clamped on disk; raise the
# threshold to the highest plausible original size to surface clamping).
CLAMP = 40_000


def _count(text: str) -> tuple[int, int | None]:
    chars = len(text)
    tokens = len(_ENC.encode(text)) if _ENC is not None else None
    return chars, tokens


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--pilot-dir", required=True, type=Path)
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    rows: list[dict] = []
    for page_dir in sorted(p for p in args.pilot_dir.iterdir() if p.is_dir() and not p.name.startswith("_")):
        rh = page_dir / "page.rendered.html"
        md_disk = page_dir / "page.markdown.txt"          # clamped to 40k
        md_meta = page_dir / "fetch.markdown.json"        # has true byte count
        if not (rh.is_file() and md_disk.is_file()):
            continue
        rh_txt = rh.read_text(encoding="utf-8", errors="replace")
        # Re-extract readability locally (un-clamped).
        rt_txt = _readability_extract(rh_txt)
        # Read clamped on-disk markdown for char counting; the markdown
        # response was potentially truncated. Use fetch.markdown.json
        # 'bytes' for the true response size if available.
        md_disk_txt = md_disk.read_text(encoding="utf-8", errors="replace")
        md_true_bytes = None
        if md_meta.is_file():
            meta = json.loads(md_meta.read_text(encoding="utf-8"))
            md_true_bytes = meta.get("bytes")
        # If true bytes are available and exceed the on-disk size, the
        # disk file was clamped. We can still tokenize only the on-disk
        # truncated text — that is what the agent would have seen.
        # For the size comparison, prefer the un-clamped readability /
        # un-clamped raw HTML so the comparison is apples-to-apples in
        # length terms.
        md_clamped_at_40k = len(md_disk_txt) >= 40_000

        rh_chars, rh_tok = _count(rh_txt)
        rt_chars, rt_tok = _count(rt_txt)
        md_chars, md_tok = _count(md_disk_txt)

        row = {
            "slug": page_dir.name,
            "rendered_html_chars": rh_chars,
            "rendered_txt_chars": rt_chars,                # un-clamped (re-extracted)
            "markdown_chars_disk": md_chars,                # clamped at 40k on disk
            "markdown_true_bytes": md_true_bytes,           # un-clamped wire size
            "markdown_clamped_at_40k": md_clamped_at_40k,
            "ratio_html_to_rendered_txt": round(rh_chars / rt_chars, 1) if rt_chars else None,
            "ratio_html_to_markdown_disk": round(rh_chars / md_chars, 1) if md_chars else None,
            "ratio_markdown_to_rendered_txt_disk": round(md_chars / rt_chars, 3) if rt_chars else None,
        }
        if md_true_bytes:
            row["ratio_html_to_markdown_true"] = round(rh_chars / md_true_bytes, 1)
            row["ratio_markdown_true_to_rendered_txt"] = round(
                md_true_bytes / rt_chars, 3
            ) if rt_chars else None
        if _TOKENS_AVAILABLE:
            row.update({
                "rendered_html_tokens": rh_tok,
                "rendered_txt_tokens": rt_tok,
                "markdown_tokens_disk": md_tok,
                "tok_ratio_html_to_rendered_txt": round(rh_tok / rt_tok, 1) if rt_tok else None,
                "tok_ratio_html_to_markdown_disk": round(rh_tok / md_tok, 1) if md_tok else None,
                "tok_ratio_markdown_to_rendered_txt_disk": round(md_tok / rt_tok, 3) if rt_tok else None,
            })
        rows.append(row)

    # --- Vendor classification (matches phase6-intersection-lift.py) ---
    vendor_prefixes = {
        "anthropic": ("docs-anthropic",),
        "aws": ("docs-aws",),
        "docker": ("docs-docker",),
        "github": ("docs-github", "help-github"),
        "gcp": ("cloud-google",),
        "k8s": ("kubernetes-io",),
        "learn": ("learn-microsoft",),
        "mdn": ("developer-mozilla",),
        "nodejs": ("nodejs-org",),
        "openai": ("platform-openai",),
        "perplexity": ("docs-perplexity",),
        "postgres": ("www-postgresql",),
        "python": ("docs-python",),
        "snowflake": ("docs-snowflake",),
        "stripe": ("docs-stripe",),
        "wikipedia": ("en-wikipedia",),
    }
    def _vendor_for(slug: str) -> str:
        for v, prefs in vendor_prefixes.items():
            if any(slug.startswith(p) for p in prefs):
                return v
        return "other"
    for r in rows:
        r["vendor"] = _vendor_for(r["slug"])

    def _stats(key: str) -> dict:
        vals = [r[key] for r in rows if r.get(key) is not None]
        if not vals:
            return {}
        return {
            "n": len(vals),
            "mean": round(statistics.fmean(vals), 2),
            "median": round(statistics.median(vals), 2),
            "min": round(min(vals), 2),
            "max": round(max(vals), 2),
        }

    summary = {
        "n_pages": len(rows),
        "tokens_available": _TOKENS_AVAILABLE,
        "n_markdown_clamped_at_40k": sum(1 for r in rows if r["markdown_clamped_at_40k"]),
        "rendered_html_chars": _stats("rendered_html_chars"),
        "rendered_txt_chars": _stats("rendered_txt_chars"),
        "markdown_chars_disk": _stats("markdown_chars_disk"),
        "markdown_true_bytes": _stats("markdown_true_bytes"),
        "ratio_html_to_rendered_txt": _stats("ratio_html_to_rendered_txt"),
        "ratio_html_to_markdown_disk": _stats("ratio_html_to_markdown_disk"),
        "ratio_html_to_markdown_true": _stats("ratio_html_to_markdown_true"),
        "ratio_markdown_to_rendered_txt_disk": _stats("ratio_markdown_to_rendered_txt_disk"),
        "ratio_markdown_true_to_rendered_txt": _stats("ratio_markdown_true_to_rendered_txt"),
    }
    if _TOKENS_AVAILABLE:
        summary.update({
            "rendered_html_tokens": _stats("rendered_html_tokens"),
            "rendered_txt_tokens": _stats("rendered_txt_tokens"),
            "markdown_tokens_disk": _stats("markdown_tokens_disk"),
            "tok_ratio_html_to_rendered_txt": _stats("tok_ratio_html_to_rendered_txt"),
            "tok_ratio_html_to_markdown_disk": _stats("tok_ratio_html_to_markdown_disk"),
            "tok_ratio_markdown_to_rendered_txt_disk": _stats("tok_ratio_markdown_to_rendered_txt_disk"),
        })
    summary["per_page"] = rows

    print(f"Pages: {len(rows)}")
    print(f"Tokenizer: {'cl100k_base' if _TOKENS_AVAILABLE else 'NOT AVAILABLE — chars only'}")
    print(f"Markdown disk-clamped at 40k: {summary['n_markdown_clamped_at_40k']} of {len(rows)}")
    print()
    print("Char counts (median):")
    print(f"  rendered HTML (raw):                {summary['rendered_html_chars']['median']:>12,.0f}")
    print(f"  readability extract (un-clamped):   {summary['rendered_txt_chars']['median']:>12,.0f}")
    print(f"  served markdown (disk, clamped):    {summary['markdown_chars_disk']['median']:>12,.0f}")
    if summary["markdown_true_bytes"].get("n"):
        print(f"  served markdown (true wire bytes):  {summary['markdown_true_bytes']['median']:>12,.0f}")
    print()
    print("Char ratios (median):")
    print(f"  HTML / readability_txt:             {summary['ratio_html_to_rendered_txt']['median']:>6,.1f}x")
    if summary["ratio_html_to_markdown_true"].get("n"):
        print(f"  HTML / markdown (true bytes):       {summary['ratio_html_to_markdown_true']['median']:>6,.1f}x")
    print(f"  HTML / markdown (disk):             {summary['ratio_html_to_markdown_disk']['median']:>6,.1f}x")
    if summary["ratio_markdown_true_to_rendered_txt"].get("n"):
        print(f"  markdown_true / readability:        {summary['ratio_markdown_true_to_rendered_txt']['median']:>6,.3f}x  (>1 = markdown bigger)")
    print(f"  markdown_disk / readability:        {summary['ratio_markdown_to_rendered_txt_disk']['median']:>6,.3f}x")
    if _TOKENS_AVAILABLE:
        print()
        print("Token counts (median, cl100k_base):")
        print(f"  rendered HTML (raw):                {summary['rendered_html_tokens']['median']:>12,.0f}")
        print(f"  readability extract:                {summary['rendered_txt_tokens']['median']:>12,.0f}")
        print(f"  served markdown (disk, clamped):    {summary['markdown_tokens_disk']['median']:>12,.0f}")
        print()
        print("Token ratios (median):")
        print(f"  HTML / readability_txt:             {summary['tok_ratio_html_to_rendered_txt']['median']:>6,.1f}x")
        print(f"  HTML / markdown_disk:               {summary['tok_ratio_html_to_markdown_disk']['median']:>6,.1f}x")
        print(f"  markdown_disk / readability:        {summary['tok_ratio_markdown_to_rendered_txt_disk']['median']:>6,.3f}x")

    # --- Per-vendor breakdown -------------------------------------------
    from collections import defaultdict
    by_vendor: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_vendor[r["vendor"]].append(r)

    vendor_table: list[dict] = []
    for vendor, vrows in sorted(by_vendor.items()):
        ratios_md_to_rt = [r["tok_ratio_markdown_to_rendered_txt_disk"]
                           for r in vrows
                           if r.get("tok_ratio_markdown_to_rendered_txt_disk") is not None]
        ratios_html_to_md = [r["tok_ratio_html_to_markdown_disk"]
                             for r in vrows
                             if r.get("tok_ratio_html_to_markdown_disk") is not None]
        n_clamped = sum(1 for r in vrows if r["markdown_clamped_at_40k"])
        median_md_tok = (
            statistics.median([r["markdown_tokens_disk"] for r in vrows])
            if vrows else None
        )
        median_rt_tok = (
            statistics.median([r["rendered_txt_tokens"] for r in vrows])
            if vrows else None
        )
        median_md_true_bytes = (
            statistics.median([r["markdown_true_bytes"] for r in vrows
                              if r.get("markdown_true_bytes") is not None])
            if any(r.get("markdown_true_bytes") for r in vrows) else None
        )
        vendor_table.append({
            "vendor": vendor,
            "n": len(vrows),
            "n_markdown_clamped_at_40k": n_clamped,
            "median_markdown_tokens_disk": int(median_md_tok) if median_md_tok else None,
            "median_rendered_txt_tokens": int(median_rt_tok) if median_rt_tok else None,
            "median_markdown_true_bytes": int(median_md_true_bytes) if median_md_true_bytes else None,
            "median_md_to_rt_token_ratio": round(statistics.median(ratios_md_to_rt), 3) if ratios_md_to_rt else None,
            "median_html_to_md_token_ratio": round(statistics.median(ratios_html_to_md), 1) if ratios_html_to_md else None,
        })

    summary["by_vendor"] = vendor_table

    print()
    print("Per-vendor breakdown (token, cl100k_base, median per page):")
    print(f"  {'vendor':<12} {'n':>3} {'clamp':>6}  {'md tok':>8}  {'rt tok':>8}  {'md/rt':>6}  {'html/md':>8}")
    for v in vendor_table:
        clamp = f"{v['n_markdown_clamped_at_40k']}/{v['n']}"
        mdtok = f"{v['median_markdown_tokens_disk']:,}" if v["median_markdown_tokens_disk"] else "-"
        rttok = f"{v['median_rendered_txt_tokens']:,}" if v["median_rendered_txt_tokens"] else "-"
        ratio = f"{v['median_md_to_rt_token_ratio']:.2f}x" if v["median_md_to_rt_token_ratio"] is not None else "-"
        hmd = f"{v['median_html_to_md_token_ratio']:.1f}x" if v["median_html_to_md_token_ratio"] is not None else "-"
        print(f"  {v['vendor']:<12} {v['n']:>3} {clamp:>6}  {mdtok:>8}  {rttok:>8}  {ratio:>6}  {hmd:>8}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print()
        print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
