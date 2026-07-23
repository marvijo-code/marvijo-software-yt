import math
import pytest
from sheet import Sheet


def test_literals_and_types():
    s = Sheet()
    s.set("A1", "5")
    s.set("A2", "5.5")
    s.set("A3", "hello")
    s.set("A4", "5.0")
    assert s.get("A1") == 5 and isinstance(s.get("A1"), int)
    assert math.isclose(s.get("A2"), 5.5)
    assert s.get("A3") == "hello"
    assert s.get("A4") == 5 and isinstance(s.get("A4"), int)
    assert s.get("Z99") == ""


def test_case_insensitive_refs():
    s = Sheet()
    s.set("a1", "7")
    assert s.get("A1") == 7
    s.set("B1", "=a1+A1")
    assert s.get("b1") == 14


def test_precedence_parens_unary():
    s = Sheet()
    s.set("A1", "=2+3*4")
    s.set("A2", "=(2+3)*4")
    s.set("A3", "=-3+10")
    s.set("A4", "= 2 * ( 1 + 1 ) ")
    assert s.get("A1") == 14
    assert s.get("A2") == 20
    assert s.get("A3") == 7
    assert s.get("A4") == 4


def test_unset_in_arithmetic_is_zero():
    s = Sheet()
    s.set("B1", "=A1+5")
    assert s.get("B1") == 5


def test_sum_range_and_args():
    s = Sheet()
    s.set("A1", "1"); s.set("A2", "2"); s.set("B1", "3"); s.set("B2", "4")
    s.set("C1", "=SUM(A1:B2)")
    s.set("C2", "=sum(A1:A2, 10, B1)")
    s.set("C3", "=SUM(B2:A1)")  # reversed corners
    assert s.get("C1") == 10
    assert s.get("C2") == 16
    assert s.get("C3") == 10


def test_min_max_count_skip_rules():
    s = Sheet()
    s.set("A1", "5"); s.set("A3", "2"); s.set("A4", "note")
    s.set("C1", "=MIN(A1:A4)")   # skips unset A2 and text A4 -> min(5,2)=2
    s.set("C2", "=MAX(A1:A4)")
    s.set("C3", "=COUNT(A1:A4)") # counts 5 and 2 only
    s.set("C4", "=MIN(B9, 5)")   # direct unset ref -> 0
    assert s.get("C1") == 2
    assert s.get("C2") == 5
    assert s.get("C3") == 2
    assert s.get("C4") == 0


def test_min_no_usable_values_error():
    s = Sheet()
    s.set("C1", "=MIN(A1:A3)")
    assert s.get("C1") == "#ERROR!"
    s.set("C2", "=SUM(A1:A3)")
    assert s.get("C2") == 0
    s.set("C3", "=COUNT(A1:A3)")
    assert s.get("C3") == 0


def test_text_in_arithmetic_error():
    s = Sheet()
    s.set("A1", "abc")
    s.set("B1", "=A1+1")
    s.set("B2", "=SUM(A1, 2)")
    assert s.get("B1") == "#ERROR!"
    assert s.get("B2") == "#ERROR!"


def test_div_zero_and_propagation():
    s = Sheet()
    s.set("A1", "=1/0")
    s.set("A2", "=A1+1")
    s.set("A3", "=SUM(A1:A2)")
    assert s.get("A1") == "#DIV/0!"
    assert s.get("A2") == "#DIV/0!"
    assert s.get("A3") == "#DIV/0!"


def test_cycles():
    s = Sheet()
    s.set("A1", "=A1")
    assert s.get("A1") == "#CYCLE!"
    s.set("B1", "=B2"); s.set("B2", "=B3"); s.set("B3", "=B1")
    assert s.get("B1") == "#CYCLE!"
    assert s.get("B2") == "#CYCLE!"
    s.set("C1", "=B1+1")
    assert s.get("C1") == "#CYCLE!"


def test_cycle_broken_by_update():
    s = Sheet()
    s.set("A1", "=B1"); s.set("B1", "=A1")
    assert s.get("A1") == "#CYCLE!"
    s.set("B1", "4")
    assert s.get("A1") == 4


def test_malformed():
    s = Sheet()
    s.set("A1", "=2+")
    s.set("A2", "=FOO(3)")
    s.set("A3", "=SUM(A1:xyz)")
    assert s.get("A1") == "#ERROR!"
    assert s.get("A2") == "#ERROR!"
    assert s.get("A3") == "#ERROR!"


def test_recompute_on_set():
    s = Sheet()
    s.set("A1", "1")
    s.set("B1", "=A1*10")
    assert s.get("B1") == 10
    s.set("A1", "2.5")
    assert math.isclose(s.get("B1"), 25.0)
    assert s.get("B1") == 25


def test_int_float_result_types():
    s = Sheet()
    s.set("A1", "=10/4")
    s.set("A2", "=10/5")
    assert math.isclose(s.get("A1"), 2.5)
    assert s.get("A2") == 2 and isinstance(s.get("A2"), int)


def test_multi_letter_cells_and_nesting():
    s = Sheet()
    s.set("AA10", "3")
    s.set("AB1", "=SUM(AA10, MAX(1, 2), MIN(5, AA10))")  # 3+2+3
    assert s.get("AB1") == 8
