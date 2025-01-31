"""
FILE: rules.py
AUTHOR: Jordan Rodriguez (jerodriguez@arizona.edu)

DESCRIPTION: 
    Module with RuleCheckers for various syntax rules, and a function to check
    code against the rules.

CLASSES:
    - `RuleType(Enum)`: RuleType.BAN and RuleType.REQUIRE.
    - `RuleViolation`: dataclass to keep track of which/where rules are violated.
    - `RuleChecker(ast.NodeVisitor)`: Keeps track of a syntax rule by visiting AST
        - `NodeRule(RuleChecker)`: Bans/requires a type of AST node.
        - `FunctionRule(RuleChecker)`: Bans/requires a particular function call.
        - `MethodRule(RuleChecker)`: Bans/requires a particular method call.

FUNCTIONS:
    - `find_violations(code: str, rules: list[RuleChecker]) -> list[RuleViolation]`

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
    """Keeps track of rule violated, line num and corresponding line if applicable."""

    rule: str
    line_num: Optional[int] = None
    line: Optional[str] = None

    def __str__(self) -> str:
        if not self.line_num and not self.line:
            return f"{self.rule} Your code does not have it."

        s = f"{self.rule}"
        if self.line_num:
            s += f" Your code has it on line {self.line_num}"
        if self.line:
            s += f": `{self.line}`"
        return s


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
        self.found_location = None

    def reset(self):
        """Resets the status of the RuleChecker to check a new file."""
        self.found_location = None

    def get_violation(self) -> Optional[RuleViolation]:
        """Returns the violation found by this RuleChecker, or None."""
        if self.ruletype is RuleType.BAN:
            rule_followed = not self.found_location
        else:
            rule_followed = self.found_location

        if rule_followed:
            return None
        else:
            return RuleViolation(str(self), self.found_location)


class MethodRule(RuleChecker):
    """RuleChecker that keeps track of calls to a particular `method`."""

    def __init__(self, ruletype: RuleType, method: str):
        super().__init__(ruletype)
        self.method = method

    # Overrides ast.NodeVisitor.visit_Attribute
    def visit_Attribute(self, node):
        if node.attr == self.method:
            self.found_location = node.lineno
        super().visit(node.value)

    def __str__(self) -> str:
        verb = "banned" if self.ruletype == RuleType.BAN else "required"
        return f"Method {self.method} is {verb}."

    __repr__ = __str__


class FunctionRule(RuleChecker):
    """RuleChecker that keeps track of calls to a particular `function`."""

    def __init__(self, ruletype: RuleType, function: str):
        super().__init__(ruletype)
        self.function = function

    # Overrides ast.NodeVisitor.visit_Call
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == self.function:
            self.found_location = node.lineno
        for e in node.args:
            super().visit(e)
        for e in node.keywords:
            super().visit(e)

    def __str__(self) -> str:
        verb = "banned" if self.ruletype == RuleType.BAN else "required"
        return f"Function {self.function} is {verb}."

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
            self.found_location = node.lineno
        super().visit(node)

    def __str__(self) -> str:
        verb = "banned" if self.ruletype == RuleType.BAN else "required"
        return f"{self.node_type.__name__} is {verb}."

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
    # Add lines of code to RuleViolations
    code_lines = [line.rstrip() for line in code.splitlines()]
    code_lines.insert(0, None) # make list indices correspond to line nums
    for violation in violations:
        if violation.line_num:
            violation.line = code_lines[violation.line_num]

    return violations


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
        print(*violations, sep="\n")


if __name__ == "__main__":
    main()
