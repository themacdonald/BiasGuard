from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .calibration import calibration_summary, load_jsonl
from .evaluation import (
    BiasGuardEvaluator,
    EvaluationPolicy,
    build_questions,
    build_state,
)
from .metrics import (
    FairnessReport,
    disparate_impact_ratio,
    equal_opportunity_difference,
    statistical_parity_difference,
)
from .typesafe_adapter import OfflineAnswersClient
from .typesafe_http import TypeSafeHTTPClient


def _load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str, payload: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def cmd_demo(args: argparse.Namespace) -> None:
    y_true_p = [1, 1, 0, 0, 1]
    y_pred_p = [1, 0, 0, 0, 1]
    y_true_r = [1, 1, 0, 0, 1]
    y_pred_r = [1, 1, 0, 0, 1]
    report = FairnessReport(
        dir=disparate_impact_ratio(y_pred_p, y_pred_r),
        spd=statistical_parity_difference(y_pred_p, y_pred_r),
        eod=equal_opportunity_difference(y_true_p, y_pred_p, y_true_r, y_pred_r),
    )
    _write_json(args.out, {
        "disparate_impact_ratio": report.dir,
        "statistical_parity_difference": report.spd,
        "equal_opportunity_difference": report.eod,
    })
    print(f"Wrote: {args.out}")


def cmd_evaluate(args: argparse.Namespace) -> None:
    case = _load_json(args.input)
    groups = case.get("protected_groups", [])
    flags = list((case.get("biasguard_flags") or {}).keys())
    state = build_state(
        case.get("decision"),
        biasguard_flags=case.get("biasguard_flags"),
        policy=case.get("policy"),
        mitigations=case.get("mitigations"),
        context=case.get("context"),
    )
    questions = build_questions(groups, flags)
    if args.answers:
        answers = _load_json(args.answers)
        client = OfflineAnswersClient(answers.get("answers", answers))
    else:
        client = TypeSafeHTTPClient(model=args.model, base_url=args.base_url)

    evaluator = BiasGuardEvaluator(
        client,
        policy=EvaluationPolicy(),
        model=args.model,
    )
    record = evaluator.evaluate(state, questions)
    payload = asdict(record)
    _write_json(args.output, payload)
    if args.append:
        Path(args.append).parent.mkdir(parents=True, exist_ok=True)
        with Path(args.append).open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    print(json.dumps(payload["result"], indent=2))


def cmd_calibrate(args: argparse.Namespace) -> None:
    judgments = load_jsonl(args.judgments)
    labels = load_jsonl(args.labels)
    summary = calibration_summary(judgments, labels)
    _write_json(args.output, summary)
    print(f"Wrote: {args.output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="biasguard",
        description="BiasGuard evaluation and governance CLI.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="Run the deterministic fairness demo.")
    demo.add_argument("--out", default="reports/report.json")
    demo.set_defaults(func=cmd_demo)

    evaluate = sub.add_parser(
        "evaluate",
        help="Evaluate a case using recorded structured answers.",
    )
    evaluate.add_argument("--input", required=True, help="Case JSON.")
    evaluate.add_argument(
        "--answers",
        help="Optional recorded answers JSON. If omitted, call TypeSafe System One.",
    )
    evaluate.add_argument(
        "--base-url",
        default="https://api.typesafe.ai",
        help="TypeSafe API base URL.",
    )
    evaluate.add_argument(
        "--model", default="jev-latest",
        help="Evaluator/model identifier recorded in the audit record.",
    )
    evaluate.add_argument(
        "--output", default="reports/judgment.json",
        help="JSON audit record output.",
    )
    evaluate.add_argument(
        "--append",
        help="Optional JSONL path for calibration data collection.",
    )
    evaluate.set_defaults(func=cmd_evaluate)

    calibrate = sub.add_parser(
        "calibrate",
        help="Calibrate recorded judgments against adjudicated labels.",
    )
    calibrate.add_argument("--judgments", required=True, help="Judgment JSONL.")
    calibrate.add_argument("--labels", required=True, help="Adjudicated label JSONL.")
    calibrate.add_argument(
        "--output", default="reports/calibration.json",
        help="Calibration report output.",
    )
    calibrate.set_defaults(func=cmd_calibrate)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
