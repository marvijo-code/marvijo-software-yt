import pytest
from minilang import run, MiniSyntaxError, MiniRuntimeError


def test_arith_precedence_and_print():
    assert run('print(2 + 3 * 4); print((2 + 3) * 4); print(-3 + 10);') == \
        ["14", "20", "7"]


def test_strings_and_concat():
    assert run('let s = "ab" + "cd"; print(s); print(len(s));') == \
        ["abcd", "4"]


def test_bools_nil_truthiness():
    src = '''
let x = nil;
if (x) { print("yes"); } else { print("no"); }
if (0) { print("zero-truthy"); }
if ("" ) { print("empty-truthy"); }
print(1 == 1 && 2 < 3);
print(false || nil == nil);
'''
    assert run(src) == ["no", "zero-truthy", "empty-truthy", "true", "true"]


def test_while_and_assignment():
    src = '''
let i = 0; let acc = 0;
while (i < 5) { acc = acc + i; i = i + 1; }
print(acc);
'''
    assert run(src) == ["10"]


def test_arrays():
    src = '''
let a = [1, 2, 3];
a[0] = 10;
push(a, 4);
print(a); print(len(a)); print(a[3]);
'''
    assert run(src) == ["[10, 2, 3, 4]", "4", "4"]


def test_closures_counter_factory():
    src = '''
fn make_counter() {
  let n = 0;
  return fn() { n = n + 1; return n; };
}
let c1 = make_counter();
let c2 = make_counter();
print(c1()); print(c1()); print(c1()); print(c2());
'''
    assert run(src) == ["1", "2", "3", "1"]


def test_first_class_functions_and_higher_order():
    src = '''
fn map(a, f) {
  let out = [];
  let i = 0;
  while (i < len(a)) { push(out, f(a[i])); i = i + 1; }
  return out;
}
fn double(x) { return x * 2; }
print(map([1, 2, 3], double));
print(map([1, 2], fn(x) { return x + 100; }));
'''
    assert run(src) == ["[2, 4, 6]", "[101, 102]"]


def test_shadowing_and_scopes():
    src = '''
let x = 1;
fn f() {
  let x = 2;
  if (true) { let x = 3; print(x); }
  print(x);
}
f();
print(x);
'''
    assert run(src) == ["3", "2", "1"]


def test_functions_print_form_and_recursion():
    src = '''
fn fib(n) { if (n < 2) { return n; } return fib(n - 1) + fib(n - 2); }
print(fib(15));
print(fib);
'''
    assert run(src) == ["610", "<fn>"]


def test_proper_tail_calls_depth_200k():
    src = '''
fn count(n, acc) {
  if (n == 0) { return acc; }
  return count(n - 1, acc + 1);
}
print(count(200000, 0));
'''
    assert run(src) == ["200000"]


def test_syntax_error_line():
    with pytest.raises(MiniSyntaxError) as e:
        run('let x = 1;\nlet y = ;\n')
    assert "line 2" in str(e.value)


def test_runtime_error_undefined_var_line():
    with pytest.raises(MiniRuntimeError) as e:
        run('let a = 1;\nprint(a);\nprint(missing);')
    assert "line 3" in str(e.value)


def test_runtime_error_type_and_index():
    with pytest.raises(MiniRuntimeError):
        run('print(1 + "x");')
    with pytest.raises(MiniRuntimeError):
        run('let a = [1]; print(a[5]);')
    with pytest.raises(MiniRuntimeError):
        run('let x = 3; x(1);')
    with pytest.raises(MiniRuntimeError):
        run('print(1 / 0);')


def test_return_outside_value_and_nested_calls():
    src = '''
fn choose(f, g, flag) { if (flag) { return f; } return g; }
fn inc(x) { return x + 1; }
fn dec(x) { return x - 1; }
print(choose(inc, dec, true)(10));
print(choose(inc, dec, false)(10));
'''
    assert run(src) == ["11", "9"]
