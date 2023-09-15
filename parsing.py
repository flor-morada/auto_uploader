"""
FILE: parsing.py
AUTHOR: Jordan Rodriguez (jerodriguez@arizona.edu)

DESCRIPTION:
    Module containing the parsing logic for aup files.

FUNCTION:
    `parse_file(filename: str) -> dict[str, list[RuleChecker]]`

USAGE:
    python3 parsing.py

    When run as a script, prompts to enter a `.aup` file and prints resulting rules.
"""


from icecream import ic

from rules import FunctionRule, MethodRule, NodeRule, RuleChecker, RuleType


def parse_file(filename: str) -> dict[str, list[RuleChecker]]:
    """
    Parses `filename`, a .aup file. 
    Returns a dictionary mapping each problem name to the list of RuleChecker 
    corresponding to the problem, as outlined in the aup file. 
    """
    rules = {}
    cur_problem = "universal"
    rules[cur_problem] = []
    for line in open(filename):
        match line.split():
            case [] | ["#", *_]:
                continue
            case ["problem", problem_name]:
                cur_problem = problem_name
                if cur_problem not in rules:
                    rules[cur_problem] = []
            case ["require", "node", node_name]:
                rules[cur_problem].append(NodeRule(RuleType.REQUIRE, node_name))
            case ["ban", "node", node_name]:
                rules[cur_problem].append(NodeRule(RuleType.BAN, node_name))
            case ["require", "function", function_name]:
                rules[cur_problem].append(FunctionRule(RuleType.REQUIRE, function_name))
            case ["ban", "function", function_name]:
                rules[cur_problem].append(FunctionRule(RuleType.BAN, function_name))
            case ["require", "method", method_name]:
                rules[cur_problem].append(MethodRule(RuleType.REQUIRE, method_name))
            case ["ban", "method", method_name]:
                rules[cur_problem].append(MethodRule(RuleType.BAN, method_name))
            case _:
                print(f"UNKNOWN line found: {line}")

    return rules


def main():
    filename = input("enter filename to parse: ")
    rules = parse_file(filename)
    ic(rules)


if __name__ == "__main__":
    main()
