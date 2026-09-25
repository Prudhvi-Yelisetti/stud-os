from backend.utils.search_query import parse_query


def test_plain_query_has_no_operators():
    p = parse_query("hello world")
    assert p.text == "hello world"
    assert p.tags == p.exclude_tags == p.notebooks == p.exclude_notebooks == p.exclude_words == []


def test_tag_operator_parsed_out_of_text():
    p = parse_query("tag:project status")
    assert p.tags == ["project"]
    assert p.text == "status"


def test_negated_tag_operator():
    p = parse_query("-tag:archived meeting")
    assert p.exclude_tags == ["archived"]
    assert p.text == "meeting"


def test_notebook_operator():
    p = parse_query("notebook:Work budget")
    assert p.notebooks == ["Work"]
    assert p.text == "budget"


def test_negated_notebook_operator():
    p = parse_query("-notebook:Archive budget")
    assert p.exclude_notebooks == ["Archive"]
    assert p.text == "budget"


def test_bare_exclude_word():
    p = parse_query("plan -draft")
    assert p.exclude_words == ["draft"]
    assert p.text == "plan"


def test_operators_and_exclude_words_combine_freely():
    p = parse_query("tag:project -done notebook:Work status")
    assert p.tags == ["project"]
    assert p.exclude_words == ["done"]
    assert p.notebooks == ["Work"]
    assert p.text == "status"


def test_hyphenated_word_is_not_mistaken_for_exclusion():
    # A leading "-" is exclusion syntax; a hyphen elsewhere in a word is just a hyphen.
    p = parse_query("well-known term")
    assert p.exclude_words == []
    assert p.text == "well-known term"
