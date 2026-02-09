"""데이터베이스 연결 관리"""
import pymysql
from config import MYSQL_CONFIG


def get_connection():
    """MySQL 연결 생성"""
    return pymysql.connect(**MYSQL_CONFIG)
