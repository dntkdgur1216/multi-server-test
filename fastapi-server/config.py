"""애플리케이션 설정"""

# MySQL 데이터베이스 설정
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "woo960525!",  # 여기에 당신이 설정한 MySQL root 비밀번호 입력
    "database": "login_system",
    "charset": "utf8mb4"
}

# 서버 설정
HOST = "0.0.0.0"
PORT = 8000
RELOAD = True  # 개발 모드

# 경로 설정
TEMPLATES_DIR = "templates"
STATIC_DIR = "static"
