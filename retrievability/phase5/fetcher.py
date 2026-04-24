"""Phase 5 dual-mode fetchers.

Two fetchers, one interface. Each returns ``(html, metadata_dict)``.

- :func:`fetch_raw` uses httpx — what a non-JS-executing agent sees
  (RAG crawlers, search indexers, API-based agents, most LLM training
  scrapers).
- :func:`fetch_rendered` uses Playwright + Chromium — what a
  browser-using agent sees (ChatGPT web tool, Claude computer use,
  Perplexity's own crawler, human-in-the-loop workflows).

Pages that fail one mode but succeed in the other are not errors — the
asymmetry is the data Phase 5 measures. Both fetchers raise on hard
failure (network error, non-2xx status) so callers can record a clean
"this fetch was attempted and failed" record. Callers should NOT
collapse a fetch failure to an empty string; that destroys the
asymmetry.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Tuple

import httpx

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36 Clipper-Phase5/0.1"
)
RAW_TIMEOUT_S = 30.0

# Rendered mode parameters chosen from probe data:
# - networkidle alone is insufficient for most modern SPAs (Next.js,
#   Docusaurus, Mintlify) — they finish XHRs before mounting content.
# - Waiting on a body-text-length threshold is a more reliable hydration
#   signal. Threshold matches the runner's MIN_DOCUMENT_CHARS so anything
#   that clears it would clear the runner's downstream guard too.
RENDERED_NAVIGATION_TIMEOUT_MS = 25_000
RENDERED_HYDRATION_TIMEOUT_MS = 15_000
RENDERED_HYDRATION_TEXT_THRESHOLD = 1500


def fetch_raw(url: str) -> Tuple[str, Dict[str, Any]]:
    """Fetch ``url`` with plain httpx (no JS execution).

    Returns the response body as text plus a metadata dict:
    ``{mode: "raw", status, final_url, bytes, elapsed_s, content_type}``.
    Raises on network failure or non-2xx status.
    """
    t0 = time.time()
    with httpx.Client(
        follow_redirects=True,
        timeout=RAW_TIMEOUT_S,
        headers={"User-Agent": USER_AGENT},
    ) as c:
        r = c.get(url)
        r.raise_for_status()
        meta = {
            "mode": "raw",
            "status": r.status_code,
            "final_url": str(r.url),
            "bytes": len(r.text),
            "elapsed_s": round(time.time() - t0, 3),
            "content_type": r.headers.get("content-type", ""),
        }
        return r.text, meta


def fetch_rendered(url: str) -> Tuple[str, Dict[str, Any]]:
    """Fetch ``url`` with Playwright Chromium and capture hydrated DOM.

    The strategy is:

    1. Navigate with ``wait_until='domcontentloaded'`` (fast, deterministic).
    2. Then wait for either ``networkidle`` (best-effort, 8 s cap) or
       a ``document.body.innerText.length > 1500`` predicate, whichever
       resolves first. The text-length predicate is the actual signal
       that an SPA finished hydrating; ``networkidle`` is a useful
       fallback for pages that lazy-load below the fold.
    3. Capture ``page.content()`` (the post-hydration serialized DOM).

    Returns the rendered HTML plus a metadata dict:
    ``{mode: "rendered", status, final_url, bytes, elapsed_s,
       hydration_signal, console_errors}``.

    ``hydration_signal`` is one of: ``"text_threshold"`` (the body-text
    predicate fired), ``"networkidle"`` (only networkidle resolved),
    ``"timeout"`` (neither fired before the cap; we captured what we
    had). Pages with ``"timeout"`` are not failures — they're the
    SPA-hostile-to-agents finding.

    Raises on hard navigation failure or non-2xx status.
    """
    # Lazy import so importing this module doesn't pay the Playwright
    # import cost when only the raw fetcher is used (tests, probe scripts).
    from playwright.sync_api import sync_playwright

    t0 = time.time()
    console_errors: list[str] = []
    hydration_signal = "timeout"
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            ctx = browser.new_context(user_agent=USER_AGENT)
            page = ctx.new_page()
            page.on("pageerror", lambda exc: console_errors.append(str(exc)[:200]))
            response = page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=RENDERED_NAVIGATION_TIMEOUT_MS,
            )
            if response is None:
                raise RuntimeError("navigation returned no response")
            status = response.status
            if status >= 400:
                # Mirror httpx.raise_for_status semantics
                raise RuntimeError(f"rendered fetch returned HTTP {status}")
            # Race networkidle vs hydration text threshold. Either signal
            # is enough; we don't require both.
            try:
                page.wait_for_function(
                    f"document.body && document.body.innerText.length > "
                    f"{RENDERED_HYDRATION_TEXT_THRESHOLD}",
                    timeout=RENDERED_HYDRATION_TIMEOUT_MS,
                )
                hydration_signal = "text_threshold"
            except Exception:
                # Fall back to a brief networkidle wait. Many SPAs finish
                # all XHRs but never reach the text threshold (e.g. their
                # content is in a virtualized list); networkidle is a
                # weaker but useful second signal.
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                    hydration_signal = "networkidle"
                except Exception:
                    hydration_signal = "timeout"
            html = page.content()
            final_url = page.url
        finally:
            browser.close()
    meta = {
        "mode": "rendered",
        "status": status,
        "final_url": final_url,
        "bytes": len(html),
        "elapsed_s": round(time.time() - t0, 3),
        "hydration_signal": hydration_signal,
        "console_errors": console_errors[:10],  # cap noise
    }
    return html, meta


# --- F4.1 tri-fetcher markdown path -----------------------------------------

# Heuristic gate for "this body is actually markdown". Avoids misidentifying
# an HTML 200 returned by servers that silently ignore our Accept header.
# Rationale: a real markdown page has at least one of these signals within
# the first 2 KB: ATX headings, fenced code blocks, bullet/numbered lists,
# or explicit front-matter. An HTML fallback will instead start with `<!`
# or `<html` / `<!DOCTYPE`.
_MARKDOWN_POSITIVE_MARKERS = ("\n# ", "# ", "\n## ", "```", "\n- ", "\n* ", "\n1. ", "---\n")
_HTML_NEGATIVE_MARKERS = ("<!doctype", "<html", "<!--", "<head", "<body")


def _looks_like_markdown(body: str, content_type: str) -> bool:
    """Return True iff the body is plausibly markdown, not HTML-in-disguise.

    Servers routinely respond 200 with `Content-Type: text/html` when asked
    for `text/markdown` — or, worse, advertise `Content-Type: text/markdown`
    while returning an HTML body. This guard protects the downstream
    pipeline from grading HTML as markdown: regardless of Content-Type, a
    body that starts with obvious HTML markers (`<!doctype`, `<html`, etc.)
    is rejected. Beyond that:

    - If Content-Type advertises markdown, accept.
    - Else require positive markdown markers (ATX headings, fences, lists,
      front-matter) within the first 2 KB.
    """
    head = body[:2048].lower().lstrip()
    if any(head.startswith(m) for m in _HTML_NEGATIVE_MARKERS):
        return False
    if any(m in head for m in _HTML_NEGATIVE_MARKERS):
        # HTML markers appear very early but after whitespace/BOM — still HTML.
        return False
    ct = (content_type or "").lower()
    if "markdown" in ct:
        return True
    if ct.startswith("text/plain") and body.lstrip().startswith("#"):
        return True
    return any(m in body[:2048] for m in _MARKDOWN_POSITIVE_MARKERS)


def _probe_markdown_accept(url: str, client: httpx.Client) -> Tuple[str, Dict[str, Any]] | None:
    """Step 1: content-negotiate `text/markdown` against the HTML URL.

    Returns (body, meta) on success; None on failure (non-2xx, disguised
    HTML, empty body). Meta carries `probe: "accept_header"`.
    """
    try:
        r = client.get(url, headers={"Accept": "text/markdown, */*;q=0.1"})
    except httpx.HTTPError:
        return None
    if r.status_code >= 400 or not r.text.strip():
        return None
    ct = r.headers.get("content-type", "")
    if not _looks_like_markdown(r.text, ct):
        return None
    return r.text, {
        "probe": "accept_header",
        "resolved_url": str(r.url),
        "status": r.status_code,
        "content_type": ct,
        "bytes": len(r.text),
    }


def _probe_markdown_alternate(
    html_body: str, base_url: str, client: httpx.Client
) -> Tuple[str, Dict[str, Any]] | None:
    """Step 2: honour `<link rel="alternate" type="text/markdown">` in HTML.

    Returns (body, meta) or None. `html_body` is the already-fetched HTML;
    we don't re-fetch it. Meta carries `probe: "link_alternate"` and the
    href that was resolved.
    """
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin

    soup = BeautifulSoup(html_body, "html.parser")
    href = None
    for link in soup.find_all("link", rel=lambda r: r and "alternate" in r):
        link_type = (link.get("type") or "").lower()
        if "markdown" in link_type and link.get("href"):
            href = link["href"]
            break
    if not href:
        return None
    resolved = urljoin(base_url, href)
    try:
        r = client.get(resolved, headers={"Accept": "text/markdown, */*;q=0.1"})
    except httpx.HTTPError:
        return None
    if r.status_code >= 400 or not r.text.strip():
        return None
    ct = r.headers.get("content-type", "")
    if not _looks_like_markdown(r.text, ct):
        return None
    return r.text, {
        "probe": "link_alternate",
        "link_href": href,
        "resolved_url": str(r.url),
        "status": r.status_code,
        "content_type": ct,
        "bytes": len(r.text),
    }


def _probe_markdown_sibling(url: str, client: httpx.Client) -> Tuple[str, Dict[str, Any]] | None:
    """Step 3: probe for a sibling `.md` path.

    Tries (in order): `<url>.md`, `<url-stripped-of-trailing-slash>.md`,
    `<url-dir>/index.md`. Returns the first that returns 2xx and looks
    like markdown. Meta carries `probe: "sibling_md"` and which variant
    succeeded.
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    path = parsed.path or "/"
    candidates: list[str] = []
    # Case A: URL already ends in a filename with no extension -> append .md
    if path.endswith("/"):
        # /foo/bar/ -> /foo/bar/index.md and /foo/bar.md (strip trailing /)
        candidates.append(f"{parsed.scheme}://{parsed.netloc}{path}index.md")
        if len(path) > 1:
            candidates.append(f"{parsed.scheme}://{parsed.netloc}{path.rstrip('/')}.md")
    else:
        # /foo/bar or /foo/bar.html -> /foo/bar.md
        if path.endswith(".html") or path.endswith(".htm"):
            stem = path.rsplit(".", 1)[0]
            candidates.append(f"{parsed.scheme}://{parsed.netloc}{stem}.md")
        else:
            candidates.append(f"{parsed.scheme}://{parsed.netloc}{path}.md")
    # Dedup while preserving order.
    seen: set[str] = set()
    ordered: list[str] = []
    for c in candidates:
        if c not in seen:
            ordered.append(c)
            seen.add(c)

    for candidate in ordered:
        try:
            r = client.get(candidate, headers={"Accept": "text/markdown, */*;q=0.1"})
        except httpx.HTTPError:
            continue
        if r.status_code >= 400 or not r.text.strip():
            continue
        ct = r.headers.get("content-type", "")
        if not _looks_like_markdown(r.text, ct):
            continue
        return r.text, {
            "probe": "sibling_md",
            "candidate_url": candidate,
            "resolved_url": str(r.url),
            "status": r.status_code,
            "content_type": ct,
            "bytes": len(r.text),
        }
    return None


