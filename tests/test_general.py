import os
import tempfile

from app.models import memo_model
from app.services import writer

# Get the directory containing this test file
TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def test_memo_model_creation():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(project_root, "tests", "template.Amd")
    m = memo_model.MemoModel.from_file(template_path)
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
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(project_root, "tests", "template.Amd")
    answer_path = os.path.join(
        project_root, "tests", "answer_test_tex_output_basic.tex"
    )

    m = memo_model.MemoModel.from_file(template_path)
    mw = writer.MemoWriter(m)

    # Use a temp file for output to avoid polluting tests directory
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as tmp:
        output_path = tmp.name

    try:
        mw.write(output_file=output_path)

        with open(output_path) as f:
            created_output = f.read()
        with open(answer_path) as f:
            answer_output = f.read()
        assert created_output == answer_output
    finally:
        # Clean up temp file
        if os.path.exists(output_path):
            os.remove(output_path)
