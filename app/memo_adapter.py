from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from armymemo import BodyItem, MemoDocument, Recipient, TableBlock, parse_text
from armymemo.examples import list_packaged_examples, read_packaged_example
from armymemo.exceptions import MemoParseError

EXAMPLE_DISPLAY_NAMES = {
    "tutorial.Amd": "Tutorial - Complete Guide",
    "long_memo.Amd": "Long Memorandum (Figure 2-2 from AR 25-50)",
    "basic_mfr.Amd": "Memorandum for Record",
    "basic_mfr_w_table.Amd": "Memorandum for Record with Table",
    "memo_for.Amd": "Memorandum For",
    "memo_multi_for.Amd": "Memorandum For Multiple",
    "memo_thru.Amd": "Memorandum Thru",
    "memo_extra_features.Amd": "Memorandum with Enclosures, Distros, Suspense Dates",
    "lost_cac_card.Amd": "Lost CAC Card Report",
    "additional_duty_appointment.Amd": "Additional Duty Appointment",
    "cq_sop.Amd": "Charge of Quarters Standard Operating Procedures",
    "leave_pass_policy.Amd": "Leave and Pass Policy",
    "cif_turn_in.Amd": "CIF Turn-in and Clearing Procedures",
}


class MemoFormError(ValueError):
    """Raised when web-form memo data cannot be normalized."""


@dataclass(slots=True)
class ProfileSubstitution:
    field_name: str
    value: str


def parse_memo_text(text: str) -> MemoDocument:
    try:
        return parse_text(text)
    except MemoParseError as exc:
        raise MemoFormError(str(exc)) from exc


def form_to_document(form_data: Mapping[str, str]) -> MemoDocument:
    return parse_memo_text(form_to_amd(form_data))


def form_to_amd(form_data: Mapping[str, str]) -> str:
    normalized = _normalize_form_data(form_data)
    body_text = normalized.get("MEMO_TEXT", "").strip()
    if not body_text:
        raise MemoFormError("Memo body content is required.")

    subject = normalized.get("SUBJECT", "").strip()
    if not subject:
        raise MemoFormError("Subject is required.")

    header_lines = [
        _required_assignment(normalized, "ORGANIZATION_NAME"),
        _required_assignment(normalized, "ORGANIZATION_STREET_ADDRESS"),
        _required_assignment(normalized, "ORGANIZATION_CITY_STATE_ZIP"),
        "",
        _required_assignment(normalized, "OFFICE_SYMBOL"),
        f"DATE = {_date_value(normalized)}",
        _required_assignment(normalized, "AUTHOR"),
        _required_assignment(normalized, "RANK"),
        _required_assignment(normalized, "BRANCH"),
    ]

    for optional_key in ("TITLE", "SUSPENSE", "AUTHORITY"):
        optional_value = normalized.get(optional_key, "").strip()
        if optional_value:
            header_lines.append(f"{optional_key} = {optional_value}")

    lines = list(header_lines)
    lines.extend(_recipient_assignments(normalized, "FOR"))
    lines.extend(_recipient_assignments(normalized, "THRU"))
    lines.extend(_list_assignments(normalized, "ENCLOSURE"))
    lines.extend(_list_assignments(normalized, "DISTRO"))
    lines.extend(_list_assignments(normalized, "CF"))
    lines.extend(["", f"SUBJECT = {subject}", "", body_text])
    return "\n".join(lines).rstrip() + "\n"


def document_to_form_context(document: MemoDocument) -> dict[str, object]:
    return {
        "unit_name": document.unit_name,
        "unit_street_address": document.unit_street_address,
        "unit_city_state_zip": document.unit_city_state_zip,
        "office_symbol": document.office_symbol,
        "todays_date": document.todays_date or current_army_date(),
        "subject": document.subject,
        "text": body_to_form_text(document.body),
        "author_name": document.author_name,
        "author_rank": document.author_rank,
        "author_branch": document.author_branch,
        "author_title": document.author_title,
        "suspense_date": document.suspense_date,
        "authority": document.authority,
        "enclosures": list(document.enclosures),
        "distros": list(document.distros),
        "cfs": list(document.cfs),
        "zipped_for": [
            (recipient.name, recipient.street_address, recipient.city_state_zip)
            for recipient in document.for_recipients
        ],
        "zipped_thru": [
            (recipient.name, recipient.street_address, recipient.city_state_zip)
            for recipient in document.thru_recipients
        ],
    }


def form_data_to_template_context(form_data: Mapping[str, str]) -> dict[str, object]:
    normalized = _normalize_form_data(form_data)
    return {
        "unit_name": normalized.get("ORGANIZATION_NAME", ""),
        "unit_street_address": normalized.get("ORGANIZATION_STREET_ADDRESS", ""),
        "unit_city_state_zip": normalized.get("ORGANIZATION_CITY_STATE_ZIP", ""),
        "office_symbol": normalized.get("OFFICE_SYMBOL", ""),
        "todays_date": _date_value(normalized),
        "subject": normalized.get("SUBJECT", ""),
        "text": normalized.get("MEMO_TEXT", ""),
        "author_name": normalized.get("AUTHOR", ""),
        "author_rank": normalized.get("RANK", ""),
        "author_branch": normalized.get("BRANCH", ""),
        "author_title": normalized.get("TITLE") or None,
        "suspense_date": normalized.get("SUSPENSE") or None,
        "authority": normalized.get("AUTHORITY") or None,
        "enclosures": _collect_numbered_values(normalized, "ENCLOSURE"),
        "distros": _collect_numbered_values(normalized, "DISTRO"),
        "cfs": _collect_numbered_values(normalized, "CF"),
        "zipped_for": [
            (recipient.name, recipient.street_address, recipient.city_state_zip)
            for recipient in _collect_recipients(normalized, "FOR")
        ],
        "zipped_thru": [
            (recipient.name, recipient.street_address, recipient.city_state_zip)
            for recipient in _collect_recipients(normalized, "THRU")
        ],
    }


