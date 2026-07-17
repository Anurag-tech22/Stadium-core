from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes import router as api_router
from app.core.limiter import limiter

# Configure standard logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("phoenix")

# RFC 9116 coordinated disclosure contact
_SECURITY_TXT = """\
Contact: mailto:security@phoenix-stadium.example
Preferred-Languages: en, hi, es, fr, pt
Policy: https://phoenix-stadium.example/security-policy
Expires: 2027-01-01T00:00:00.000Z
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Phoenix Stadium Application Starting Up")
    yield
    logger.info("Phoenix Stadium Application Shutting Down")


app = FastAPI(title="Phoenix Stadium", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# GZip all responses ≥ 1 KB — reduces bandwidth ~70% for JSON payloads
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS — explicit origin allowlist; adjust for your deployment domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8080", "http://localhost:8080"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(api_router, prefix="/api")


@app.middleware("http")
async def limit_request_size(request: Request, call_next: Any) -> Any:  # noqa: ANN401
    # Reject large payloads (DoS prevention)
    if request.method == "POST" and request.url.path.startswith("/api"):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > 100 * 1024:  # 100KB limit
                    return JSONResponse(
                        status_code=413, content={"detail": "Request entity too large"}
                    )
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "Invalid content-length"})
    return await call_next(request)


@app.middleware("http")
async def security_headers(request: Request, call_next: Any) -> Any:  # noqa: ANN401
    logger.info("Incoming request: %s %s", request.method, request.url.path)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    # HSTS — tell browsers to always use HTTPS (1 year)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self'; "
        "img-src 'self' data:"
    )
    return response


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/ops", response_class=HTMLResponse)
async def ops_dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="ops.html")


@app.get("/health")
@app.get("/healthz")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/.well-known/security.txt", response_class=PlainTextResponse)
async def security_txt() -> PlainTextResponse:
    """RFC 9116 coordinated vulnerability disclosure endpoint."""
    return PlainTextResponse(_SECURITY_TXT, media_type="text/plain")
