# Task: Mini Spreadsheet Engine (Python)

Create a file `sheet.py` in this directory implementing a class `Sheet`.

## API
- `Sheet()` - empty sheet.
- `sheet.set(cell: str, raw: str) -> None` - set a cell's raw content.
- `sheet.get(cell: str)` - return the evaluated value of the cell.

Cell names are one or more letters followed by one or more digits (e.g. `A1`, `bc12`). Cell names are CASE-INSENSITIVE everywhere (`a1` == `A1`).

## Raw content rules
- If `raw` parses as a number -> the cell is numeric. `get` returns `int` if the number is integral (e.g. "5", "5.0" -> 5) else `float`.
- If `raw` starts with `=` -> it is a formula (see below).
- Otherwise the cell is text; `get` returns the string exactly as given.
- An unset cell: `get` returns the empty string `""`.

## Formulas
After `=`: an expression with:
- numbers (int/float literals),
- cell references,
- binary operators `+ - * /` with standard precedence, parentheses, unary minus,
- functions `SUM`, `MIN`, `MAX`, `COUNT` (case-insensitive), whose arguments are comma-separated expressions and/or ranges `A1:B3` (a rectangular range; either corner order is allowed, e.g. `B3:A1` == `A1:B3`).
- Whitespace anywhere between tokens is allowed.

Evaluation rules:
- A referenced cell that is unset or text-empty... precisely: an unset cell used in arithmetic or as a function argument counts as `0` for SUM/MIN/MAX arithmetic BUT `COUNT` counts only cells in its arguments that are numeric (set, and numeric or numeric-valued formula). For MIN/MAX, unset cells inside a RANGE are skipped (not treated as 0); an unset cell referenced DIRECTLY (e.g. `=MIN(A1, 5)` with A1 unset) is treated as 0.
- A TEXT cell used in arithmetic or inside SUM/MIN/MAX -> the formula evaluates to the string `"#ERROR!"`. Text cells inside a range are skipped for SUM/MIN/MAX and not counted by COUNT.
- Division by zero -> `"#DIV/0!"`.
- Any reference cycle (direct or indirect, including self-reference) -> every cell in the cycle evaluates to `"#CYCLE!"`.
- A malformed formula (syntax error, unknown function, bad range) -> `"#ERROR!"`.
- Error propagation: if a referenced cell (directly or via range) evaluates to an error string, the referencing formula evaluates to that same error string. If multiple, any one of the involved errors is acceptable.
- Numeric formula results: return `int` if integral else `float`.
- `SUM()` over only-empty/skipped -> 0. `COUNT` similarly can be 0. `MIN`/`MAX` with no usable values -> `"#ERROR!"`.
- Setting a cell later must change results of formulas that reference it (recompute on `get`).

## Examples
```python
s = Sheet()
s.set("A1", "2"); s.set("A2", "3")
s.set("B1", "=A1+A2*2")      # 8
s.set("B2", "=SUM(A1:A2, 5)") # 10
s.set("C1", "=C1")            # "#CYCLE!"
s.set("D1", "=1/0")           # "#DIV/0!"
```

Only the spec above is authoritative. Your solution is graded by hidden tests that follow this spec strictly. Write `sheet.py` (plus any helper files you want) in THIS directory only. Python 3.13, stdlib only. You may write and run your own tests.
