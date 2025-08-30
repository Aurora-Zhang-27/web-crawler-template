# core/parser.py
from typing import Dict, Any, Union, Tuple, List
from bs4 import BeautifulSoup

SelectorRule = Union[str, Tuple[str, str]]  # either CSS selector (text) or (selector, attr)


def extract_fields(html: str, selectors: Dict[str, SelectorRule]) -> Dict[str, Any]:
    """
    Generic field extractor using BeautifulSoup.

    - html: raw HTML string
    - selectors: mapping field_name -> selector or (selector, attribute)
      Examples:
        { "title": "h1.node-title",
          "pdf": ("a.download", "href") }

    Returns a dict of extracted values. If element not found -> None.
    """
    soup = BeautifulSoup(html or "", "html.parser")
    out: Dict[str, Any] = {}

    for field, rule in (selectors or {}).items():
        if not rule:
            out[field] = None
            continue

        # attribute extraction: (selector, attr)
        if isinstance(rule, (list, tuple)) and len(rule) == 2:
            sel, attr = rule
            elem = soup.select_one(sel)
            if not elem:
                out[field] = None
            else:
                # fetch attribute safely
                out[field] = elem.get(attr, None)
            continue

        # string rule -> CSS selector for text
        if isinstance(rule, str):
            # If selector contains '||' treat as multi-selector fallback
            if '||' in rule:
                parts = [r.strip() for r in rule.split('||') if r.strip()]
            else:
                parts = [rule]

            value = None
            for part in parts:
                elem = soup.select_one(part)
                if elem:
                    text = elem.get_text(separator=' ', strip=True)
                    if text:
                        value = text
                        break
            out[field] = value
            continue

        # Unknown rule type
        out[field] = None

    return out
