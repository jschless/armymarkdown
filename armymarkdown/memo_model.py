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
    # options: MFR, MEMORANDUM FOR, MEMORANDUM THRU
    todays_date: str = date.today().strftime("%d %B %Y")
    
    # optional, less frequently used parameters
    suspense_date: str = None
    document_mark: str = None
    enclosures: list = None 
    distros: list = None 
    cfs: list = None


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

inv_key_converter = {v: k for k, v in key_converter.items()}


def parse(file_name):
    # Takes a .Amd file and processes it into a memo_model
    with open(file_name, "r") as f:
        file_lines = f.readlines()

        return parse_lines(file_lines)


def parse_lines(file_lines):
    memo_dict = {}

    # remove comments and empty lines
    file_lines = [
        line for line in file_lines if len(line.strip()) > 0 and line.strip()[0] != "#"
    ]
    try:
        memo_begin_loc = [i for i, s in enumerate(file_lines) if "SUBJECT" in s][0]
    except IndexError:
        return """ERROR: missing the keyword SUBJECT. Please add SUBJECT=(your subject) above the start of your memo"""

    memo_begin_loc += 1
    for line in file_lines[:memo_begin_loc]:
        # parse all the admin info
        if "=" in line:
            key, text = line.split("=")
            try:
                memo_dict[key_converter[key.strip()]] = text.strip()
            except KeyError:
                return f"ERROR: No such keyword as {key.strip()}, please remove or fix {line}"

    master_list = []
    indent_level = 0
    for line in file_lines[memo_begin_loc:]:
        dash_location = line.find("-")
        if dash_location == -1:
            continue

        begin_line = dash_location + 1
        line_text = line[begin_line:].strip()
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
    try:
        return MemoModel(**memo_dict)
    except TypeError:
        missing_keys = set(inv_key_converter.keys()) - set(memo_dict.keys())
        for k in ["author_title", "todays_date"]:
            if k in missing_keys:
                missing_keys.remove(k)  # remove optional keys

        return f"Missing the following keys: {','.join([inv_key_converter[k] for k in missing_keys])}"
