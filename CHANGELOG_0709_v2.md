# 0709 v2 changes

Focused change: move domain-specific default helpers out of the generic helper-selector/workflow layer.

## Changed

- `helper_selector.cards.update_card_with_helpers()` now defaults to `default_helpers=()` instead of `("read_lhco",)`.
- The standalone `helper-selector update-card` CLI no longer injects `read_lhco` by default; callers may still pass `--default-helper read_lhco` explicitly.
- `DomainAssets` now includes `default_helpers`, also loaded from `default_helper_names` for compatibility.
- The workflow CLI passes `domain_assets.default_helpers` through `generate_and_review()` into `update_card_with_helpers()`.
- `lhco_domain:DOMAIN` now declares `default_helpers=("read_lhco",)`.
- `dummy_domain:DOMAIN` declares an empty default helper tuple.

## Not changed

- Helper selector prompt behavior from `0709_v1`.
- Code generation profile text.
- Tracer / critique prompts or domain critique rules.
- I/O contract behavior.
