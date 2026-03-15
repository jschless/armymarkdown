from armymemo import parse_text

from app.memo_adapter import (
    MemoFormError,
    document_to_form_context,
    form_data_to_template_context,
    form_to_amd,
    form_to_document,
)


def test_form_to_amd_roundtrip(sample_form_data):
    amd_text = form_to_amd(sample_form_data)

    document = parse_text(amd_text)

    assert document.subject == sample_form_data["SUBJECT"]
    assert document.author_name == sample_form_data["AUTHOR"]
    assert document.body[0].text == "This is a test memo."


def test_form_to_amd_preserves_descending_address_order(sample_form_data):
    sample_form_data.update(
        {
            "FOR_ORGANIZATION_NAME1": "Lower Address",
            "FOR_ORGANIZATION_STREET_ADDRESS1": "1 Main St",
            "FOR_ORGANIZATION_CITY_STATE_ZIP1": "Town, ST 11111",
            "FOR_ORGANIZATION_NAME2": "Upper Address",
            "FOR_ORGANIZATION_STREET_ADDRESS2": "2 Main St",
            "FOR_ORGANIZATION_CITY_STATE_ZIP2": "Town, ST 22222",
        }
    )

    document = form_to_document(sample_form_data)

    assert [recipient.name for recipient in document.for_recipients] == [
        "Upper Address",
        "Lower Address",
    ]


def test_document_to_form_context_roundtrip(sample_memo_text):
    context = document_to_form_context(parse_text(sample_memo_text))

    assert context["subject"] == "Test Memo Subject"
    assert "First sub-item" in context["text"]
    assert context["author_branch"] == "EN"


def test_form_data_to_template_context_keeps_partial_values():
    context = form_data_to_template_context(
        {
            "ORGANIZATION_NAME": "Test Unit",
            "SUBJECT": "Partial Subject",
            "MEMO_TEXT": "- Draft body",
            "FOR_ORGANIZATION_NAME2": "Higher",
            "FOR_ORGANIZATION_NAME1": "Lower",
        }
    )

    assert context["unit_name"] == "Test Unit"
    assert context["subject"] == "Partial Subject"
    assert context["zipped_for"][0][0] == "Higher"


def test_form_to_amd_requires_subject(sample_form_data):
    sample_form_data["SUBJECT"] = " "

    try:
        form_to_amd(sample_form_data)
    except MemoFormError as exc:
        assert "Subject is required" in str(exc)
    else:
        raise AssertionError("Expected MemoFormError for missing subject")
