"""
RepoCheck AI Service — FastAPI 入口
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.analyze import router as analyze_router
from app.api.repo_analyze import router as repo_analyze_router
from app.api.environment import router as environment_router
from app.core.config import settings
from app.core.logger import logger
import traceback

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="RepoCheck AI Service - Paper Code Reproducibility Analyzer",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理 — 返回统一 JSON 错误格式"""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "code": 4003,
            "message": f"外部 API 调用失败：{str(exc)}",
            "detail": str(exc),
        },
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    """RuntimeError — 返回 500 并携带错误说明"""
    logger.error(f"RuntimeError on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "code": 4003,
            "message": str(exc),
            "detail": str(exc),
        },
    )


# 注册路由
app.include_router(analyze_router, prefix="/api")
app.include_router(repo_analyze_router, prefix="/api")
app.include_router(environment_router, prefix="/api")


@app.get("/")
async def root():
    return {"service": settings.APP_NAME, "version": settings.VERSION}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
