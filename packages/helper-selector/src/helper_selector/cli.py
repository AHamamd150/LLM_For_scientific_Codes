from __future__ import annotations

import argparse
import json
from pathlib import Path

from .cards import update_card_with_helpers
from .io import read_selection, write_selection, write_summary
from .providers.huggingface import HuggingFaceChatProvider
from .registry import load_registry_json, load_registry_module
from .selection import select_helpers


def _registry(args: argparse.Namespace):
    if args.registry_json:
        return load_registry_json(args.registry_json)
    return load_registry_module(args.registry_module)


def _select(args: argparse.Namespace) -> None:
    run_dir: Path = args.run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    spec_text = args.spec.read_text(encoding="utf-8")
    registry = _registry(args)
    policy = args.policy.read_text(encoding="utf-8") if args.policy else ""
    provider = HuggingFaceChatProvider(
        args.model,
        token=args.hf_token,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    )
    result, raw_response = select_helpers(
        spec_text, registry, provider, policy=policy
    )
    request = {
        "spec": str(args.spec),
        "model": args.model,
        "registry": args.registry_module or str(args.registry_json),
        "policy": str(args.policy) if args.policy else None,
    }
    (run_dir / "request.json").write_text(
        json.dumps(request, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (run_dir / "raw_response.txt").write_text(raw_response + "\n", encoding="utf-8")
    write_selection(result, run_dir / "selection.json")
    write_summary(result, run_dir / "summary.txt")


def _update_card(args: argparse.Namespace) -> None:
    card = args.card.read_text(encoding="utf-8")
    selection = read_selection(args.selection)
    revised = update_card_with_helpers(
        card,
        selection,
        default_helpers=tuple(args.default_helper),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(revised, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="helper-selector")
    subparsers = parser.add_subparsers(required=True)

    select_parser = subparsers.add_parser("select")
    select_parser.add_argument("--spec", required=True, type=Path)
    registry_group = select_parser.add_mutually_exclusive_group(required=True)
    registry_group.add_argument("--registry-json", type=Path)
    registry_group.add_argument("--registry-module")
    select_parser.add_argument("--policy", type=Path)
    select_parser.add_argument("--model", required=True)
    select_parser.add_argument("--hf-token")
    select_parser.add_argument("--max-tokens", type=int, default=1200)
    select_parser.add_argument("--temperature", type=float, default=0.0)
    select_parser.add_argument("--run-dir", required=True, type=Path)
    select_parser.set_defaults(handler=_select)

    card_parser = subparsers.add_parser("update-card")
    card_parser.add_argument("--card", required=True, type=Path)
    card_parser.add_argument("--selection", required=True, type=Path)
    card_parser.add_argument("--output", required=True, type=Path)
    card_parser.add_argument(
        "--default-helper",
        action="append",
        default=[],
    )
    card_parser.set_defaults(handler=_update_card)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()

