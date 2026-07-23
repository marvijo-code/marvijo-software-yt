"""Async job scheduler with dependencies (asyncio)."""

import asyncio
from collections import deque


class JobResult:
    __slots__ = ("status", "value", "error", "attempts")

    def __init__(self, status=None, value=None, error=None, attempts=0):
        self.status = status
        self.value = value
        self.error = error
        self.attempts = attempts

    def __repr__(self):
        return (
            f"JobResult(status={self.status!r}, value={self.value!r}, "
            f"error={self.error!r}, attempts={self.attempts})"
        )


class JobScheduler:
    def __init__(self, max_concurrency: int):
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be >= 1")
        self.max_concurrency = max_concurrency
        self._jobs = {}          # name -> (coro_factory, deps, retries)
        self._order = []         # registration order

    def add_job(self, name, coro_factory, deps=(), retries: int = 0) -> None:
        if name in self._jobs:
            raise ValueError(f"duplicate job name: {name!r}")
        self._jobs[name] = (coro_factory, list(deps), retries)
        self._order.append(name)

    def _validate(self):
        # Unknown dependency names.
        for name in self._order:
            for d in self._jobs[name][1]:
                if d not in self._jobs:
                    raise ValueError(f"unknown dependency {d!r} for job {name!r}")
        # Cycle detection (Kahn's algorithm). Self-deps are cycles.
        indeg = {n: 0 for n in self._order}
        adj = {n: [] for n in self._order}
        for n in self._order:
            for d in self._jobs[n][1]:
                adj[d].append(n)
                indeg[n] += 1
        q = deque(n for n in self._order if indeg[n] == 0)
        seen = 0
        while q:
            x = q.popleft()
            seen += 1
            for m in adj[x]:
                indeg[m] -= 1
                if indeg[m] == 0:
                    q.append(m)
        if seen != len(self._order):
            raise ValueError("dependency cycle detected")

    async def run(self, fail_policy: str = "fail_fast") -> dict:
        self._validate()

        results = {name: JobResult() for name in self._order}
        running = {}          # name -> task
        task_to_name = {}     # task -> name
        aborted = False

        async def job_runner(name):
            factory, _deps, retries = self._jobs[name]
            r = results[name]
            attempts = 0
            while True:
                attempts += 1
                r.attempts = attempts
                try:
                    value = await factory()
                except asyncio.CancelledError:
                    r.status = "cancelled"
                    raise
                except Exception as e:  # noqa: BLE001
                    if attempts <= retries:
                        continue
                    r.status = "failed"
                    r.error = e
                    return
                else:
                    r.status = "ok"
                    r.value = value
                    return

        while True:
            # Cascade "skipped": any pending job with a dep that finished non-ok.
            changed = True
            while changed:
                changed = False
                for name in self._order:
                    if results[name].status is not None or name in running:
                        continue
                    deps = self._jobs[name][1]
                    if any(
                        results[d].status in ("failed", "cancelled", "skipped")
                        for d in deps
                    ):
                        results[name].status = "skipped"
                        changed = True

            # Start ready jobs in registration order while slots are free.
            if not aborted:
                for name in self._order:
                    if len(running) >= self.max_concurrency:
                        break
                    if results[name].status is not None or name in running:
                        continue
                    deps = self._jobs[name][1]
                    if all(results[d].status == "ok" for d in deps):
                        task = asyncio.ensure_future(job_runner(name))
                        running[name] = task
                        task_to_name[task] = name

            if not running:
                break

            done, _ = await asyncio.wait(
                list(running.values()), return_when=asyncio.FIRST_COMPLETED
            )
            for task in done:
                name = task_to_name.pop(task)
                del running[name]
                # Surface any unexpected (non-cancel) error state; status was set
                # inside job_runner. Consume cancellation exception cleanly.
                if task.cancelled():
                    if results[name].status is None:
                        results[name].status = "cancelled"
                else:
                    task.exception()  # retrieve to avoid "never retrieved" warnings
                if (
                    results[name].status == "failed"
                    and fail_policy == "fail_fast"
                    and not aborted
                ):
                    aborted = True
                    for t in running.values():
                        t.cancel()

        # Anything still undecided never started -> skipped.
        for name in self._order:
            if results[name].status is None:
                results[name].status = "skipped"

        return results
