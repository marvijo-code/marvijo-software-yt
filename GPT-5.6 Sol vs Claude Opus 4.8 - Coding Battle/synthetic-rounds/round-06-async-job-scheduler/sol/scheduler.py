"""A small dependency-aware asyncio job scheduler."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable


@dataclass
class JobResult:
    """The outcome of one scheduled job."""

    status: str
    value: Any = None
    error: BaseException | None = None
    attempts: int = 0


@dataclass(frozen=True)
class _Job:
    name: str
    factory: Callable[[], Awaitable[Any]]
    deps: tuple[str, ...]
    retries: int


class JobScheduler:
    def __init__(self, max_concurrency: int):
        if (
            not isinstance(max_concurrency, int)
            or isinstance(max_concurrency, bool)
            or max_concurrency < 1
        ):
            raise ValueError("max_concurrency must be a positive integer")
        self.max_concurrency = max_concurrency
        self._jobs: dict[str, _Job] = {}
        self._running = False

    def add_job(
        self,
        name: str,
        coro_factory: Callable[[], Awaitable[Any]],
        deps: list[str] = (),
        retries: int = 0,
    ) -> None:
        if self._running:
            raise ValueError("jobs cannot be added while the scheduler is running")
        if name in self._jobs:
            raise ValueError(f"duplicate job name: {name!r}")
        if not callable(coro_factory):
            raise ValueError("coro_factory must be callable")
        if not isinstance(retries, int) or isinstance(retries, bool) or retries < 0:
            raise ValueError("retries must be a non-negative integer")

        try:
            dependency_names = tuple(deps)
        except TypeError as exc:
            raise ValueError("deps must be an iterable of job names") from exc
        if any(not isinstance(dep, str) for dep in dependency_names):
            raise ValueError("dependency names must be strings")

        self._jobs[name] = _Job(
            name=name,
            factory=coro_factory,
            deps=dependency_names,
            retries=retries,
        )

    def _validate_graph(self) -> None:
        names = set(self._jobs)
        for job in self._jobs.values():
            unknown = [dep for dep in job.deps if dep not in names]
            if unknown:
                raise ValueError(
                    f"job {job.name!r} has unknown dependency {unknown[0]!r}"
                )

        # Kahn's algorithm validates the whole graph before any task is made.
        dependencies = {
            job.name: set(job.deps) for job in self._jobs.values()
        }
        dependents: dict[str, list[str]] = {name: [] for name in self._jobs}
        for name, deps in dependencies.items():
            for dep in deps:
                dependents[dep].append(name)

        ready = [name for name, deps in dependencies.items() if not deps]
        visited = 0
        while ready:
            completed = ready.pop()
            visited += 1
            for name in dependents[completed]:
                dependencies[name].remove(completed)
                if not dependencies[name]:
                    ready.append(name)
        if visited != len(self._jobs):
            raise ValueError("dependency cycle detected")

    @staticmethod
    async def _execute(job: _Job) -> JobResult:
        attempts = 0
        while True:
            attempts += 1
            try:
                awaitable = job.factory()
                value = await awaitable
                return JobResult("ok", value=value, attempts=attempts)
            except asyncio.CancelledError:
                return JobResult("cancelled", attempts=attempts)
            except BaseException as exc:
                if attempts > job.retries:
                    return JobResult("failed", error=exc, attempts=attempts)

    async def run(self, fail_policy: str = "fail_fast") -> dict[str, JobResult]:
        if fail_policy not in {"fail_fast", "continue"}:
            raise ValueError("fail_policy must be 'fail_fast' or 'continue'")
        if self._running:
            raise ValueError("the scheduler is already running")

        self._validate_graph()
        self._running = True
        results: dict[str, JobResult] = {}
        running: dict[str, asyncio.Task[JobResult]] = {}

        try:
            while len(results) < len(self._jobs):
                # A non-ok terminal dependency makes a never-started job
                # impossible to run. Repeat to propagate skips down a chain.
                changed = True
                while changed:
                    changed = False
                    for job in self._jobs.values():
                        if job.name in results or job.name in running:
                            continue
                        if any(
                            dep in results and results[dep].status != "ok"
                            for dep in job.deps
                        ):
                            results[job.name] = JobResult("skipped")
                            changed = True

                # Iterating the insertion-ordered job dict enforces start order.
                for job in self._jobs.values():
                    if len(running) >= self.max_concurrency:
                        break
                    if job.name in results or job.name in running:
                        continue
                    if all(
                        dep in results and results[dep].status == "ok"
                        for dep in job.deps
                    ):
                        running[job.name] = asyncio.create_task(
                            self._execute(job), name=f"job:{job.name}"
                        )

                if not running:
                    # Graph validation means this is reachable only when all
                    # remaining jobs were resolved as skipped.
                    break

                done_tasks, _ = await asyncio.wait(
                    running.values(), return_when=asyncio.FIRST_COMPLETED
                )
                # Include tasks that finished before the coordinator resumed.
                done_tasks.update(task for task in running.values() if task.done())

                failure_seen = False
                for name in self._jobs:
                    task = running.get(name)
                    if task not in done_tasks:
                        continue
                    result = task.result()
                    results[name] = result
                    del running[name]
                    if result.status == "failed":
                        failure_seen = True

                if failure_seen and fail_policy == "fail_fast":
                    # Snapshot the executing jobs: even a cancellation-resistant
                    # coroutine is reported as cancelled after this point.
                    cancelling = list(running.items())
                    for _, task in cancelling:
                        task.cancel()
                    if cancelling:
                        await asyncio.gather(
                            *(task for _, task in cancelling),
                            return_exceptions=True,
                        )
                    for name, task in cancelling:
                        try:
                            attempts = task.result().attempts
                        except BaseException:
                            attempts = 0
                        results[name] = JobResult(
                            "cancelled",
                            attempts=attempts,
                        )
                    running.clear()
                    for name in self._jobs:
                        if name not in results:
                            results[name] = JobResult("skipped")
                    break
        except BaseException:
            for task in running.values():
                task.cancel()
            if running:
                await asyncio.gather(*running.values(), return_exceptions=True)
            raise
        finally:
            self._running = False

        # Preserve registration order regardless of completion order.
        return {name: results[name] for name in self._jobs}
