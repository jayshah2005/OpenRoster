"""Source adapters. Each turns one kind of source (iCal, campus API, RSS, HTML, ...) into Candidates.

To add a kind of source: subclass Adapter in a new module, register it in ADAPTERS below, and add a fixture test.
"""

from .api import HackClubAdapter
from .base import Adapter
from .campus import LocalistAdapter, TribeAdapter
from .feeds import JsonAdapter, RssAdapter
from .html import HeadlessAdapter, HtmlAdapter
from .ics import IcsAdapter
from .jsonld import JsonLdAdapter, SitemapAdapter

ADAPTERS: dict[str, Adapter] = {
    a.name: a
    for a in (
        IcsAdapter(), TribeAdapter(), LocalistAdapter(), JsonLdAdapter(), SitemapAdapter(),
        HtmlAdapter(), HeadlessAdapter(), HackClubAdapter(), RssAdapter(), JsonAdapter(),
    )
}
