from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import OracleRequest
from .oracle import run_oracle
from .profiles import DEFAULT_PROFILE, PROFILE_FILES, load_system_prompt
from .prompt import build_user_message
from .providers.huggingface import HuggingFaceChatProvider
from .registry import load_registry_json, load_registry_module


def _registry_text(args: argparse.Namespace) -> str:
    if args.registry_json:
        return load_registry_json(args.registry_json)
    if args.registry_module:
        return load_registry_module(args.registry_module)
    return ""


def _run(args: argparse.Namespace) -> None:
    args.run_dir.mkdir(parents=True, exist_ok=True)
    request = OracleRequest(
        card_text=args.card.read_text(encoding="utf-8"),
        registry_text=_registry_text(args),
        codegen_system_prompt=(
            args.codegen_system_prompt.read_text(encoding="utf-8")
            if args.codegen_system_prompt
            else ""
        ),
        profile=args.profile,
    )
    oracle_context = (
        args.oracle_context.read_text(encoding="utf-8")
        if args.oracle_context
        else ""
    )
    system_prompt = load_system_prompt(
        args.profile,
        args.system_prompt,
        context=oracle_context,
        output_contract=args.oracle_output_contract,
    )
    user_message = build_user_message(
        request.card_text,
        registry_text=request.registry_text,
        codegen_system_prompt=request.codegen_system_prompt,
    )
    manifest = {
        **request.to_manifest(),
        "card": str(args.card),
        "registry": args.registry_module
        or (str(args.registry_json) if args.registry_json else None),
        "codegen_system_prompt": (
            str(args.codegen_system_prompt) if args.codegen_system_prompt else None
        ),
        "model": args.model,
        "system_prompt": (
            str(args.system_prompt)
            if args.system_prompt
            else f"bundled {args.profile}"
        ),
        "oracle_context": str(args.oracle_context) if args.oracle_context else None,
        "oracle_output_contract": args.oracle_output_contract,
        "runs": args.runs,
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
    }
    (args.run_dir / "request.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (args.run_dir / "user_message.txt").write_text(
        user_message + "\n",
        encoding="utf-8",
    )

    provider = HuggingFaceChatProvider(
        args.model,
        token=args.hf_token,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    )
    for index in range(1, args.runs + 1):
        response = run_oracle(
            request,
            provider,
            system_prompt=system_prompt,
        )
        (args.run_dir / f"response_{index:03d}.txt").write_text(
            response.text.rstrip() + "\n",
            encoding="utf-8",
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="golden-axe")
    subparsers = parser.add_subparsers(required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--card", required=True, type=Path)
    registry = run_parser.add_mutually_exclusive_group()
    registry.add_argument("--registry-json", type=Path)
    registry.add_argument("--registry-module")
    run_parser.add_argument("--codegen-system-prompt", type=Path)
    run_parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_FILES),
        default=DEFAULT_PROFILE,
    )
    run_parser.add_argument("--system-prompt", type=Path)
    run_parser.add_argument("--oracle-context", type=Path)
    run_parser.add_argument(
        "--oracle-output-contract",
        choices=("auto", "system", "domain", "none"),
        default="auto",
        help=(
            "Choose the output-format contract for split Oracle prompts. "
            "auto uses the profile default; system appends the shared "
            "system output contract; domain expects the domain prompt to "
            "define output; none appends no output contract."
        ),
    )
    run_parser.add_argument("--model", required=True)
    run_parser.add_argument("--hf-token")
    run_parser.add_argument("--max-tokens", type=int, default=1800)
    run_parser.add_argument("--temperature", type=float, default=0.2)
    run_parser.add_argument("--runs", type=int, default=1)
    run_parser.add_argument("--run-dir", required=True, type=Path)
    run_parser.set_defaults(handler=_run)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
