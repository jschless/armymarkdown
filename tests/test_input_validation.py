from armymarkdown import memo_model

test_dict = dict(
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


def test_date_validation():
    m = memo_model.MemoModel(**test_dict)
    test_dates = ["1 June 2023", "03 JUN 2019", "30 May 22", "2 may 2022"]
    for date in test_dates:
        answer = f"The entered date {date} does not"
        answer += " conform to pattern ## Month ####"
        assert m._check_date(date) == answer

    assert m._check_date("23 June 2019") is None


def test_branch_validation():
    m = memo_model.MemoModel(**test_dict)
    test_branches = ["En", "Infantri", "Operator"]
    for branch in test_branches:
        assert (
            m._check_branch(branch)
            == f"{branch} is mispelled or not a valid Army branch"
        )

    assert m._check_branch("EN") is None
