from backend.utils.frontmatter import parse_frontmatter, serialize_frontmatter


def test_no_frontmatter_returns_empty_properties_and_full_content():
    properties, body = parse_frontmatter("just a normal note")
    assert properties == {}
    assert body == "just a normal note"


def test_parses_simple_frontmatter_block():
    content = "---\nstatus: draft\npriority: 2\n---\n\nBody text here."
    properties, body = parse_frontmatter(content)
    assert properties == {"status": "draft", "priority": 2}
    assert body == "Body text here."


def test_parses_list_valued_property():
    content = "---\ntags:\n  - algorithms\n  - review\n---\nBody"
    properties, _ = parse_frontmatter(content)
    assert properties == {"tags": ["algorithms", "review"]}


def test_malformed_yaml_leaves_content_untouched():
    content = "---\nthis: is: not: valid: yaml: at: all\n---\nBody"
    properties, body = parse_frontmatter(content)
    assert properties == {}
    assert body == content  # left alone, not silently discarded


def test_frontmatter_block_that_is_not_a_mapping_is_ignored():
    content = "---\n- just\n- a\n- list\n---\nBody"
    properties, body = parse_frontmatter(content)
    assert properties == {}
    assert body == content


def test_dashes_mid_document_are_not_treated_as_frontmatter():
    content = "Some text\n---\nnot: frontmatter\n---\nmore text"
    properties, body = parse_frontmatter(content)
    assert properties == {}
    assert body == content


def test_serialize_empty_properties_returns_body_unchanged():
    assert serialize_frontmatter({}, "just body text") == "just body text"


def test_serialize_and_reparse_round_trips():
    original_properties = {"status": "draft", "tags": ["a", "b"]}
    body = "The actual note content."
    content = serialize_frontmatter(original_properties, body)
    reparsed_properties, reparsed_body = parse_frontmatter(content)
    assert reparsed_properties == original_properties
    assert reparsed_body == body
