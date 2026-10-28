from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityHeadersMiddleware:
    """Tüm HTTP yanıtlarına `Content-Security-Policy: frame-ancestors ...` ekler.

    X-Frame-Options hiçbir zaman gönderilmez (CSP ile çakışmasın diye); varsa kaldırılır.
    """

    def __init__(self, app: ASGIApp, frame_ancestors: str) -> None:
        self.app = app
        self._csp = f"frame-ancestors {frame_ancestors}".encode("latin-1")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() not in (b"x-frame-options", b"content-security-policy")
                ]
                headers.append((b"content-security-policy", self._csp))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)
