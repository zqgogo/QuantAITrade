"""
QuantAITrade API服务入口
基于FastAPI的高性能API服务
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.api.routes import api_router
from config import get_config


def create_app() -> FastAPI:
    """创建并配置FastAPI应用"""
    app = FastAPI(
        title="QuantAITrade API",
        description="智能量化交易系统 API 接口",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    app.include_router(api_router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup_event():
        logger.info("QuantAITrade API 服务启动")
        config = get_config()
        logger.info(f"运行模式: {config.get('run_mode', 'manual')}")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("QuantAITrade API 服务关闭")

    return app


app = create_app()


def main():
    """启动API服务"""
    port = int(os.getenv('API_PORT', '8000'))
    host = os.getenv('API_HOST', '0.0.0.0')

    logger.info(f"启动QuantAITrade API服务 on {host}:{port}")

    uvicorn.run(
        "src.api.server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()