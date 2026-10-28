from starlette.types import ASGIApp, Receive, Scope, Send


class RootPathMiddleware:
    """ROOT_PATH'i ASGI scope'a uygular (proxy prefix'i siler varsayımı).

    Güncel ASGI/Starlette anlayışında scope["path"], root_path önekini İÇERİR (uvicorn --root-path
    da böyle yapar); Mount/StaticFiles yol çözümü buna dayanır. Proxy öneki sildiği için gelen yol
    prefix'sizdir: burada root_path ayarlanır ve öneki path/raw_path'e geri eklenir. Starlette
    yönlendirmede öneki tekrar çıkarır, böylece uygulama yolları prefix'siz kalır.
    ROOT_PATH boşsa scope'a dokunulmaz (örn. uvicorn --root-path çalışmaya devam eder).
    """

    def __init__(self, app: ASGIApp, root_path: str) -> None:
        self.app = app
        self.root_path = root_path.rstrip("/")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if self.root_path and scope["type"] in ("http", "websocket"):
            scope = {**scope, "root_path": self.root_path, "path": self.root_path + scope["path"]}
            if "raw_path" in scope and scope["raw_path"] is not None:
                scope["raw_path"] = self.root_path.encode("latin-1") + scope["raw_path"]
        await self.app(scope, receive, send)
