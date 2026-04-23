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
