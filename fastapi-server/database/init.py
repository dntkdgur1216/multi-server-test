"""데이터베이스 초기화"""
from .base import get_connection


def init_db():
    """데이터베이스 초기화"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # users 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    ''')
    
    # items 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            stock INT NOT NULL DEFAULT 0,
            price INT NOT NULL DEFAULT 0
        )
    ''')
    
    # purchases 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            item_id INT NOT NULL,
            quantity INT NOT NULL DEFAULT 1,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    ''')
    
    # seats 테이블 (좌석 예약)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            seat_number VARCHAR(10) UNIQUE NOT NULL,
            row_num INT NOT NULL,
            col_num INT NOT NULL,
            x_pos INT NOT NULL,
            y_pos INT NOT NULL,
            width INT NOT NULL,
            height INT NOT NULL,
            status ENUM('available', 'reserved') DEFAULT 'available',
            reserved_by INT NULL,
            reserved_at TIMESTAMP NULL,
            FOREIGN KEY (reserved_by) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()
