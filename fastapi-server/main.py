"""FastAPI 애플리케이션 메인 진입점"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import HOST, PORT, RELOAD, STATIC_DIR
from database import init_db
from routes.auth import router as auth_router
from routes.shop import router as shop_router
from routes.seats import router as seats_router


# FastAPI 앱 생성
app = FastAPI(title="간단한 로그인 시스템")

# CORS 설정 (Spring Boot와 통신)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8082"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 설정
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 라우터 등록
app.include_router(auth_router)
app.include_router(shop_router)
app.include_router(seats_router)

# 데이터베이스 초기화
init_db()


if __name__ == "__main__":
    # python main.py로 직접 실행 가능
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=RELOAD
    )

