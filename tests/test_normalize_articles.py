import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "normalize_articles.py"
spec = importlib.util.spec_from_file_location("normalize_articles", MODULE_PATH)
normalizer = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(normalizer)


class NormalizeArticlesTests(unittest.TestCase):
    def doc(self, body: str) -> str:
        return f'---\ntitle: "Test Post"\ndate: 2026-09-11\nlayout: post\n---\n\n{body}'

    def normalize(self, body: str):
        path = Path("_posts/2026-09-11-test.md")
        return normalizer.normalize_document(self.doc(body), path)

    def test_clean_markdown_is_idempotent(self):
        source = self.doc("Intro.\n\n## Heading\n\nBody.\n")
        first, changed = normalizer.normalize_document(source, Path("_posts/2026-09-11-test.md"))
        second, changed_again = normalizer.normalize_document(first, Path("_posts/2026-09-11-test.md"))
        self.assertFalse(changed)
        self.assertFalse(changed_again)
        self.assertEqual(first, second)

    def test_valid_json_envelope_is_unwrapped(self):
        payload = r'{"title":"Better title","meta_description":"Better description","body":"Intro.\n\n## Heading\n\nBody."}'
        output, changed = self.normalize(payload)
        self.assertTrue(changed)
        self.assertIn('title: "Better title"', output)
        self.assertIn('description: "Better description"', output)
        self.assertIn("## Heading", output)
        self.assertNotIn('"body":', output)

    def test_fenced_json_is_unwrapped(self):
        payload = '```json\n{"title":"T","body":"Hello\\n\\n## H"}\n```'
        output, changed = self.normalize(payload)
        self.assertTrue(changed)
        self.assertIn("## H", output)
        self.assertNotIn("```json", output)

    def test_truncated_generator_envelope_is_recovered(self):
        payload = r'{"title":"Recovered","meta_description":"Desc","tags":["x"],"body":"Intro.\n\n## H\n\nLast partial sentence'
        output, changed = self.normalize(payload)
        self.assertTrue(changed)
        self.assertIn('title: "Recovered"', output)
        self.assertIn("## H", output)
        self.assertIn("Last partial sentence", output)
        self.assertNotIn(r"\n\n", output)

    def test_double_encoded_json_is_unwrapped(self):
        payload = r'"{\"title\":\"Nested\",\"body\":\"Hello\\n\\nWorld\"}"'
        output, changed = self.normalize(payload)
        self.assertTrue(changed)
        self.assertIn('title: "Nested"', output)
        self.assertIn("Hello\n\nWorld", output)

    def test_normal_markdown_json_code_sample_is_not_rewritten(self):
        body = 'Example:\n\n```json\n{"body":"this is documentation"}\n```\n'
        output, changed = self.normalize(body)
        self.assertFalse(changed)
        self.assertIn('```json', output)

    def test_validator_rejects_script(self):
        front, body = normalizer.split_document(self.doc('<script>alert(1)</script>'))
        errors = normalizer.validate(front, body, Path("_posts/2026-09-11-test.md"))
        self.assertIn("unsafe active HTML detected", errors)

    def test_validator_rejects_event_handler(self):
        front, body = normalizer.split_document(self.doc('<img src="x" onerror="alert(1)">'))
        errors = normalizer.validate(front, body, Path("_posts/2026-09-11-test.md"))
        self.assertIn("unsafe active HTML detected", errors)

    def test_write_mode_shape_has_valid_front_matter(self):
        output, _ = self.normalize(r'{"title":"T","body":"Body"}')
        front, body = normalizer.split_document(output)
        self.assertEqual(normalizer.front_value(front, "title"), "T")
        self.assertEqual(body.strip(), "Body")


if __name__ == "__main__":
    unittest.main()
