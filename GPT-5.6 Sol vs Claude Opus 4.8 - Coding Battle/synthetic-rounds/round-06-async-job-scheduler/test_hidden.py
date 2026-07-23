import asyncio

import pytest
from scheduler import JobScheduler


def run(coro):
    return asyncio.run(coro)


def test_basic_values_and_order():
    async def main():
        s = JobScheduler(2)
        order = []

        def mk(name):
            async def job():
                order.append(name)
                await asyncio.sleep(0)
                return name.upper()
            return job

        for n in ["a", "b", "c"]:
            s.add_job(n, mk(n))
        res = await s.run()
        assert {k: v.status for k, v in res.items()} == {
            "a": "ok", "b": "ok", "c": "ok"}
        assert res["a"].value == "A" and res["c"].value == "C"
        assert order[:2] == ["a", "b"]  # registration order among ready jobs
        return True
    assert run(main())


def test_dependency_ordering():
    async def main():
        s = JobScheduler(4)
        seq = []

        def mk(name, delay=0.01):
            async def job():
                seq.append(("start", name))
                await asyncio.sleep(delay)
                seq.append(("end", name))
                return name
            return job

        s.add_job("build", mk("build"))
        s.add_job("test", mk("test"), deps=["build"])
        s.add_job("deploy", mk("deploy"), deps=["test"])
        res = await s.run()
        assert all(r.status == "ok" for r in res.values())
        assert seq.index(("end", "build")) < seq.index(("start", "test"))
        assert seq.index(("end", "test")) < seq.index(("start", "deploy"))
        return True
    assert run(main())


def test_concurrency_ceiling():
    async def main():
        s = JobScheduler(3)
        active = 0
        peak = 0

        def mk(i):
            async def job():
                nonlocal active, peak
                active += 1
                peak = max(peak, active)
                await asyncio.sleep(0.03)
                active -= 1
            return job

        for i in range(10):
            s.add_job(f"j{i}", mk(i))
        res = await s.run()
        assert all(r.status == "ok" for r in res.values())
        assert peak == 3
        return True
    assert run(main())


def test_retries_and_attempts():
    async def main():
        s = JobScheduler(1)
        calls = {"n": 0}

        def flaky():
            async def job():
                calls["n"] += 1
                if calls["n"] < 3:
                    raise RuntimeError("boom")
                return 42
            return job
        s.add_job("f", flaky(), retries=3)
        res = await s.run()
        assert res["f"].status == "ok"
        assert res["f"].value == 42
        assert res["f"].attempts == 3
        return True
    assert run(main())


def test_failed_after_retries_exhausted():
    async def main():
        s = JobScheduler(1)

        def bad():
            async def job():
                raise ValueError("nope")
            return job
        s.add_job("b", bad(), retries=2)
        res = await s.run(fail_policy="continue")
        assert res["b"].status == "failed"
        assert isinstance(res["b"].error, ValueError)
        assert res["b"].attempts == 3
        return True
    assert run(main())


def test_skip_propagation_continue():
    async def main():
        s = JobScheduler(2)

        def ok():
            async def job():
                return 1
            return job

        def bad():
            async def job():
                raise RuntimeError("x")
            return job
        s.add_job("a", bad())
        s.add_job("b", ok(), deps=["a"])
        s.add_job("c", ok(), deps=["b"])
        s.add_job("d", ok())
        res = await s.run(fail_policy="continue")
        assert res["a"].status == "failed"
        assert res["b"].status == "skipped"
        assert res["c"].status == "skipped"
        assert res["d"].status == "ok"
        return True
    assert run(main())


def test_fail_fast_cancels_running_and_skips_rest():
    async def main():
        s = JobScheduler(3)
        started = asyncio.Event()
        gate = asyncio.Event()  # never set

        def hang():
            async def job():
                started.set()
                await gate.wait()
            return job

        def bad():
            async def job():
                await started.wait()
                await asyncio.sleep(0.02)
                raise RuntimeError("die")
            return job

        def never():
            async def job():
                return 1
            return job
        s.add_job("hang", hang())
        s.add_job("bad", bad())
        s.add_job("late", never(), deps=["bad"])
        res = await s.run(fail_policy="fail_fast")
        assert res["bad"].status == "failed"
        assert res["hang"].status == "cancelled"
        assert res["late"].status == "skipped"
        return True
    assert run(main())


def test_fail_fast_does_not_raise_and_returns_all():
    async def main():
        s = JobScheduler(1)

        def bad():
            async def job():
                raise RuntimeError("x")
            return job

        def ok():
            async def job():
                return 5
            return job
        s.add_job("a", bad())
        s.add_job("b", ok())
        res = await s.run(fail_policy="fail_fast")
        assert set(res) == {"a", "b"}
        assert res["a"].status == "failed"
        assert res["b"].status == "skipped"
        return True
    assert run(main())


def test_diamond_dependency():
    async def main():
        s = JobScheduler(4)

        def mk(v):
            async def job():
                await asyncio.sleep(0.01)
                return v
            return job
        s.add_job("root", mk(1))
        s.add_job("l", mk(2), deps=["root"])
        s.add_job("r", mk(3), deps=["root"])
        s.add_job("join", mk(4), deps=["l", "r"])
        res = await s.run()
        assert all(r.status == "ok" for r in res.values())
        return True
    assert run(main())


def test_cycle_raises():
    async def main():
        s = JobScheduler(1)

        def ok():
            async def job():
                return 1
            return job
        s.add_job("a", ok(), deps=["b"])
        s.add_job("b", ok(), deps=["a"])
        with pytest.raises(ValueError):
            await s.run()
        return True
    assert run(main())


def test_unknown_dep_raises():
    async def main():
        s = JobScheduler(1)

        def ok():
            async def job():
                return 1
            return job
        s.add_job("a", ok(), deps=["ghost"])
        with pytest.raises(ValueError):
            await s.run()
        return True
    assert run(main())


def test_duplicate_name_raises():
    def ok():
        async def job():
            return 1
        return job
    s = JobScheduler(1)
    s.add_job("a", ok())
    with pytest.raises(ValueError):
        s.add_job("a", ok())
