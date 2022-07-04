from dataclasses import dataclass
from datetime import date
import re

from armymarkdown.utils import branch_to_abbrev, abbrev_to_branch
from armymarkdown.utils import (
    key_converter,
    inv_key_converter,
    list_keys,
    optional_keys,
)


def flatten(x):
    if isinstance(x, list):
        return [a for i in x for a in flatten(i)]
    else:
        return [x]


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
    for_unit_name: list = None
    for_unit_street_address: list = None
    for_unit_city_state_zip: list = None

    thru_unit_name: list = None
    thru_unit_street_address: list = None
    thru_unit_city_state_zip: list = None

    suspense_date: str = None
    document_mark: str = None
    enclosures: list = None
    distros: list = None
    cfs: list = None
    document_mark: str = None

    def language_check(self):
        return self._check_admin()

    def _check_date(self, date_str):
        # form 08 May 2022
        date_pattern = re.compile("\d\d [A-Z][a-z]+ \d\d\d\d")
        if date_pattern.match(date_str) is None:
            return (
                f"The entered date {date_str} does not conform to pattern"
                " ## Month ####"
            )

    def _check_branch(self, branch):
        if (
            branch not in abbrev_to_branch.keys()
            and branch not in branch_to_abbrev.keys()
        ):
            return f"{branch} is mispelled or not a valid Army branch"

    def _check_admin(self):
        # TODO validate the format of each attribute with REGEX

        errors = []
        errors.append(("DATE", self._check_date(self.todays_date)))
        if self.suspense_date is not None:
            errors.append(
                ("SUSPENSE_DATE", self._check_date(self.suspense_date))
            )

        return [e for e in errors if e[1] is not None]

    def _check_body(self):
        return []


def parse(file_name):
    # Takes a .Amd file and processes it into a memo_model
    with open(file_name, "r") as f:
        file_lines = f.readlines()

    return parse_lines(file_lines)


def add_latex_escape_chars(s):
    special_chars = {
        "~": "\\textasciitilde ",
        "^": "\\textasciicircum",
        "\\": "\\textbackslash",
    }
    normal_chars = ["&", "%", "$", "#", "_", "{", "}"]

    for c, r in special_chars.items():
        s = s.replace(c, r)

    for c in normal_chars:
        s = s.replace(c, f"\\{c}")

    return s


def parse_lines(file_lines):
    # processes a text block into a latex memo_model
    memo_dict = {}

    # remove comments and empty lines

    file_lines = list(
        filter(  # remove comments and blank lines
            lambda line: len(line.strip()) > 0 and line.strip()[0] != "#",
            file_lines,
        )
    )

    try:
        memo_begin_loc = [
            i for i, s in enumerate(file_lines) if "SUBJECT" in s
        ][0]
    except IndexError:
        return (
            "ERROR: missing the keyword SUBJECT. "
            "Please add SUBJECT=(your subject) above the start of your memo"
        )

    memo_begin_loc += 1  # advance to next line after SUBJECT
    for line in file_lines[:memo_begin_loc]:
        # parse all the admin info
        if "=" in line:
            key, text = line.split("=")

            if key.strip() not in key_converter:
                return (
                    f"ERROR: No such keyword as {key.strip()}, "
                    "please remove or fix {line}"
                )
                return

            processed_text = add_latex_escape_chars(text.strip())
            if key_converter[key.strip()] in list_keys:
                temp = memo_dict.get(key_converter[key.strip()], [])
                temp.append(processed_text)
                memo_dict[key_converter[key.strip()]] = temp
            else:
                memo_dict[key_converter[key.strip()]] = processed_text

    master_list = []
    indent_level = 0
    for line in file_lines[memo_begin_loc:]:
        dash_location = line.find("-")
        if dash_location == -1:
            continue

        begin_line = dash_location + 1
        line_text = add_latex_escape_chars(line[begin_line:].strip())
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
    except TypeError as e:
        print(e)
        missing_keys = set(inv_key_converter.keys()) - set(memo_dict.keys())
        for k in optional_keys:
            if k in missing_keys:
                missing_keys.remove(k)  # remove optional keys

        return (
            f"Missing the following keys: "
            f"{','.join([inv_key_converter[k] for k in missing_keys])}"
        )