def body_to_form_text(nodes: list[BodyItem | TableBlock], indent: int = 0) -> str:
    lines: list[str] = []
    prefix = " " * indent
    for node in nodes:
        if isinstance(node, TableBlock):
            rows = node.normalized_rows()
            if not node.headers:
                continue
            lines.append(f"{prefix}| " + " | ".join(node.headers) + " |")
            lines.append(f"{prefix}| " + " | ".join("---" for _ in node.headers) + " |")
            for row in rows:
                lines.append(f"{prefix}| " + " | ".join(row) + " |")
            lines.append("")
            continue

        if not node.paragraphs:
            continue
        lines.append(f"{prefix}- {node.paragraphs[0]}")
        for paragraph in node.paragraphs[1:]:
            lines.append(f"{prefix}{paragraph}")
        if node.children:
            child_block = body_to_form_text(node.children, indent + 4).rstrip()
            if child_block:
                lines.append(child_block)
        lines.append("")
    return "\n".join(lines).rstrip()


def example_choices() -> list[tuple[str, str]]:
    examples = [name for name in list_packaged_examples() if name.endswith(".Amd")]
    examples.sort(key=lambda name: (name != "tutorial.Amd", name))
    return [
        (
            name,
            EXAMPLE_DISPLAY_NAMES.get(
                name, name.replace(".Amd", "").replace("_", " ").title()
            ),
        )
        for name in examples
    ]


def packaged_example_names() -> set[str]:
    return {name for name, _label in example_choices()}


def read_example_text(name: str) -> str:
    return read_packaged_example(name)


def substitute_profile_fields(
    text: str, substitutions: list[ProfileSubstitution]
) -> str:
    values = {item.field_name: item.value for item in substitutions if item.value}
    if not values:
        return text

    updated_lines: list[str] = []
    for line in text.splitlines():
        if "=" not in line or line.strip().startswith("#"):
            updated_lines.append(line)
            continue
        field_name, _existing = line.split("=", 1)
        normalized_name = field_name.strip()
        replacement = values.get(normalized_name)
        if replacement is None:
            updated_lines.append(line)
            continue
        updated_lines.append(f"{normalized_name} = {replacement}")
    return "\n".join(updated_lines)


def current_army_date() -> str:
    return datetime.now().strftime("%d %B %Y")


def _normalize_form_data(form_data: Mapping[str, str]) -> dict[str, str]:
    return {
        str(key).strip(): value.strip() if isinstance(value, str) else str(value)
        for key, value in form_data.items()
    }


def _required_assignment(form_data: Mapping[str, str], key: str) -> str:
    value = form_data.get(key, "").strip()
    if not value:
        readable = key.replace("_", " ").title()
        raise MemoFormError(f"{readable} is required.")
    return f"{key} = {value}"


def _date_value(form_data: Mapping[str, str]) -> str:
    value = form_data.get("DATE", "").strip()
    return value or current_army_date()


def _recipient_assignments(form_data: Mapping[str, str], prefix: str) -> list[str]:
    recipients = _collect_recipients(form_data, prefix)
    if not recipients:
        return []

    lines = [""]
    for recipient in recipients:
        lines.extend(
            [
                f"{prefix}_ORGANIZATION_NAME = {recipient.name}",
                f"{prefix}_ORGANIZATION_STREET_ADDRESS = {recipient.street_address}",
                f"{prefix}_ORGANIZATION_CITY_STATE_ZIP = {recipient.city_state_zip}",
            ]
        )
    return lines


def _collect_recipients(form_data: Mapping[str, str], prefix: str) -> list[Recipient]:
    names = _collect_numbered_values(form_data, f"{prefix}_ORGANIZATION_NAME")
    streets = _collect_numbered_values(
        form_data, f"{prefix}_ORGANIZATION_STREET_ADDRESS"
    )
    cities = _collect_numbered_values(
        form_data, f"{prefix}_ORGANIZATION_CITY_STATE_ZIP"
    )

    recipients: list[Recipient] = []
    for index, name in enumerate(names):
        recipients.append(
            Recipient(
                name=name,
                street_address=streets[index] if index < len(streets) else "",
                city_state_zip=cities[index] if index < len(cities) else "",
            )
        )
    return recipients


def _list_assignments(form_data: Mapping[str, str], key: str) -> list[str]:
    values = _collect_numbered_values(form_data, key)
    if not values:
        return []
    return ["", *(f"{key} = {value}" for value in values)]


def _collect_numbered_values(form_data: Mapping[str, str], prefix: str) -> list[str]:
    matches: list[tuple[int, str]] = []
    for key, value in form_data.items():
        if not key.startswith(prefix):
            continue
        suffix = key[len(prefix) :].strip()
        if suffix and not suffix.isdigit():
            continue
        if not value.strip():
            continue
        order = int(suffix) if suffix.isdigit() else 0
        matches.append((order, value.strip()))
    matches.sort(key=lambda item: item[0], reverse=True)
    return [value for _order, value in matches]
