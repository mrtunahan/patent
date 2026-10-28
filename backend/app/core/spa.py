from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.routing import APIRoute
from starlette.routing import Match
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

MISSING_FRONTEND_MESSAGE = "Frontend derlenmemiş: frontend/ içinde npm run build çalıştırın"
ASSETS_CACHE = "public, max-age=31536000, immutable"  # Vite hash'li dosya adları
INDEX_CACHE = "no-cache"


class ImmutableStaticFiles(StaticFiles):
    """/assets için StaticFiles (ETag, 304, güvenli yol çözümü) + uzun ömürlü önbellek başlığı."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        if response.status_code in (200, 304):
            response.headers["Cache-Control"] = ASSETS_CACHE
        return response


def _route_path(scope: Scope) -> str:
    """Yönlendirmeye esas yol (root_path varsa önekini çıkarır; Starlette ile aynı mantık)."""
    path = scope["path"]
    root_path = scope.get("root_path", "")
    if root_path and path.startswith(root_path):
        path = path[len(root_path):]
    return path


class SpaRoute(APIRoute):
    """/api ve altını ASLA eşleştirmez: bilinmeyen /api yolları varsayılan 404 JSON'a düşer,
    var olan /api yolunda yanlış metot ise doğru şekilde 405 döner."""

    def matches(self, scope: Scope) -> tuple[Match, Scope]:
        if scope["type"] == "http":
            path = _route_path(scope)
            if path == "/api" or path.startswith("/api/"):
                return Match.NONE, {}
        return super().matches(scope)


def _not_found() -> JSONResponse:
    return JSONResponse({"detail": "Not Found"}, status_code=404)


def _resolve_file(dist: Path, relative: str) -> Path | None:
    """dist içindeki var olan dosyayı döndürür; dist dışına çıkan her yol None'dır."""
    try:
        candidate = (dist / relative.lstrip("/")).resolve()
    except (ValueError, OSError):  # örn. gömülü null bayt
        return None
    if candidate.is_file() and candidate.is_relative_to(dist):
        return candidate
    return None


def mount_spa(app: FastAPI, dist_dir: Path) -> None:
    """frontend/dist'i aynı porttan servis eder; router'lardan SONRA çağrılmalıdır.

    Kurallar: /api/... asla index.html dönmez; uzantılı (veya gizli) yol yoksa 404;
    diğer bilinmeyen GET/HEAD yolları SPA için index.html'e düşer.
    dist (veya index.html) yoksa uygulama çökmez, kök yol açıklayıcı 404 JSON döner.
    """
    dist = Path(dist_dir).resolve()
    index = dist / "index.html"
    ready = index.is_file()

    if ready and (dist / "assets").is_dir():
        app.mount("/assets", ImmutableStaticFiles(directory=dist / "assets"), name="assets")

    def serve(full_path: str) -> Response:
        if not ready:
            return JSONResponse({"detail": MISSING_FRONTEND_MESSAGE}, status_code=404)

        segments = [s for s in full_path.split("/") if s]
        if any(s.startswith(".") for s in segments):  # gizli dosyalar (.env, .vite vb.)
            return _not_found()

        if segments:
            file = _resolve_file(dist, full_path)
            if file is not None:
                headers = {"Cache-Control": INDEX_CACHE} if file == index else None
                return FileResponse(file, headers=headers)
            if "." in segments[-1]:  # uzantılı ve yok: SPA rotası değil
                return _not_found()

        return FileResponse(index, headers={"Cache-Control": INDEX_CACHE})

    app.router.add_api_route(
        "/{full_path:path}",
        serve,
        methods=["GET", "HEAD"],
        include_in_schema=False,
        route_class_override=SpaRoute,
    )
