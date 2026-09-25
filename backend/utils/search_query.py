"""
Parses Obsidian-style search operators out of a raw query string:

  tag:foo          only chapters/journal entries tagged #foo
  notebook:Name     only chapters in a notebook whose title contains Name
                    (chapters only -- tasks/journal/notebooks have no
                    notebook to filter by, so this operator is a no-op
                    for those result types)
  -word             exclude results whose title/content contains word
                    (applies the same substring test the plain keyword
                    search already does, just inverted)

Operators can be combined and mixed freely with plain keywords in any
order, space-separated: `tag:project -done notebook:Work status`. A
`tag:` or `notebook:` value with spaces isn't supported (no quoting) --
matches the scope of the other single-token operators here.
"""
import re
from dataclasses import dataclass, field

_OPERATOR = re.compile(r"(?:^|\s)(-?)(tag|notebook):(\S+)")


@dataclass
class ParsedQuery:
    text: str  # remaining plain keywords, joined back into one string
    tags: list[str] = field(default_factory=list)
    exclude_tags: list[str] = field(default_factory=list)
    notebooks: list[str] = field(default_factory=list)
    exclude_notebooks: list[str] = field(default_factory=list)
    exclude_words: list[str] = field(default_factory=list)


def parse_query(raw: str) -> ParsedQuery:
    tags: list[str] = []
    exclude_tags: list[str] = []
    notebooks: list[str] = []
    exclude_notebooks: list[str] = []

    def consume_operator(m: re.Match) -> str:
        negate, field_name, value = m.group(1), m.group(2), m.group(3)
        target_list = {
            ("tag", ""): tags,
            ("tag", "-"): exclude_tags,
            ("notebook", ""): notebooks,
            ("notebook", "-"): exclude_notebooks,
        }[(field_name, negate)]
        target_list.append(value)
        return " "

    without_operators = _OPERATOR.sub(consume_operator, raw)

    exclude_words: list[str] = []
    remaining_terms: list[str] = []
    for token in without_operators.split():
        if token.startswith("-") and len(token) > 1:
            exclude_words.append(token[1:])
        else:
            remaining_terms.append(token)

    return ParsedQuery(
        text=" ".join(remaining_terms).strip(),
        tags=tags,
        exclude_tags=exclude_tags,
        notebooks=notebooks,
        exclude_notebooks=exclude_notebooks,
        exclude_words=exclude_words,
    )
