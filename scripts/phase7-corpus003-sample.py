"""
phase7-corpus003-sample.py — Deterministic stratified sampler for corpus-003.

Reads candidate-pool files from `evaluation/corpus-003/candidate-pools/<vendor>.txt`,
classifies each URL by profile via the same URL-path heuristics the live classifier
uses (see retrievability/profiles.py), and produces a stratified random sample of
~25 URLs per vendor with a per-(vendor x profile) cell floor of 5 where the pool
supports it. Adds the 20 hard-coded challenged-fetch URLs at the end.

Pre-registration artifact:
- This script (selection rule, seed, challenged-fetch list, vendor list)
- The candidate-pool files in evaluation/corpus-003/candidate-pools/
- The output evaluation/corpus-003/urls.txt

Re-running with no input changes must produce a byte-identical urls.txt
(acceptance gate G6).

Spec: evaluation/corpus-003/spec.md
"""
from __future__ import annotations

import argparse
import hashlib
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SEED = 20260427  # locked in spec.md §3 step 3
TARGET_PER_VENDOR = 25
PROFILE_FLOOR = 5

VALID_PROFILES = ("article", "landing", "reference", "sample", "faq", "tutorial")

# Mirrors retrievability/profiles.py URL_HEURISTICS (first-hit-wins substring match).
URL_HEURISTICS: Tuple[Tuple[str, str], ...] = (
    ("/api/", "reference"),
    ("/reference/", "reference"),
    ("/samples/", "sample"),
    ("/sample/", "sample"),
    ("/faq", "faq"),
    ("/tutorial", "tutorial"),
    ("/quickstart", "tutorial"),
    ("/how-to", "tutorial"),
    ("/overview", "landing"),
    ("/landing", "landing"),
)

VENDORS = (
    "python",
    "learn",
    "aws",
    "cloudflare",
    "mongodb",
    "terraform",
    "huggingface",
    "databricks",
    "vercel",
    "clickhouse",
)

# Challenged-fetch stratum — 20 deliberate stress URLs (spec.md §2.4).
# Each entry: (url, vendor, profile, sub_stratum).
# sub_stratum is one of: cf_challenge, robots_blocked, ua_variant.
CHALLENGED_URLS: Tuple[Tuple[str, str, str, str], ...] = (
    # 8 Cloudflare-challenged
    ("https://developers.cloudflare.com/bots/concepts/bot/", "cloudflare", "article", "cf_challenge"),
    ("https://developers.cloudflare.com/turnstile/get-started/", "cloudflare", "tutorial", "cf_challenge"),
    ("https://developers.cloudflare.com/waf/", "cloudflare", "landing", "cf_challenge"),
    ("https://developers.cloudflare.com/ddos-protection/", "cloudflare", "landing", "cf_challenge"),
    ("https://docs.databricks.com/aws/en/security/network/", "databricks", "article", "cf_challenge"),
    ("https://huggingface.co/docs/hub/spaces", "huggingface", "landing", "cf_challenge"),
    ("https://vercel.com/docs/edge-network/regions", "vercel", "reference", "cf_challenge"),
    ("https://clickhouse.com/docs/cloud/manage/api/api-overview", "clickhouse", "reference", "cf_challenge"),
    # 6 robots-blocked
    ("https://learn.microsoft.com/en-us/dotnet/api/system.threading.cancellationtoken", "learn", "reference", "robots_blocked"),
    ("https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingMetadata.html", "aws", "article", "robots_blocked"),
    ("https://www.mongodb.com/docs/manual/core/authentication/", "mongodb", "article", "robots_blocked"),
    ("https://developer.hashicorp.com/terraform/language/providers/requirements", "terraform", "article", "robots_blocked"),
    ("https://docs.python.org/3/library/typing.html", "python", "reference", "robots_blocked"),
    ("https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-aux", "databricks", "reference", "robots_blocked"),
    # 6 UA-allowlist-variant
    ("https://huggingface.co/docs/text-generation-inference/index", "huggingface", "landing", "ua_variant"),
    ("https://vercel.com/docs/edge-network/caching", "vercel", "article", "ua_variant"),
    ("https://www.mongodb.com/docs/atlas/atlas-search/", "mongodb", "landing", "ua_variant"),
    ("https://clickhouse.com/docs/cloud/manage/billing", "clickhouse", "article", "ua_variant"),
    ("https://developer.hashicorp.com/terraform/cloud-docs/api-docs", "terraform", "reference", "ua_variant"),
    ("https://learn.microsoft.com/en-us/azure/openai/concepts/models", "learn", "article", "ua_variant"),
)


