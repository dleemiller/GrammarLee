from grammarlee import parse_document

def test_core_parse_roundtrip():
    doc = """The [student::1] is studying for [their::2] test. She walked quickly[#3].

--- BACKMATTER ---
[1] REPLACE "students" -> "student" [GRAMMAR](singular subject)
[2] REPLACE "there" -> "their" [SPELLING](possessive)
[3] DELETE "very" -> "" [WORDINESS](unnecessary intensifier)
"""
    result = parse_document(doc)
    assert not result.errors
    assert result.final_text == "The student is studying for their test. She walked quickly."
    assert {a.id for a in result.anchors} == {1, 2, 3}
    assert {e.id for e in result.edits} == {1, 2, 3}

