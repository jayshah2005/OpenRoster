"""Different hosts run concurrently; the same host never does."""

import threading
import time

from openroster.parallel import by_host


class FakeFetcher:
    def close(self):
        pass


def test_same_host_is_never_concurrent_and_order_is_kept():
    active: dict[str, int] = {}
    peak: dict[str, int] = {}
    lock = threading.Lock()
    hosts_seen_together = set()

    def work(url, fetcher):
        host = url.split("/")[2]
        with lock:
            active[host] = active.get(host, 0) + 1
            peak[host] = max(peak.get(host, 0), active[host])
            if sum(1 for v in active.values() if v) > 1:
                hosts_seen_together.add(True)
        time.sleep(0.02)
        with lock:
            active[host] -= 1
        return url.upper()

    urls = [f"https://{h}.example/{i}" for i in range(4) for h in ("a", "b", "c")]
    out = by_host(urls, url_of=lambda u: u, work=work, workers=3, fetcher_factory=FakeFetcher)
    assert [u for u, _ in out] == urls and all(r == u.upper() for u, r in out)
    assert max(peak.values()) == 1          # never two at once on one host
    assert hosts_seen_together              # but different hosts overlapped
