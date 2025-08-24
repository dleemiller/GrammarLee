import re
import pytest

try:
    from hypothesis import given, strategies as st
    HYP = True
except Exception:
    HYP = False

from grammarlee import parse_backmatter

pytestmark = pytest.mark.skipif(not HYP, reason="Hypothesis not installed")

@st.composite
def bm_line(draw, start_id=1):
    i = draw(st.integers(min_value=start_id, max_value=start_id + 1000))
    action = draw(st.sampled_from(["REPLACE", "INSERT", "DELETE"]))
    cat = draw(st.sampled_from(["GRAMMAR", "SPELLING", "PUNCTUATION", "STYLE", "CLARITY", "WORD", "WORDINESS"]))

    # Avoid quotes, backslashes, and newlines in old/new
    safe_chars = st.characters(blacklist_characters='"\r\n\\')
    word = st.text(min_size=1, max_size=5, alphabet=safe_chars)

    if action == "REPLACE":
        old = draw(word)
        new = draw(word)
    elif action == "INSERT":
        old, new = "", draw(word)
    else:  # DELETE
        old, new = draw(word), ""

    # Comments: no newlines/backslashes; escape ) afterward
    comment_raw = draw(st.text(min_size=0, max_size=10,
                               alphabet=st.characters(blacklist_characters="\r\n\\")))
    comment = comment_raw.replace(")", r"\)")

    return f'[{i}] {action} "{old}" -> "{new}" [{cat}]({comment})'

@given(st.lists(bm_line(1), min_size=1, max_size=10).map(lambda lines: "\n".join(lines) + "\n"))
def test_parse_backmatter_hypothesis(bm):
    edits = parse_backmatter(bm)
    expected = len(re.findall(r'^\s*\[\d+\]\s+(?:REPLACE|INSERT|DELETE)\b', bm, flags=re.M))
    assert len(edits) == expected
    for e in edits:
        if e.action.value == "REPLACE":
            assert e.old and e.new
        elif e.action.value == "INSERT":
            assert e.old == "" and e.new
        else:  # DELETE
            assert e.old and e.new == ""
        assert e.is_valid_category
        assert e.consistency_ok

