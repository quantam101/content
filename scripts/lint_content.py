#!/usr/bin/env python3
"""Site-wide content quality gate for generated Jekyll content.

Complements ``normalize_articles.py`` (single-document hygiene) with checks that
only make sense across the whole corpus:

* **URL collisions** — two files that would publish to the same URL. For posts
  the effective slug is the filename minus the ``YYYY-MM-DD-`` prefix (or an
  explicit ``slug:`` override); pages and files with ``permalink:`` are
  resolved the same way Jekyll resolves them.
* **Stale year references** — years older than the file's own publish date in
  SEO-critical fields (title, description, headings) or in "currency" body
  lines ("best X 2024", "in 2024", "updated 2024"). A recent-but-not-current
  year is the signature of regenerated content carrying a stale date.
* **Front-matter completeness** — ``title`` everywhere, ``description`` on
  posts and city pages, and a ``date`` consistent with the filename date.

Usage:
  python scripts/lint_content.py _posts city-pages campaigns
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

# Reuse the single-document parser from the sibling script.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from normalize_articles import ContentError, front_value, split_document  # noqa: E402

POST_FILENAME = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2})-(?P<slug>.+)\.md$")
DATE_VALUE = re.compile(r"(\d{4})-\d{2}-\d{2}")
YEAR_TOKEN = re.compile(r"\b(20\d\d)\b")
HEADING = re.compile(r"(?m)^#{1,6}\s+.*$")

# Body lines where a year is being presented as the reference/freshness year.
CURRENCY_LINE = re.compile(
    r"\b(best|top|guide|review|comparison|vs\.?|versus|updated|wins|"
    r"checklist|trends|strategies|ranked|edition|state of|in 20\d\d|"
    r"for 20\d\d)\b",
    re.I,
)

# A year is "stale" when it is close enough to the publish year to read as
# current but is not. Older references are treated as legitimate history.
STALE_YEAR_WINDOW = 4

# Directories whose files are full articles and must carry a meta description.
DESCRIPTION_REQUIRED_DIRS = ("_posts", "city-pages")


def iter_markdown(targets: Iterable[str]) -> Iterable[Path]:
    for raw in targets:
        target = Path(raw)
        if target.is_dir():
            yield from sorted(target.rglob("*.md"))
        elif target.is_file():
            yield target


def publish_year(path: Path, front: str) -> int | None:
    """Year the content claims to be published in (filename wins, then date:)."""
    match = POST_FILENAME.match(path.name)
    if match:
        return int(match.group("date")[:4])
    date_field = front_value(front, "date")
    if date_field:
        m = DATE_VALUE.search(date_field)
        if m:
            return int(m.group(1))
    return None


def output_url(path: Path, front: str) -> str:
    """The URL path Jekyll will emit for this file (relative to baseurl)."""
    permalink = front_value(front, "permalink")
    if permalink:
        return permalink.strip().strip("/") + "/"

    parts = path.parts
    if "_posts" in parts:
        match = POST_FILENAME.match(path.name)
        slug = match.group("slug") if match else path.stem
        slug_override = front_value(front, "slug")
        if slug_override:
            slug = slug_override.strip().strip("/")
        return f"posts/{slug}/"
    if path.name.lower() == "index.md":
        parent = str(path.parent).replace("\\", "/")
        return parent + "/" if parent != "." else ""
    return str(path.with_suffix("")).replace("\\", "/") + "/"


def check_front_matter(path: Path, front: str, body: str) -> list[str]:
    errors: list[str] = []
    if not front_value(front, "title"):
        errors.append("missing title")
    in_description_dir = any(p in DESCRIPTION_REQUIRED_DIRS for p in path.parts)
    if in_description_dir and not front_value(front, "description"):
        errors.append("missing description")

    file_date = POST_FILENAME.match(path.name)
    date_field = front_value(front, "date")
    if "_posts" in path.parts and not file_date:
        errors.append("post filename missing YYYY-MM-DD prefix")
    if file_date and date_field:
        m = DATE_VALUE.search(date_field)
        if m and m.group(0) != file_date.group("date"):
            errors.append(
                f"front-matter date {m.group(0)} differs from filename date {file_date.group('date')}"
            )
    if not body.strip():
        errors.append("empty body")
    return errors


def check_stale_years(path: Path, front: str, body: str) -> list[str]:
    errors: list[str] = []
    year = publish_year(path, front)
    if year is None:
        return errors
    floor = year - STALE_YEAR_WINDOW

    def stale(tok_year: int) -> bool:
        return tok_year < year

    for field in ("title", "description"):
        value = front_value(front, field)
        if not value:
            continue
        for tok in YEAR_TOKEN.findall(value):
            if stale(int(tok)):
                errors.append(f"stale year {tok} in {field} (published {year})")
                break

    for heading in HEADING.findall(body):
        for tok in YEAR_TOKEN.findall(heading):
            if stale(int(tok)):
                errors.append(f"stale year {tok} in heading: {heading.strip()[:80]}")
                break

    for line in body.splitlines():
        years = [int(y) for y in YEAR_TOKEN.findall(line)]
        recent_stale = [y for y in years if floor <= y < year]
        if recent_stale and CURRENCY_LINE.search(line):
            errors.append(
                f"stale year {recent_stale[0]} in body line: {line.strip()[:80]}"
            )
    return errors


def lint_file(path: Path) -> tuple[list[str], str | None]:
    """Return (errors, output_url). output_url is None when the file fails to parse."""
    try:
        text = path.read_text(encoding="utf-8")
        front, body = split_document(text)
    except (OSError, UnicodeError, ContentError) as exc:
        return [f"{exc}"], None
    errors = check_front_matter(path, front, body)
    errors.extend(check_stale_years(path, front, body))
    return errors, output_url(path, front)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="+", help="Markdown files or directories (searched recursively)")
    args = parser.parse_args()

    files = list(iter_markdown(args.targets))
    if not files:
        print("ERROR: no Markdown files found", file=sys.stderr)
        return 2

    failures = 0
    urls: dict[str, list[Path]] = {}
    for path in files:
        errors, url = lint_file(path)
        if url is not None:
            urls.setdefault(url, []).append(path)
        for error in errors:
            print(f"ERROR {path}: {error}", file=sys.stderr)
        if errors:
            failures += 1

    for url, owners in urls.items():
        if len(owners) > 1:
            names = ", ".join(str(p) for p in owners)
            print(f"ERROR duplicate output URL /{url} published by: {names}", file=sys.stderr)
            failures += 1

    if failures:
        print(f"Content lint failed: {failures} problem(s) across {len(files)} file(s)", file=sys.stderr)
        return 1
    print(f"Content lint passed: {len(files)} file(s), {len(urls)} unique URLs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
