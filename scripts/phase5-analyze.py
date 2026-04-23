"""Phase 5 pilot analysis — consume corpus-001 results.

Reads per-page ``summary.json`` files + the corpus URL file (for tier/vendor
labels) and emits:

  1. Headline means (overall, by tier, by profile, by vendor).
  2. Raw-vs-rendered accuracy delta buckets.
  3. Correlation of Clipper's ``parseability_score`` / ``universal_score``
     with measured accuracy (Pearson r), per mode.
  4. Fetch status counts.
  5. A per-page CSV dump + a per-page markdown table (top of file) for
     inclusion in the methodology note.

No third-party deps (stdlib only — Pearson r computed by hand).

Usage:
    python scripts/phase5-analyze.py \
        --results evaluation/phase5-results/corpus-001 \
        --corpus  urls/phase5-corpus-urls.txt \
        --out     evaluation/phase5-results/corpus-001-analysis
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Corpus file parsing
# ---------------------------------------------------------------------------


def load_corpus_metadata(corpus_path: Path) -> Dict[str, Dict[str, str]]:
    """Parse the N=43 URL file. Returns ``{url: {profile, vendor, tier}}``.

    Expected format (tab-separated):
        <url>\t<profile>\t<vendor>  # tier1

    Lines beginning with '#' or blank are skipped.
    """
    meta: Dict[str, Dict[str, str]] = {}
    for raw in corpus_path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        # Split the trailing "# tierN" comment off before column-splitting.
        tier = ""
        if "#" in line:
            body, _, comment = line.partition("#")
            tier = comment.strip().lower()  # e.g. "tier1" or "tier2"
            line = body.rstrip()
        else:
            body = line

        cols = [c.strip() for c in line.split("\t") if c.strip()]
        if len(cols) < 2:
            continue
        url = cols[0]
        profile = cols[1] if len(cols) > 1 else ""
        vendor = cols[2] if len(cols) > 2 else ""
        meta[url] = {"profile": profile, "vendor": vendor, "tier": tier or "unknown"}
    return meta


# ---------------------------------------------------------------------------
# Summary loading
# ---------------------------------------------------------------------------


def load_summaries(results_dir: Path) -> List[Dict[str, Any]]:
    """Load every per-page ``summary.json`` under ``results_dir``."""
    out: List[Dict[str, Any]] = []
    for child in sorted(results_dir.iterdir()):
        if not child.is_dir():
            continue
        sj = child / "summary.json"
        if not sj.is_file():
            continue
        try:
            out.append(json.loads(sj.read_text(encoding="utf-8")))
        except json.JSONDecodeError as exc:
            print(f"  WARN: could not parse {sj}: {exc}", file=sys.stderr)
    return out


def merge_tier_vendor(
    summaries: List[Dict[str, Any]], corpus_meta: Dict[str, Dict[str, str]]
) -> None:
    """Mutate each summary in place to include tier + vendor."""
    for s in summaries:
        m = corpus_meta.get(s.get("url", ""), {})
        s["tier"] = m.get("tier", "unknown")
        s["vendor"] = m.get("vendor", "unknown")


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------


def pearson_r(xs: List[float], ys: List[float]) -> Optional[float]:
    """Pearson correlation coefficient. Returns None if undefined (n<2 or
    zero variance in either series)."""
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    try:
        mx = statistics.mean(xs)
        my = statistics.mean(ys)
    except statistics.StatisticsError:
        return None
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def mean_or_none(vs: Iterable[Optional[float]]) -> Optional[float]:
    clean = [v for v in vs if isinstance(v, (int, float))]
    return statistics.mean(clean) if clean else None


def fmt(v: Optional[float], digits: int = 3) -> str:
    if v is None:
        return "—"
    return f"{v:.{digits}f}"


# ---------------------------------------------------------------------------
# Group aggregation
# ---------------------------------------------------------------------------


def group_stats(
    summaries: List[Dict[str, Any]], key: str
) -> List[Tuple[str, Dict[str, Any]]]:
    """Bucket summaries by a key (``tier``, ``profile``, ``vendor``) and
    compute mean accuracy raw/rendered/delta per bucket.
    """
    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for s in summaries:
        buckets[str(s.get(key, "unknown"))].append(s)

    rows: List[Tuple[str, Dict[str, Any]]] = []
    for label, items in sorted(buckets.items()):
        rows.append(
            (
                label,
                {
                    "n": len(items),
                    "mean_acc_raw": mean_or_none(x.get("accuracy_raw") for x in items),
                    "mean_acc_rendered": mean_or_none(
                        x.get("accuracy_rendered") for x in items
                    ),
                    "mean_acc_delta": mean_or_none(
                        x.get("accuracy_delta") for x in items
                    ),
                    "mean_parseability_raw": mean_or_none(
                        x.get("parseability_score_raw") for x in items
                    ),
                    "mean_parseability_rendered": mean_or_none(
                        x.get("parseability_score_rendered") for x in items
                    ),
                    "mean_universal_raw": mean_or_none(
                        x.get("universal_score_raw") for x in items
                    ),
                    "mean_universal_rendered": mean_or_none(
                        x.get("universal_score_rendered") for x in items
                    ),
                    "raw_fetch_failed": sum(
                        1 for x in items if x.get("raw_fetch_status") != "ok"
                    ),
                    "rendered_fetch_failed": sum(
                        1 for x in items if x.get("rendered_fetch_status") != "ok"
                    ),
                },
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Correlation analysis — Clipper score vs measured accuracy
# ---------------------------------------------------------------------------


def correlation_table(summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute Pearson r between each Clipper score and measured accuracy.

    Only pages where BOTH the score field and the accuracy field are
    numeric contribute. Returns one row per (score_field, accuracy_field)
    pair.
    """
    pairs = [
        ("parseability_score_raw", "accuracy_raw"),
        ("parseability_score_rendered", "accuracy_rendered"),
        ("universal_score_raw", "accuracy_raw"),
        ("universal_score_rendered", "accuracy_rendered"),
    ]
    rows: List[Dict[str, Any]] = []
    for score_key, acc_key in pairs:
        xs: List[float] = []
        ys: List[float] = []
        for s in summaries:
            sv = s.get(score_key)
            av = s.get(acc_key)
            if isinstance(sv, (int, float)) and isinstance(av, (int, float)):
                xs.append(float(sv))
                ys.append(float(av))
        rows.append(
            {
                "score_field": score_key,
                "accuracy_field": acc_key,
                "n": len(xs),
                "pearson_r": pearson_r(xs, ys),
                "mean_score": mean_or_none(xs),
                "mean_accuracy": mean_or_none(ys),
            }
        )
    return rows


