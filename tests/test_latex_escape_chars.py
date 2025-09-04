from armymarkdown import memo_model


def test_escapes():
    ans = memo_model.add_latex_escape_chars("&")
    assert ans == "\\&"
