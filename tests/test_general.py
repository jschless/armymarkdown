from armymarkdown import memo_model, writer


def test_memo_model_creation():
    m = memo_model.parse("./template.Amd")
    assert m == memo_model.MemoModel(
        unit_name="4th Engineer Battalion",
        unit_street_address="588 Wetzel Road",
        unit_city_state_zip="Colorado Springs, CO 80904",
        office_symbol="ABC-DEF-GH",
        subject="Army markdown",
        text=[
            "This memo is a demo.",
            "This item contains sub items.",
            ["Thing one.", "Thing two.", ["Here is a sub sub item"]],
            "Point of contact is the undersigned.",
        ],
        author_name="Joseph C. Schlessinger",
        author_rank="1LT",
        author_branch="EN",
        author_title="Maintenance Platoon Leader",
        memo_type="MEMORANDUM FOR RECORD",
        todays_date="13 June 2022",
        suspense_date=None,
        document_mark=None,
        enclosures=None,
        distros=None,
        cfs=None,
    )


def test_latex_file():
    m = memo_model.parse("./template.Amd")
    mw = writer.MemoWriter(m)
    mw.write(output_file="./tests/test_tex_output_basic.tex")

    created_output = open("./tests/test_tex_output_basic.tex", "r").read()
    answer_output = open("./tests/answer_test_tex_output_basic.tex", "r").read()
    assert created_output == answer_output
