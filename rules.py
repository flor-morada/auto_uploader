"""
FILE: rules.py
AUTHOR: Jordan Rodriguez (jerodriguez@arizona.edu)

DESCRIPTION: 
    Module with RuleCheckers for various syntax rules, and functions to check
    rules and print output.

CLASSES:
    - `RuleType(Enum)`: RuleType.BAN and RuleType.REQUIRE.
    - `RuleViolation`: dataclass with (rule: str, line: Optional[int])
    - `RuleChecker(ast.NodeVisitor)`: Keeps track of a syntax rule by visiting AST
        - `NodeRule(RuleChecker)`: Keeps track of a type of AST node.
        - `FunctionRule(RuleChecker)`: For a particular function call.
        - `MethodRule(RuleChecker)`: For a particular method call.

FUNCTIONS:
    - `get_violations(code: str, rules: list[RuleChecker]) -> list[RuleViolation]`
    - `print_violations(violations: list[RuleViolation], filename: str)`

USAGE:
    python3 rules.py

    When run as a script, prompts to enter a filename, and checks that file 
    with the list of examples RuleCheckers in main, printing results.
"""


import ast
from enum import Enum
from typing import Optional
from dataclasses import dataclass

from icecream import ic

# ANSI escape codes
RED = "\033[91m"
RESET = "\033[0m"


class RuleType(Enum):
    """Rules can either BAN something, or REQUIRE it. Used for RuleCheckers."""

    REQUIRE = "Require"
    BAN = "Ban"


@dataclass(slots=True)
class RuleViolation:
    """Keeps track of rule violated, and (maybe) the line it was violated on."""

    rule: str
    line: Optional[int]

    def __str__(self) -> str:
        if self.line is None:
            return f"rule {self.rule} not fulfilled"
        else:
            return f"rule {self.rule} violated on line {self.line}"


class RuleChecker(ast.NodeVisitor):
    """
    A RuleChecker is a kind of NodeVisitor that keeps track of whether it has found
    a particular function call / type of node / etc. as it visits each node
    in the AST (Abstract Syntax Tree).

    The general logic for whether a rule has been violated is below, and each
    subclass will contain specific logic by overriding the various visit* methods
    of a NodeVisitor.
    """

    def __init__(self, ruletype: RuleType):
        self.ruletype = ruletype
        self.location = None
        self.found_instance = False

    def reset(self):
        """Resets the status of the RuleChecker to check a new file."""
        self.location = None
        self.found_instance = False

    def get_violation(self) -> Optional[RuleViolation]:
        """Returns the violation found by this RuleChecker, or None."""
        if self.ruletype is RuleType.BAN:
            rule_followed = not self.found_instance
        else:
            rule_followed = self.found_instance

        if rule_followed:
            return None
        else:
            return RuleViolation(str(self), self.location)


class MethodRule(RuleChecker):
    """RuleChecker that keeps track of calls to a particular `method`."""

    def __init__(self, ruletype: RuleType, method: str):
        super().__init__(ruletype)
        self.method = method

    # Overrides ast.NodeVisitor.visit_Attribute
    def visit_Attribute(self, node):
        if node.attr == self.method:
            self.found_instance = True
            self.location = node.lineno

    def __str__(self) -> str:
        return f"{self.ruletype.value}MethodCall({self.method})"

    __repr__ = __str__


class FunctionRule(RuleChecker):
    """RuleChecker that keeps track of calls to a particular `function`."""

    def __init__(self, ruletype: RuleType, function: str):
        super().__init__(ruletype)
        self.function = function

    # Overrides ast.NodeVisitor.visit_Call
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == self.function:
            self.found_instance = True
            self.location = node.lineno

    def __str__(self) -> str:
        return f"{self.ruletype.value}FunctionCall({self.function})"

    __repr__ = __str__


class NodeRule(RuleChecker):
    """
    RuleChecker that keeps track of instances of a particular `node_type`.

    NOTE: `node_type` must be an attribute of the ast module (one of its node types)
    """

    def __init__(self, ruletype: RuleType, node_type: str):
        super().__init__(ruletype)
        self.node_type = getattr(ast, node_type)

    # Overrides ast.NodeVisitor.visit
    def visit(self, node):
        if isinstance(node, self.node_type):
            self.found_instance = True
            self.location = node.lineno
        super().visit(node)

    def __str__(self) -> str:
        return f"{self.ruletype.value}{self.node_type.__name__}"

    __repr__ = __str__


def find_violations(code: str, rules: list[RuleChecker]) -> list[RuleViolation]:
    """
    Finds any violations of `rules` in `code`, by having each RuleChecker
    visit the AST of `code`.
    Returns a list of any such violations found, as list[RuleViolation]
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    for rulechecker in rules:
        rulechecker.reset()
        rulechecker.visit(tree)

    violations = (rule.get_violation() for rule in rules)
    violations = [v for v in violations if v is not None]
    return violations


def print_violations(
        violations: list[RuleViolation], filename: Optional[str] = None, 
) -> None:
    """
    Prints each of the `violations` alongside the corresponding line in `filename`
    if applicable.
    """
    if filename:
        lines = open(filename).readlines()
        lines.insert(0, "")  # so line numbers are correct
    for v in violations:
        s = str(v)
        if filename and v.line:
            s += f"{RED} `{lines[v.line].rstrip()}`{RESET}"
        print(s)


def main():
    rules = [
        NodeRule(RuleType.BAN, "For"),
        NodeRule(RuleType.BAN, "While"),
        MethodRule(RuleType.BAN, "join"),
        NodeRule(RuleType.REQUIRE, "For"),
        NodeRule(RuleType.BAN, "ListComp"),
        NodeRule(RuleType.REQUIRE, "FunctionDef"),
        NodeRule(RuleType.BAN, "List"),
        FunctionRule(RuleType.BAN, "test"),
        MethodRule(RuleType.BAN, "join"),
    ]

    filename = input("enter file to check: ")
    code = open(filename).read()
    violations = ic(find_violations(code, rules))
    if len(violations) == 0:
        print("all rules followed.")
    else:
        print_violations(violations, "test.py")


if __name__ == "__main__":
    main()
