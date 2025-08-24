import pytest
from grammarlee import parse_document

def test_core_parse_roundtrip():
    doc = """The [student::1] is studying for [their::2] test. She walked quickly[#3].

--- BACKMATTER ---
[1] REPLACE "students" -> "student" [GRAMMAR](singular subject)
[2] REPLACE "there" -> "their" [SPELLING](possessive)
[3] DELETE "very" -> "" [WORDINESS](unnecessary intensifier)
"""
    result = parse_document(doc)
    assert result.errors == []
    assert result.final_text == "The student is studying for their test. She walked quickly."
    assert {a.id for a in result.anchors} == {1, 2, 3}
    assert {e.id for e in result.edits} == {1, 2, 3}

@pytest.mark.parametrize("pad", ["", " ", "   \t"])
def test_delimiter_is_whitespace_tolerant(pad):
    doc = f"""Hello world.

{pad}--- BACKMATTER ---{pad}
[1] INSERT "" -> "Hello" [STYLE](lead-in)
"""
    result = parse_document(doc)
    assert result.errors == []
    assert result.final_text == "Hello world."
    assert len(result.edits) == 1
    assert result.edits[0].action.value == "INSERT"

def test_no_backmatter_is_ok():
    doc = "Alpha [#1] beta.\n"
    result = parse_document(doc)
    assert result.errors == []
    assert result.final_text == "Alpha  beta."
    assert len(result.edits) == 0
    assert len(result.anchors) == 1 and result.anchors[0].kind == "delete"

def test_windows_crlf_and_extra_blank_lines():
    doc = "Line one.\r\n\r\n--- BACKMATTER ---\r\n\r\n[12] INSERT \"\" -> \"Line\" [STYLE](title)\r\n"
    result = parse_document(doc)
    assert result.errors == []
    assert len(result.edits) == 1
    assert result.edits[0].id == 12

def test_quoted_and_comment_escaping():
    doc = r"""Say [\"hi\"::1] now.

--- BACKMATTER ---
[1] REPLACE "say \"hi\"" -> "\"hi\"" [GRAMMAR](some comment)
"""
    result = parse_document(doc)
    assert result.errors == []
    assert result.final_text == 'Say "hi" now.'
    e = result.edits[0]
    assert e.old == 'say "hi"'
    assert e.new == '"hi"'
    assert e.comment == "some comment"

def test_invalid_category_flag_only():
    doc = """Word.

--- BACKMATTER ---
[2] REPLACE "Word" -> "Word" [BADCAT](not a valid category)
"""
    result = parse_document(doc)
    assert result.errors == []  # parsed, category flagged
    assert len(result.edits) == 1
    assert result.edits[0].category == "BADCAT"
    assert result.edits[0].is_valid_category is False

def test_action_shape_consistency_flags():
    doc = """x

--- BACKMATTER ---
[1] INSERT "nonempty" -> "y" [STYLE](insert must have empty old)
[2] DELETE "" -> "" [WORDINESS](delete must have nonempty old and empty new)
[3] REPLACE "" -> "" [GRAMMAR](replace must have both old/new)
"""
    result = parse_document(doc)
    assert result.errors == []            # parsed, but flags set
    flags = {e.id: e.consistency_ok for e in result.edits}
    assert flags[1] is False
    assert flags[2] is False
    assert flags[3] is False

def test_duplicate_ids_are_preserved_not_deduped():
    doc = """Text [x::1] and [y::1].

--- BACKMATTER ---
[1] REPLACE "Text" -> "Text" [STYLE](noop)
[1] INSERT "" -> "More" [STYLE](second line same id)
"""
    result = parse_document(doc)
    assert result.errors == []
    assert [e.id for e in result.edits] == [1, 1]
    assert [a.id for a in result.anchors] == [1, 1]

def test_apply_inline_strips_only_trailing_newlines_preserves_internal():
    doc = "A [B::1]\nC [D::2]\n\n--- BACKMATTER ---\n[1] INSERT \"\" -> \"B\" [STYLE](x)\n[2] INSERT \"\" -> \"D\" [STYLE](y)\n"
    result = parse_document(doc)
    assert result.errors == []
    assert result.final_text == "A B\nC D"

