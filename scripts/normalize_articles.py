#!/usr/bin/env python3
"""Normalize and validate Jekyll article payloads before publication.

The content generator has historically emitted valid Markdown as a JSON object in
an article body. Jekyll then renders that object literally. This tool provides a
single deterministic boundary between generated content and the public site.

Usage:
  python scripts/normalize_articles.py --check _posts
  python scripts/normalize_articles.py --write path/to/post.md

No third-party dependencies are required.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Iterable

FRONT_MATTER = re.compile(r"\A---\s*\n(?P<front>.*?)\n---\s*\n(?P<body>.*)\Z", re.S)
FENCED_JSON = re.compile(r"\A\s*```(?:json)?\s*\n(?P<payload>.*)\n```\s*\Z", re.S | re.I)
SCRIPT_TAG = re.compile(r"<\s*/?\s*(?:script|iframe|object|embed)(?:\s|>)", re.I)
EVENT_HANDLER = re.compile(r"\son[a-z]+\s*=", re.I)
JAVASCRIPT_URL = re.compile(r"(?:href|src)\s*=\s*['\"]\s*javascript:", re.I)
JSON_BODY_START = re.compile(r'"(?:body|content|article)"\s*:\s*"')
JSON_META_KEYS = ("title", "slug", "meta_description", "description", "tags")


class ContentError(ValueError):
    pass


def split_document(text: str) -> tuple[str, str]:
    match = FRONT_MATTER.match(text)
    if not match:
        raise ContentError("missing or malformed YAML front matter")
    return match.group("front"), match.group("body")


def front_value(front: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", front)
    if not match:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def upsert_front_value(front: str, key: str, value: str) -> str:
    replacement = f"{key}: {yaml_quote(value)}"
    pattern = re.compile(rf"(?m)^{re.escape(key)}:\s*.*$")
    if pattern.search(front):
        return pattern.sub(replacement, front, count=1)
    return front.rstrip() + "\n" + replacement


def strip_outer_fence(body: str) -> str:
    match = FENCED_JSON.match(body)
    return match.group("payload") if match else body


def decode_json_layers(value: object, limit: int = 4) -> object:
    current = value
    for _ in range(limit):
        if not isinstance(current, str):
            return current
        candidate = current.strip()
        if not candidate or candidate[0] not in '{["':
            return current
        try:
            current = json.loads(candidate)
        except json.JSONDecodeError:
            return current
    return current


def extract_payload(body: str) -> tuple[str, dict[str, object]] | None:
    """Return normalized Markdown body and metadata when body is JSON-wrapped.

    Supports valid JSON, fenced JSON, double encoded JSON and the historically
    observed truncated envelope where the `body` string itself is complete or
    truncated at EOF. The fallback decoder intentionally activates only when a
    JSON metadata envelope is present so normal Markdown/code examples are not
    rewritten.
    """
    raw = strip_outer_fence(body).strip()
    if not raw:
        return None

    parsed: object = raw
    try:
        parsed = json.loads(raw)
        parsed = decode_json_layers(parsed)
    except json.JSONDecodeError:
        parsed = raw

    if isinstance(parsed, dict):
        payload = parsed
        for key in ("body", "content", "article", "markdown"):
            candidate = payload.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return normalize_markdown(candidate), payload
        return None

    # Recover a partial generator envelope such as:
    # {"title":"...","body":"Markdown\\n...   <EOF>
    looks_like_envelope = raw.startswith("{") and any(
        f'"{key}"' in raw[:1200] for key in JSON_META_KEYS
    )
    marker = JSON_BODY_START.search(raw) if looks_like_envelope else None
    if not marker:
        return None

    encoded = raw[marker.end():]
    # If a closing JSON quote/brace exists, prefer the syntactically bounded
    # string. For the known truncated failure, decode all remaining bytes.
    if encoded.endswith('"}'):
        encoded = encoded[:-2]
    try:
        decoded = json.loads('"' + encoded + '"')
    except json.JSONDecodeError:
        # Python's string literal decoder is tolerant of a missing JSON envelope
        # but still decodes escaped newlines/quotes. Escape raw single quotes so
        # they cannot terminate the temporary literal.
        try:
            decoded = ast.literal_eval("'" + encoded.replace("'", "\\'") + "'")
        except (SyntaxError, ValueError):
            decoded = encoded.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")

    metadata: dict[str, object] = {}
    prefix = raw[: marker.start()]
    for key in ("title", "slug", "meta_description", "description"):
        m = re.search(rf'"{key}"\s*:\s*"((?:\\.|[^"\\])*)"', prefix)
        if m:
            try:
                metadata[key] = json.loads('"' + m.group(1) + '"')
            except json.JSONDecodeError:
                metadata[key] = m.group(1)
    return normalize_markdown(decoded), metadata


def normalize_markdown(body: str) -> str:
    text = body.replace("\r\n", "\n").replace("\r", "\n").strip()
    # Only decode literal newlines when they are clearly serialization residue.
    if "\\n" in text and text.count("\\n") >= 2 and "\n" not in text:
        text = text.replace("\\n", "\n")
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.rstrip() + "\n"


def validate(front: str, body: str, path: Path) -> list[str]:
    errors: list[str] = []
    if not front_value(front, "title"):
        errors.append("missing title")
    if not front_value(front, "date") and not re.match(r"\d{4}-\d{2}-\d{2}-", path.name):
        errors.append("missing date")
    if not body.strip():
        errors.append("empty body")
    if SCRIPT_TAG.search(body) or EVENT_HANDLER.search(body) or JAVASCRIPT_URL.search(body):
        errors.append("unsafe active HTML detected")
    extracted = extract_payload(body)
    if extracted is not None:
        errors.append("serialized article payload remains in body")
    # Literal escaped newlines in prose are almost always generator leakage.
    if body.count("\\n") >= 3:
        errors.append("serialized newline escapes remain in body")
    return errors


def normalize_document(text: str, path: Path) -> tuple[str, bool]:
    front, body = split_document(text)
    extracted = extract_payload(body)
    changed = False
    if extracted:
        body, metadata = extracted
        changed = True
        title = metadata.get("title")
        description = metadata.get("meta_description") or metadata.get("description")
        if isinstance(title, str) and title.strip():
            front = upsert_front_value(front, "title", title.strip())
        if isinstance(description, str) and description.strip():
            front = upsert_front_value(front, "description", description.strip())

    normalized_body = normalize_markdown(body)
    if normalized_body != body:
        body = normalized_body
        changed = True

    output = f"---\n{front.rstrip()}\n---\n\n{body}"
    return output, changed


def iter_files(targets: Iterable[str]) -> Iterable[Path]:
    for raw in targets:
        target = Path(raw)
        if target.is_dir():
            yield from sorted(target.glob("*.md"))
        else:
            yield target


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="fail if content is malformed or needs normalization")
    mode.add_argument("--write", action="store_true", help="normalize files in place, then validate")
    parser.add_argument("targets", nargs="+", help="Markdown files or directories")
    args = parser.parse_args()

    failures = 0
    checked = 0
    for path in iter_files(args.targets):
        if not path.exists():
            print(f"ERROR {path}: not found", file=sys.stderr)
            failures += 1
            continue
        checked += 1
        try:
            original = path.read_text(encoding="utf-8")
            normalized, changed = normalize_document(original, path)
            front, body = split_document(normalized)
            errors = validate(front, body, path)
        except (OSError, UnicodeError, ContentError) as exc:
            print(f"ERROR {path}: {exc}", file=sys.stderr)
            failures += 1
            continue

        if args.check and changed:
            errors.append("file is not normalized")
        if errors:
            for error in errors:
                print(f"ERROR {path}: {error}", file=sys.stderr)
            failures += 1
            continue
        if args.write and changed:
            path.write_text(normalized, encoding="utf-8")
            print(f"NORMALIZED {path}")

    if checked == 0:
        print("ERROR: no Markdown files found", file=sys.stderr)
        return 2
    if failures:
        print(f"Content validation failed: {failures}/{checked} file(s)", file=sys.stderr)
        return 1
    print(f"Content validation passed: {checked} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
