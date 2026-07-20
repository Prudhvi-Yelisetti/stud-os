from backend.utils.wiki_parser import extract_wiki_links


def test_extracts_single_link():
    assert extract_wiki_links("See [[BFS]] for details") == ["BFS"]


def test_extracts_multiple_links_in_order():
    assert extract_wiki_links("[[A]] then [[B]] then [[C]]") == ["A", "B", "C"]


def test_dedupes_repeated_links_keeping_first_position():
    assert extract_wiki_links("[[A]] ... [[B]] ... [[A]]") == ["A", "B"]


def test_no_links_returns_empty_list():
    assert extract_wiki_links("plain text, no links here") == []


def test_ignores_empty_brackets():
    assert extract_wiki_links("[[]] and [[  ]]") == []


def test_strips_whitespace_in_link_title():
    assert extract_wiki_links("[[  Padded Title  ]]") == ["Padded Title"]


def test_does_not_match_single_brackets():
    assert extract_wiki_links("[not a link] and [[real link]]") == ["real link"]
