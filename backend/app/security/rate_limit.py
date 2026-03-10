from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._events: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        identity = request.client.host if request.client else "unknown"
        now = time.time()
        window = self._events[identity]

        while window and now - window[0] > 60:
            window.popleft()

        if len(window) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Limite de requisições excedido. Tente novamente em instantes."},
            )

        window.append(now)
        return await call_next(request)

