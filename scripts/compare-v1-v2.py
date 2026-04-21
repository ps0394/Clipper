"""Compare v1 vs v2 evaluation scores."""
import json

def load(path):
    with open(path) as f:
        return json.load(f)

def short_url(u):
    parts = u.rstrip('/').split('/')
    return '/'.join(parts[-2:]) if len(parts) > 2 else u

def compare(name, v1_path, v2_path):
    v1 = load(v1_path)
    v2 = load(v2_path)
    v1_map = {e['url']: e for e in v1}
    v2_map = {e['url']: e for e in v2}
    all_urls = sorted(set(list(v1_map.keys()) + list(v2_map.keys())))

    print('=' * 110)
    print(f'{name}: v1 vs v2 COMPARISON')
    print('=' * 110)
    hdr = f"{'URL':>55} | {'v1':>6} | {'v2':>6} | {'Delta':>7} | {'v1 Class':<24} | v2 Class"
    print(hdr)
    print('-' * 110)

    v1_scores, v2_scores = [], []
    for url in all_urls:
        e1 = v1_map.get(url)
        e2 = v2_map.get(url)
        s1 = e1['parseability_score'] if e1 else None
        s2 = e2['parseability_score'] if e2 else None
        f1 = e1.get('failure_mode', 'N/A') if e1 else 'N/A'
        f2 = e2.get('failure_mode', 'N/A') if e2 else 'N/A'
        delta_str = f"{s2 - s1:>+7.1f}" if s1 and s2 else "    N/A"
        s1_str = f"{s1:>6.1f}" if s1 else "   N/A"
        s2_str = f"{s2:>6.1f}" if s2 else "   N/A"
        if s1: v1_scores.append(s1)
        if s2: v2_scores.append(s2)
        print(f"{short_url(url):>55} | {s1_str} | {s2_str} | {delta_str} | {f1:<24} | {f2}")

    print('-' * 110)
    avg1 = sum(v1_scores)/len(v1_scores) if v1_scores else 0
    avg2 = sum(v2_scores)/len(v2_scores) if v2_scores else 0
    print(f"{'AVERAGE':>55} | {avg1:>6.1f} | {avg2:>6.1f} | {avg2-avg1:>+7.1f}")

    # Component averages
    print()
    print(f"COMPONENT AVERAGES ({name})")
    print('-' * 70)
    v1_comps, v2_comps = {}, {}
    for e in v1:
        for k, v in e['component_scores'].items():
            v1_comps.setdefault(k, []).append(v)
    for e in v2:
        for k, v in e['component_scores'].items():
            v2_comps.setdefault(k, []).append(v)

    all_keys = sorted(set(list(v1_comps.keys()) + list(v2_comps.keys())))
    print(f"{'Component':>30} | {'v1 Avg':>8} | {'v2 Avg':>8} | {'Delta':>8}")
    print('-' * 70)
    for k in all_keys:
        a1 = sum(v1_comps[k])/len(v1_comps[k]) if k in v1_comps else None
        a2 = sum(v2_comps[k])/len(v2_comps[k]) if k in v2_comps else None
        if a1 is not None and a2 is not None:
            print(f"{k:>30} | {a1:>8.1f} | {a2:>8.1f} | {a2-a1:>+8.1f}")
        elif a1 is not None:
            print(f"{k:>30} | {a1:>8.1f} | {'(gone)':>8} |")
        else:
            print(f"{k:>30} | {'(new)':>8} | {a2:>8.1f} |")
    print()

compare("LEARN ANALYSIS",
        "evaluation/learn-analysis/learn-ms-topic-analysis_scores.json",
        "evaluation/learn-analysis-v2/learn-v2-scores_scores.json")

compare("COMPETITIVE ANALYSIS",
        "evaluation/competitive-analysis/competitive-comparison_scores.json",
        "evaluation/competitive-analysis-v2/competitive-v2-scores_scores.json")
