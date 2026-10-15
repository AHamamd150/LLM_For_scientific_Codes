from .contracts import DUMMY_IO_CONTRACT
from .profile import (
    DUMMY_PROFILE,
    DummyGenerationProfile,
    load_codegen_system_prompt,
    load_critique_context,
    load_helper_policy,
    load_oracle_context,
)
from .registry import HELPER_REGISTRY

__all__ = [
    "DUMMY_PROFILE",
    "DummyGenerationProfile",
    "HELPER_REGISTRY",
    "load_codegen_system_prompt",
    "load_critique_context",
    "load_helper_policy",
    "load_oracle_context",
    "DOMAIN_ASSETS",
    "DOMAIN",
    "DUMMY_IO_CONTRACT",
    "DEFAULT_HELPERS",
]


DEFAULT_HELPERS = ()


DOMAIN_ASSETS = {
    "generation_profile": DUMMY_PROFILE,
    "helper_registry": HELPER_REGISTRY,
    "load_helper_policy": load_helper_policy,
    "load_critique_context": load_critique_context,
    "io_contract": DUMMY_IO_CONTRACT,
    "default_helpers": DEFAULT_HELPERS,
}

# Shorter alias for command-line use, e.g. ``--domain-assets my_domain:DOMAIN``.
DOMAIN = DOMAIN_ASSETS
