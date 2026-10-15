import unittest

from critique_pipeline.critique import (
    append_non_overlapping_findings,
    filter_findings,
    needs_critique_repair,
)
from critique_pipeline.workflow import build_critique_messages


class CritiqueTests(unittest.TestCase):
    def test_incomplete_output_requests_repair(self):
        self.assertTrue(needs_critique_repair("⚠️ mismatch"))

    def test_appends_non_overlapping_repair(self):
        result = append_non_overlapping_findings("first", "second")
        self.assertIn("first", result)
        self.assertIn("second", result)

    def test_filter_keeps_raw_candidate_and_drops_noise(self):
        text = (
            "⚠️ mismatch\nReason:\nreal issue\n\n"
            "🌟 extra behavior\nReason:\nmatches the spec"
        )
        kept, dropped = filter_findings(text, ["matches the spec"])
        self.assertEqual(len(kept), 1)
        self.assertEqual(len(dropped), 1)

    def test_domain_context_is_injected_by_caller(self):
        messages = build_critique_messages(
            spec_text="spec",
            tracer_text="trace",
            domain_context="Domain context: test domain.",
        )
        self.assertIn(
            "Domain context: test domain.",
            messages[0]["content"],
        )


if __name__ == "__main__":
    unittest.main()
