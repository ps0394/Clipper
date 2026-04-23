"""Build calibration triples (review) and hand-labels template."""
import json
from pathlib import Path

base = Path('evaluation/phase5-results/pilot-001')
out = []
template = []
for slug_dir in sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith('_')):
    qa_path = slug_dir / 'qapairs.json'
    sc_path = slug_dir / 'scoring.primary.json'
    jg_path = slug_dir / 'grades.primary.judged.json'
    if not (qa_path.is_file() and sc_path.is_file() and jg_path.is_file()):
        continue
    qa = json.loads(qa_path.read_text(encoding='utf-8'))
    sc = json.loads(sc_path.read_text(encoding='utf-8'))
    jg = json.loads(jg_path.read_text(encoding='utf-8'))
    for i, pair in enumerate(qa):
        answer = next(a for a in sc if a['pair_index'] == i and a['run_index'] == 0)
        judged = next(g for g in jg if g['pair_index'] == i and g['run_index'] == 0)
        out.append({
            'slug': slug_dir.name,
            'pair_index': i,
            'question': pair['question'],
            'ground_truth': pair['answer'],
            'candidate': answer['answer'],
            'judge_label': judged['label'],
            'judge_rationale': judged['rationale'],
        })
        template.append({
            'slug': slug_dir.name,
            'pair_index': i,
            'label': 'TODO',  # hand-label: correct | incorrect | not_in_document
        })

(base / '_calibration').mkdir(exist_ok=True)
(base / '_calibration' / 'review-triples.json').write_text(
    json.dumps(out, indent=2), encoding='utf-8'
)
(base / '_calibration' / 'hand-labels-template.json').write_text(
    json.dumps(template, indent=2), encoding='utf-8'
)
print(f'wrote {len(out)} triples to {base / "_calibration"}')
