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
