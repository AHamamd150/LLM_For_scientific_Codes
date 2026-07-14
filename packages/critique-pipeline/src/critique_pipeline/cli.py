from __future__ import annotations

import argparse
import json
from pathlib import Path

from .providers.huggingface import HuggingFaceRouterProvider
from .workflow import run_critique_stage, run_tracer_stage


def _run(args: argparse.Namespace) -> None:
    spec_text = args.card.read_text(encoding="utf-8")
    code_text = args.code.read_text(encoding="utf-8")
    domain_context = (
        args.domain_context.read_text(encoding="utf-8")
        if args.domain_context
        else ""
    )
    args.run_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "card": str(args.card),
        "code": str(args.code),
        "tracer_model": args.tracer_model,
        "critique_model": args.critique_model,
        "n_runs": args.n_runs,
    }
    (args.run_dir / "request.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    tracer_text = run_tracer_stage(
        spec_text=spec_text,
        code_text=code_text,
        provider=HuggingFaceRouterProvider(args.tracer_model),
        output_dir=args.run_dir / "tracer",
        max_rounds=args.max_rounds,
        max_tokens_per_round=args.tracer_max_tokens,
    )
    run_critique_stage(
        spec_text=spec_text,
        code_text=code_text,
        tracer_text=tracer_text,
        provider=HuggingFaceRouterProvider(args.critique_model),
        output_dir=args.run_dir / "critique",
        domain_context=domain_context,
        n_runs=args.n_runs,
        max_tokens=args.critique_max_tokens,
        enable_repair=not args.no_repair,
        drop_signals_path=args.drop_signals,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="critique-pipeline")
    subparsers = parser.add_subparsers(required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--card", required=True, type=Path)
    run_parser.add_argument("--code", required=True, type=Path)
    run_parser.add_argument("--tracer-model", required=True)
    run_parser.add_argument("--critique-model", required=True)
    run_parser.add_argument("--domain-context", type=Path)
    run_parser.add_argument("--n-runs", type=int, default=1)
    run_parser.add_argument("--max-rounds", type=int, default=8)
    run_parser.add_argument("--tracer-max-tokens", type=int, default=2500)
    run_parser.add_argument("--critique-max-tokens", type=int, default=8000)
    run_parser.add_argument("--drop-signals", type=Path)
    run_parser.add_argument("--no-repair", action="store_true")
    run_parser.add_argument("--run-dir", required=True, type=Path)
    run_parser.set_defaults(handler=_run)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
