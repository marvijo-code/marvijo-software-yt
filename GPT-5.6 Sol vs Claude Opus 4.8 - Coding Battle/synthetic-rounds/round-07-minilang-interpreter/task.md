# Task: MiniLang - interpreter with closures and proper tail calls

Create `minilang.py` in this directory exporting:

```python
def run(source: str) -> list[str]   # returns printed lines, in order
class MiniSyntaxError(Exception): ...
class MiniRuntimeError(Exception): ...
```

## Language

Statements (semicolon-terminated unless block-shaped):
```
let x = expr;          // declare in current scope (shadowing allowed)
x = expr;              // assign to nearest enclosing declaration
print(expr);           // append str form of value to the output list
if (e) { ... } else { ... }     // else optional
while (e) { ... }
fn name(a, b) { ... }  // function declaration (sugar for let name = fn)
return expr;           // only inside functions; bare `return;` returns nil
expr;                  // expression statement
```

Expressions: integer literals, string literals `"..."` (no escapes needed
beyond `\"` and `\\`), `true`, `false`, `nil`, variables, `fn (a, b) { ... }`
(anonymous function), calls `f(x, y)`, array literals `[e1, e2]`, indexing
`a[i]`, index assignment `a[i] = e;`, grouping `( )`.

Operators (C-like precedence, all left-assoc; `!` and unary `-` prefix):
`|| && == != < <= > >= + - * / % ! -`
- `+` on two ints = addition; on two strings = concatenation; anything else
  is a runtime error.
- `/` and `%` are integer ops; division by zero is a runtime error.
- `==`/`!=` compare ints, strings, bools, nil by value; arrays by identity.
- `&&`/`||` short-circuit and return a bool.
- Only `false` and `nil` are falsy.

Builtins: `len(x)` (string or array), `push(a, v)` (append, returns nil).

## Required semantics
- Lexical scoping; closures capture variables by reference (a counter
  factory works; two counters are independent).
- First-class functions (pass/return/store them).
- **Proper tail calls**: `return f(...);` where the call is the entire
  returned expression must reuse the stack - a self-recursive countdown of
  depth 200,000 must run without RecursionError or crash.
- `print` formatting: ints as usual, strings raw (no quotes), `true`,
  `false`, `nil`, arrays as `[v1, v2]` (recursive, comma+space), functions
  as `<fn>`.

## Errors
- Parse problems -> raise `MiniSyntaxError` whose message contains
  `line N` (1-based line of the offending token).
- Runtime problems (undefined variable, bad operand types, index out of
  range, calling a non-function, wrong arg count, div by zero) -> raise
  `MiniRuntimeError` whose message contains `line N` of the operation.

Python 3.13 stdlib only. Work only in this directory. Hidden tests grade
programs end-to-end via `run()`. Hard cap: finish within 10 minutes.
