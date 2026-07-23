"""A small, dependency-free spreadsheet expression engine."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import TypeAlias


ERROR = "#ERROR!"
DIV_ZERO = "#DIV/0!"
CYCLE = "#CYCLE!"

_CELL_RE = re.compile(r"[A-Za-z]+[0-9]+\Z")
_NUMBER_RE = re.compile(
    r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
)
_RAW_INTEGER_RE = re.compile(r"[+-]?[0-9]+\Z")


class _FormulaError(Exception):
    pass


@dataclass(frozen=True)
class _Value:
    kind: str
    value: object = None


@dataclass(frozen=True)
class _Number:
    value: int | float


@dataclass(frozen=True)
class _Reference:
    cell: str


@dataclass(frozen=True)
class _Unary:
    operand: "_Node"


@dataclass(frozen=True)
class _Binary:
    operator: str
    left: "_Node"
    right: "_Node"


@dataclass(frozen=True)
class _Range:
    start: str
    end: str


@dataclass(frozen=True)
class _Function:
    name: str
    arguments: tuple["_Argument", ...]


_Node: TypeAlias = _Number | _Reference | _Unary | _Binary | _Function
_Argument: TypeAlias = _Node | _Range


def _tokenize(source: str) -> list[tuple[str, object]]:
    tokens: list[tuple[str, object]] = []
    position = 0
    while position < len(source):
        character = source[position]
        if character.isspace():
            position += 1
            continue

        match = _NUMBER_RE.match(source, position)
        if match:
            literal = match.group()
            try:
                if "." not in literal and "e" not in literal.lower():
                    number: int | float = int(literal)
                else:
                    number = float(literal)
            except (ValueError, OverflowError):
                raise _FormulaError from None
            tokens.append(("NUMBER", number))
            position = match.end()
            continue

        if character.isalpha():
            end = position + 1
            while end < len(source) and source[end].isalpha():
                end += 1
            digit_end = end
            while digit_end < len(source) and source[digit_end].isdigit():
                digit_end += 1
            if digit_end > end:
                tokens.append(("REF", source[position:digit_end].upper()))
                position = digit_end
            else:
                tokens.append(("IDENT", source[position:end].upper()))
                position = end
            continue

        if character in "+-*/(),:":
            tokens.append((character, character))
            position += 1
            continue
        raise _FormulaError

    tokens.append(("EOF", None))
    return tokens


class _Parser:
    def __init__(self, source: str) -> None:
        self.tokens = _tokenize(source)
        self.position = 0

    def parse(self) -> _Node:
        expression = self._expression()
        if self._peek() != "EOF":
            raise _FormulaError
        return expression

    def _peek(self) -> str:
        return self.tokens[self.position][0]

    def _take(self, expected: str | None = None) -> tuple[str, object]:
        token = self.tokens[self.position]
        if expected is not None and token[0] != expected:
            raise _FormulaError
        self.position += 1
        return token

    def _expression(self) -> _Node:
        node = self._term()
        while self._peek() in ("+", "-"):
            operator = str(self._take()[1])
            node = _Binary(operator, node, self._term())
        return node

    def _term(self) -> _Node:
        node = self._unary()
        while self._peek() in ("*", "/"):
            operator = str(self._take()[1])
            node = _Binary(operator, node, self._unary())
        return node

    def _unary(self) -> _Node:
        if self._peek() == "-":
            self._take("-")
            return _Unary(self._unary())
        return self._primary()

    def _primary(self) -> _Node:
        token_type = self._peek()
        if token_type == "NUMBER":
            return _Number(self._take()[1])  # type: ignore[arg-type]
        if token_type == "REF":
            return _Reference(str(self._take()[1]))
        if token_type == "IDENT":
            name = str(self._take()[1])
            self._take("(")
            arguments: list[_Argument] = []
            if self._peek() != ")":
                while True:
                    arguments.append(self._argument())
                    if self._peek() != ",":
                        break
                    self._take(",")
            self._take(")")
            return _Function(name, tuple(arguments))
        if token_type == "(":
            self._take("(")
            node = self._expression()
            self._take(")")
            return node
        raise _FormulaError

    def _argument(self) -> _Argument:
        first = self._expression()
        if self._peek() != ":":
            return first
        self._take(":")
        second = self._expression()
        if not isinstance(first, _Reference) or not isinstance(second, _Reference):
            raise _FormulaError
        return _Range(first.cell, second.cell)


@dataclass
class _Evaluation:
    sheet: "Sheet"
    memo: dict[str, _Value]
    active: set[str]

    def cell(self, name: str) -> _Value:
        if name in self.memo:
            return self.memo[name]
        if name in self.active:
            return _Value("error", CYCLE)

        raw = self.sheet._cells.get(name)
        if raw is None:
            return _Value("unset")

        self.active.add(name)
        try:
            numeric = _parse_raw_number(raw)
            if numeric is not None:
                result = _Value("number", numeric)
            elif raw.startswith("="):
                try:
                    tree = _Parser(raw[1:]).parse()
                    result = self.node(tree)
                except _FormulaError:
                    result = _Value("error", ERROR)
            else:
                result = _Value("text", raw)
            self.memo[name] = result
            return result
        finally:
            self.active.remove(name)

    def node(self, node: _Node) -> _Value:
        if isinstance(node, _Number):
            return _Value("number", node.value)
        if isinstance(node, _Reference):
            return self.cell(node.cell)
        if isinstance(node, _Unary):
            value = self._arithmetic_value(self.node(node.operand))
            if value.kind == "number":
                return _Value("number", -value.value)  # type: ignore[operator]
            return value
        if isinstance(node, _Binary):
            left = self._arithmetic_value(self.node(node.left))
            right = self._arithmetic_value(self.node(node.right))
            errors = [value for value in (left, right) if value.kind == "error"]
            if errors:
                return next(
                    (value for value in errors if value.value == CYCLE), errors[0]
                )
            try:
                if node.operator == "+":
                    result = left.value + right.value  # type: ignore[operator]
                elif node.operator == "-":
                    result = left.value - right.value  # type: ignore[operator]
                elif node.operator == "*":
                    result = left.value * right.value  # type: ignore[operator]
                else:
                    if right.value == 0:
                        return _Value("error", DIV_ZERO)
                    result = left.value / right.value  # type: ignore[operator]
            except (ArithmeticError, OverflowError, TypeError):
                return _Value("error", ERROR)
            return _Value("number", result)
        if isinstance(node, _Function):
            return self.function(node)
        return _Value("error", ERROR)

    @staticmethod
    def _arithmetic_value(value: _Value) -> _Value:
        if value.kind == "unset":
            return _Value("number", 0)
        if value.kind == "text":
            return _Value("error", ERROR)
        return value

    def function(self, function: _Function) -> _Value:
        if function.name not in {"SUM", "MIN", "MAX", "COUNT"}:
            return _Value("error", ERROR)

        values: list[int | float] = []
        errors: list[_Value] = []
        for argument in function.arguments:
            if isinstance(argument, _Range):
                range_values = self._range(argument)
                for value in range_values:
                    if value.kind == "error":
                        errors.append(value)
                    elif value.kind == "number":
                        values.append(value.value)  # type: ignore[arg-type]
                continue

            value = self.node(argument)
            if value.kind == "error":
                errors.append(value)
                continue
            if function.name == "COUNT":
                if value.kind == "number":
                    values.append(value.value)  # type: ignore[arg-type]
            else:
                value = self._arithmetic_value(value)
                if value.kind == "error":
                    errors.append(value)
                else:
                    values.append(value.value)  # type: ignore[arg-type]

        if errors:
            return next((value for value in errors if value.value == CYCLE), errors[0])
        if function.name == "COUNT":
            return _Value("number", len(values))
        if function.name == "SUM":
            return _Value("number", sum(values))
        if not values:
            return _Value("error", ERROR)
        if function.name == "MIN":
            return _Value("number", min(values))
        return _Value("number", max(values))

    def _range(self, cell_range: _Range) -> list[_Value]:
        first = _split_cell(cell_range.start)
        second = _split_cell(cell_range.end)
        if first is None or second is None:
            raise _FormulaError
        first_column, first_row = first
        second_column, second_row = second
        column_start, column_end = sorted((first_column, second_column))
        row_start, row_end = sorted((first_row, second_row))
        values: list[_Value] = []
        for column in range(column_start, column_end + 1):
            letters = _column_name(column)
            for row in range(row_start, row_end + 1):
                values.append(self.cell(f"{letters}{row}"))
        return values


def _parse_raw_number(raw: str) -> int | float | None:
    stripped = raw.strip()
    if _RAW_INTEGER_RE.fullmatch(stripped):
        return int(stripped)
    try:
        value = float(raw)
    except (TypeError, ValueError, OverflowError):
        return None
    if math.isfinite(value) and value.is_integer():
        return int(value)
    return value


def _split_cell(name: str) -> tuple[int, int] | None:
    if _CELL_RE.fullmatch(name) is None:
        return None
    index = 0
    while index < len(name) and name[index].isalpha():
        index += 1
    column = 0
    for character in name[:index].upper():
        column = column * 26 + ord(character) - ord("A") + 1
    return column, int(name[index:])


def _column_name(column: int) -> str:
    result = ""
    while column:
        column, remainder = divmod(column - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def _public_value(value: _Value):
    if value.kind == "unset":
        return ""
    if value.kind in {"text", "error"}:
        return value.value
    number = value.value
    if isinstance(number, float) and math.isfinite(number) and number.is_integer():
        return int(number)
    return number


class Sheet:
    """An in-memory collection of case-insensitive spreadsheet cells."""

    def __init__(self) -> None:
        self._cells: dict[str, str] = {}

    @staticmethod
    def _normalize_cell(cell: str) -> str:
        if not isinstance(cell, str) or _CELL_RE.fullmatch(cell) is None:
            raise ValueError(f"invalid cell name: {cell!r}")
        return cell.upper()

    def set(self, cell: str, raw: str) -> None:
        if not isinstance(raw, str):
            raise TypeError("raw cell content must be a string")
        self._cells[self._normalize_cell(cell)] = raw

    def get(self, cell: str):
        name = self._normalize_cell(cell)
        evaluation = _Evaluation(self, {}, set())
        return _public_value(evaluation.cell(name))
