import subprocess
import os

from . import memo_model


class MemoWriter:
    def __init__(self, data: memo_model.MemoModel):
        self.data = data
        self.lines = []

    def write(self, output_file=None):
        self.output_file = output_file

        self.lines.append("\\documentclass{armymemo}")
        self._write_admin()
        self._write_body()
        self.temp_dir = os.path.join(os.getcwd(), "assets")
        self.temp_file = os.path.join(self.temp_dir, "temp_file.tex")
        if output_file is None:
            self.output_file = self.temp_file
        with open(self.output_file, "w+") as f:
            print("\n".join(self.lines), file=f)

    def generate_memo(self):
        subprocess.run(
            [
                "latexmk",
                "-quiet",
                "-lualatex",
                self.output_file,
            ]
        )

    def _write_memo_line(self):
        if self.data.memo_type == "MEMORANDUM FOR RECORD":
            return "MEMORANDUM FOR RECORD"
        elif self.data.memo_type == "MEMORANDUM FOR":
            assert (  # must have the same number of units
                len(self.data.for_unit_city_state_zip)
                == len(self.data.for_unit_name)
                == len(self.data.for_unit_street_address)
            )
            if len(self.data.for_unit_city_state_zip) == 1:
                ans = "MEMORANDUM FOR "
                ans += self.data.for_unit_name[0]
                ans += ", " + self.data.for_unit_street_address[0]
                ans += ", " + self.data.for_unit_city_state_zip[0]
                return ans
            else:
                raise NotImplementedError("Need to do multiple fors")

                for name, add, csz in zip(
                    self.data.for_unit_name,
                    self.data.for_unit_street_address,
                    self.data.for_unit_city_state_zip,
                ):
                    ans += f"{name}, {add}, {csz}\\\\"
                return ans
        elif self.data.memo_type == "MEMORANDUM THRU":
            ans = "FOR "
            ans += self.data.for_unit_name[0]
            ans += ", " + self.data.for_unit_street_address[0]
            ans += ", " + self.data.for_unit_city_state_zip[0]
            return ans

    def _write_thru_lines(self) -> list:
        ans = []
        for name, add, csz in zip(
            self.data.thru_unit_name,
            self.data.thru_unit_street_address,
            self.data.thru_unit_city_state_zip,
        ):
            ans.append(f"\\multimemothru{{{name}, {add}, {csz}}}")
        return ans

    def _write_admin(self):
        self.lines.append(f"\\address{{{self.data.unit_name}}}")
        self.lines.append(f"\\address{{{self.data.unit_street_address}}}")
        self.lines.append(f"\\address{{{self.data.unit_city_state_zip}}}")

        temp_str = f"\\author{{{self.data.author_name}}}"
        temp_str += f"\\rank{{{self.data.author_rank}}}"
        temp_str += f"\\branch{{{self.data.author_branch}}}"
        self.lines.append(temp_str)

        self.lines.append(f"\\officesymbol{{{self.data.office_symbol}}}")
        self.lines.append(f"\\signaturedate{{{self.data.todays_date}}}")

        if self.data.memo_type == "MEMORANDUM THRU":
            self.lines += self._write_thru_lines()
        self.lines.append(f"\\memoline{{{self._write_memo_line()}}}")

        self.lines.append(f"\\subject{{{self.data.subject}}}")
        if self.data.author_title is not None:
            self.lines.append(f"\\title{{{self.data.author_title}}}")

    def _write_body(self):
        self.lines.append("\\begin{document}")
        self.lines.append("\\begin{enumerate}")
        self._iterate_lols(self.data.text)
        self.lines.append("\\end{enumerate}")
        self.lines.append("\\end{document}")

    def _iterate_lols(self, lol):
        for i in lol:
            if isinstance(i, list):
                self.lines.append("\\begin{enumerate}")
                self._iterate_lols(i)
                self.lines.append("\\end{enumerate}")
            else:
                self.lines.append("\\item " + i)
