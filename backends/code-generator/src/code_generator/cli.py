from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path

from .generator import CodeGenerator, GenerationProfile
from .models import GenerationRequest
from .providers.huggingface import HuggingFaceCodeProvider


def load_profile(reference: str) -> GenerationProfile:
    module_name, separator, attribute = reference.partition(":")
    if not separator or not module_name or not attribute:
        raise ValueError("Profile reference must use MODULE:ATTRIBUTE syntax.")
    module = importlib.import_module(module_name)
    return getattr(module, attribute)


def _generate(args: argparse.Namespace) -> None:
    args.run_dir.mkdir(parents=True, exist_ok=True)
    card_text = args.card.read_text(encoding="utf-8")
    generator = CodeGenerator(
        HuggingFaceCodeProvider(
            args.model,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        ),
        load_profile(args.profile),
    )
    result = generator.generate(GenerationRequest(card_text=card_text))
    (args.run_dir / "request.json").write_text(
        json.dumps(
            {
                "card": str(args.card),
                "profile": args.profile,
                "model": args.model,
                "max_tokens": args.max_tokens,
                "temperature": args.temperature,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    for index, response in enumerate(result.raw_responses, start=1):
        (args.run_dir / f"response_{index:03d}.txt").write_text(
            response.rstrip() + "\n",
            encoding="utf-8",
        )
    source_dir = args.run_dir / "src"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "analysis.py").write_text(
        result.code.rstrip() + "\n",
        encoding="utf-8",
    )
    (args.run_dir / "result.json").write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="code-generate")
    subparsers = parser.add_subparsers(required=True)
    generate = subparsers.add_parser("generate")
    generate.add_argument("--card", required=True, type=Path)
    generate.add_argument(
        "--profile",
        required=True,
        help="Generation profile as MODULE:ATTRIBUTE.",
    )
    generate.add_argument("--model", required=True)
    generate.add_argument("--max-tokens", type=int, default=4096)
    generate.add_argument("--temperature", type=float, default=0.0)
    generate.add_argument("--run-dir", required=True, type=Path)
    generate.set_defaults(handler=_generate)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
