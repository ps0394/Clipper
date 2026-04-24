"""F4.1 tri-fetcher unit tests.

Uses a local http server that routes requests by path and Accept header
so we exercise the real httpx code path without mocking transports.
"""
from __future__ import annotations

import http.server
import socketserver
import threading
from urllib.parse import urlparse

import pytest

from retrievability.phase5.fetcher import (
    _looks_like_markdown,
    fetch_markdown,
)


# --- markdown-gate unit tests ----------------------------------------------


def test_looks_like_markdown_accepts_markdown_ct():
    assert _looks_like_markdown("anything really", "text/markdown; charset=utf-8")


def test_looks_like_markdown_rejects_html_in_disguise():
    body = "<!doctype html><html><head><title>x</title></head><body>hi</body></html>"
    assert not _looks_like_markdown(body, "text/html")


def test_looks_like_markdown_accepts_md_markers_in_plain_text():
    body = "# My Title\n\nSome prose with a `code` word.\n"
    assert _looks_like_markdown(body, "text/plain")


def test_looks_like_markdown_rejects_plain_text_without_markers():
    body = "Just some prose. No structure. Nothing to see.\n"
    assert not _looks_like_markdown(body, "text/plain")


# --- tri-fetcher integration tests against a local server -------------------


class _FakeHandler(http.server.BaseHTTPRequestHandler):
    # class-level routing table, set in the fixture
    routes: dict = {}

    def log_message(self, fmt, *args):  # pragma: no cover - silence test logs
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        key = parsed.path
        accept = (self.headers.get("Accept") or "").lower()
        route = self.routes.get(key)
        if route is None:
            self.send_response(404)
            self.end_headers()
            return
        # route: dict with either "html" and/or "md" subkeys, each
        # (status, content_type, body). Server chooses by Accept header:
        # if markdown is requested and "md" exists, return it; else html.
        if "markdown" in accept and "md" in route:
            status, ct, body = route["md"]
        elif "html" in route:
            status, ct, body = route["html"]
        elif "md" in route:
            status, ct, body = route["md"]
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(status)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))


@pytest.fixture
def fake_server():
    _FakeHandler.routes = {}
    server = socketserver.TCPServer(("127.0.0.1", 0), _FakeHandler)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}", _FakeHandler.routes
    server.shutdown()
    server.server_close()


def test_tri_fetcher_resolves_via_accept_header(fake_server):
    base, routes = fake_server
    routes["/docs/page"] = {
        "html": (200, "text/html", "<!doctype html><html><body>hi</body></html>"),
        "md":   (200, "text/markdown", "# Page\n\nHello.\n"),
    }
    body, meta = fetch_markdown(f"{base}/docs/page")
    assert body is not None
    assert body.startswith("# Page")
    assert meta["resolved_by"] == "accept_header"
    assert meta["attempts"][0]["ok"] is True


def test_tri_fetcher_falls_through_to_link_alternate(fake_server):
    base, routes = fake_server
    # Page serves HTML regardless of Accept header (server ignores it).
    md_path = "/docs/page.markdown"
    html_body = (
        '<!doctype html><html><head>'
        f'<link rel="alternate" type="text/markdown" href="{md_path}">'
        '</head><body>hi</body></html>'
    )
    routes["/docs/page"] = {"html": (200, "text/html", html_body)}
    routes[md_path] = {"md": (200, "text/markdown", "# From link-alternate\n")}
    body, meta = fetch_markdown(f"{base}/docs/page")
    assert body is not None
    assert body.startswith("# From link-alternate")
    assert meta["resolved_by"] == "link_alternate"
    assert meta["link_href"] == md_path


def test_tri_fetcher_falls_through_to_sibling_md(fake_server):
    base, routes = fake_server
    routes["/docs/page.html"] = {
        "html": (200, "text/html", "<!doctype html><html><body>hi</body></html>"),
    }
    routes["/docs/page.md"] = {
        "md": (200, "text/markdown", "# From sibling\n"),
    }
    body, meta = fetch_markdown(f"{base}/docs/page.html")
    assert body is not None
    assert body.startswith("# From sibling")
    assert meta["resolved_by"] == "sibling_md"


def test_tri_fetcher_records_miss_on_html_only_site(fake_server):
    base, routes = fake_server
    routes["/docs/page"] = {
        "html": (200, "text/html", "<!doctype html><html><body>hi</body></html>"),
    }
    body, meta = fetch_markdown(f"{base}/docs/page")
    assert body is None
    assert meta["resolved_by"] is None
    # Every step must be recorded for F4.3 diagnostics.
    probes = [a["probe"] for a in meta["attempts"]]
    assert probes == ["accept_header", "link_alternate", "sibling_md"]
    assert all(a["ok"] is False for a in meta["attempts"])


def test_tri_fetcher_rejects_html_disguised_as_markdown(fake_server):
    base, routes = fake_server
    # Server advertises text/markdown but returns HTML anyway. The gate
    # should reject it so the downstream pipeline never grades HTML-as-md.
    routes["/docs/page"] = {
        "html": (200, "text/markdown", "<!doctype html><html><body>hi</body></html>"),
        "md":   (200, "text/markdown", "<!doctype html><html><body>hi</body></html>"),
    }
    body, meta = fetch_markdown(f"{base}/docs/page")
    assert body is None, "HTML-in-disguise must not be accepted as markdown"
    assert meta["resolved_by"] is None
