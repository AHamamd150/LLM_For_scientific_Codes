"""Selected-object-safe LHCO helper registry.

The legacy registry is preserved in ``registry_legacy.py``.  This safe view keeps
low-level object access and composable helper functions, but hides higher-level
helpers that take an entire event, internally re-extract objects, or perform
analysis-level candidate finding.  Those
legacy helpers are convenient, but they can bypass explicitly selected electron,
muon, lepton, jet, or photon collections in generated analyses.
"""

from __future__ import annotations

from .registry_legacy import HELPER_REGISTRY as LEGACY_HELPER_REGISTRY


# Helpers removed from the default registry because they operate on an entire
# event and rebuild physics objects internally.  Generated code should instead
# compose lower-level helpers using explicitly selected objects/collections.
UNSAFE_SELECTED_OBJECT_HELPERS: tuple[str, ...] = (
    "compute_ht",
    "helper_delta_phi_ll",
    "helper_delta_phi_l_twojet",
    "helper_delta_eta_ll",
    "helper_delta_r_ll",
    "dilepton_mass",
    "dijet_mass",
    "dielectron_mass",
    "dimuon_mass",
    "four_lepton_mass",
    "visible_mass",
    "mt_lepton_met",
    "met_over_sqrt_ht",
    "met_over_ht",
    "find_z_candidate",
    "find_w_candidate_leptonic",
    "find_higgs_candidate_4l",
    "find_higgs_candidate_2b",
    "find_higgs_candidate_gammagamma",
    "find_ditau_os_pair",
    "find_ditau_ss_pair",
)


HELPER_REGISTRY = [
    spec
    for spec in LEGACY_HELPER_REGISTRY
    if spec.name not in UNSAFE_SELECTED_OBJECT_HELPERS
]
