# Task: Async job scheduler with dependencies (Python, asyncio)

Create `scheduler.py` in this directory:

```python
class JobResult:  # attributes: status, value, error, attempts
class JobScheduler:
    def __init__(self, max_concurrency: int): ...
    def add_job(self, name: str, coro_factory, deps: list[str] = (), retries: int = 0) -> None: ...
    async def run(self, fail_policy: str = "fail_fast") -> dict[str, JobResult]: ...
```

`coro_factory` is a zero-arg callable returning a fresh awaitable each attempt.

## Semantics (all graded)
- `run()` executes every registered job at most once to completion, respecting:
  - **Dependencies**: a job may start only after ALL its deps finished with
    status `"ok"`.
  - **Concurrency**: at most `max_concurrency` job coroutines may be
    executing (started, not finished) at any instant.
  - **Start order**: among jobs whose deps are satisfied and a free slot
    exists, start them in registration order.
- **JobResult.status** is one of:
  - `"ok"` - the awaitable returned; `value` = its return value.
  - `"failed"` - raised an exception on the final attempt; `error` = that
    exception instance.
  - `"cancelled"` - it was executing and got cancelled by fail_fast.
  - `"skipped"` - it never started (dep not ok, or aborted by fail_fast).
- **Retries**: if an attempt raises, re-run the factory up to `retries`
  extra times. `attempts` = number of attempts actually made (success stops
  retrying). Cancellation is not retried.
- **fail_policy="fail_fast"**: the first time any job FAILS (exhausts
  retries), cancel all currently-executing jobs (their status:
  `"cancelled"`) and start nothing else (remaining: `"skipped"`). The
  failing job keeps `"failed"`. `run()` still returns normally with the
  full dict - it must NOT raise.
- **fail_policy="continue"**: keep running everything whose deps are ok;
  jobs whose deps did not end `"ok"` are `"skipped"`.
- Unknown dep name, duplicate job name, or dependency cycle -> `add_job`
  or `run` raises `ValueError` before any job starts.
- `run()` returns a dict with a JobResult for EVERY registered job.

Python 3.13 stdlib only. Work only in this directory. Hidden asyncio tests
grade exact statuses, attempt counts, concurrency ceiling, and ordering.
Hard cap: finish within 10 minutes of wall clock.
