from dataclasses import dataclass
from datetime import date


@dataclass
class MemoModel:
    unit_name: str
    unit_street_address: str
    unit_city_state_zip: str

    office_symbol: str
    subject: str

    text: list

    author_name: str
    author_rank: str
    author_branch: str
    author_title: str = None

    memo_type: str = "MEMORANDUM FOR RECORD"
    todays_date: str = date.today().strftime("%d %B %Y")


key_converter = {
    "ORGANIZATION_NAME": "unit_name",
    "ORGANIZATION_STREET_ADDRESS": "unit_street_address",
    "ORGANIZATION_CITY_STATE_ZIP": "unit_city_state_zip",
    "OFFICE_SYMBOL": "office_symbol",
    "DATE": "todays_date",
    "AUTHOR": "author_name",
    "RANK": "author_rank",
    "BRANCH": "author_branch",
    "TITLE": "author_title",
    "MEMO_TYPE": "memo_type",
    "SUBJECT": "subject",
}


def parse(file_name):
    # Takes a .Amd file and processes it into a memo_model
    with open(file_name, "r") as f:
        memo_dict = {}
        file_lines = f.readlines()

        memo_begin_loc = [i for i, s in enumerate(file_lines) if "SUBJECT" in s][0] + 1

        for line in file_lines[:memo_begin_loc]:
            # parse all the admin info
            if "=" in line:
                key, text = line.split("=")
                memo_dict[key_converter[key]] = text.strip()

        master_list = []
        indent_level = 0
        for line in file_lines[memo_begin_loc:]:
            dash_location = line.find("-")
            if dash_location == -1:
                continue

            line_text = line[dash_location + 1 :].strip()
            proper_indent_level = master_list  # level 0

            for i in range(dash_location // 4):
                if isinstance(proper_indent_level[-1], list):
                    proper_indent_level = proper_indent_level[-1]

            if dash_location > indent_level:
                proper_indent_level.append([line_text])
            elif dash_location <= indent_level:
                proper_indent_level.append(line_text)
            indent_level = dash_location

        memo_dict["text"] = master_list
        return MemoModel(**memo_dict)
