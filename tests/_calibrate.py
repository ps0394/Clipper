"""One-off calibration script: prints component scores for every fixture.

Not part of the pytest suite. Run it manually when adding a new fixture to
pick reasonable range bounds for assertions.
"""

from pathlib import Path

from retrievability.access_gate_evaluator import AccessGateEvaluator
from retrievability.parse import _parse_html_file


FIXTURES = Path(__file__).parent / "fixtures"


def main() -> None:
    evaluator = AccessGateEvaluator()
    for fixture in sorted(FIXTURES.glob("*.html")):
        parse_result = _parse_html_file(fixture)
        score = evaluator.evaluate_access_gate(
            parse_result.to_dict(), url=None, crawl_data=None
        )
        print(f"\n=== {fixture.name} ===")
        print(f"  parseability_score = {score.parseability_score:.1f}")
        for pillar, value in score.component_scores.items():
            print(f"    {pillar:<26} {value:6.1f}")


if __name__ == "__main__":
    main()
