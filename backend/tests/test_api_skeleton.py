import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import database
from app.config import Settings
from app.main import create_app

ENV_EXAMPLE = Path(__file__).resolve().parents[2] / ".env.example"
ENV_KEYS = ["HOST", "PORT", "CORS_ORIGINS", "FRAME_ANCESTORS", "ROOT_PATH"]

PATENT_BODY = {"title": "T", "applicant_id": 1, "fsmh_type_id": 1}
LOOKUP_BODIES = {
    "applicants": {"full_name": "A"},
    "departments": {"name": "D"},
    "fsmh_types": {"name": "T"},
    "attorney_firms": {"name": "F"},
}

# Madde 7 tablosu: (metot, yol, gövde)
SKELETON = [
    ("GET", "/api/patents", None),
    ("POST", "/api/patents", PATENT_BODY),
    ("GET", "/api/patents/1", None),
    ("PUT", "/api/patents/1", PATENT_BODY),
    ("DELETE", "/api/patents/1", None),
    ("GET", "/api/settings", None),
    ("PUT", "/api/settings", {"institution_name": "ÇAKÜ"}),
]
# Gerçek mantığı yazılmış router'lar artık 501 vermez; kendi test dosyalarında sınanır.
IMPLEMENTED = {"departments"}
ALL_ROUTES = list(SKELETON)
for _name, _body in LOOKUP_BODIES.items():
    _routes = [
        ("GET", f"/api/{_name}", None),
        ("POST", f"/api/{_name}", _body),
        ("GET", f"/api/{_name}/1", None),
        ("PUT", f"/api/{_name}/1", _body),
        ("DELETE", f"/api/{_name}/1", None),
    ]
    ALL_ROUTES += _routes
    if _name not in IMPLEMENTED:
        SKELETON += _routes


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def make_client(**overrides) -> TestClient:
    return TestClient(create_app(Settings(_env_file=None, **overrides)))


@pytest.fixture
def client():
    return make_client()


# --- health ---

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_health_does_not_create_db_file(client):
    existed = database.DB_PATH.exists()
    client.get("/api/health")
    assert database.DB_PATH.exists() == existed


def test_importing_main_does_not_create_db_file():
    if database.DB_PATH.exists():
        pytest.skip("data/patent.db zaten var")
    backend = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, "-c", "import app.main"], cwd=backend, check=True)
    assert not database.DB_PATH.exists()


# --- iskelet: 501 ---

@pytest.mark.parametrize("method,path,body", SKELETON, ids=[f"{m} {p}" for m, p, _ in SKELETON])
def test_skeleton_endpoints_return_501(client, method, path, body):
    r = client.request(method, path, json=body)
    assert r.status_code == 501, r.text
    assert r.json() == {"detail": "Henüz uygulanmadı"}


def test_every_skeleton_route_is_in_openapi(client):
    paths = client.get("/openapi.json").json()["paths"]
    for method, path, _ in ALL_ROUTES:  # iskelet + gerçek uçlar: Madde 7 tablosu eksiksiz
        template = path
        for name in ("patents", "applicants", "departments", "fsmh_types", "attorney_firms"):
            if path.startswith(f"/api/{name}/1"):
                template = path.replace("/1", "/{patent_id}" if name == "patents" else "/{item_id}")
        assert method.lower() in paths[template], (method, path)


def test_openapi_uses_phase7_schemas(client):
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    for name in ("PatentIn", "PatentRead", "ApplicantIn", "ApplicantRead", "DepartmentRead",
                 "FsmhTypeRead", "AttorneyFirmRead", "DuplicateWarning", "ErrorResponse"):
        assert name in schemas, name


# --- doğrulama: 422 ---

@pytest.mark.parametrize(
    "query",
    [
        "page=0",
        "page_size=101",
        "bogus=1",
        "date_from=2026-02-01&date_to=2026-01-01",
        "sort_by=notes",
        "sort_dir=up",
    ],
)
def test_invalid_list_query_is_422(client, query):
    assert client.get(f"/api/patents?{query}").status_code == 422


