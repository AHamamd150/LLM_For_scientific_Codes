# Dummy Domain

This deliberately small non-collider domain verifies that the generic
components do not depend on LHCO.

It provides a generation profile, helper registry, helper policy, Oracle
context, Critique context, and a typed generated-script I/O contract.  The
root integration test composes these assets with Golden Axe, Helper Selector,
Code Generator, workflow orchestration, execution, tracer, and Critique.

This package is a test fixture, not a user-facing analysis domain.

## Generated script I/O contract

The dummy domain is also the minimal example for how a new domain should define
the connection between an input file and generated code.  The contract is
exposed as `dummy_domain.DUMMY_IO_CONTRACT` and included in
`dummy_domain:DOMAIN` as `io_contract`.

```text
Input argument:
  sys.argv[1:]

Input format:
  UTF-8 text file containing one number per non-empty line.

Output location:
  The current working directory. The workflow sets this to RUN_DIR/execution.

Standard output:
  Print a concise count/sum summary. The workflow stores this as
  execution/stdout.txt.

Required output file:
  result.txt containing the numeric sum followed by a newline.
```

A corresponding example is provided in `examples/dummy_cases/`:

```text
examples/dummy_cases/numbers.txt
examples/dummy_cases/sum_numbers_card.txt
```

The important point for new domains is that the workflow always knows only the
execution-level contract.  The domain tells the model how to interpret
`sys.argv[1:]`, what kind of file it is, and what files the generated script
should write.
