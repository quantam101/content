# ProfitEngine Content

Public Jekyll content site for ProfitEngine articles.

## Purpose

This repository publishes owned content, preserves SEO metadata, and produces Jekyll output for the public site.

## Verify locally

```bash
bundle install
bundle exec jekyll build --strict_front_matter
```

## Release rule

Publish only reviewed articles with valid front matter, clear title, clear description, relevant call to action, and successful Jekyll build output.

## CI

The repository includes a blocking Jekyll build workflow. A release is acceptable only when the site builds and produces `index.html`, `sitemap.xml`, and `feed.xml`.
