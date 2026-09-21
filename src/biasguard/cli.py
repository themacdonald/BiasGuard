from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .audit import audit_csv, render_markdown
from .calibration import calibration_summary, load_jsonl
from .evaluation import BiasGuardEvaluator, EvaluationPolicy, build_questions, build_state
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
    _write_json(args.out, asdict(report))
    print(f"Wrote: {args.out}")


def cmd_audit(args: argparse.Namespace) -> None:
    try:
        report = audit_csv(
            args.dataset,
            y_true=args.y_true,
            y_pred=args.y_pred,
            group=args.group,
            protected=args.protected,
            reference=args.reference,
            allow_missing=args.allow_missing,
        )
    except ValueError as exc:
        raise SystemExit(f"Audit input error: {exc}") from exc

    _write_json(args.output, report)
    if args.markdown:
        out = Path(args.markdown)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["metrics"], indent=2))


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

    evaluator = BiasGuardEvaluator(client, policy=EvaluationPolicy(), model=args.model)
    payload = asdict(evaluator.evaluate(state, questions))
    _write_json(args.output, payload)
    if args.append:
        Path(args.append).parent.mkdir(parents=True, exist_ok=True)
        with Path(args.append).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    print(json.dumps(payload["result"], indent=2))


def cmd_calibrate(args: argparse.Namespace) -> None:
    summary = calibration_summary(
        load_jsonl(args.judgments),
        load_jsonl(args.labels),
    )
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

    audit = sub.add_parser(
        "audit",
        help="Run a deterministic fairness audit against a CSV dataset.",
    )
    audit.add_argument("dataset", help="Path to the CSV dataset.")
    audit.add_argument("--y-true", required=True, help="Ground-truth outcome column.")
    audit.add_argument("--y-pred", required=True, help="Model prediction column.")
    audit.add_argument("--group", required=True, help="Protected-group column.")
    audit.add_argument("--protected", required=True, help="Protected group value.")
    audit.add_argument("--reference", required=True, help="Reference group value.")
    audit.add_argument("--allow-missing", action="store_true")
    audit.add_argument("--output", default="reports/audit.json")
    audit.add_argument("--markdown", help="Optional Markdown report path.")
    audit.set_defaults(func=cmd_audit)

    evaluate = sub.add_parser("evaluate", help="Evaluate a case with structured judgments.")
    evaluate.add_argument("--input", required=True)
    evaluate.add_argument("--answers")
    evaluate.add_argument("--base-url", default="https://api.typesafe.ai")
    evaluate.add_argument("--model", default="jev-latest")
    evaluate.add_argument("--output", default="reports/judgment.json")
    evaluate.add_argument("--append")
    evaluate.set_defaults(func=cmd_evaluate)

    calibrate = sub.add_parser("calibrate", help="Calibrate recorded judgments.")
    calibrate.add_argument("--judgments", required=True)
    calibrate.add_argument("--labels", required=True)
    calibrate.add_argument("--output", default="reports/calibration.json")
    calibrate.set_defaults(func=cmd_calibrate)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)
