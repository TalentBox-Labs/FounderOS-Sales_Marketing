from src.tools.metadata_checker import _split_front_matter


def test_split_front_matter_parses_keys():
    text = """---
week_id: W05
article_title: Hello
---

# Body
"""
    fm, body = _split_front_matter(text)
    assert fm is not None
    assert fm["week_id"] == "W05"
    assert fm["article_title"] == "Hello"
    assert "# Body" in body


def test_split_front_matter_missing_returns_none():
    text = "# No front matter\n"
    fm, body = _split_front_matter(text)
    assert fm is None
