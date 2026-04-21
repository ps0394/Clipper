import json
d = json.load(open('evaluation/competitive-analysis-v2/competitive-v2-fix3_scores.json'))
for e in d:
    url = e['url'][-45:]
    score = e['parseability_score']
    comps = {k: round(v, 1) for k, v in e['component_scores'].items()}
    print(f"{url}: {score:.1f} -> {comps}")
print(f"\nAvg: {sum(e['parseability_score'] for e in d)/len(d):.1f}")