def fetch_markdown(
    url: str,
    *,
    html_body: str | None = None,
) -> Tuple[str | None, Dict[str, Any]]:
    """F4.1 tri-fetcher: resolve a page to its served-markdown source.

    Resolution order (per PRD §7.4):

    1. Content negotiate ``Accept: text/markdown`` against the HTML URL.
    2. Honour ``<link rel="alternate" type="text/markdown" href="...">``
       in the page's HTML (requires ``html_body`` or an inline fetch).
    3. Probe sibling ``.md`` paths: ``<url>.md`` or the closest analogue
       for URLs ending in ``.html``/``.htm``/``/``.

    Each step falls through on failure. Returns ``(body, meta)`` where
    ``body`` is the markdown text on success or ``None`` on total miss,
    and ``meta`` always carries at minimum ``{"attempts": [...],
    "resolved_by": <probe-name or None>, "elapsed_s": float}``.

    This is a *pure HTTP* operation: no browser, no Playwright. Designed
    to run alongside :func:`fetch_raw` and :func:`fetch_rendered` during
    corpus-002/003 re-grading. It deliberately does not raise on miss —
    "no markdown available" is a first-class recordable outcome for F4.3.
    """
    t0 = time.time()
    attempts: list[Dict[str, Any]] = []
    with httpx.Client(
        follow_redirects=True,
        timeout=RAW_TIMEOUT_S,
        headers={"User-Agent": USER_AGENT},
    ) as c:
        # Step 1
        r1 = _probe_markdown_accept(url, c)
        if r1 is not None:
            body, meta = r1
            attempts.append({k: v for k, v in meta.items() if k != "probe"} | {"probe": "accept_header", "ok": True})
            return body, {
                "mode": "markdown",
                "resolved_by": "accept_header",
                "attempts": attempts,
                "elapsed_s": round(time.time() - t0, 3),
                **{k: meta[k] for k in ("resolved_url", "status", "content_type", "bytes")},
            }
        attempts.append({"probe": "accept_header", "ok": False})

        # Step 2 — needs the HTML body
        if html_body is None:
            try:
                r = c.get(url)
                r.raise_for_status()
                html_body = r.text
            except httpx.HTTPError:
                html_body = ""
        r2 = _probe_markdown_alternate(html_body, url, c) if html_body else None
        if r2 is not None:
            body, meta = r2
            attempts.append({k: v for k, v in meta.items() if k != "probe"} | {"probe": "link_alternate", "ok": True})
            return body, {
                "mode": "markdown",
                "resolved_by": "link_alternate",
                "attempts": attempts,
                "elapsed_s": round(time.time() - t0, 3),
                **{k: meta[k] for k in ("resolved_url", "status", "content_type", "bytes", "link_href")},
            }
        attempts.append({"probe": "link_alternate", "ok": False})

        # Step 3
        r3 = _probe_markdown_sibling(url, c)
        if r3 is not None:
            body, meta = r3
            attempts.append({k: v for k, v in meta.items() if k != "probe"} | {"probe": "sibling_md", "ok": True})
            return body, {
                "mode": "markdown",
                "resolved_by": "sibling_md",
                "attempts": attempts,
                "elapsed_s": round(time.time() - t0, 3),
                **{k: meta[k] for k in ("resolved_url", "status", "content_type", "bytes", "candidate_url")},
            }
        attempts.append({"probe": "sibling_md", "ok": False})

    return None, {
        "mode": "markdown",
        "resolved_by": None,
        "attempts": attempts,
        "elapsed_s": round(time.time() - t0, 3),
    }