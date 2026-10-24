"""Run work for different websites at the same time, but never two requests to the same website at once.

Items are grouped by host. Each group goes to one worker thread with its own Fetcher, and that worker handles the
group's items one after another, so the per-host spacing, robots.txt checks and Crawl-delay in fetch.py hold
exactly as in a sequential run. Different hosts proceed in parallel, which turns a run over hundreds of sites
from hours into minutes.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit

from .fetch import Fetcher

DEFAULT_WORKERS = 8


def host_of(url: str) -> str:
    return (urlsplit(url).hostname or "").removeprefix("www.")


def by_host[T, R](
    items: Iterable[T],
    url_of: Callable[[T], str],
    work: Callable[[T, Fetcher], R],
    workers: int = DEFAULT_WORKERS,
    fetcher_factory: Callable[[], Fetcher] = Fetcher,
) -> list[tuple[T, R]]:
    """Apply `work(item, fetcher)` to every item; items on the same host share one worker and one Fetcher.

    Results come back in the original order of `items`.
    """
    ordered = list(items)
    groups: dict[str, list[int]] = defaultdict(list)
    for i, item in enumerate(ordered):
        groups[host_of(url_of(item))].append(i)

    results: dict[int, R] = {}

    def run_group(indexes: list[int]) -> None:
        fetcher = fetcher_factory()
        try:
            for i in indexes:
                results[i] = work(ordered[i], fetcher)
        finally:
            fetcher.close()

    if workers <= 1 or len(groups) <= 1:
        for indexes in groups.values():
            run_group(indexes)
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            # Longest groups first, so one slow host with a long Crawl-delay does not start last.
            for f in [pool.submit(run_group, idx) for idx in sorted(groups.values(), key=len, reverse=True)]:
                f.result()
    return [(ordered[i], results[i]) for i in range(len(ordered))]
