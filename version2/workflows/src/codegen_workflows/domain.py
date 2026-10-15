from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any


@dataclass(frozen=True)
class DomainAssets:
    """Generic domain assets consumed by the workflow CLI.

    A domain package can expose these assets as a dict or a small object via an
    import path such as ``my_domain:DOMAIN``.  The workflow package
    intentionally treats the fields generically; only the domain package knows
    how the input file should be interpreted.
    """

    generation_profile: Any
    helper_registry: Any
    helper_policy: str = ""
    critique_context: str = ""
    io_contract: Any = None
    default_helpers: tuple[str, ...] = ()


def import_object(spec: str) -> Any:
    """Import ``module:object`` or ``module:object.subobject``."""
    module_name, separator, object_path = spec.partition(":")
    if not module_name:
        raise ValueError("Import spec must include a module name.")
    module = import_module(module_name)
    if not separator:
        return module
    obj: Any = module
    for name in object_path.split("."):
        if not name:
            raise ValueError(f"Invalid import spec: {spec!r}")
        obj = getattr(obj, name)
    return obj


def _get(raw: Any, *names: str) -> Any:
    for name in names:
        if isinstance(raw, dict) and name in raw:
            return raw[name]
        if hasattr(raw, name):
            return getattr(raw, name)
    return None




def _tuple_from_value(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if callable(value):
        value = value()
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    try:
        return tuple(str(item) for item in value)
    except TypeError as exc:
        raise TypeError(
            "Domain default_helpers must be a string, iterable of strings, "
            "or zero-argument callable returning one of those values, "
            f"got {type(value).__name__}."
        ) from exc


def _text_from_value(value: Any) -> str:
    if value is None:
        return ""
    if callable(value):
        value = value()
    if value is None:
        return ""
    if not isinstance(value, str):
        raise TypeError(
            "Domain text assets must be strings or zero-argument callables "
            f"returning strings, got {type(value).__name__}."
        )
    return value


def load_domain_assets(spec: str) -> DomainAssets:
    """Load and normalize generic domain assets from an import spec."""
    raw = import_object(spec)
    profile = _get(raw, "generation_profile", "profile")
    registry = _get(raw, "helper_registry", "registry")
    helper_policy = _get(raw, "helper_policy", "load_helper_policy")
    critique_context = _get(raw, "critique_context", "load_critique_context")
    io_contract = _get(raw, "io_contract", "execution_contract")
    default_helpers = _get(raw, "default_helpers", "default_helper_names")

    missing = []
    if profile is None:
        missing.append("generation_profile")
    if registry is None:
        missing.append("helper_registry")
    if missing:
        raise ValueError(
            f"Domain assets {spec!r} are missing required field(s): "
            + ", ".join(missing)
        )

    return DomainAssets(
        generation_profile=profile,
        helper_registry=registry,
        helper_policy=_text_from_value(helper_policy),
        critique_context=_text_from_value(critique_context),
        io_contract=io_contract,
        default_helpers=_tuple_from_value(default_helpers),
    )
