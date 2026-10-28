from starlette.types import ASGIApp, Receive, Scope, Send


class RootPathMiddleware:
    """scope["root_path"] değerini ROOT_PATH'ten ayarlar (proxy prefix'i siler varsayımı).

    FastAPI(root_path=...) kullanımdan kaldırıldığı için bu şekilde uygulanır.
    ROOT_PATH boşsa scope'a dokunulmaz (örn. uvicorn --root-path çalışmaya devam eder).
    """

    def __init__(self, app: ASGIApp, root_path: str) -> None:
        self.app = app
        self.root_path = root_path.rstrip("/")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if self.root_path and scope["type"] in ("http", "websocket"):
            scope = {**scope, "root_path": self.root_path}
        await self.app(scope, receive, send)
