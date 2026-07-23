import pytest
from eventlib import parse_event, expand, merge_busy, free_slots


def test_parse_ok():
    e = parse_event("2026-07-23 09:30-11:00 Team sync meeting")
    assert e == {"day": "2026-07-23", "start": 570, "end": 660,
                 "title": "Team sync meeting"}


def test_parse_zero_length_rejected():
    with pytest.raises(ValueError):
        parse_event("2026-07-23 09:30-09:30 Nothing")


def test_parse_negative_rejected():
    with pytest.raises(ValueError):
        parse_event("2026-07-23 10:00-09:00 TimeTravel")


def test_parse_malformed():
    with pytest.raises(ValueError):
        parse_event("2026-07-23 0930 Lunch")


def test_expand_single_is_copy():
    ev = {"day": "2026-07-01", "start": 0, "end": 60, "title": "x"}
    out = expand(ev)
    assert out == [ev]
    out[0]["title"] = "changed"
    assert ev["title"] == "x"


def test_expand_daily_until_inclusive():
    ev = {"day": "2026-07-01", "start": 60, "end": 120, "title": "run"}
    out = expand(ev, {"freq": "daily", "until": "2026-07-04"})
    assert [o["day"] for o in out] == [
        "2026-07-01", "2026-07-02", "2026-07-03", "2026-07-04"]


def test_expand_weekly_spacing():
    ev = {"day": "2026-07-01", "start": 60, "end": 120, "title": "gym"}
    out = expand(ev, {"freq": "weekly", "until": "2026-07-22"})
    assert [o["day"] for o in out] == [
        "2026-07-01", "2026-07-08", "2026-07-15", "2026-07-22"]


def test_expand_occurrences_independent_and_input_unmutated():
    ev = {"day": "2026-07-01", "start": 60, "end": 120, "title": "a"}
    out = expand(ev, {"freq": "daily", "until": "2026-07-03"})
    assert len(out) == 3
    assert len({id(o) for o in out}) == 3
    out[0]["start"] = 999
    assert out[1]["start"] == 60
    assert ev == {"day": "2026-07-01", "start": 60, "end": 120, "title": "a"}


def test_merge_touching():
    assert merge_busy([(60, 120), (120, 180)]) == [(60, 180)]


def test_merge_unsorted_containment():
    assert merge_busy([(300, 360), (60, 600), (100, 200)]) == [(60, 600)]


def test_merge_disjoint_sorted_output():
    assert merge_busy([(500, 550), (10, 20), (100, 110)]) == [
        (10, 20), (100, 110), (500, 550)]


def test_free_slots_trailing_gap():
    assert free_slots([(540, 600)], 480, 1020) == [(480, 540), (600, 1020)]


def test_free_slots_empty_busy():
    assert free_slots([], 480, 1020) == [(480, 1020)]


def test_free_slots_full_and_touching():
    assert free_slots([(480, 750), (750, 1020)], 480, 1020) == []
