# Task: Hindley-Milner type inference (Algorithm W)

Create `hm.py` in this directory exporting:

```python
class HMTypeError(Exception): ...
def infer(ast) -> str
```

`infer` type-checks a lambda-calculus expression and returns its
principal type as a canonical string, or raises `HMTypeError` for any
ill-typed program.

## AST (nested Python lists)
```
["lit", v]              # v is a Python int -> type int, or bool -> type bool
["var", name]
["lam", name, body]     # lambda name. body
["app", f, x]           # application
["let", name, e1, e2]   # let name = e1 in e2   (POLYMORPHIC generalization)
["letrec", name, e1, e2]# recursive let (name visible in e1, monomorphic
                        # inside e1, generalized in e2)
["if", c, t, e]         # c : bool, branches unify
["pair", a, b]          # (a, b)
["fst", e] / ["snd", e]
["binop", op, a, b]     # op in {"+", "-", "<", "=="}:
                        #   + -  : int -> int -> int
                        #   < == : int -> int -> bool
```

## Semantics (standard HM)
- Lambda-bound variables are MONOMORPHIC; let/letrec-bound are generalized
  over type variables not free in the environment.
- Occurs check required (`fun x -> x x` is ill-typed).
- Unbound variable -> HMTypeError.

## Canonical type string
- Base types: `int`, `bool`.
- Type variables: `a`, `b`, `c`, ... assigned in order of FIRST APPEARANCE
  scanning the final printed type left to right.
- Function type: `T1 -> T2`, right-associative; parenthesize a function
  type in argument position: `(a -> b) -> c`.
- Pair type: `(T1 * T2)` - always parenthesized, `*` with single spaces.
- Examples: identity -> `a -> a`; `fun f -> fun g -> fun x -> f (g x)`
  -> `(a -> b) -> (c -> a) -> c -> b`; `fun p -> fst p` -> `(a * b) -> a`.

Python 3.13 stdlib only. Work only in this directory. Hidden tests grade
principal types character-exact and required failures. Hard cap: finish
within 10 minutes.
