"""Render review-triples.json as a markdown labeling sheet."""
import json
from pathlib import Path

base = Path('evaluation/phase5-results/pilot-001/_calibration')
triples = json.loads((base / 'review-triples.json').read_text(encoding='utf-8'))

lines = [
    '# Phase 5 judge-calibration hand-labels',
    '',
    'For each item, decide whether the **candidate** is a correct answer to the **question**, '
    'given that the **ground truth** is the authoritative answer. The **judge** column shows '
    'what Llama 3.3 said.',
    '',
    'Your job: fill in the `hand` column with `correct`, `incorrect`, or `not_in_document`. ',
    '',
    'When done, copy your labels into `hand-labels-template.json` (rename to `hand-labels.json`) '
    'and run `python main.py phase5 kappa evaluation/phase5-results/pilot-001`.',
    '',
]

current_slug = None
for t in triples:
    if t['slug'] != current_slug:
        current_slug = t['slug']
        lines.append('')
        lines.append(f"## {current_slug}")
        lines.append('')
    lines.append(f"### Pair {t['pair_index']}")
    lines.append('')
    lines.append(f"**Q:** {t['question']}")
    lines.append('')
    lines.append(f"**Ground truth:** {t['ground_truth']}")
    lines.append('')
    lines.append(f"**Candidate:** {t['candidate']}")
    lines.append('')
    lines.append(f"**Judge:** `{t['judge_label']}` — {t['judge_rationale']}")
    lines.append('')
    lines.append(f"**Your label:** `TODO`")
    lines.append('')
    lines.append('---')
    lines.append('')

out_path = base / 'labeling-sheet.md'
out_path.write_text('\n'.join(lines), encoding='utf-8')
print(f'wrote {out_path}')
