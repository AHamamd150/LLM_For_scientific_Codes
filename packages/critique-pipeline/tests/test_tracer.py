import unittest

from critique_pipeline.tracer import (
    extract_filtered_objects_from_trace,
    keep_only_last_definition_summary,
    merge_with_overlap,
    safe_template_expand,
)


class TracerTests(unittest.TestCase):
    def test_template_preserves_python_braces(self):
        rendered = safe_template_expand(
            "SPEC={spec}\nCODE={code}",
            {"spec": "x", "code": "value = {'key': 1}"},
        )
        self.assertIn("value = {'key': 1}", rendered)

    def test_continuation_overlap_is_removed(self):
        merged = merge_with_overlap("one\ntwo\nthree", "two\nthree\nfour")
        self.assertEqual(merged, "one\ntwo\nthree\nfour")

    def test_keeps_last_definition_summary_and_spec_bullets(self):
        text = (
            "✅ * item; computed as: x; 〔L1〕\n"
            "* [CHECK CAREFULLY] DEFINITION SUMMARY\nold\n"
            "* [CHECK CAREFULLY] DEFINITION SUMMARY\nnew"
        )
        result = keep_only_last_definition_summary(text)
        self.assertIn("✅ * item", result)
        self.assertNotIn("\nold\n", result)
        self.assertIn("\nnew", result)

    def test_extracts_backtick_wrapped_collection(self):
        text = """* [CHECK CAREFULLY] DEFINITION SUMMARY

* mass
  - computed/defined as: candidate['mass']
  - upstream chain: candidate
  - collection definition: `selected = [x for x in objects if x['pt'] > 20]`
  - structure: single-constituent
"""
        collections = extract_filtered_objects_from_trace(text)
        self.assertEqual(
            collections["selected"]["definition"],
            "[x for x in objects if x['pt'] > 20]",
        )


if __name__ == "__main__":
    unittest.main()
