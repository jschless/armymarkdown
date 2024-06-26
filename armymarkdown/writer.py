import subprocess
import os


class MemoWriter:
    def __init__(self, data):
        self.data = data
        self.lines = []

    def write(self, output_file=None):
        self.output_file = output_file

        self.lines.append("\\documentclass{./latex/armymemo-notikz}")
        self._write_admin()
        self._write_body()
        self.temp_dir = os.path.join(os.getcwd(), "assets")
        self.temp_file = os.path.join(self.temp_dir, "temp_file.tex")
        if output_file is None:
            self.output_file = self.temp_file
        with open(self.output_file, "w+") as f:
            print("\n".join(self.lines), file=f)

    def generate_memo(self):
        subprocess.run(["lualatex", self.output_file])

    def _write_for_lines(self) -> list:
        ans = []
        if self.data.memo_type == "MEMORANDUM FOR RECORD":
            ans.append("\\memoline{{MEMORANDUM FOR RECORD}}")
        else:
            prefix = "MEMORANDUM FOR" if self.data.thru_unit_name is None else "FOR"

            for name, add, csz in zip(
                self.data.for_unit_name,
                self.data.for_unit_street_address,
                self.data.for_unit_city_state_zip,
            ):
                if len(self.data.for_unit_name) == 1:
                    ans.append(f"\\memoline{{{prefix} {name}, {add}, {csz}}}")
                    return ans
                ans.append(f"\\multimemofor{{{name}, {add}, {csz}}}")
        return ans

    def _write_thru_lines(self) -> list:
        ans = []
        for name, add, csz in zip(
            self.data.thru_unit_name,
            self.data.thru_unit_street_address,
            self.data.thru_unit_city_state_zip,
        ):
            if len(self.data.thru_unit_name) == 1:
                ans.append(f"\\addmemoline{{MEMORANDUM THRU {name}, {add}, {csz} }}")
                return ans

            ans.append(f"\\multimemothru{{{name}, {add}, {csz}}}")
        return ans

    def _add_opt_strings(self):
        ans = []
        for name, val in [
            ("authority", self.data.authority),
            ("title", self.data.author_title),
            # ("documentmark", self.data.document_mark),
            ("suspensedate", self.data.suspense_date),
        ]:
            if val is not None:
                ans.append(f"\\{name}{{{val}}}")

        return ans

    def _add_opt_lists(self):
        ans = []
        for name, val in [
            ("encl", self.data.enclosures),
            ("distro", self.data.distros),
            ("cf", self.data.cfs),
        ]:
            if val is not None:
                for v in val:
                    ans.append(f"\\add{name}{{{v}}}")
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
        self.lines.append(f"\\subject{{{self.data.subject}}}")

        if self.data.memo_type == "MEMORANDUM THRU":
            self.lines += self._write_thru_lines()

        self.lines += self._write_for_lines()

        # OPTIONAL LINES
        self.lines += self._add_opt_lists()

        self.lines += self._add_opt_strings()

    def _write_body(self):
        self.lines.append("\\begin{document}")
        self.lines.append("\\begin{enumerate}")
        self._iterate_lols(self.data.text)
        self.lines.append("\\end{enumerate}")
        self.lines.append("\\end{document}")

    def _process_table(self, a):
        # need to add hlines and vertical lines
        s1 = a.find("tabular") + 9
        s2 = a.find("}", s1)
        new_a = a.replace(a[s1:s2], "".join(["|" + c for c in a[s1:s2]]) + "|")
        s3 = 4  # start after the header, which will be index 5
        s4 = -3  # end before the bottom rule
        return "\n".join(
            [
                s.replace("\\\\", "\\\\\hline")
                if i >= s3 and i < len(new_a.split("\n")) + s4
                else s
                for i, s in enumerate(new_a.split("\n"))
            ]
        )

    def _iterate_lols(self, lol):
        for i in lol:
            if isinstance(i, list):
                self.lines.append("\\begin{enumerate}")
                self._iterate_lols(i)
                self.lines.append("\\end{enumerate}")
            else:
                if "tabular" in i:
                    self.lines += [
                        "",
                        "",
                        "\\begin{center}",
                        self._process_table(i),
                        "\\end{center}",
                    ]
                else:
                    self.lines.append("\\item " + i)
