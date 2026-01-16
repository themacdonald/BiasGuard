from __future__ import annotations

import argparse
import json
from pathlib import Path

from .metrics import FairnessReport, disparate_impact_ratio, equal_opportunity_difference, statistical_parity_difference


def main() -> None:
    parser = argparse.ArgumentParser(prog="biasguard", description="BiasGuard CLI (v0.1)")
    parser.add_argument("--out", default="reports/report.json", help="Output path for report JSON")
    parser.add_argument("--demo", action="store_true", help="Run a small demo report (no CSV yet)")
    args = parser.parse_args()

    if not args.demo:
        raise SystemExit("v0.1 supports --demo only. Next step: add CSV loader + audit command.")

    # Tiny demo data
    y_true_p = [1, 1, 0, 0, 1]
    y_pred_p = [1, 0, 0, 0, 1]
    y_true_r = [1, 1, 0, 0, 1]
    y_pred_r = [1, 1, 0, 0, 1]

    report = FairnessReport(
        dir=disparate_impact_ratio(y_pred_p, y_pred_r),
        spd=statistical_parity_difference(y_pred_p, y_pred_r),
        eod=equal_opportunity_difference(y_true_p, y_pred_p, y_true_r, y_pred_r),
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"disparate_impact_ratio": report.dir, "statistical_parity_difference": report.spd, "equal_opportunity_difference": report.eod}
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote: {out_path}")
