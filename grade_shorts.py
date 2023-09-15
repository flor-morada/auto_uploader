"""
FILE: grade_shorts.py
AUTHOR: Jordan Rodriguez (jerodriguez@arizona.edu)

DESCRIPTION:
    Main file to process autograded shorts using .aup files to outline rules. 
    For a full explanation, refer to README.md.

USAGE:
    python3 grade_shorts.py [DIRECTORY]

    The script looks inside the specified `DIRECTORY` to find a CSV file, 
    an AUP file, and a directory containing student code.

    Dependent on `YEARLY_CONFIG` pointing to a JSON file containing "names_map"
    and "ignored_ids" attributes.

OUTPUTS:
    - PDF Template: `[DIRECTORY]/gradescope_template.pdf`
    - Full PDF: `[DIRECTORY]/gradescope_output.pdf`
"""


import json
import os
import sys

import pandas as pd
from fpdf import FPDF

from parsing import parse_file
from rules import RuleChecker, RuleViolation, find_violations, print_violations

YEARLY_CONFIG = "2023-24_config.json"
# ANSI escape codes
GREEN = "\033[92m"
BOLD = "\033[1m"
RESET = "\033[0m"


def create_template_pdf(
    scores: pd.DataFrame, problem_list: list[str], filename: str
) -> None:
    """
    Given the `scores` df and the `problem_list` in desired order, outputs
    a template pdf to `filename`.
    """
    template = FPDF()
    template.set_font("Courier", size=10)

    template.add_page()
    template.set_text_color(0, 0, 0)
    template.cell(200, 20, txt="NAME:", ln=1, align="L")
    template.cell(200, 20, txt="NETID:", ln=2, align="L")
    template.line(10, 50, 200, 50)
    template.line(10, 10, 200, 10)

    for problem in problem_list:
        max_points = scores[f"{problem} cases"].iloc[0]
        template.add_page()
        score_line = f"{problem} score:   / {max_points} |  XXXXXXXX"
        template.cell(10, 10, txt=score_line, ln=1, align="L")

    template.output(filename)


def find_all_violations(
    scores: pd.DataFrame, rules: dict[str, list[RuleChecker]], code_dir: str
) -> dict[str, dict[str, list[RuleViolation]]]:
    """
    Iterates through student code in the `code_dir` to find violations of the `rules`.
    `rules` maps problem names to a list of RuleCheckers, each called to visit the
    syntax tree and return any violations.

    Updates `scores` to reflect 0 points for any questions with violated rules.

    Returns a dict containing the rule violations for each student:
        {NETID -> {PROBLEM -> list[RuleViolation]}}
    """
    violations = {}
    files = os.walk(code_dir)
    next(files)  # skip over the folder itself
    for netid_folder, _, assignments in files:
        netid = os.path.basename(netid_folder)

        for problem_file in sorted(assignments):
            problem_name = problem_file.removesuffix(".py")
            problem_rules = rules["universal"] + rules[problem_name]
            problem_filepath = os.path.join(netid_folder, problem_file)

            problem_violations = find_violations(problem_filepath, problem_rules)
            violations.setdefault(netid, {})
            violations[netid][problem_name] = problem_violations

            if len(problem_violations) != 0:
                print(f"VIOLATION FOUND IN {problem_file} FOR {netid}")
                print_violations(problem_violations, problem_filepath)
                print()
                # If any violations found, score is 0
                scores.at[netid, f"{problem_name} passed"] = 0

    return violations


def add_code_to_pdf(pdf: FPDF, code_file: str, violations: list[RuleViolation]) -> None:
    """
    Adds the lines in `code_file` to `pdf`; any lines in `violations` highlighted red.
    """
    lines = open(code_file).readlines()

    violation_lines = [v.line for v in violations]
    for i, line in enumerate(lines[:28], 1):
        if i in violation_lines:
            pdf.set_text_color(255, 0, 0)
        else:
            pdf.set_text_color(0, 0, 0)
        pdf.cell(400, 6, txt=f"{i:2}| {line}", ln=i, align="L")

    pdf.set_text_color(255, 0, 0)
    for i, v in enumerate(violations, 28):
        pdf.cell(400, 6, txt=str(v), ln=i, align="L")


