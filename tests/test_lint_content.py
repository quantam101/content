import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "lint_content.py"
spec = importlib.util.spec_from_file_location("lint_content", MODULE_PATH)
linter = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = linter
assert spec.loader
spec.loader.exec_module(linter)


def doc(front: str, body: str = "Body text.\n") -> str:
    return f"---\n{front}\n---\n\n{body}"


class LintContentTests(unittest.TestCase):
    def post_path(self, name: str = "2026-10-12-my-post.md") -> Path:
        return Path("_posts") / name

    def test_output_url_uses_filename_slug(self):
        front = 'title: "T"\ndescription: "D"\ndate: 2026-10-12\n'
        self.assertEqual(
            linter.output_url(self.post_path(), front),
            "posts/my-post/",
        )

    def test_output_url_honors_slug_override(self):
        front = 'title: "T"\ndescription: "D"\nslug: "custom-slug"\n'
        self.assertEqual(
            linter.output_url(self.post_path(), front),
            "posts/custom-slug/",
        )

    def test_output_url_honors_permalink(self):
        front = 'title: "T"\npermalink: /campaigns/foo/\n'
        path = Path("campaigns/2026-06-11-foo.md")
        self.assertEqual(linter.output_url(path, front), "campaigns/foo/")

    def test_output_url_for_nested_page(self):
        front = 'title: "T"\ndescription: "D"\n'
        path = Path("city-pages/plumbers/phoenix.md")
        self.assertEqual(linter.output_url(path, front), "city-pages/plumbers/phoenix/")

    def test_duplicate_slug_is_reported(self):
        front = 'title: "T"\ndescription: "D"\n'
        with tempfile.TemporaryDirectory() as tmp:
            posts = Path(tmp) / "_posts"
            posts.mkdir()
            (posts / "2026-01-01-same.md").write_text(doc(front))
            (posts / "2026-10-01-same.md").write_text(doc(front))
            old_argv = sys.argv
            try:
                sys.argv = ["lint_content.py", str(posts)]
                self.assertEqual(linter.main(), 1)
            finally:
                sys.argv = old_argv

    def test_stale_year_in_title_and_description(self):
        front = (
            'title: "Best tools in 2024"\n'
            'description: "Updated for 2024"\n'
            "date: 2026-10-12\n"
        )
        errors = linter.check_stale_years(self.post_path(), front, "Body.\n")
        self.assertTrue(any("2024" in e and "title" in e for e in errors))
        self.assertTrue(any("2024" in e and "description" in e for e in errors))

    def test_stale_year_in_currency_body_line(self):
        body = "Intro.\n\nChoosing a host in 2024 requires care.\n"
        errors = linter.check_stale_years(self.post_path(), 'title: "T"\n', body)
        self.assertTrue(any("2024" in e for e in errors))

    def test_historical_year_is_allowed(self):
        body = "GitHub launched Pages in 2008 and it grew steadily.\n"
        errors = linter.check_stale_years(self.post_path(), 'title: "T"\n', body)
        self.assertEqual(errors, [])

    def test_current_year_is_allowed(self):
        front = 'title: "Best tools in 2026"\ndescription: "Fresh 2026 review"\n'
        body = "## Top picks for 2026\n\nOur 2026 guide covers hosts.\n"
        errors = linter.check_stale_years(self.post_path(), front, body)
        self.assertEqual(errors, [])

    def test_missing_description_on_post(self):
        errors = linter.check_front_matter(
            self.post_path(), 'title: "T"\ndate: 2026-10-12\n', "Body.\n"
        )
        self.assertIn("missing description", errors)

    def test_front_matter_date_mismatch(self):
        front = 'title: "T"\ndescription: "D"\ndate: 2026-05-05\n'
        errors = linter.check_front_matter(self.post_path(), front, "Body.\n")
        self.assertTrue(any("differs from filename date" in e for e in errors))

    def test_clean_file_has_no_errors(self):
        front = 'title: "T"\ndescription: "D"\ndate: 2026-10-12\n'
        errs = linter.check_front_matter(self.post_path(), front, "Body.\n")
        errs += linter.check_stale_years(self.post_path(), front, "Body.\n")
        self.assertEqual(errs, [])


if __name__ == "__main__":
    unittest.main()
