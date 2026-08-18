from backend.utils.tags import extract_inline_tags, extract_frontmatter_tags, extract_tags


def test_extracts_single_inline_tag():
    assert extract_inline_tags("this is about #algorithms today") == {"algorithms"}


def test_extracts_multiple_inline_tags():
    assert extract_inline_tags("#todo and also #review") == {"todo", "review"}


def test_dedupes_case_insensitively():
    assert extract_inline_tags("#Project and #project again") == {"project"}


def test_supports_nested_tags_with_slash():
    assert extract_inline_tags("filed under #work/urgent") == {"work/urgent"}


def test_does_not_match_markdown_headers():
    assert extract_inline_tags("# Heading One\n## Heading Two") == set()


def test_does_not_match_purely_numeric_hash():
    # "#123" has no leading letter -- not a valid tag, same as Obsidian
    assert extract_inline_tags("issue #123 was fixed") == set()


def test_skips_tags_inside_fenced_code_block():
    content = "before #real\n```bash\n#!/bin/bash\necho #notatag\n```\nafter"
    assert extract_inline_tags(content) == {"real"}


def test_skips_tags_inside_inline_code():
    assert extract_inline_tags("see `#notatag` but #real is fine") == {"real"}


def test_no_tags_returns_empty_set():
    assert extract_inline_tags("plain text with no tags") == set()


def test_frontmatter_tags_from_list():
    assert extract_frontmatter_tags({"tags": ["Algorithms", "Review "]}) == {"algorithms", "review"}


def test_frontmatter_tags_from_comma_separated_string():
    assert extract_frontmatter_tags({"tags": "algorithms, review"}) == {"algorithms", "review"}


def test_frontmatter_tags_missing_key_returns_empty():
    assert extract_frontmatter_tags({"status": "draft"}) == set()


def test_extract_tags_unions_inline_and_frontmatter():
    body = "some #inline tag here"
    properties = {"tags": ["frontmatter-tag"]}
    assert extract_tags(body, properties) == {"inline", "frontmatter-tag"}
