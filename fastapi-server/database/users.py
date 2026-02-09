"""사용자 관련 데이터베이스 함수"""
import pymysql
import hashlib
from .base import get_connection


def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username: str, password: str) -> bool:
    """사용자 생성"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        hashed_pw = hash_password(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", 
                      (username, hashed_pw))
        conn.commit()
        conn.close()
        return True
    except pymysql.IntegrityError:
        conn.close()
        return False


def verify_user(username: str, password: str) -> bool:
    """사용자 인증"""
    conn = get_connection()
    cursor = conn.cursor()
    
    hashed_pw = hash_password(password)
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", 
                  (username, hashed_pw))
    user = cursor.fetchone()
    conn.close()
    
    return user is not None


def get_user_id(username: str) -> int:
    """사용자 ID 조회"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None