def test_valid_list_query_reaches_501(client):
    r = client.get(
        "/api/patents?q=tuz&applicant_id=1&department_id=2&fsmh_type_id=1&attorney_firm_id=3"
        "&date_from=2026-01-01&date_to=2026-12-31&has_attorney=true&sort_by=title&sort_dir=desc"
        "&page=2&page_size=50"
    )
    assert r.status_code == 501


def test_invalid_body_is_422(client):
    assert client.post("/api/patents", json={**PATENT_BODY, "id": 5}).status_code == 422
    assert client.post("/api/patents", json={"title": "T"}).status_code == 422
    assert client.put("/api/applicants/1", json={"full_name": "A", "created_at": "x"}).status_code == 422
    assert client.put("/api/settings", json={"k": 5}).status_code == 422
    assert client.get("/api/patents/abc").status_code == 422


def test_unknown_path_404_json(client):
    r = client.get("/api/yok")
    assert r.status_code == 404
    assert r.json() == {"detail": "Not Found"}


# --- Madde 13: frame-ancestors ---

RESPONSES = [
    ("GET", "/api/health", None, 200),
    ("GET", "/api/yok", None, 404),
    ("GET", "/api/patents?page=0", None, 422),
    ("GET", "/api/patents", None, 501),
]


@pytest.mark.parametrize("method,path,body,status", RESPONSES)
def test_default_frame_ancestors_header(client, method, path, body, status):
    r = client.request(method, path, json=body)
    assert r.status_code == status
    assert r.headers["content-security-policy"] == "frame-ancestors 'self'"
    assert "x-frame-options" not in r.headers


@pytest.mark.parametrize("method,path,body,status", RESPONSES)
def test_custom_frame_ancestors_header(method, path, body, status):
    c = make_client(FRAME_ANCESTORS="'self' https://ana-site.edu.tr")
    r = c.request(method, path, json=body)
    assert r.status_code == status
    assert r.headers["content-security-policy"] == "frame-ancestors 'self' https://ana-site.edu.tr"
    assert "x-frame-options" not in r.headers


def test_x_frame_options_stripped_if_inner_app_sets_it():
    from fastapi import Response

    app = create_app(Settings(_env_file=None))

    @app.get("/xfo")
    def xfo(response: Response):
        response.headers["X-Frame-Options"] = "DENY"
        return {"ok": True}

    r = TestClient(app).get("/xfo")
    assert r.status_code == 200
    assert "x-frame-options" not in r.headers
    assert r.headers["content-security-policy"] == "frame-ancestors 'self'"


def test_only_one_csp_header(client):
    r = client.get("/api/health")
    assert len(r.headers.get_list("content-security-policy")) == 1


# --- CORS ---

EVIL = {"Origin": "https://evil.example"}


