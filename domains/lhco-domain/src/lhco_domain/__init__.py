from .profile import (
    LHCO_PROFILE,
    LHCOGenerationProfile,
    load_codegen_system_prompt,
    load_critique_context,
    load_helper_policy,
    load_oracle_context,
    load_oraclet_domain_prompt,
)
from .registry import HELPER_REGISTRY

__all__ = [
    "HELPER_REGISTRY",
    "LHCO_PROFILE",
    "LHCOGenerationProfile",
    "load_codegen_system_prompt",
    "load_critique_context",
    "load_helper_policy",
    "load_oracle_context",
    "load_oraclet_domain_prompt",
    "DEFAULT_HELPERS",
    "DOMAIN_ASSETS",
    "DOMAIN",
]


DEFAULT_HELPERS = ("read_lhco",)


DOMAIN_ASSETS = {
    "generation_profile": LHCO_PROFILE,
    "helper_registry": HELPER_REGISTRY,
    "load_helper_policy": load_helper_policy,
    "load_critique_context": load_critique_context,
    "default_helpers": DEFAULT_HELPERS,
}

# Shorter alias for command-line use, e.g. ``--domain-assets my_domain:DOMAIN``.
DOMAIN = DOMAIN_ASSETS
