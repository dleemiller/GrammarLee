from grammarlee import parse_backmatter

def test_multiple_lines_parse():
    bm = """[1] REPLACE "a" -> "b" [GRAMMAR](g)
[2] INSERT "" -> "c" [STYLE](s)
[3] DELETE "d" -> "" [WORDINESS](w)
"""
    edits = parse_backmatter(bm)
    assert [e.id for e in edits] == [1, 2, 3]
    assert [e.action.value for e in edits] == ["REPLACE", "INSERT", "DELETE"]
    assert [e.is_valid_category for e in edits] == [True, True, True]
    assert all(e.consistency_ok for e in edits)

def test_blank_backmatter_returns_empty_list():
    assert parse_backmatter("") == []
    assert parse_backmatter("   \n \r\n") == []

def test_malformed_backmatter_yields_empty_list_not_exception():
    # Missing quotes around OLD
    bm = '[1] REPLACE a -> "b" [GRAMMAR](oops)\n'
    edits = parse_backmatter(bm)
    assert edits == []  # runtime-friendly

def test_whitespace_tolerance_between_tokens():
    bm = "[1]   REPLACE   \"x\"   ->   \"y\"   [STYLE](ok)\n"
    edits = parse_backmatter(bm)
    assert len(edits) == 1
    assert edits[0].old == "x" and edits[0].new == "y"

def test_empty_comment_is_allowed():
    bm = '[1] REPLACE "a" -> "b" [GRAMMAR]()\n'
    edits = parse_backmatter(bm)
    assert len(edits) == 1
    assert edits[0].comment == ""