def classify_profile(url: str, override: Optional[str]) -> str:
    """Classify a URL into a profile.

    If `override` is set, return it (it must be in VALID_PROFILES).
    Otherwise apply URL_HEURISTICS (first-hit-wins substring match).
    Default to 'article' if no heuristic matches.
    """
    if override:
        if override not in VALID_PROFILES:
            raise ValueError(f"Invalid profile override {override!r} for {url!r}")
        return override
    lower = url.lower()
    for needle, profile in URL_HEURISTICS:
        if needle in lower:
            return profile
    return "article"


def load_pool(path: Path) -> List[Tuple[str, str]]:
    """Load a vendor's candidate pool. Returns list of (url, profile)."""
    entries: List[Tuple[str, str]] = []
    seen_urls: set = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        # Tab-separated: URL [TAB] profile_override
        parts = line.split("\t")
        url = parts[0].strip()
        override = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
        if not url:
            continue
        if url in seen_urls:
            raise ValueError(f"Duplicate URL in {path.name}: {url}")
        seen_urls.add(url)
        profile = classify_profile(url, override)
        entries.append((url, profile))
    return entries


def stratified_sample(
    vendor: str,
    pool: List[Tuple[str, str]],
    target: int,
    floor: int,
    rng: random.Random,
) -> List[Tuple[str, str]]:
    """Stratified random sample from pool.

    Strategy:
    1. Group pool by profile, shuffle each bucket.
    2. Floor allocation: take min(floor, len(bucket)) from each profile.
       Floor is sacred — never truncated. Total may slightly exceed target.
    3. Fill remaining slots up to target from leftovers (round-robin shuffle).
    """
    by_profile: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    for url, profile in pool:
        by_profile[profile].append((url, profile))
    for profile in list(by_profile.keys()):
        rng.shuffle(by_profile[profile])

    selected: List[Tuple[str, str]] = []
    extras: List[Tuple[str, str]] = []

    for profile in VALID_PROFILES:
        bucket = by_profile.get(profile, [])
        take = min(floor, len(bucket))
        selected.extend(bucket[:take])
        extras.extend(bucket[take:])

    rng.shuffle(extras)
    while len(selected) < target and extras:
        selected.append(extras.pop(0))

    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root (default: parent of script directory)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run sampling twice and verify byte-identical output (G6 check). Does not write urls.txt.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output path (default: <repo>/evaluation/corpus-003/urls.txt)",
    )
    args = parser.parse_args()

    repo = args.repo_root
    pool_dir = repo / "evaluation" / "corpus-003" / "candidate-pools"
    out_path = args.out or (repo / "evaluation" / "corpus-003" / "urls.txt")

    if not pool_dir.exists():
        print(f"ERROR: pool directory not found: {pool_dir}", file=sys.stderr)
        return 2

    # ---- Load pools ----
    pools: Dict[str, List[Tuple[str, str]]] = {}
    for vendor in VENDORS:
        pool_file = pool_dir / f"{vendor}.txt"
        if not pool_file.exists():
            print(f"ERROR: missing pool file: {pool_file}", file=sys.stderr)
            return 2
        pools[vendor] = load_pool(pool_file)

    # ---- Sample (deterministic) ----
    def sample_once() -> List[Tuple[str, str, str, str]]:
        """Return list of (url, vendor, profile, challenged_tag).

        challenged_tag is "" for non-challenged URLs, or one of the sub-strata.
        """
        rows: List[Tuple[str, str, str, str]] = []
        # Stratified per-vendor sample. Use a per-vendor RNG seeded deterministically
        # from SEED + vendor name so adding/reordering vendors doesn't reshuffle others.
        for vendor in VENDORS:
            vendor_seed = int(hashlib.sha256(f"{SEED}:{vendor}".encode()).hexdigest()[:12], 16)
            rng = random.Random(vendor_seed)
            picked = stratified_sample(
                vendor, pools[vendor], TARGET_PER_VENDOR, PROFILE_FLOOR, rng
            )
            # Sort within vendor for stable output
            picked_sorted = sorted(picked, key=lambda x: (x[1], x[0]))
            for url, profile in picked_sorted:
                rows.append((url, vendor, profile, ""))

        # Append challenged-fetch URLs (not sampled; explicit list)
        challenged_seen: set = set()
        for url, vendor, profile, sub in CHALLENGED_URLS:
            if url in challenged_seen:
                raise ValueError(f"Duplicate challenged URL: {url}")
            challenged_seen.add(url)
            rows.append((url, vendor, profile, sub))

        return rows

    rows = sample_once()

    # ---- Format output ----
    def format_output(rs: List[Tuple[str, str, str, str]]) -> str:
        # Phase 5 loader (retrievability/phase5/runner.py::_parse_pilot_line) splits on
        # TAB or comma: parts[0]=url, parts[1]=profile, parts[2]=vendor (ignored).
        # We keep challenged-fetch sub-stratum as a trailing inline comment so the loader
        # treats it as a comment but corpus-003 analysis scripts can still recover it.
        lines = [
            "# corpus-003 URL list",
            f"# Generated by scripts/phase7-corpus003-sample.py (seed={SEED})",
            "# Pre-registered methodology — see evaluation/corpus-003/spec.md",
            "# Format: <url>\\t<profile>\\t<vendor>  [# challenged=<sub_stratum>]",
            "",
        ]
        for url, vendor, profile, sub in rs:
            base = f"{url}\t{profile}\t{vendor}"
            if sub:
                lines.append(f"{base}  # challenged={sub}")
            else:
                lines.append(base)
        return "\n".join(lines) + "\n"

    out_text = format_output(rows)

    # ---- Reproducibility check (G6) ----
    if args.check:
        rows2 = sample_once()
        out_text2 = format_output(rows2)
        h1 = hashlib.sha256(out_text.encode()).hexdigest()
        h2 = hashlib.sha256(out_text2.encode()).hexdigest()
        if h1 != h2:
            print(f"FAIL G6 reproducibility: {h1} != {h2}", file=sys.stderr)
            return 1
        print(f"G6 OK: deterministic, hash={h1}")
        return 0

    # ---- Write output ----
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out_text, encoding="utf-8")

    # ---- Acceptance gates report (G1-G6) ----
    vendor_counts: Counter = Counter()
    cell_counts: Counter = Counter()
    profile_counts: Counter = Counter()
    challenged_counts: Counter = Counter()
    challenged_total = 0
    for url, vendor, profile, sub in rows:
        vendor_counts[vendor] += 1
        cell_counts[(vendor, profile)] += 1
        profile_counts[profile] += 1
        if sub:
            challenged_counts[sub] += 1
            challenged_total += 1

    total = len(rows)
    print(f"\n=== corpus-003 sampler report ===")
    print(f"Total URLs:      {total}")
    print(f"Output:          {out_path}")
    print(f"Output sha256:   {hashlib.sha256(out_text.encode()).hexdigest()}")

    print(f"\nPer-vendor counts:")
    for v in VENDORS:
        print(f"  {v:14s} {vendor_counts[v]:3d}")

    print(f"\nPer-profile totals:")
    for p in VALID_PROFILES:
        print(f"  {p:14s} {profile_counts[p]:3d}")

    print(f"\nChallenged-fetch sub-strata:")
    for sub in ("cf_challenge", "robots_blocked", "ua_variant"):
        print(f"  {sub:18s} {challenged_counts[sub]:3d}")
    print(f"  {'TOTAL':18s} {challenged_total:3d}")

    # Gate evaluation
    print(f"\n=== Acceptance gates ===")
    g1 = all(vendor_counts[v] > 0 for v in VENDORS)
    print(f"G1 vendor coverage:    {'PASS' if g1 else 'FAIL'} (10/{sum(1 for v in VENDORS if vendor_counts[v] > 0)} vendors present)")

    floor_failures: List[str] = []
    floor_under_pool_capacity: List[str] = []
    for vendor in VENDORS:
        pool_profile_counts: Counter = Counter(p for _, p in pools[vendor])
        for profile in VALID_PROFILES:
            available = pool_profile_counts[profile]
            sampled = cell_counts[(vendor, profile)]
            if available >= PROFILE_FLOOR and sampled < PROFILE_FLOOR:
                # Pool could supply >= floor but sampler under-delivered — real failure
                floor_failures.append(f"{vendor}/{profile}={sampled}/pool={available}")
            elif 0 < available < PROFILE_FLOOR and sampled < available:
                # Pool has some entries but fewer than floor; sampler should still take all
                floor_failures.append(f"{vendor}/{profile}={sampled}/pool={available}")
            elif 0 < available < PROFILE_FLOOR:
                # Pool capacity below floor — recorded as deviation, not failure
                floor_under_pool_capacity.append(f"{vendor}/{profile}={sampled}(pool={available})")
    g2 = len(floor_failures) == 0
    print(f"G2 per-cell floor>={PROFILE_FLOOR}:  {'PASS' if g2 else 'FAIL'}"
          + (f" — under-floor cells: {', '.join(floor_failures)}" if floor_failures else ""))
    if floor_under_pool_capacity:
        print(f"   (pool-capacity deviations, allowed by spec §2.3): "
              f"{', '.join(floor_under_pool_capacity)}")

    g3 = (
        challenged_total == 20
        and challenged_counts.get("cf_challenge", 0) == 8
        and challenged_counts.get("robots_blocked", 0) == 6
        and challenged_counts.get("ua_variant", 0) == 6
    )
    print(f"G3 challenged-fetch:   {'PASS' if g3 else 'FAIL'} (got {challenged_total} total: "
          f"cf={challenged_counts.get('cf_challenge', 0)}, "
          f"robots={challenged_counts.get('robots_blocked', 0)}, "
          f"ua={challenged_counts.get('ua_variant', 0)})")

    g4 = 230 <= total <= 290
    print(f"G4 total size 230-290: {'PASS' if g4 else 'FAIL'} (n={total})")

    # G5 corpus-002 overlap — checked separately if corpus-002 manifest available
    corpus002_summary = repo / "evaluation" / "phase5-results" / "corpus-002" / "pilot-summary.json"
    g5_status = "SKIP (corpus-002 pilot-summary.json not found)"
    g5 = True
    if corpus002_summary.exists():
        import json
        c002 = json.loads(corpus002_summary.read_text(encoding="utf-8"))
        c002_urls = {p["url"] for p in c002.get("pages", []) if p.get("url")}
        c003_urls = {url for url, _, _, _ in rows}
        overlap = c002_urls & c003_urls
        g5 = len(overlap) == 0
        g5_status = (
            f"PASS (checked {len(c002_urls)} corpus-002 URLs)"
            if g5 else f"FAIL — overlap: {sorted(overlap)}"
        )
    print(f"G5 no corpus-002 overlap: {g5_status}")

    print(f"G6 reproducibility:    run with --check to verify")

    all_pass = g1 and g2 and g3 and g4 and g5
    print(f"\nResult: {'ALL GATES PASS' if all_pass else 'SOME GATES FAIL — see above'}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
