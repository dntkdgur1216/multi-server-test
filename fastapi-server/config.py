"""애플리케이션 설정 (환경변수 기반)"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# MySQL 데이터베이스 설정
MYSQL_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "woo960525!"),
    "database": os.getenv("DB_NAME", "login_system"),
    "charset": "utf8mb4"
}

# 서버 설정
HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
PORT = int(os.getenv("FASTAPI_PORT", "8000"))
RELOAD = os.getenv("RELOAD", "True").lower() == "true"

# 외부 서비스 URL
SPRING_BOOT_URL = os.getenv("SPRING_BOOT_URL", "http://localhost:8082")

# 경로 설정
TEMPLATES_DIR = "templates"
STATIC_DIR = "static"
