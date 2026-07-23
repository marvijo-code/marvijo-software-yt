# Benchmark Task RW5 - sympy

**Repo:** sympy/sympy

## Issue #28219: `Pow.as_real_imag` is inconsistent with evaluating `Pow(0, -1)` as ComplexInfinity

> Another example of something causing this issue: `1/Sum(1, (Symbol("p"), 8, 6))`
>
> I think this boils down to the following inconsistency:
> - `Pow(0,-1).as_real_imag() == (nan, nan)`
> - `Sum(1, (Symbol("p"), 8, 6)).is_nonzero is None`
> - `Pow(Sum(1, (Symbol("p"), 8, 6)), -1).as_real_imag() == (Pow(Sum(1, (Symbol("p"), 8, 6)), -1), 0)`
>
> I guess power.py `as_real_imag` should have a case first about what to do
> if `not self.base.is_nonzero` when `not exp >= 0`.

`Pow(base, -1)` with a zero base is `ComplexInfinity` (`zoo`), whose real and
imaginary parts are both undefined (`nan`). But `Pow.as_real_imag()` takes the
real-base short-circuit (`if not im_e: return self, S.Zero`) and reports the
imaginary part as `0`, which is inconsistent.

## Minimal repro

```python
from sympy import Pow, S, Symbol

# BUG: base is zero, exponent negative -> should be (nan, nan)
print(Pow(S.Zero, -1, evaluate=False).as_real_imag())
# actual (buggy): (1/0, 0)
# expected:       (nan, nan)

# a nonzero real base must be unaffected:
x = Symbol('x', real=True)
print(Pow(x, -1, evaluate=False).as_real_imag())   # -> (1/x, 0)
```

## Rules

Fix the bug in the library source. Do NOT modify test files. Hidden
maintainer-written tests for this exact bug will grade you. The virtualenv at
`.venv` is ready (`.venv/Scripts/python`). Wall-clock time counts. Hard cap 10
minutes.