def test_cors_disabled_by_default(client):
    r = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert "access-control-allow-origin" not in r.headers
    pre = client.options(
        "/api/health",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in pre.headers


def test_cors_allowed_and_denied_origins():
    c = make_client(CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173")
    ok = c.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert ok.headers["access-control-allow-origin"] == "http://localhost:5173"
    bad = c.get("/api/health", headers=EVIL)
    assert "access-control-allow-origin" not in bad.headers
    pre = c.options(
        "/api/health",
        headers={"Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "PUT"},
    )
    assert pre.status_code == 200
    assert pre.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert pre.headers["content-security-policy"] == "frame-ancestors 'self'"  # ön kontrolde de


def test_cors_origins_from_env_example_file_parsed_as_list():
    # Ayrıştırmanın kendisi tests/test_config.py::test_env_example_loads_quoted_self ile de kapsanır;
    # burada uçtan uca: .env.example gerçekten yüklenip uygulamaya verilir.
    cfg = Settings(_env_file=ENV_EXAMPLE)
    assert cfg.CORS_ORIGINS == ["http://localhost:5173", "http://127.0.0.1:5173"]
    c = TestClient(create_app(cfg))
    ok = c.get("/api/health", headers={"Origin": "http://127.0.0.1:5173"})
    assert ok.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert "access-control-allow-origin" not in c.get("/api/health", headers=EVIL).headers
    assert ok.headers["content-security-policy"] == "frame-ancestors 'self'"


# --- ROOT_PATH ---

def test_root_path_health_and_openapi():
    c = make_client(ROOT_PATH="/patent")
    r = c.get("/api/health")  # proxy prefix'i siler varsayımı: uygulama prefix'siz yolları servis eder
    assert r.status_code == 200 and r.json() == {"status": "ok"}
    spec = c.get("/openapi.json").json()
    assert spec["servers"] == [{"url": "/patent"}]
    assert "/api/health" in spec["paths"]  # yollar prefix'siz kalır; servers[0].url prefix'i verir
    assert c.get("/api/patents").status_code == 501


def test_root_path_trailing_slash_normalized():
    c = make_client(ROOT_PATH="/patent/")
    assert c.get("/openapi.json").json()["servers"] == [{"url": "/patent"}]


def test_root_path_applies_to_error_responses_too():
    c = make_client(ROOT_PATH="/patent")
    assert c.get("/api/yok").status_code == 404
    assert c.get("/api/patents?page=0").status_code == 422


def test_root_path_default_empty_has_no_servers_prefix(client):
    spec = client.get("/openapi.json").json()
    assert spec.get("servers") in (None, [])


# --- RootPathMiddleware: path önekini geri ekler (proxy prefix'i siler varsayımı) ---

def _run_root_path_middleware(root_path, scope):
    import asyncio

    from app.core.root_path import RootPathMiddleware

    captured = {}

    async def inner(received_scope, receive, send):
        captured.update(received_scope)

    asyncio.run(RootPathMiddleware(inner, root_path)(scope, None, None))
    return captured


def test_root_path_middleware_prepends_prefix_to_path_and_raw_path():
    out = _run_root_path_middleware(
        "/patent/", {"type": "http", "path": "/api/health", "raw_path": b"/api/health"}
    )
    assert out["root_path"] == "/patent"
    assert out["path"] == "/patent/api/health"
    assert out["raw_path"] == b"/patent/api/health"


def test_root_path_middleware_noop_when_empty_or_not_http():
    scope = {"type": "http", "path": "/api/health", "raw_path": b"/api/health", "root_path": ""}
    assert _run_root_path_middleware("", scope) == scope
    lifespan = {"type": "lifespan"}
    assert _run_root_path_middleware("/patent", lifespan) == lifespan


# --- HOST/PORT: python -m app.main (Madde 11) ---

def _run_main_module(monkeypatch, run_name, cfg):
    import runpy
    import sys

    import uvicorn

    import app.config

    # `python -m` gerçekte modülü sys.modules'ta bulmadan çalıştırır; testte aynısını sağla.
    monkeypatch.delitem(sys.modules, "app.main", raising=False)
    calls = []
    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setattr(app.config, "settings", cfg)
    runpy.run_module("app.main", run_name=run_name)
    return calls


def test_main_block_runs_uvicorn_with_settings_host_and_port(monkeypatch):
    cfg = Settings(_env_file=None, HOST="127.0.0.2", PORT=8123)
    calls = _run_main_module(monkeypatch, "__main__", cfg)
    assert calls == [(("app.main:app",), {"host": "127.0.0.2", "port": 8123})]


def test_main_block_defaults_are_127_0_0_1_8001(monkeypatch):
    calls = _run_main_module(monkeypatch, "__main__", Settings(_env_file=None))
    assert calls == [(("app.main:app",), {"host": "127.0.0.1", "port": 8001})]


def test_importing_main_does_not_start_server(monkeypatch):
    calls = _run_main_module(monkeypatch, "app.main_imported", Settings(_env_file=None))
    assert calls == []
