from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, settings
from app.core.security_headers import SecurityHeadersMiddleware
from app.routers import applicants, attorney_firms, departments, fsmh_types, patents
from app.routers import settings as settings_router


def create_app(settings_obj: Settings | None = None) -> FastAPI:
    cfg = settings_obj or settings
    app = FastAPI(title="Patent Takip", root_path=cfg.ROOT_PATH)

    @app.get("/api/health", tags=["health"])
    def health():
        return {"status": "ok"}

    for module in (patents, applicants, departments, fsmh_types, attorney_firms, settings_router):
        app.include_router(module.router, prefix="/api")

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
    return app


app = create_app()
