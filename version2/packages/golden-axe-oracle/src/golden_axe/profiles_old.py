from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Literal


OutputContractMode = Literal["auto", "system", "domain", "none"]
ResolvedOutputContractMode = Literal["system", "domain", "none"]

DEFAULT_PROFILE = "oracle"
CONTEXT_PLACEHOLDER = "{{DOMAIN_CONTEXT}}"


@dataclass(frozen=True)
class OracleProfileSpec:
    """Bundled Golden Axe prompt profile.

    Profiles describe how a prompt is assembled.

    - split profiles use a bundled system front, a domain prompt supplied via
      context, and optionally a bundled system output contract;
    - monolithic profiles use a bundled complete prompt file;
    - domain-complete profiles use a complete prompt supplied by the domain via
      context.  These profiles must not receive a system output contract.
    """

    name: str
    prompt_file: str | None = None
    front_file: str | None = None
    system_output_file: str | None = None
    default_output_contract: ResolvedOutputContractMode = "system"
    requires_context: bool = False
    context_is_complete_prompt: bool = False
    alias_of: str | None = None


PROFILE_SPECS: dict[str, OracleProfileSpec] = {
    # Release/default name. This is the former oracle-split-v3 prompt rendered
    # from generic system front matter, a domain prompt/context, and the shared
    # system-owned output contract.
    "oracle": OracleProfileSpec(
        name="oracle",
        front_file="oracle_front.txt",
        system_output_file="oracle_output_contract.txt",
        default_output_contract="system",
    ),
    # Backward-compatible development alias for the release oracle. This alias
    # does not require a separate bundled prompt file.
    "oracle-split-v3": OracleProfileSpec(
        name="oracle-split-v3",
        alias_of="oracle",
    ),
    # Pre-package monolithic Golden Axe prompt. "Lite" means legacy single-file
    # prompt, not a smaller model profile.
    "oracle-lite": OracleProfileSpec(
        name="oracle-lite",
        prompt_file="oracle_lite.txt",
        default_output_contract="domain",
    ),
    "oracle-lite-v2": OracleProfileSpec(
        name="oracle-lite-v2",
        prompt_file="oracle_lite_v2.txt",
        default_output_contract="domain",
    ),
    "oracle-lite-v3": OracleProfileSpec(
        name="oracle-lite-v3",
        prompt_file="oracle_lite_v3.txt",
        default_output_contract="domain",
    ),
    "oracle-lite-v4": OracleProfileSpec(
        name="oracle-lite-v4",
        prompt_file="oracle_lite_v4.txt",
        default_output_contract="domain",
    ),
    "oracle-lite-v5": OracleProfileSpec(
        name="oracle-lite-v5",
        prompt_file="oracle_lite_v5.txt",
        default_output_contract="domain",
    ),

    # OracleT is domain-complete: the selected domain supplies the full prompt,
    # including domain categories and output-format rules.  The system package
    # must not add front matter or a separate output contract.
    "oraclet": OracleProfileSpec(
        name="oraclet",
        default_output_contract="domain",
        requires_context=True,
        context_is_complete_prompt=True,
    ),
}

# Compatibility export used by existing CLI/tests.  Values are descriptive; use
# PROFILE_SPECS for rendering behavior.
PROFILE_FILES = {
    name: spec.prompt_file or spec.front_file or spec.alias_of or "<domain-complete>"
    for name, spec in PROFILE_SPECS.items()
}


def _profile_dir():
    return files("golden_axe").joinpath("profiles")


def _read_profile_file(filename: str) -> str:
    return _profile_dir().joinpath(filename).read_text(encoding="utf-8")


def _resolve_spec(profile: str) -> OracleProfileSpec:
    try:
        spec = PROFILE_SPECS[profile]
    except KeyError as exc:
        raise ValueError(
            f"Unknown profile {profile!r}; choose from {sorted(PROFILE_SPECS)}"
        ) from exc
    if spec.alias_of is not None:
        return _resolve_spec(spec.alias_of)
    return spec


def _resolve_output_contract(
    spec: OracleProfileSpec,
    output_contract: OutputContractMode,
) -> ResolvedOutputContractMode:
    if output_contract == "auto":
        return spec.default_output_contract
    if output_contract not in {"system", "domain", "none"}:
        raise ValueError(
            "output_contract must be one of 'auto', 'system', 'domain', or 'none'"
        )
    return output_contract


def _inject_context(prompt: str, context: str) -> str:
    if CONTEXT_PLACEHOLDER in prompt:
        return prompt.replace(
            CONTEXT_PLACEHOLDER,
            context.strip() or "(No domain context supplied.)",
        )
    if context:
        return prompt + "\n\nDOMAIN_CONTEXT:\n" + context
    return prompt


def _render_split_prompt(
    spec: OracleProfileSpec,
    *,
    context: str,
    output_contract: ResolvedOutputContractMode,
) -> str:
    if spec.front_file is None:
        raise ValueError(f"Profile {spec.name!r} is not a split prompt profile")

    parts = [_inject_context(_read_profile_file(spec.front_file), context).rstrip()]

    if output_contract == "system":
        if spec.system_output_file is None:
            raise ValueError(
                f"Profile {spec.name!r} has no system output contract file"
            )
        parts.append(_read_profile_file(spec.system_output_file).rstrip())
    elif output_contract in {"domain", "none"}:
        # Domain-owned output rules are assumed to be present in the supplied
        # domain prompt.  'none' intentionally leaves output rules absent.
        pass
    else:  # pragma: no cover - guarded by _resolve_output_contract
        raise ValueError(f"Unknown output contract mode: {output_contract!r}")

    return "\n\n".join(part for part in parts if part).rstrip() + "\n"


def load_system_prompt(
    profile: str = DEFAULT_PROFILE,
    path: Path | None = None,
    *,
    context: str = "",
    output_contract: OutputContractMode = "auto",
) -> str:
    """Load and render a Golden Axe system prompt.

    output_contract controls whether split profiles append the shared system
    output format contract or rely on the domain prompt to define output:

    - auto: use the profile default
    - system: append the profile's shared system output contract
    - domain: do not append system output; domain prompt owns output rules
    - none: do not append any output contract
    """

    if path is not None:
        # A local prompt is treated as an already complete prompt.  This keeps
        # previous --system-prompt behavior unchanged.
        return _inject_context(path.read_text(encoding="utf-8"), context)

    spec = _resolve_spec(profile)
    mode = _resolve_output_contract(spec, output_contract)

    if spec.requires_context and not context.strip():
        raise ValueError(
            f"Profile {profile!r} requires a domain prompt/context via --oracle-context"
        )

    if spec.context_is_complete_prompt:
        if mode == "system":
            raise ValueError(
                f"Profile {profile!r} is a complete/domain-owned prompt and cannot "
                "receive a separate system output contract"
            )
        return context.rstrip() + "\n"

    if spec.front_file is not None:
        return _render_split_prompt(spec, context=context, output_contract=mode)

    if spec.prompt_file is None:  # pragma: no cover - invalid profile spec
        raise ValueError(f"Profile {profile!r} has no prompt file")

    prompt = _read_profile_file(spec.prompt_file)
    if output_contract == "system":
        raise ValueError(
            f"Profile {profile!r} is a complete/domain-owned prompt and cannot "
            "receive a separate system output contract"
        )
    return _inject_context(prompt, context)
