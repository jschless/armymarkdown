from dataclasses import dataclass, fields
from datetime import date
from io import StringIO
import re

import pandas as pd
from tabulate import tabulate

from armymarkdown.utils import (
    abbrev_to_branch,
    branch_to_abbrev,
    inv_key_converter,
    key_converter,
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
    authority: str = None

    def language_check(self):
        return self._check_admin()

    def _check_date(self, date_str):
        # form 08 May 2022 - full month names only, no abbreviations
        valid_months = r"January|February|March|April|May|June|July|August|September|October|November|December"
        date_pattern = re.compile(rf"\d\d ({valid_months}) \d\d\d\d")
        if date_pattern.match(date_str) is None:
            return (
                f"The entered date {date_str} does not conform to pattern ## Month ####"
            )

    def _check_branch(self, branch):
        if branch not in abbrev_to_branch and branch not in branch_to_abbrev:
            return f"{branch} is mispelled or not a valid Army branch"

    def _check_admin(self):
        # TODO validate the format of each attribute with REGEX

        errors = []
        errors.append(("DATE", self._check_date(self.todays_date)))
        if self.suspense_date is not None:
            errors.append(("SUSPENSE_DATE", self._check_date(self.suspense_date)))

        return [e for e in errors if e[1] is not None]

    def _check_body(self):
        return []

    def to_dict(self):
        return {field.name: getattr(self, field.name) for field in fields(self)}

    def to_form(self):
        form_dict = {
            field.name: getattr(self, field.name)
            for field in fields(self)
            if field.name not in list_keys
        }
        form_dict["text"] = nested_list_to_string(form_dict["text"])

        if self.for_unit_name is not None:
            form_dict["zipped_for"] = list(
                zip(
                    self.for_unit_name,
                    self.for_unit_street_address,
                    self.for_unit_city_state_zip,
                    strict=False,
                )
            )

        if self.thru_unit_name is not None:
            form_dict["zipped_thru"] = list(
                zip(
                    self.thru_unit_name,
                    self.thru_unit_street_address,
                    self.thru_unit_city_state_zip,
                    strict=False,
                )
            )

        form_dict["enclosures"] = self.enclosures
        form_dict["distros"] = self.distros
        form_dict["cfs"] = self.cfs

        return form_dict

    def to_amd(self):
        str_builder = ""
        fields(self)
        for write_key, attrib in [
            ("ORGANIZATION_NAME", "unit_name"),
            ("ORGANIZATION_STREET_ADDRESS", "unit_street_address"),
            ("ORGANIZATION_CITY_STATE_ZIP", "unit_city_state_zip"),
            ("OFFICE_SYMBOL", "office_symbol"),
            ("DATE", "todays_date"),
            ("AUTHOR", "author_name"),
            ("RANK", "author_rank"),
            ("BRANCH", "author_branch"),
            ("TITLE", "author_title"),
            ("SUSPENSE", "suspense_date"),
            ("AUTHORITY", "authority"),
        ]:
            if getattr(self, attrib, None):
                str_builder += f"{write_key} = {getattr(self, attrib)}\n"

        if getattr(self, "for_unit_name", None):
            for a, b, c in zip(
                self.for_unit_name,
                self.for_unit_street_address,
                self.for_unit_city_state_zip,
                strict=False,
            ):
                str_builder += "\n"
                str_builder += f"FOR_ORGANIZATION_NAME = {a}\n"
                str_builder += f"FOR_ORGANIZATION_STREET_ADDRESS = {b}\n"
                str_builder += f"FOR_ORGANIZATION_CITY_STATE_ZIP = {c}\n"

        if getattr(self, "thru_unit_name", None):
            for a, b, c in zip(
                self.thru_unit_name,
                self.thru_unit_street_address,
                self.thru_unit_city_state_zip,
                strict=False,
            ):
                str_builder += "\n"
                str_builder += f"THRU_ORGANIZATION_NAME = {a}\n"
                str_builder += f"THRU_ORGANIZATION_STREET_ADDRESS = {b}\n"
                str_builder += f"THRU_ORGANIZATION_CITY_STATE_ZIP = {c}\n"

        for write_key, attrib in [
            ("ENCLOSURE", "enclosures"),
            ("DISTRO", "distros"),
            ("CF", "cfs"),
        ]:
            if getattr(self, attrib, None):
                str_builder += "\n"
                for v in getattr(self, attrib):
                    str_builder += f"{write_key} = {v}\n"

        str_builder += "\n"
        str_builder += f"SUBJECT = {remove_latex_escape_chars(self.subject)}\n\n"
        str_builder += f"{nested_list_to_string(self.text)}"

        return str_builder

    @classmethod
    def from_dict(cls, memo_dict):
        # creates the class given a dictionary of keys

        # deduce memo type based on arguments
        if "thru_unit_name" in memo_dict:
            memo_dict["memo_type"] = "MEMORANDUM THRU"
        elif "for_unit_name" in memo_dict:
            memo_dict["memo_type"] = "MEMORANDUM FOR"
        else:
            memo_dict["memo_type"] = "MEMORANDUM FOR RECORD"

        try:
            return cls(**memo_dict)
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

    @classmethod
    def from_form(cls, form_dict):
        memo_dict = {
            key_converter[k]: v for k, v in form_dict.items() if k in key_converter
        }
        memo_dict["text"] = parse_memo_body(
            list(
                filter(  # remove comments and blank lines
                    lambda line: len(line.strip()) > 0 and line.strip()[0] != "#",
                    form_dict["MEMO_TEXT"].split("\n"),
                )
            )
        )
        # If there are list keys in form_dict, they will be of the form list_key1, list_key2, list_key3
        # So, let's check each list_key to see if it is in there...

        r_key_converter = {v: k for k, v in key_converter.items()}

        for key in [r_key_converter[key] for key in list_keys]:
            val = []
            for i in range(7, 0, -1):
                if key + str(i) in form_dict:
                    val.append(form_dict[key + str(i)])

            if len(val) > 0:
                memo_dict[key_converter[key]] = val

        return MemoModel.from_dict(memo_dict)

    @classmethod
    def from_file(cls, filepath):
        with open(filepath) as f:
            file_lines = f.readlines()

        return parse_lines(file_lines)

    @classmethod
    def from_text(cls, text):
        return parse_lines(text.split("\n"))


def parse_memo_body(lines):
    master_list = []
    cur_indent = 0
    indent_levels = set()
    table = []
    for line in lines:
        dash_loc = line.find("-")
        if (dash_loc == -1 or line.count("-") > 1) and line.count("|") > 1:
            table.append(line)
            continue
        elif dash_loc == -1:
            # not a table and not a new line, so it's a new paragraph within same item
            cur_list = master_list
            # Only process if there are existing items to append to
            if cur_list:
                while len(cur_list) > 0 and isinstance(cur_list[-1], list):
                    cur_list = cur_list[-1]
                if cur_list:  # Make sure cur_list still has items
                    cur_list[-1] += "\n\n" + add_latex_escape_chars(line.strip())
            continue
        if table != [] and line.count("|") < 2:
            master_list.append(process_table(table))
            table = []

        begin_line = dash_loc + 1
        indent_levels.add(dash_loc)

        line_text = add_latex_escape_chars(line[begin_line:].strip())
        proper_indent_level = master_list  # start at level 0

        for _i in list(filter(lambda x: x < dash_loc, sorted(indent_levels))):
            if isinstance(proper_indent_level[-1], list):
                proper_indent_level = proper_indent_level[-1]

        if dash_loc > cur_indent:
            proper_indent_level.append([line_text])
        elif dash_loc <= cur_indent:
            proper_indent_level.append(line_text)
        cur_indent = dash_loc

    return master_list


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
        memo_begin_loc = next(i for i, s in enumerate(file_lines) if "SUBJECT" in s)
    except StopIteration:
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

            processed_text = add_latex_escape_chars(text.strip())
            if key_converter[key.strip()] in list_keys:
                memo_dict[key_converter[key.strip()]] = [
                    *memo_dict.get(key_converter[key.strip()], []),
                    processed_text,
                ]

            else:
                memo_dict[key_converter[key.strip()]] = processed_text

    memo_dict["text"] = parse_memo_body(file_lines[memo_begin_loc:])
    return MemoModel.from_dict(memo_dict)


def nested_list_to_string(lst, indent=0):
    result = ""
    for item in lst:
        if isinstance(item, list):
            result += nested_list_to_string(item, indent + 4)
        else:
            result += (
                " " * indent + "- " + remove_latex_escape_chars(str(item)) + "\n\n"
            )
    return result


def add_latex_escape_chars(s):
    # Process backslash first to avoid interfering with other escape sequences
    s = s.replace("\\", "\\textbackslash")

    special_chars = {
        "~": "\\textasciitilde ",
        "^": "\\textasciicircum",
    }
    normal_chars = ["&", "%", "$", "#", "_", "{", "}"]

    for c, r in special_chars.items():
        s = s.replace(c, r)

    for c in normal_chars:
        s = s.replace(c, f"\\{c}")

    underline_regex = re.compile(r"\*\*\*(.*?)\*\*\*")
    bold_regex = re.compile(r"\*\*(.*?)\*\*")
    italics_regex = re.compile(r"\*(.*?)\*")
    s = re.sub(underline_regex, r"\\underline{\1}", s)
    s = re.sub(bold_regex, r"\\textbf{\1}", s)
    s = re.sub(italics_regex, r"\\textit{\1}", s)

    return s


def remove_latex_escape_chars(s):
    special_chars = {
        "\\textasciitilde ": "~",
        "\\textasciicircum": "^",
        "\\textbackslash": "\\",
    }
    normal_chars = ["&", "%", "$", "#", "_", "{", "}"]

    for r, c in special_chars.items():
        s = s.replace(r, c)

    for c in normal_chars:
        s = s.replace(f"\\{c}", c)

    underline_regex = re.compile(r"\\underline{(.*?)}")
    bold_regex = re.compile(r"\\textbf{(.*?)}")
    italics_regex = re.compile(r"\\textit{(.*?)}")
    s = re.sub(underline_regex, r"***\1***", s)
    s = re.sub(bold_regex, r"**\1**", s)
    s = re.sub(italics_regex, r"*\1*", s)

    return s


def process_table(line_list):
    table_str = "\n".join(line_list)
    try:
        table = (
            pd.read_table(
                StringIO(table_str),
                sep="|",
                header=0,
                index_col=1,
                skipinitialspace=True,
            )
            .dropna(axis=1, how="all")
            .iloc[1:]
        )
        return tabulate(table, table.columns, tablefmt="latex")
    except Exception:
        return ""
