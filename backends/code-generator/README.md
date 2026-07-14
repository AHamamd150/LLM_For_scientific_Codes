# Code Generator Backend

This package provides domain-independent Python code generation:

- profile-driven message construction;
- one continuation pass for truncated code;
- model-response cleanup and Python extraction;
- independent Python syntax validation;
- execution and error-driven fixing utilities.

It does not import or contain LHCO prompts, card parsing, helper metadata, or
physics conventions. Those are supplied by `lhco-domain`.

```bash
python -m pip install -e ".[huggingface]"

code-generate generate \
  --card cases/case_001/card.txt \
  --profile lhco_domain.profile:LHCO_PROFILE \
  --model Qwen/Qwen2.5-Coder-14B-Instruct \
  --run-dir runs/case_001/generation
```