def component_correlations(
    summaries: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Per-pillar correlation with rendered-mode accuracy.

    Uses ``component_scores_rendered`` against ``accuracy_rendered``, since
    rendered is the ground-truth extraction.
    """
    pillars = [
        "semantic_html",
        "content_extractability",
        "structured_data",
        "dom_navigability",
        "metadata_completeness",
        "http_compliance",
    ]
    rows: List[Dict[str, Any]] = []
    for pillar in pillars:
        xs: List[float] = []
        ys: List[float] = []
        for s in summaries:
            comps = s.get("component_scores_rendered") or {}
            sv = comps.get(pillar)
            av = s.get("accuracy_rendered")
            if isinstance(sv, (int, float)) and isinstance(av, (int, float)):
                xs.append(float(sv))
                ys.append(float(av))
        rows.append(
            {
                "pillar": pillar,
                "n": len(xs),
                "pearson_r": pearson_r(xs, ys),
                "mean_pillar_score": mean_or_none(xs),
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Report emission
# ---------------------------------------------------------------------------


def write_csv(path: Path, summaries: List[Dict[str, Any]]) -> None:
    fieldnames = [
        "slug",
        "url",
        "tier",
        "profile",
        "vendor",
        "num_pairs",
        "accuracy_raw",
        "accuracy_rendered",
        "accuracy_delta",
        "raw_fetch_status",
        "rendered_fetch_status",
        "parseability_score_raw",
        "parseability_score_rendered",
        "universal_score_raw",
        "universal_score_rendered",
        "content_type",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for s in summaries:
            w.writerow(s)


def render_markdown(
    summaries: List[Dict[str, Any]],
    overall: Dict[str, Any],
    by_tier: List[Tuple[str, Dict[str, Any]]],
    by_profile: List[Tuple[str, Dict[str, Any]]],
    by_vendor: List[Tuple[str, Dict[str, Any]]],
    corr_rows: List[Dict[str, Any]],
    comp_corr: List[Dict[str, Any]],
    fetch_counts: Dict[str, Counter],
) -> str:
    lines: List[str] = []
    a = lines.append

    a(f"# Phase 5 pilot analysis — N={len(summaries)}\n")

    a("## Headline: raw vs rendered accuracy\n")
    a("| Metric | Raw | Rendered | Delta |")
    a("|---|---|---|---|")
    a(
        f"| Mean accuracy | {fmt(overall['mean_acc_raw'])} | "
        f"{fmt(overall['mean_acc_rendered'])} | "
        f"{fmt(overall['mean_acc_delta'])} |"
    )
    a(
        f"| Mean parseability_score | {fmt(overall['mean_parseability_raw'], 1)} | "
        f"{fmt(overall['mean_parseability_rendered'], 1)} | — |"
    )
    a(
        f"| Mean universal_score | {fmt(overall['mean_universal_raw'], 1)} | "
        f"{fmt(overall['mean_universal_rendered'], 1)} | — |"
    )
    a("")

    def _group_table(title: str, rows: List[Tuple[str, Dict[str, Any]]]) -> None:
        a(f"## By {title}\n")
        a("| " + title + " | n | acc raw | acc rend | delta | parse raw | parse rend |")
        a("|---|---|---|---|---|---|---|")
        for label, v in rows:
            a(
                f"| {label} | {v['n']} | "
                f"{fmt(v['mean_acc_raw'])} | {fmt(v['mean_acc_rendered'])} | "
                f"{fmt(v['mean_acc_delta'])} | "
                f"{fmt(v['mean_parseability_raw'], 1)} | "
                f"{fmt(v['mean_parseability_rendered'], 1)} |"
            )
        a("")

    _group_table("tier", by_tier)
    _group_table("profile", by_profile)
    _group_table("vendor", by_vendor)

    a("## Fetch outcomes\n")
    a("| Mode | Statuses |")
    a("|---|---|")
    for mode, ctr in fetch_counts.items():
        a(f"| {mode} | " + ", ".join(f"{k}: {v}" for k, v in ctr.most_common()) + " |")
    a("")

    a("## Correlation: Clipper score vs measured accuracy\n")
    a("| Score field | Accuracy field | n | Pearson r | mean score | mean accuracy |")
    a("|---|---|---|---|---|---|")
    for r in corr_rows:
        a(
            f"| {r['score_field']} | {r['accuracy_field']} | {r['n']} | "
            f"{fmt(r['pearson_r'])} | {fmt(r['mean_score'], 1)} | "
            f"{fmt(r['mean_accuracy'])} |"
        )
    a("")

    a("## Per-pillar correlation with rendered accuracy\n")
    a("| Pillar | n | Pearson r | mean pillar score |")
    a("|---|---|---|---|")
    for r in comp_corr:
        a(
            f"| {r['pillar']} | {r['n']} | {fmt(r['pearson_r'])} | "
            f"{fmt(r['mean_pillar_score'], 1)} |"
        )
    a("")

    a("## Per-page detail\n")
    a(
        "| slug | tier | profile | vendor | acc raw | acc rend | "
        "parse raw | parse rend | raw fetch | rend fetch |"
    )
    a("|---|---|---|---|---|---|---|---|---|---|")
    for s in sorted(
        summaries,
        key=lambda x: (
            x.get("tier", "z"),
            x.get("profile", "z"),
            x.get("slug", ""),
        ),
    ):
        a(
            f"| {s.get('slug', '')[:50]} | {s.get('tier', '')} | "
            f"{s.get('profile', '')} | {s.get('vendor', '')} | "
            f"{fmt(s.get('accuracy_raw'))} | "
            f"{fmt(s.get('accuracy_rendered'))} | "
            f"{fmt(s.get('parseability_score_raw'), 1)} | "
            f"{fmt(s.get('parseability_score_rendered'), 1)} | "
            f"{s.get('raw_fetch_status', '')} | "
            f"{s.get('rendered_fetch_status', '')} |"
        )
    a("")

    return "\n".join(lines)


def compute_overall(summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "n": len(summaries),
        "mean_acc_raw": mean_or_none(s.get("accuracy_raw") for s in summaries),
        "mean_acc_rendered": mean_or_none(
            s.get("accuracy_rendered") for s in summaries
        ),
        "mean_acc_delta": mean_or_none(s.get("accuracy_delta") for s in summaries),
        "mean_parseability_raw": mean_or_none(
            s.get("parseability_score_raw") for s in summaries
        ),
        "mean_parseability_rendered": mean_or_none(
            s.get("parseability_score_rendered") for s in summaries
        ),
        "mean_universal_raw": mean_or_none(
            s.get("universal_score_raw") for s in summaries
        ),
        "mean_universal_rendered": mean_or_none(
            s.get("universal_score_rendered") for s in summaries
        ),
    }


def fetch_counts(summaries: List[Dict[str, Any]]) -> Dict[str, Counter]:
    return {
        "raw": Counter(s.get("raw_fetch_status", "missing") for s in summaries),
        "rendered": Counter(
            s.get("rendered_fetch_status", "missing") for s in summaries
        ),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("evaluation/phase5-results/corpus-001"),
        help="Directory containing per-page <slug>/summary.json files.",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path("urls/phase5-corpus-urls.txt"),
        help="Corpus URL file (for tier + vendor labels).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory. Defaults to <results>-analysis.",
    )
    args = parser.parse_args()

    results_dir: Path = args.results
    if not results_dir.is_dir():
        print(f"error: results dir not found: {results_dir}", file=sys.stderr)
        return 2

    corpus_meta = load_corpus_metadata(args.corpus)
    summaries = load_summaries(results_dir)
    if not summaries:
        print(f"error: no summary.json files found under {results_dir}", file=sys.stderr)
        return 2
    merge_tier_vendor(summaries, corpus_meta)

    out_dir: Path = args.out or Path(str(results_dir) + "-analysis")
    out_dir.mkdir(parents=True, exist_ok=True)

    overall = compute_overall(summaries)
    by_tier = group_stats(summaries, "tier")
    by_profile = group_stats(summaries, "profile")
    by_vendor = group_stats(summaries, "vendor")
    corr_rows = correlation_table(summaries)
    comp_corr = component_correlations(summaries)
    fc = fetch_counts(summaries)

    md = render_markdown(
        summaries, overall, by_tier, by_profile, by_vendor, corr_rows, comp_corr, fc
    )
    (out_dir / "analysis.md").write_text(md, encoding="utf-8")

    write_csv(out_dir / "per-page.csv", summaries)

    stats_json = {
        "n": overall["n"],
        "overall": overall,
        "by_tier": [{"label": k, **v} for k, v in by_tier],
        "by_profile": [{"label": k, **v} for k, v in by_profile],
        "by_vendor": [{"label": k, **v} for k, v in by_vendor],
        "fetch_counts": {k: dict(v) for k, v in fc.items()},
        "correlation_score_vs_accuracy": corr_rows,
        "correlation_pillar_vs_rendered_accuracy": comp_corr,
    }
    (out_dir / "stats.json").write_text(
        json.dumps(stats_json, indent=2), encoding="utf-8"
    )

    print(f"wrote {out_dir / 'analysis.md'}")
    print(f"wrote {out_dir / 'per-page.csv'}")
    print(f"wrote {out_dir / 'stats.json'}")
    print()
    print(f"N = {overall['n']}")
    print(
        f"  mean accuracy: raw={fmt(overall['mean_acc_raw'])}  "
        f"rendered={fmt(overall['mean_acc_rendered'])}  "
        f"delta={fmt(overall['mean_acc_delta'])}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
