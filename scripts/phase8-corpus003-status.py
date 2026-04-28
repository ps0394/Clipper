import json
import sys
from pathlib import Path

p = Path("evaluation/phase5-results/corpus-003/pilot-summary.json")
d = json.loads(p.read_text(encoding="utf-8"))
pages = d["pages"]
print(f"pages in summary: {len(pages)}")
print(f"mean_accuracy_rendered (all pages incl. fetch failures): {d['mean_accuracy_rendered']:.3f}")
print(f"mean_accuracy_raw: {d['mean_accuracy_raw']:.3f}")
print(f"pages_raw_only_failure: {d['pages_raw_only_failure']}")
print(f"pages_both_failed: {d['pages_both_failed']}")

scored = [p for p in pages if p.get("num_pairs", 0) > 0]
print(f"\npages with num_pairs > 0: {len(scored)}")
if scored:
    accs = [p["accuracy"] for p in scored]
    print(f"mean accuracy (scored only): {sum(accs)/len(accs):.3f}")

zero = [p for p in pages if p.get("num_pairs", 0) == 0]
print(f"\npages with num_pairs == 0 (fetch/extract too short): {len(zero)}")

# Per-vendor breakdown
from collections import defaultdict
by_vendor = defaultdict(list)
for pg in scored:
    url = pg["url"]
    # crude vendor extraction
    if "docs.python.org" in url: v = "python"
    elif "learn.microsoft.com" in url: v = "learn"
    elif "docs.aws.amazon.com" in url: v = "aws"
    elif "developers.cloudflare.com" in url: v = "cloudflare"
    elif "mongodb.com" in url: v = "mongodb"
    elif "developer.hashicorp.com" in url: v = "terraform"
    elif "huggingface.co" in url: v = "huggingface"
    elif "docs.databricks.com" in url: v = "databricks"
    elif "vercel.com" in url: v = "vercel"
    elif "clickhouse.com" in url: v = "clickhouse"
    else: v = "other"
    by_vendor[v].append(pg["accuracy"])

print(f"\nPer-vendor scored counts and mean accuracy:")
for v in sorted(by_vendor):
    accs = by_vendor[v]
    print(f"  {v:14s} n={len(accs):3d}  mean_acc={sum(accs)/len(accs):.3f}")

# Profile breakdown
by_profile = defaultdict(list)
for pg in scored:
    by_profile[pg["profile"]].append(pg["accuracy"])
print(f"\nPer-profile scored counts and mean accuracy:")
for prof in sorted(by_profile):
    accs = by_profile[prof]
    print(f"  {prof:14s} n={len(accs):3d}  mean_acc={sum(accs)/len(accs):.3f}")
