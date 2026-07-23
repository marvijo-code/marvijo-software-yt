import pytest
from hm import infer, HMTypeError


def lam(x, b):
    return ["lam", x, b]


def app(f, x):
    return ["app", f, x]


def var(x):
    return ["var", x]


def lit(v):
    return ["lit", v]


def test_identity():
    assert infer(lam("x", var("x"))) == "a -> a"


def test_const():
    assert infer(lam("x", lam("y", var("x")))) == "a -> b -> a"


def test_literals_and_binop():
    assert infer(lit(3)) == "int"
    assert infer(lit(True)) == "bool"
    assert infer(["binop", "+", lit(1), lit(2)]) == "int"
    assert infer(["binop", "<", lit(1), lit(2)]) == "bool"


def test_compose():
    compose = lam("f", lam("g", lam("x", app(var("f"), app(var("g"), var("x"))))))
    assert infer(compose) == "(a -> b) -> (c -> a) -> c -> b"


def test_apply_twice():
    twice = lam("f", lam("x", app(var("f"), app(var("f"), var("x")))))
    assert infer(twice) == "(a -> a) -> a -> a"


def test_pair_and_projections():
    assert infer(["pair", lit(1), lit(True)]) == "(int * bool)"
    assert infer(lam("p", ["fst", var("p")])) == "(a * b) -> a"
    assert infer(lam("p", ["snd", var("p")])) == "(a * b) -> b"


def test_if_unifies_branches():
    e = lam("c", ["if", var("c"), lit(1), lit(2)])
    assert infer(e) == "bool -> int"
    with pytest.raises(HMTypeError):
        infer(["if", lit(1), lit(1), lit(2)])       # cond not bool
    with pytest.raises(HMTypeError):
        infer(["if", lit(True), lit(1), lit(False)])  # branch mismatch


def test_let_polymorphism():
    e = ["let", "id", lam("x", var("x")),
         ["pair", app(var("id"), lit(1)), app(var("id"), lit(True))]]
    assert infer(e) == "(int * bool)"


def test_lambda_bound_is_monomorphic():
    e = lam("f", ["pair", app(var("f"), lit(1)), app(var("f"), lit(True))])
    with pytest.raises(HMTypeError):
        infer(e)


def test_occurs_check():
    with pytest.raises(HMTypeError):
        infer(lam("x", app(var("x"), var("x"))))


def test_unbound_variable():
    with pytest.raises(HMTypeError):
        infer(var("ghost"))


def test_letrec_sum():
    # letrec sum = fun n -> if n == 0 then 0 else n + sum (n - 1) in sum
    body = lam("n", ["if", ["binop", "==", var("n"), lit(0)],
                     lit(0),
                     ["binop", "+", var("n"),
                      app(var("sum"), ["binop", "-", var("n"), lit(1)])]])
    e = ["letrec", "sum", body, var("sum")]
    assert infer(e) == "int -> int"


def test_letrec_polymorphic_after_binding():
    # letrec f = fun x -> x in (f 1, f true)
    e = ["letrec", "f", lam("x", var("x")),
         ["pair", app(var("f"), lit(1)), app(var("f"), lit(True))]]
    assert infer(e) == "(int * bool)"


def test_no_overgeneralization_of_env_vars():
    # fun y -> let f = fun x -> y in (f 1, f true)  : both results share y's type
    e = lam("y", ["let", "f", lam("x", var("y")),
                  ["pair", app(var("f"), lit(1)), app(var("f"), lit(True))]])
    assert infer(e) == "a -> (a * a)"


def test_nested_arrows_printing():
    # fun f -> f (fun x -> x)   : ((a -> a) -> b) -> b
    e = lam("f", app(var("f"), lam("x", var("x"))))
    assert infer(e) == "((a -> a) -> b) -> b"
