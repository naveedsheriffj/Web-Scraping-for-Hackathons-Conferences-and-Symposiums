"""
URL normalization and canonicalization helpers.
"""

from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse
from typing import Optional

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "ref", "ref_feature", "ref_medium", "ref_content", "gclid", "fbclid"
}


def canonicalize_url(url: Optional[str], base_url: Optional[str] = None) -> Optional[str]:
    """
    Normalizes and canonicalizes URL strings:
    - Resolves relative links against base_url
    - Strips fragment identifiers (#...)
    - Removes tracking parameters (utm_*, ref, ref_*, etc.)
    - Removes redundant trailing slashes for clean paths
    """
    if not url:
        return None

    cleaned = url.strip()
    if base_url and not cleaned.startswith(("http://", "https://")):
        cleaned = urljoin(base_url, cleaned)

    parsed = urlparse(cleaned)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None

    # Filter out tracking query parameters
    query_params = parse_qs(parsed.query, keep_blank_values=False)
    filtered_params = {
        k: v for k, v in query_params.items()
        if k.lower() not in TRACKING_PARAMS
    }
    new_query = urlencode(filtered_params, doseq=True)

    # Clean path (strip trailing slash unless path is '/')
    path = parsed.path
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    # Reconstruct URL without fragment
    canonical = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        path,
        parsed.params,
        new_query,
        ""  # Remove fragment
    ))

    return canonical


def extract_canonical_link(page_element, base_url: Optional[str] = None) -> Optional[str]:
    """
    Extracts canonical URL from <link rel="canonical" href="..."> tag if present in DOM.
    Returns canonicalized URL or None.
    """
    if page_element is None:
        return None
    
    try:
        if hasattr(page_element, "css"):
            canonical_tags = page_element.css('link[rel="canonical"]::attr(href)')
            if canonical_tags:
                href = canonical_tags[0].get() if hasattr(canonical_tags[0], "get") else str(canonical_tags[0])
                return canonicalize_url(href, base_url=base_url)
    except Exception:
        pass

    return None


def normalize_url(url: Optional[str], base_url: Optional[str] = None) -> Optional[str]:
    """Alias for canonicalize_url."""
    return canonicalize_url(url, base_url=base_url)
