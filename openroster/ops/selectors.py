"""Rule-based selector suggestions for a changed HTML source: find repeated sibling blocks whose text contains
dates. Used in health issues and as the starting point for the AI repair job."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from selectolax.lexbor import LexborHTMLParser as HTMLParser
from selectolax.lexbor import LexborNode

from ..extract.dates import MDY


@dataclass
class Suggestion:
    item: str
    title: str | None
    count: int
    dated: int
    sample: str


def _sig(n: LexborNode) -> str:
    cls = (n.attributes.get("class") or "").split()
    stable = [c for c in cls if not any(ch.isdigit() for ch in c)][:2]  # skip hashed class names
    return (n.tag or "") + "".join(f".{c}" for c in stable)


def suggest(html: str, limit: int = 5) -> list[Suggestion]:
    tree = HTMLParser(html)
    found: dict[str, Suggestion] = {}
    for parent in tree.css("body *"):
        kids = [k for k in parent.iter() if k.tag not in ("-text", "script", "style")]
        if len(kids) < 3:
            continue
        sigs = Counter(_sig(k) for k in kids)
        sig, n = sigs.most_common(1)[0]
        if n < 3 or sig in found:
            continue
        same = [k for k in kids if _sig(k) == sig]
        texts = [" ".join((k.text(separator=" ") or "").split()) for k in same]
        dated = sum(1 for t in texts if MDY.search(t))
        if dated < 2:
            continue
        first = same[0]
        heading = first.css_first("h1, h2, h3, h4, h5, h6, a, strong")
        found[sig] = Suggestion(
            item=sig, title=_sig(heading) if heading is not None else None, count=len(same), dated=dated,
            sample=texts[0][:160],
        )
    return sorted(found.values(), key=lambda s: (s.dated, s.count), reverse=True)[:limit]
