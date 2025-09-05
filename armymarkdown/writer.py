import subprocess
import os


class MemoWriter:
    def __init__(self, data):
        self.data = data
        self.lines = []

    def write(self, output_file=None):
        self.output_file = output_file

        # Use absolute path to avoid issues in containerized/Celery environments
        import os
        # Get the absolute path to the latex directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        latex_dir = os.path.join(os.path.dirname(current_dir), "latex")
        latex_class_path = os.path.join(latex_dir, "armymemo-notikz")
        
        # Use the absolute path for the documentclass
        self.lines.append(f"\\documentclass{{{latex_class_path}}}")
        self._write_admin()
        self._write_body()
        self.temp_dir = os.path.join(os.getcwd(), "assets")
        self.temp_file = os.path.join(self.temp_dir, "temp_file.tex")
        if output_file is None:
            self.output_file = self.temp_file
        with open(self.output_file, "w+") as f:
            print("\n".join(self.lines), file=f)

    def generate_memo(self):
        """Generate PDF from LaTeX file with robust error handling and timeout."""
        import logging
        import signal

        # Set up working directory (directory containing the .tex file)
        work_dir = os.path.dirname(self.output_file)
        tex_filename = os.path.basename(self.output_file)

        # LaTeX command with comprehensive flags for production reliability
        cmd = [
            "lualatex",
            "-interaction=nonstopmode",  # Never stop for user input
            "-halt-on-error",  # Stop on first error
            "-file-line-error",  # Include file and line in error messages
            "-synctex=0",  # Disable synctex for speed
            "-output-directory=.",  # Output in working directory
            tex_filename,  # Just the filename, not full path
        ]

        try:
            logging.info(f"Running LaTeX command: {' '.join(cmd)}")
            logging.info(f"Working directory: {work_dir}")
            
            # Run with timeout and capture output
            result = subprocess.run(
                cmd,
                cwd=work_dir,  # Set working directory
                timeout=60,  # 60 second timeout
                capture_output=True,  # Capture stdout/stderr
                text=True,  # Return strings not bytes
                check=False,  # Don't raise on non-zero exit
            )

            # Log the LaTeX output for debugging
            logging.info(f"LaTeX exit code: {result.returncode}")
            if result.stdout:
                logging.info(f"LaTeX STDOUT: {result.stdout}")
            if result.stderr:
                logging.info(f"LaTeX STDERR: {result.stderr}")
            
            # Check if PDF was created successfully
            pdf_path = self.output_file.replace(".tex", ".pdf")
            if not os.path.exists(pdf_path):
                error_msg = (
                    f"LaTeX compilation failed. Exit code: {result.returncode}\n"
                    f"Working directory: {work_dir}\n"
                    f"LaTeX file: {tex_filename}\n"
                    f"Expected PDF: {pdf_path}\n"
                )
                if result.stderr:
                    error_msg += f"STDERR: {result.stderr}\n"
                if result.stdout:
                    error_msg += f"STDOUT: {result.stdout}\n"
                raise Exception(error_msg)

            logging.info(f"LaTeX compilation successful: {pdf_path}")

        except subprocess.TimeoutExpired:
            raise Exception("LaTeX compilation timed out after 60 seconds")
        except Exception as e:
            logging.error(f"LaTeX compilation error: {e}")
            raise

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
                s.replace("\\\\", "\\\\\\hline")
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