def create_score_pdf(
    scores: pd.DataFrame,
    problem_list: list[str],
    violations: dict[str, dict[str, list[RuleViolation]]],
    code_dir: str,
    ignore_ids: set[str],
    name_map: dict[str, str],
    filename: str,
) -> None:
    """
    Outputs a pdf containing the scores for each student in the `scores`. Includes
    the problems in the order of `problem_list`, and includes code from the `code_dir`.
    Uses `violations` to highlight in red lines where students violated rules.

    Ignores any netids in `ignore_ids`, and uses names in the `name_map` where applicable.

    Outputs to `filename`.
    """
    pdf = FPDF()
    pdf.set_font("Courier", size=10)

    for netid, row in scores.iterrows():
        if netid in ignore_ids:
            continue

        if netid in name_map:
            name = name_map[netid]
        else:
            name = f"{row['Firstname']} {row['Lastname']}"

        pdf.add_page()
        pdf.set_text_color(0, 0, 0)
        pdf.cell(200, 20, txt=f"NAME: {name}", ln=1, align="L")
        pdf.cell(200, 20, txt=f"NETID: {netid}", ln=2, align="L")
        pdf.line(10, 50, 200, 50)
        pdf.line(10, 10, 200, 10)

        for problem in problem_list:
            pdf.set_text_color(0, 0, 0)
            pdf.add_page()

            points = row[f"{problem} passed"]
            max_points = row[f"{problem} cases"]
            score_line = f"{problem} score: {points} / {max_points} |  {netid}"
            pdf.cell(10, 10, txt=score_line, ln=1, align="L")
            codefile = os.path.join(code_dir, netid, problem + ".py")
            if os.path.exists(codefile):
                problem_violations = violations[netid][problem]
                add_code_to_pdf(pdf, codefile, problem_violations)

    pdf.output(filename)


def get_args(args: list[str]) -> tuple[str, str, str, str]:
    """
    Searches through the `directory` given by args[1] to find a csv, code
    directory, and aup

    Returns: directory, csv, code_directory, aup
    """
    if len(args) != 2:
        print("Error: please give a directory which contains aup, csv, and code dir")
        sys.exit(1)
    _, folder = args

    csv_file, aup_file, code_dir = None, None, None
    for elem in os.listdir(folder):
        path = os.path.join(folder, elem)
        if path.endswith(".csv"):
            csv_file = path
        elif path.endswith(".aup"):
            aup_file = path
        elif os.path.isdir(path):
            code_dir = path

    if not csv_file:
        print("Error: missing csv file in given directory")
        sys.exit(1)
    if not aup_file:
        print("Error: missing aup file in given directory")
        sys.exit(1)
    if not code_dir:
        print("Error: missing code directory in given directory")
        sys.exit(1)

    return folder, csv_file, code_dir, aup_file


def get_config(filename: str) -> tuple[dict[str, str], set[str]]:
    """Reads config json and returns name_map and ignored_ids as a dict and set"""
    if not os.path.exists(filename):
        print(f"Error: `{YEARLY_CONFIG}` does not exist. proceeding without.")
        return {}, set()

    with open(filename, "r") as file:
        config = json.load(file)

    name_map = config["name_map"]
    ignored_ids = set(config["ignored_ids"])

    return name_map, ignored_ids


def main():
    input_dir, csv_file, code_dir, aup_file = get_args(sys.argv)

    name_map, ignored_ids = get_config(YEARLY_CONFIG)

    rules = parse_file(aup_file)
    problem_list = sorted(rules.keys())
    problem_list.remove("universal")
    scores_df = pd.read_csv(csv_file).set_index("netid")

    template_output = os.path.join(input_dir, "gradescope_template.pdf")
    full_pdf_output = os.path.join(input_dir, "gradescope_output.pdf")

    create_template_pdf(scores_df, problem_list, template_output)
    violations = find_all_violations(scores_df, rules, code_dir)
    create_score_pdf(
        scores_df,
        problem_list,
        violations,
        code_dir,
        ignored_ids,
        name_map,
        full_pdf_output,
    )

    print(f"{GREEN}{BOLD}template PDF saved to `{template_output}`")
    print(f"output PDF saved to `{full_pdf_output}`{RESET}")


if __name__ == "__main__":
    main()
