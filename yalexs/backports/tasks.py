from __future__ import annotations

import sys
from asyncio import AbstractEventLoop, Task, get_running_loop
from collections.abc import Coroutine
from typing import Any, TypeVar

_T = TypeVar("_T")

if sys.version_info >= (3, 12, 0):

    def create_eager_task(
        coro: Coroutine[Any, Any, _T],
        *,
        name: str | None = None,
        loop: AbstractEventLoop | None = None,
    ) -> Task[_T]:
        """Create a task from a coroutine and schedule it to run immediately."""
        return Task(coro, loop=loop or get_running_loop(), name=name, eager_start=True)

else:

    def create_eager_task(
        coro: Coroutine[Any, Any, _T],
        *,
        name: str | None = None,
        loop: AbstractEventLoop | None = None,
    ) -> Task[_T]:
        """Create a task from a coroutine and schedule it to run immediately."""
        return Task(
            coro,
            loop=loop or get_running_loop(),
            name=name,
        )
