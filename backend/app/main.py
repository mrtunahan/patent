from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import PROJECT_ROOT, Settings, settings
from app.core.errors import ConflictError, NotFoundError, UnprocessableError
from app.core.root_path import RootPathMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.spa import mount_spa
from app.routers import applicants, attorney_firms, departments, fsmh_types, patents
from app.routers import settings as settings_router

DIST_DIR = PROJECT_ROOT / "frontend" / "dist"


def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Servis katmanının HTTP bilmeyen hatalarını {"detail": "..."} JSON'una çevirir."""
    status = {NotFoundError: 404, ConflictError: 409, UnprocessableError: 422}[type(exc)]
    return JSONResponse({"detail": str(exc)}, status_code=status)


def create_app(settings_obj: Settings | None = None, dist_dir: Path | None = None) -> FastAPI:
    cfg = settings_obj or settings
    app = FastAPI(title="Patent Takip")

    app.add_exception_handler(NotFoundError, domain_error_handler)
    app.add_exception_handler(ConflictError, domain_error_handler)
    app.add_exception_handler(UnprocessableError, domain_error_handler)

    @app.get("/api/health", tags=["health"])
    def health():
        return {"status": "ok"}

    for module in (patents, applicants, departments, fsmh_types, attorney_firms, settings_router):
        app.include_router(module.router, prefix="/api")

    # Statik servis ve SPA fallback router'lardan sonra kaydedilir (/api gölgelenmesin).
    mount_spa(app, dist_dir or DIST_DIR)

    # Varsayılan kapalı/aynı origin (Madde 11): yalnızca CORS_ORIGINS doluysa eklenir.
    if cfg.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cfg.CORS_ORIGINS,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    # En son eklenen en dışta çalışır: CORS ön kontrol yanıtları dahil her yanıta başlık eklenir.
    app.add_middleware(SecurityHeadersMiddleware, frame_ancestors=cfg.FRAME_ANCESTORS)
    # En dışta: iç katmanlar (OpenAPI dahil) doğru root_path'i görsün.
    app.add_middleware(RootPathMiddleware, root_path=cfg.ROOT_PATH)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT)
