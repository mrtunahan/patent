import asyncio
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import database
from app.config import PROJECT_ROOT, Settings
from app.core.spa import MISSING_FRONTEND_MESSAGE
from app.main import DIST_DIR, create_app

ENV_KEYS = ["HOST", "PORT", "CORS_ORIGINS", "FRAME_ANCESTORS", "ROOT_PATH"]
INDEX_HTML = "<!doctype html><html><body>INDEX-OK</body></html>"
SECRET = "TOP-SECRET-DO-NOT-LEAK"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def site(tmp_path):
    """tmp/secret.txt dist'in DIŞINDA; tmp/dist geçici frontend çıktısı."""
    (tmp_path / "secret.txt").write_text(SECRET)
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text(INDEX_HTML)
    (dist / "assets" / "app.js").write_text("console.log('app');")
    (dist / "robots.txt").write_text("User-agent: *")
    (dist / ".hidden").write_text("hidden")
    (dist / "link.txt").symlink_to(tmp_path / "secret.txt")  # dist dışına işaret eden symlink
    return dist


def make_app(dist, **overrides):
    return create_app(Settings(_env_file=None, **overrides), dist_dir=dist)


@pytest.fixture
def client(site):
    return TestClient(make_app(site))


def asgi_get(app, raw_path: str, method: str = "GET"):
    """Ham yolu (normalize edilmeden) doğrudan ASGI uygulamasına verir."""
    from urllib.parse import unquote

    sent = []

    delivered = False

    async def receive():
        # Gövde bir kez verilir; sonrasında istemci bağlı kalmış gibi askıda bekler
        # (Starlette'in bağlantı koparma dinleyicisi yanıt bitince iptal eder).
        nonlocal delivered
        if not delivered:
            delivered = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await asyncio.Event().wait()

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": method,
        "scheme": "http", "path": unquote(raw_path), "raw_path": raw_path.encode(),
        "query_string": b"", "root_path": "", "headers": [], "server": ("testserver", 80),
        "client": ("127.0.0.1", 1),
    }
    asyncio.run(app(scope, receive, send))
    status = next(m["status"] for m in sent if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return status, body.decode("utf-8", "replace")


# --- SPA fallback ve dosyalar ---

@pytest.mark.parametrize("path", ["/", "/applicants", "/patents/5", "/patents/new", "/a/b/c/d", "/settings/"])
def test_spa_routes_return_index(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert r.text == INDEX_HTML
    assert r.headers["content-type"].startswith("text/html")


def test_existing_files_served_as_is(client):
    r = client.get("/assets/app.js")
    assert r.status_code == 200 and r.text == "console.log('app');"
    r = client.get("/robots.txt")
    assert r.status_code == 200 and r.text == "User-agent: *"


def test_explicit_index_html_served(client):
    r = client.get("/index.html")
    assert r.status_code == 200 and r.text == INDEX_HTML
    assert r.headers["cache-control"] == "no-cache"


@pytest.mark.parametrize("path", ["/assets/yok.js", "/favicon.ico", "/yok.css", "/assets/", "/assets/alt/yok.png"])
def test_missing_files_with_extension_404(client, path):
    r = client.get(path)
    assert r.status_code == 404
    assert INDEX_HTML not in r.text


def test_hidden_files_not_served(client):
    for path in ("/.hidden", "/assets/.env", "/.vite/manifest.json"):
        r = client.get(path)
        assert r.status_code == 404
    assert "hidden" not in client.get("/.hidden").text


# --- /api gölgelenmiyor ---

def test_api_not_shadowed(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/patents").status_code == 501
    assert client.get("/api/settings").status_code == 501
    assert client.get("/openapi.json").status_code == 200


@pytest.mark.parametrize("path", ["/api/yok", "/api/yok/derin", "/api", "/api/"])
def test_unknown_api_paths_404_json_never_index(client, path):
    r = client.get(path)
    assert r.status_code == 404
    assert r.json() == {"detail": "Not Found"}
    assert INDEX_HTML not in r.text


def test_non_get_methods_do_not_fall_back(client):
    for method in ("POST", "PUT", "DELETE", "PATCH"):
        r = client.request(method, "/applicants-olmayan-yol", json={})
        assert r.status_code in (404, 405)
        assert INDEX_HTML not in r.text
    r = client.post("/api/health")
    assert r.status_code == 405  # gerçek yol için hâlâ 405
    assert client.post("/api/yok").status_code == 404  # bilinmeyen /api yolu: 404 JSON
    assert client.post("/api/patents", json={"title": "T", "applicant_id": 1, "fsmh_type_id": 1}).status_code == 501


def test_head_requests(client):
    r = client.head("/applicants")
    assert r.status_code == 200 and r.content == b""
    assert r.headers["content-type"].startswith("text/html")
    r = client.head("/assets/app.js")
    assert r.status_code == 200 and r.content == b""
    assert client.head("/assets/yok.js").status_code == 404
    assert client.head("/api/health").status_code == 405  # var olan GET-only API yolu
    assert client.head("/api/yok").status_code == 404


# --- path traversal ---

TRAVERSAL = [
    "/../secret.txt",
    "/%2e%2e/secret.txt",
    "/%2E%2E/secret.txt",
    "/assets/../../secret.txt",
    "/assets/%2e%2e/%2e%2e/secret.txt",
    "/..%2fsecret.txt",
    "/assets/..%2f..%2fsecret.txt",
    "/%252e%252e/secret.txt",
    "/%252e%252e%252fsecret.txt",
    "//secret.txt",
    "///etc/passwd",
    "/../backend/app/config.py",
    "/%2e%2e/.env.example",
    "/..\\secret.txt",
    "/assets/..\\..\\secret.txt",
    "/secret.txt%00.js",
    "/link.txt",  # dist içindeki symlink dışarıyı gösteriyor
]


@pytest.mark.parametrize("path", TRAVERSAL)
def test_traversal_never_leaks_via_http_client(client, path):
    r = client.get(path)
    assert SECRET not in r.text
    assert "root:" not in r.text and "class Settings" not in r.text and "FRAME_ANCESTORS" not in r.text
    assert r.status_code in (200, 400, 404)
    if r.status_code == 200:
        assert r.text == INDEX_HTML  # yalnızca SPA fallback olabilir


@pytest.mark.parametrize("path", TRAVERSAL)
def test_traversal_never_leaks_raw_asgi(site, path):
    status, body = asgi_get(make_app(site), path)
    assert SECRET not in body
    assert "class Settings" not in body and "root:" not in body and "FRAME_ANCESTORS" not in body
    if status == 200:
        assert body == INDEX_HTML


def test_symlink_escape_blocked(site):
    status, body = asgi_get(make_app(site), "/link.txt")
    assert SECRET not in body


# --- dist yok ---

def test_missing_dist_does_not_crash(tmp_path):
    app = make_app(tmp_path / "yok")
    c = TestClient(app)
    assert c.get("/api/health").json() == {"status": "ok"}
    assert c.get("/api/patents").status_code == 501
    for path in ("/", "/applicants", "/assets/x.js"):
        r = c.get(path)
        assert r.status_code == 404
        assert r.json() == {"detail": MISSING_FRONTEND_MESSAGE}
    assert c.get("/api/yok").json() == {"detail": "Not Found"}


def test_dist_without_index_treated_as_missing(tmp_path):
    (tmp_path / "dist").mkdir()
    c = TestClient(make_app(tmp_path / "dist"))
    assert c.get("/").json() == {"detail": MISSING_FRONTEND_MESSAGE}
    assert c.get("/api/health").status_code == 200


def test_dist_without_assets_dir_works(tmp_path):
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "index.html").write_text(INDEX_HTML)
    c = TestClient(make_app(tmp_path / "dist"))
    assert c.get("/").text == INDEX_HTML
    assert c.get("/assets/x.js").status_code == 404


# --- başlıklar ---

def test_cache_control_headers(client):
    assert client.get("/").headers["cache-control"] == "no-cache"
    assert client.get("/applicants").headers["cache-control"] == "no-cache"
    assert client.get("/assets/app.js").headers["cache-control"] == "public, max-age=31536000, immutable"
    assert "immutable" not in client.get("/robots.txt").headers.get("cache-control", "")


def test_assets_conditional_request_still_immutable(client):
    first = client.get("/assets/app.js")
    etag = first.headers["etag"]
    second = client.get("/assets/app.js", headers={"If-None-Match": etag})
    assert second.status_code == 304
    assert second.headers["cache-control"] == "public, max-age=31536000, immutable"


@pytest.mark.parametrize("path,status", [
    ("/", 200), ("/applicants", 200), ("/assets/app.js", 200), ("/robots.txt", 200),
    ("/assets/yok.js", 404), ("/favicon.ico", 404), ("/api/yok", 404), ("/api/health", 200),
])
def test_frame_ancestors_on_static_and_fallback(client, path, status):
    r = client.get(path)
    assert r.status_code == status
    assert r.headers["content-security-policy"] == "frame-ancestors 'self'"
    assert "x-frame-options" not in r.headers


def test_custom_frame_ancestors_on_static(site):
    c = TestClient(make_app(site, FRAME_ANCESTORS="'self' https://ana-site.edu.tr"))
    for path in ("/", "/assets/app.js", "/assets/yok.js"):
        assert c.get(path).headers["content-security-policy"] == "frame-ancestors 'self' https://ana-site.edu.tr"


# --- ROOT_PATH ---

def test_root_path_with_static_and_api(site):
    c = TestClient(make_app(site, ROOT_PATH="/patent"))  # proxy prefix'i siler: istekler prefix'siz gelir
    assert c.get("/").text == INDEX_HTML
    assert c.get("/applicants").text == INDEX_HTML
    assert c.get("/assets/app.js").text == "console.log('app');"
    assert c.get("/assets/yok.js").status_code == 404
    assert c.get("/api/health").json() == {"status": "ok"}
    assert c.get("/api/patents").status_code == 501
    assert c.get("/api/yok").json() == {"detail": "Not Found"}
    assert c.get("/").headers["content-security-policy"] == "frame-ancestors 'self'"


# --- varsayılan dist yolu / yan etkiler ---

def test_default_dist_dir_is_project_root_based():
    assert DIST_DIR == PROJECT_ROOT / "frontend" / "dist"
    assert DIST_DIR.is_absolute()


def test_static_serving_does_not_create_db(site):
    existed = database.DB_PATH.exists()
    c = TestClient(make_app(site))
    c.get("/")
    c.get("/api/health")
    assert database.DB_PATH.exists() == existed


def test_import_has_no_filesystem_side_effects(tmp_path):
    backend = Path(__file__).resolve().parents[1]
    if database.DB_PATH.exists():
        pytest.skip("data/patent.db zaten var")
    subprocess.run([sys.executable, "-c", "import app.main"], cwd=backend, check=True)
    assert not database.DB_PATH.exists()
