from grammarlee import parse_inline_anchors, apply_inline

def test_anchor_parse_and_render_repl_and_del():
    inline = "T [xx::12] m [#3]\n"
    anchors = parse_inline_anchors(inline)
    assert [(a.id, a.kind, a.new_text) for a in anchors] == [(12, "replace_or_insert", "xx"), (3, "delete", "")]
    final_text = apply_inline(inline)
    assert final_text == "T xx m "

def test_anchor_spans_cover_bracket_tokens():
    s = "A [b::9] C [#10] D"
    for a in parse_inline_anchors(s):
        token_text = s[a.span[0]:a.span[1]]
        assert token_text.startswith("[") and token_text.endswith("]")
        if a.kind == "replace_or_insert":
            assert "::" in token_text
        else:
            assert token_text[1] == "#"

def test_multidigit_ids_and_no_leading_zeros():
    s = "X [y::123] Z"
    anchors = parse_inline_anchors(s)
    assert anchors[0].id == 123

