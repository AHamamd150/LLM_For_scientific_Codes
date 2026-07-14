import io
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from codegen_workflows.cli import build_parser, _resolve_input_path, _resolve_input_paths
from codegen_workflows.domain import load_domain_assets


BASE_ARGS = [
    "generate-review",
    "--card",
    "card.txt",
    "--domain-assets",
    "dummy_domain:DOMAIN",
    "--helper-model",
    "helper-model",
    "--generator-model",
    "generator-model",
    "--tracer-model",
    "tracer-model",
    "--critique-model",
    "critique-model",
    "--run-dir",
    "run-dir",
]


class WorkflowCliTests(unittest.TestCase):
    def test_loads_generic_domain_assets(self):
        assets = load_domain_assets("dummy_domain:DOMAIN")

        self.assertEqual(assets.helper_registry[0].name, "add_numbers")
        self.assertTrue(assets.helper_policy)
        self.assertTrue(assets.critique_context)
        self.assertEqual(assets.io_contract.input_argument, "sys.argv[1:]")
        self.assertEqual(assets.default_helpers, ())

    def test_generate_review_requires_domain_assets(self):
        missing_domain = [
            item
            for item in BASE_ARGS
            if item not in ("--domain-assets", "dummy_domain:DOMAIN")
        ]

        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit):
            build_parser().parse_args(missing_domain)

    def test_generate_review_accepts_generic_input(self):
        args = build_parser().parse_args(BASE_ARGS + ["--input", "data.dat"])

        self.assertEqual(args.input_paths, [Path("data.dat")])
        self.assertEqual(_resolve_input_paths(args), (Path("data.dat"),))
        self.assertEqual(_resolve_input_path(args), Path("data.dat"))

    def test_generate_review_accepts_multiple_inputs(self):
        args = build_parser().parse_args(
            BASE_ARGS + ["--input", "a.dat", "b.dat"]
        )

        self.assertEqual(args.input_paths, [Path("a.dat"), Path("b.dat")])
        self.assertEqual(
            _resolve_input_paths(args),
            (Path("a.dat"), Path("b.dat")),
        )

    def test_generate_review_input_is_optional(self):
        args = build_parser().parse_args(BASE_ARGS)

        self.assertEqual(_resolve_input_paths(args), ())
        self.assertIsNone(_resolve_input_path(args))


if __name__ == "__main__":
    unittest.main()
