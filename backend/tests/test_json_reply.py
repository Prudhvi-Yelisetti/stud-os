import pytest
from backend.ai.json_reply import parse_json_reply


def test_parses_plain_json():
    assert parse_json_reply('{"a": 1}') == {"a": 1}


def test_strips_markdown_json_fence():
    assert parse_json_reply('```json\n{"a": 1}\n```') == {"a": 1}


def test_strips_bare_fence_without_language_tag():
    assert parse_json_reply('```\n{"a": 1}\n```') == {"a": 1}


def test_strips_surrounding_whitespace():
    assert parse_json_reply('  \n {"a": 1} \n  ') == {"a": 1}


def test_raises_on_invalid_json():
    with pytest.raises(Exception):
        parse_json_reply("this is not json")
