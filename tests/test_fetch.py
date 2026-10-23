import httpx
import pytest

from openroster.fetch import BudgetExceeded, Fetcher, FetchRefused, policy_check


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.t

    def sleep(self, s: float) -> None:
        self.sleeps.append(s)
        self.t += s


def make(handler, tmp_path, **kw):
    clock = FakeClock()
    f = Fetcher(transport=httpx.MockTransport(handler), cache_dir=tmp_path, sleep=clock.sleep, clock=clock, **kw)
    return f, clock


def ok_robots(request: httpx.Request) -> httpx.Response | None:
    if request.url.path == "/robots.txt":
        return httpx.Response(200, text="User-agent: *\nDisallow: /private\n")
    return None


@pytest.mark.parametrize(
    "url",
    [
        "https://devpost.com/hackathons",
        "https://foo.devpost.com/",
        "https://mlh.io/seasons/2027/events",
        "https://www.eventbrite.ca/e/123",
        "https://lu.ma/toronto",
        "https://api.lu.ma/calendar/get-items",
        "https://docs.google.com/forms/d/abc/viewform",
        "https://tally.so/r/abc",
        "https://www.linkedin.com/events/1",
        "ftp://example.com/x",
    ],
)
def test_policy_refuses_known_blocked(url):
    with pytest.raises(FetchRefused):
        policy_check(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://api.lu.ma/ics/get?entity=calendar&id=cal-abc",
        "https://calendar.google.com/calendar/ical/x%40group.calendar.google.com/public/basic.ics",
        "https://brocku.ca/events/",
    ],
)
def test_policy_allows(url):
    policy_check(url)


def test_user_agent_is_honest(tmp_path):
    seen = {}

    def handler(request):
        if (r := ok_robots(request)) is not None:
            return r
        seen["ua"] = request.headers["user-agent"]
        return httpx.Response(200, text="hi")

    f, _ = make(handler, tmp_path)
    f.get("https://example.com/a")
    assert seen["ua"].startswith("OpenRosterBot/")
    assert "github.com/jayshah2005/OpenRoster" in seen["ua"]


def test_robots_disallow_is_obeyed(tmp_path):
    def handler(request):
        return ok_robots(request) or httpx.Response(200, text="secret")

    f, _ = make(handler, tmp_path)
    with pytest.raises(FetchRefused):
        f.get("https://example.com/private/x")


def test_robots_5xx_means_disallow(tmp_path):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(503)
        return httpx.Response(200, text="x")

    f, _ = make(handler, tmp_path, max_retries=0)
    with pytest.raises(FetchRefused):
        f.get("https://example.com/a")


def test_rate_limit_two_seconds_per_host(tmp_path):
    def handler(request):
        return ok_robots(request) or httpx.Response(200, text="x")

    f, clock = make(handler, tmp_path)
    f.get("https://example.com/a")
    f.get("https://example.com/b")
    f.get("https://other.org/c")
    # example.com: robots, a, b -> 2 waits; other.org: robots, c -> 1 wait (hosts are independent)
    assert clock.sleeps == [2.0, 2.0, 2.0]


def test_crawl_delay_is_honoured(tmp_path):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nCrawl-delay: 10\n")
        return httpx.Response(200, text="x")

    f, clock = make(handler, tmp_path)
    f.get("https://slow.example/a")
    f.get("https://slow.example/b")
    assert 10.0 in clock.sleeps


def test_redirect_to_blocked_host_is_refused(tmp_path):
    def handler(request):
        if (r := ok_robots(request)) is not None:
            return r
        return httpx.Response(302, headers={"location": "https://devpost.com/x"})

    f, _ = make(handler, tmp_path)
    with pytest.raises(FetchRefused):
        f.get("https://example.com/go")


def test_budget(tmp_path):
    def handler(request):
        return ok_robots(request) or httpx.Response(200, text="x")

    f, _ = make(handler, tmp_path)
    f.set_budget("s", 1)
    f.get("https://example.com/a", source_id="s")
    with pytest.raises(BudgetExceeded):
        f.get("https://example.com/b", source_id="s")


def test_conditional_request_uses_cache(tmp_path):
    calls = []

    def handler(request):
        if (r := ok_robots(request)) is not None:
            return r
        calls.append(request.headers.get("if-none-match"))
        if request.headers.get("if-none-match") == '"v1"':
            return httpx.Response(304)
        return httpx.Response(200, text="body", headers={"etag": '"v1"'})

    f, _ = make(handler, tmp_path)
    assert f.get("https://example.com/a").text == "body"
    f2, _ = make(handler, tmp_path)
    r = f2.get("https://example.com/a")
    assert r.from_cache and r.text == "body"
    assert calls == [None, '"v1"']


def test_backoff_on_429(tmp_path):
    n = {"c": 0}

    def handler(request):
        if (r := ok_robots(request)) is not None:
            return r
        n["c"] += 1
        if n["c"] == 1:
            return httpx.Response(429, headers={"retry-after": "7"})
        return httpx.Response(200, text="ok")

    f, clock = make(handler, tmp_path)
    assert f.get("https://example.com/a").text == "ok"
    assert 7.0 in clock.sleeps
