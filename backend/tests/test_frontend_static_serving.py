"""
Covers the FRONTEND_DIST static-serving block in main.py -- the piece
that lets the packaged AppImage serve the built React app and the API
from one process/port. Normal dev (`npm run dev`) never sets
FRONTEND_DIST, so this is exercised nowhere else in the suite.

Isolated in its own file and reloads backend.main under a monkeypatched
env var rather than importing the shared `app`/`client` fixtures --
FRONTEND_DIST is only read at module import time, and conftest.py's
`app` reference was already bound before this test file ever runs.
Reloading here creates a separate app object, so nothing here can leak
into (or be affected by) the rest of the suite.
"""
import importlib

from fastapi.testclient import TestClient


def test_serves_built_index_html_and_falls_back_for_spa_routes(tmp_path, monkeypatch):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html><body>stud-os shell</body></html>")
    (dist / "assets" / "app.js").write_text("console.log('hi')")
    (dist / "favicon.ico").write_bytes(b"\x00")

    monkeypatch.setenv("FRONTEND_DIST", str(dist))
    import backend.main as main_module
    importlib.reload(main_module)

    try:
        with TestClient(main_module.app) as client:
            # API routes still work -- the catch-all must not shadow them.
            assert client.get("/api/health").json() == {"status": "ok"}

            # Root serves the built index.html.
            root = client.get("/")
            assert root.status_code == 200
            assert "stud-os shell" in root.text

            # A client-side route (React Router, not a real file on disk)
            # falls back to index.html instead of 404ing.
            spa_route = client.get("/notes")
            assert spa_route.status_code == 200
            assert "stud-os shell" in spa_route.text

            # A real built asset is served as itself, not the fallback.
            asset = client.get("/assets/app.js")
            assert asset.status_code == 200
            assert "console.log" in asset.text

            # A real top-level file (favicon) is served as itself too.
            favicon = client.get("/favicon.ico")
            assert favicon.status_code == 200
    finally:
        # Restore the module to its normal (no FRONTEND_DIST) state so a
        # stray import elsewhere later in the run doesn't pick up the
        # static-serving routes by surprise.
        monkeypatch.delenv("FRONTEND_DIST", raising=False)
        importlib.reload(main_module)


def test_no_static_routes_registered_without_frontend_dist(monkeypatch):
    monkeypatch.delenv("FRONTEND_DIST", raising=False)
    import backend.main as main_module
    importlib.reload(main_module)

    with TestClient(main_module.app) as client:
        assert client.get("/api/health").json() == {"status": "ok"}
        # No FRONTEND_DIST -> no catch-all -> an arbitrary unknown path
        # is a real 404, not an accidental index.html fallback.
        assert client.get("/some/random/path").status_code == 404
