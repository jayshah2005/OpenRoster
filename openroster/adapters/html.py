"""Server-rendered HTML lists with per-source selectors, plus the headless last resort.

Source options:
  item:        CSS selector for one event block (required)
  title:       selector inside the item for the title (default: first heading or link)
  date:        selector for the date text (default: the whole item text)
  link:        selector for the link (default: first a[href])
  location:    selector for location text (optional)
  infer_year:  true if the source lists dates without a year (see extract/dates.py)
  title_template: e.g. "Scotiabank on campus: {title}"
  item_filter: regex an item's text must match (e.g. "hackathon|competition")
  each_date:   one item lists several sessions; emit one candidate per date
  strip:       regexes removed from the item text before keyword classification (field labels)
  default_mode: mode to use when the item does not say (e.g. "online" for a webinar list)
  wait_for:    (headless only) selector to wait for before reading the page
"""

from __future__ import annotations

import hashlib
import re
from urllib.parse import urljoin

from selectolax.lexbor import LexborHTMLParser as HTMLParser
from selectolax.lexbor import LexborNode as Node

from ..config import Source
from ..extract.dates import MDY as MONTH_DAY
from ..extract.dates import has_ambiguous_date, parse_when
from ..fetch import Fetcher, FetchRefused, policy_check
from .base import Adapter, AdapterResult, Candidate
from .common import clean, keep


def _text(node: Node | None) -> str:
    return clean(node.text(separator=" ")) if node is not None else ""


def fingerprint(tree: HTMLParser, item_sel: str) -> str:
    """A structure signature: how many items match, and the tag/class path of the first item's children."""
    items = tree.css(item_sel)
    shape = ""
    if items:
        child_tags = [f"{c.tag}.{(c.attributes.get('class') or '').split(' ')[0]}" for c in items[0].iter()]
        shape = "|".join(child_tags[:12])
    bucket = "0" if not items else "1-4" if len(items) < 5 else "5+"
    return hashlib.sha1(f"{bucket}:{shape}".encode()).hexdigest()[:12]


def parse_html_list(html_text: str, page_url: str, source: Source) -> AdapterResult:
    o = source.options
    res = AdapterResult()
    tree = HTMLParser(html_text)
    res.fingerprint = fingerprint(tree, o["item"])
    for item in tree.css(o["item"]):
        res.raw_count += 1
        item_text = _text(item)
        if o.get("item_filter") and not re.search(o["item_filter"], item_text, re.I):
            continue
        title_node = item.css_first(o["title"]) if o.get("title") else (
            item.css_first("h1, h2, h3, h4, h5") or item.css_first("a")
        )
        title = _text(title_node)
        if not title:
            continue
        if o.get("title_template"):
            title = o["title_template"].format(title=title)
        link_node = item.css_first(o["link"]) if o.get("link") else item.css_first("a[href]")
        if link_node is None and item.tag == "a":
            link_node = item
        href = link_node.attributes.get("href") if link_node is not None else None
        url = urljoin(page_url, href) if href else page_url
        date_text = " ".join(_text(n) for n in item.css(o["date"])) if o.get("date") else item_text
        loc_text = _text(item.css_first(o["location"])) if o.get("location") else ""
        if not keep(source, item_text, title):
            continue
        class_text = item_text
        for rx in o.get("strip", []):  # labels like "Virtual/In-person:" that would confuse keyword rules
            class_text = re.sub(rx, " ", class_text, flags=re.I)
        infer = bool(o.get("infer_year"))
        # each_date: one block lists several sessions ("Oct 22 | 2-3 PM | Nov 19 | 3-4 PM") -> one candidate each
        chunks = _date_chunks(date_text) if o.get("each_date") else [date_text]
        for chunk in chunks:
            parsed = parse_when(chunk, source.timezone, infer_year=infer)
            cand = Candidate(
                source_id=source.id,
                adapter="html",
                url=url,
                title=title,
                timezone=source.timezone,
                venue=loc_text or None,
                mode=o.get("default_mode"),
                text=class_text,
            )
            if parsed:
                cand.start, cand.end, cand.all_day = parsed.start, parsed.end, parsed.all_day
                cand.timezone = parsed.timezone
                cand.date_evidence, cand.date_confidence = parsed.evidence, parsed.confidence
                if len(chunks) > 1:
                    cand.series_id = f"{source.id}|{url}|{title}"
            else:
                cand.date_confidence = "none"
                cand.date_evidence = chunk[:300]
                cand.review_reasons.append(
                    "ambiguous numeric date" if has_ambiguous_date(chunk) else "no date could be parsed with confidence"
                )
            res.candidates.append(cand)
    return res


def _date_chunks(text: str) -> list[str]:
    """Split text at each month-day date so every session gets its own following time range."""
    starts = [m.start() for m in MONTH_DAY.finditer(text)]
    if not starts:
        return [text]
    return [text[a:b] for a, b in zip(starts, [*starts[1:], len(text)], strict=True)]


class HtmlAdapter(Adapter):
    name = "html"

    def run(self, source: Source, fetcher: Fetcher) -> AdapterResult:
        res = AdapterResult()
        for url in [source.url, *source.options.get("urls", [])]:
            r = fetcher.get(url, source_id=source.id)
            page = parse_html_list(r.text, url, source)
            res.candidates += page.candidates
            res.raw_count += page.raw_count
            res.fingerprint = res.fingerprint or page.fingerprint
            res.pages += 1
        return res


class HeadlessAdapter(Adapter):
    """Renders the page in Chromium (Playwright), then reuses the HTML list parser.

    Same politeness rules: policy and robots checks go through the Fetcher, the budget is one page per URL,
    and the per-host interval is honoured. Images, fonts and media are not downloaded.
    """

    name = "headless"

    def run(self, source: Source, fetcher: Fetcher) -> AdapterResult:
        from playwright.sync_api import sync_playwright  # optional dependency

        from ..config import user_agent

        res = AdapterResult()
        urls = [source.url, *source.options.get("urls", [])]
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            ctx = browser.new_context(user_agent=user_agent())

            def block_heavy(route):  # type: ignore[no-untyped-def]
                req = route.request
                try:
                    policy_check(req.url)
                except FetchRefused:
                    return route.abort()
                if req.resource_type in ("image", "media", "font"):
                    return route.abort()
                return route.continue_()

            ctx.route("**/*", block_heavy)
            page = ctx.new_page()
            for url in urls:
                policy_check(url)
                if not fetcher.robots_allows(url):
                    raise FetchRefused(f"{url}: disallowed by robots.txt")
                fetcher._spend(source.id)
                fetcher._wait_turn(url.split("/")[2])
                page.goto(url, wait_until="networkidle", timeout=45_000)
                if source.options.get("wait_for"):
                    page.wait_for_selector(source.options["wait_for"], timeout=15_000)
                parsed = parse_html_list(page.content(), url, source)
                for c in parsed.candidates:
                    c.adapter = "headless"
                res.candidates += parsed.candidates
                res.raw_count += parsed.raw_count
                res.fingerprint = res.fingerprint or parsed.fingerprint
                res.pages += 1
            browser.close()
        return res
