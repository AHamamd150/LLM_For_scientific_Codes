from __future__ import annotations

import argparse
from pathlib import Path

from code_generator import CodeGenerator
from code_generator.providers.huggingface import HuggingFaceCodeProvider
from critique_pipeline.providers.huggingface import HuggingFaceRouterProvider
from helper_selector.providers.huggingface import (
    HuggingFaceChatProvider as HelperProvider,
)

from .domain import load_domain_assets
from .pipeline import ResearchCodeWorkflow


def _resolve_input_paths(args: argparse.Namespace) -> tuple[Path, ...]:
    paths = getattr(args, "input_paths", None)
    if not paths:
        return ()
    return tuple(paths)


def _resolve_input_path(args: argparse.Namespace) -> Path | None:
    """Backward-compatible helper for callers that still expect one input."""
    paths = _resolve_input_paths(args)
    return paths[0] if paths else None


def _read_optional_text(path: Path | None) -> str | None:
    if path is None:
        return None
    return path.read_text(encoding="utf-8")


def _generate_review(args: argparse.Namespace) -> None:
    input_paths = _resolve_input_paths(args)
    domain_assets = load_domain_assets(args.domain_assets)
    workflow = ResearchCodeWorkflow(domain_assets.helper_registry)
    helper_policy = (
        _read_optional_text(args.helper_policy)
        if args.helper_policy
        else domain_assets.helper_policy
    )
    critique_context = (
        _read_optional_text(args.critique_context)
        if args.critique_context
        else domain_assets.critique_context
    )
    generator_provider = HuggingFaceCodeProvider(
        args.generator_model,
        max_tokens=args.generator_max_tokens,
        temperature=args.generator_temperature,
    )
    fixer_provider = None
    if input_paths and args.max_retries > 0:
        fixer_provider = HuggingFaceCodeProvider(
            args.fixer_model or args.generator_model
        )
    workflow.generate_and_review(
        accepted_card_text=args.card.read_text(encoding="utf-8"),
        helper_provider=HelperProvider(
            args.helper_model,
            max_tokens=args.helper_max_tokens,
        ),
        generator=CodeGenerator(
            generator_provider,
            domain_assets.generation_profile,
        ),
        tracer_provider=HuggingFaceRouterProvider(args.tracer_model),
        critique_provider=HuggingFaceRouterProvider(args.critique_model),
        run_root=args.run_dir,
        helper_policy=helper_policy,
        critique_context=critique_context or "",
        default_helpers=domain_assets.default_helpers,
        critique_runs=args.critique_runs,
        input_paths=input_paths,
        fixer_provider=fixer_provider,
        max_retries=args.max_retries,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentic-code-workbench")
    commands = parser.add_subparsers(required=True)

    generate = commands.add_parser("generate-review")
    generate.add_argument("--card", required=True, type=Path)
    generate.add_argument(
        "--domain-assets",
        required=True,
        help=(
            "Import path for generic domain assets, for example "
            "'my_domain:DOMAIN'. The loaded object must provide "
            "generation_profile and helper_registry, and may provide "
            "helper_policy and critique_context text or loaders."
        ),
    )
    generate.add_argument("--helper-policy", type=Path)
    generate.add_argument("--critique-context", type=Path)
    generate.add_argument("--helper-model", required=True)
    generate.add_argument("--helper-max-tokens", type=int, default=1200)
    generate.add_argument("--generator-model", required=True)
    generate.add_argument("--generator-max-tokens", type=int, default=4096)
    generate.add_argument("--generator-temperature", type=float, default=0.0)
    generate.add_argument("--tracer-model", required=True)
    generate.add_argument("--critique-model", required=True)
    generate.add_argument("--critique-runs", type=int, default=1)
    generate.add_argument(
        "--input",
        dest="input_paths",
        type=Path,
        nargs="+",
        help=(
            "Optional input file path(s) passed to the generated script as "
            "command-line arguments after the script name. The selected "
            "domain profile defines how the generated script should "
            "interpret these files, typically via sys.argv[1:]."
        ),
    )
    generate.add_argument("--fixer-model")
    generate.add_argument(
        "--max-retries",
        "--max-fix-attempts",
        dest="max_retries",
        type=int,
        default=3,
        help=(
            "Number of fix-then-regenerate trials after execution failure."
        ),
    )
    generate.add_argument("--run-dir", required=True, type=Path)
    generate.set_defaults(handler=_generate_review)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
