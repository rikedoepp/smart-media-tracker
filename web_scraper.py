import re
import html
import socket
from urllib.parse import urlparse
from typing import Optional
import requests
from bs4 import BeautifulSoup

# Network safety defaults
REQUEST_TIMEOUT = 10  # seconds
MAX_CONTENT_BYTES = 1_000_000  # 1 MB hard cap for preview extraction
HEADERS = {
    "User-Agent": "MediaTrackerBot/1.0 (+https://example.com) requests"
}


def _is_private_ip(ip: str) -> bool:
    try:
        import ipaddress

        addr = ipaddress.ip_address(ip)
        return addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved
    except Exception:
        return True  # fail closed


def _resolve_and_validate_host(hostname: str) -> None:
    # Resolve to protect against SSRF / internal host access
    try:
        infos = socket.getaddrinfo(hostname, None)
    except Exception as e:
        raise ValueError(f"DNS resolution failed for {hostname}") from e

    for family, _, _, _, sockaddr in infos:
        ip = sockaddr[0]
        if _is_private_ip(ip):
            raise ValueError("Blocked private or local IP address")


def _validate_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http/https URLs are allowed")
    if not parsed.netloc:
        raise ValueError("URL missing host")
    _resolve_and_validate_host(parsed.hostname)
    return url


def extract_domain_from_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        return parsed.netloc or ""
    except Exception:
        return ""


def _clean_text(text: str) -> str:
    # Collapse whitespace and escape odd HTML entities
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_article_title(url: str) -> Optional[str]:
    try:
        _validate_url(url)
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Try common title locations
        if soup.title and soup.title.string:
            return _clean_text(soup.title.string)

        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return _clean_text(og_title["content"])

        h1 = soup.find("h1")
        if h1 and h1.get_text():
            return _clean_text(h1.get_text())
    except Exception:
        return None
    return None


def get_website_text_content(url: str) -> Optional[str]:
    """
    Fetches the page and extracts a reasonable article-like text.
    Keeps things simple: grabs common containers or falls back to paragraphs.
    Safety: URL validation, size cap, request timeout.
    """
    _validate_url(url)
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True, stream=True)
    resp.raise_for_status()

    # Enforce content-size limit
    content = b""
    for chunk in resp.iter_content(chunk_size=8192):
        content += chunk
        if len(content) > MAX_CONTENT_BYTES:
            break

    text = content.decode(resp.encoding or "utf-8", errors="replace")
    soup = BeautifulSoup(text, "html.parser")

    # Prefer common article containers
    selectors = [
        {"name": "article"},
        {"name": "div", "attrs": {"itemprop": "articleBody"}},
        {"name": "div", "attrs": {"role": "main"}},
        {"name": "main"},
    ]

    for sel in selectors:
        node = soup.find(**sel)
        if node:
            joined = " ".join(p.get_text(separator=" ", strip=True) for p in node.find_all(["p", "h2", "li"]))
            cleaned = _clean_text(joined)
            if cleaned:
                return cleaned

    # Fallback to paragraphs
    paras = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
    cleaned = _clean_text(" ".join(paras))
    return cleaned or None
