import types
import pytest
from grammarlee.parser import INLINE_TOKEN_RE, parse_document, iter_inline_matches, parse_inline_anchors, apply_inline

@pytest.mark.parametrize(
    "text,expected",
    [
        ("The [student::1] is ready.", "The student is ready."),
        ("She walked [very::2] quickly.", "She walked very quickly."),
        ("He moved quickly[::3].", "He moved quickly."),
        ("[A::1] and [::2] then [B C::3].", "A and  then B C."),
        (r"Quote: [\"hi\"::4] done.", 'Quote: "hi" done.'),
        ("Café [au lait::5] — nice.", "Café au lait — nice."),
        ("Line[::6]\n", "Line"),
    ],
)
def test_apply_inline_expected_output(text, expected):
    assert apply_inline(text) == expected

def test_parse_inline_kinds_and_spans():
    text = "X [alpha::1] Y [::2] Z [beta::3]"
    anchors = parse_inline_anchors(text)
    assert [a.id for a in anchors] == [1, 2, 3]
    assert [a.kind for a in anchors] == ["replace_or_insert", "delete", "replace_or_insert"]
    for a in anchors:
        s, e = a.span
        chunk = text[s:e]
        assert chunk.startswith("[") and chunk.endswith("]")
        assert chunk.endswith(f"::{a.id}]")

@pytest.mark.parametrize(
    "snippet,should_find",
    [
        ("[x::1]", True),
        ("[::9]", True),      # delete
        ("[::01]", False),    # leading zero not allowed
        ("[x::0]", False),    # zero not allowed
        ("[]", False),
        ("[::]", False),
        ("[x::]", False),
        ("[#7]", False),      # legacy delete must not match
        ("[a[b::1]", False),  # nested '[': do not match inner token
    ],
)
def test_depth_aware_scanner(snippet, should_find):
    matches = list(iter_inline_matches(snippet))
    assert (len(matches) > 0) == should_find

def test_inline_token_re_matches_clean_token():
    m = INLINE_TOKEN_RE.search("ok [xx::12] ok")
    assert m and m.group("new") == "xx" and m.group("id") == "12"


class _Pred(types.SimpleNamespace):
    pass

def test_can_import_and_parse_document():
    pred = _Pred(
        edited_text="He walked [very::1] quickly[::2].",
        edits=[],            # optional for this test
        backmatter_text="",  # optional
    )
    out = parse_document(pred)
    assert out.final_text == "He walked very quickly."
    ids = [a.id for a in out.anchors]
    kinds = [a.kind for a in out.anchors]
    assert ids == [1, 2]
    assert kinds == ["replace_or_insert", "delete"]
