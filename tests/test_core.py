import unittest

from mini_newline_preservation_unifier import (
    LineEndingRecord,
    NewlineStyle,
    UnifyResult,
    detect_newline_style,
    unify_newlines,
)


class DetectNewlineStyleTests(unittest.TestCase):
    def test_empty_string_defaults_to_lf(self):
        self.assertIs(detect_newline_style(""), NewlineStyle.LF)

    def test_no_line_endings_defaults_to_lf(self):
        self.assertIs(detect_newline_style("abc"), NewlineStyle.LF)

    def test_pure_lf(self):
        self.assertIs(detect_newline_style("a\nb\n"), NewlineStyle.LF)

    def test_pure_cr(self):
        self.assertIs(detect_newline_style("a\rb\r"), NewlineStyle.CR)

    def test_pure_crlf(self):
        self.assertIs(detect_newline_style("a\r\nb\r\n"), NewlineStyle.CRLF)

    def test_mixed(self):
        self.assertIs(detect_newline_style("a\r\nb\nc\rd"), NewlineStyle.MIXED)

    def test_crlf_is_not_two_endings(self):
        # A CRLF document must not be reported as MIXED just because it
        # contains both a CR and an LF byte.
        self.assertIs(detect_newline_style("a\r\nb\r\n"), NewlineStyle.CRLF)


class UnifyNewlinesTests(unittest.TestCase):
    def test_explicit_lf_from_crlf(self):
        result = unify_newlines("a\r\nb\r\n", NewlineStyle.LF)
        self.assertIsInstance(result, UnifyResult)
        self.assertEqual(result.text, "a\nb\n")
        self.assertIs(result.target_style, NewlineStyle.LF)

    def test_explicit_crlf_from_lf(self):
        result = unify_newlines("a\nb\n", NewlineStyle.CRLF)
        self.assertEqual(result.text, "a\r\nb\r\n")
        self.assertIs(result.target_style, NewlineStyle.CRLF)

    def test_explicit_cr_from_lf(self):
        result = unify_newlines("a\nb\n", NewlineStyle.CR)
        self.assertEqual(result.text, "a\rb\r")
        self.assertIs(result.target_style, NewlineStyle.CR)

    def test_mixed_document_inferred_to_lf(self):
        result = unify_newlines("a\r\nb\nc\rd")
        self.assertEqual(result.text, "a\nb\nc\nd")
        self.assertIs(result.target_style, NewlineStyle.LF)

    def test_consistent_document_inferred_to_its_own_style(self):
        result = unify_newlines("a\r\nb\r\n")
        self.assertEqual(result.text, "a\r\nb\r\n")
        self.assertIs(result.target_style, NewlineStyle.CRLF)

    def test_empty_document(self):
        result = unify_newlines("")
        self.assertEqual(result.text, "")
        self.assertEqual(result.records, ())
        self.assertIs(result.target_style, NewlineStyle.LF)

    def test_document_without_endings_is_unchanged(self):
        result = unify_newlines("abc")
        self.assertEqual(result.text, "abc")
        self.assertEqual(result.records, ())

    def test_trailing_text_preserved(self):
        result = unify_newlines("a\r\nb", NewlineStyle.LF)
        self.assertEqual(result.text, "a\nb")

    def test_leading_text_preserved(self):
        result = unify_newlines("\r\na", NewlineStyle.LF)
        self.assertEqual(result.text, "\na")

    def test_rejects_mixed_target(self):
        with self.assertRaises(ValueError):
            unify_newlines("a\n", NewlineStyle.MIXED)

    def test_rejects_non_string(self):
        with self.assertRaises(TypeError):
            unify_newlines(b"a\n")  # type: ignore[arg-type]


class RecordMappingTests(unittest.TestCase):
    def test_one_record_per_original_ending(self):
        result = unify_newlines("a\r\nb\nc\rd", NewlineStyle.LF)
        self.assertEqual(len(result.records), 3)
        self.assertEqual(
            [r.style for r in result.records],
            [NewlineStyle.CRLF, NewlineStyle.LF, NewlineStyle.CR],
        )

    def test_original_offsets_point_at_the_endings(self):
        text = "a\r\nb\nc\rd"
        result = unify_newlines(text, NewlineStyle.LF)
        for record in result.records:
            original = text[record.original_start : record.original_end]
            self.assertIn(original, ("\r\n", "\n", "\r"))
            self.assertIsInstance(record, LineEndingRecord)

    def test_unified_offsets_point_at_the_replacements(self):
        result = unify_newlines("a\r\nb\nc\rd", NewlineStyle.LF)
        for record in result.records:
            self.assertEqual(result.text[record.unified_start : record.unified_end], "\n")

    def test_offsets_account_for_length_change(self):
        # CRLF is two characters, LF is one, so the unified offsets must
        # drift relative to the original ones once the first replacement is
        # made.
        result = unify_newlines("a\r\nb\r\n", NewlineStyle.LF)
        first, second = result.records
        self.assertEqual((first.original_start, first.original_end), (1, 3))
        self.assertEqual((first.unified_start, first.unified_end), (1, 2))
        self.assertEqual((second.original_start, second.original_end), (4, 6))
        self.assertEqual((second.unified_start, second.unified_end), (3, 4))

    def test_records_are_immutable(self):
        result = unify_newlines("a\n", NewlineStyle.LF)
        with self.assertRaises(Exception):
            result.records[0].original_start = 99  # type: ignore[misc]

    def test_crlf_record_covers_both_characters(self):
        result = unify_newlines("a\r\nb", NewlineStyle.CRLF)
        record = result.records[0]
        self.assertEqual(record.original_end - record.original_start, 2)
        self.assertEqual(record.unified_end - record.unified_start, 2)


if __name__ == "__main__":
    unittest.main()
