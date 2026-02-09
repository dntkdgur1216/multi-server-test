"""아이템 및 구매 관련 데이터베이스 함수"""
import pymysql
import logging
from .base import get_connection


def init_sample_items():
    """샘플 아이템 데이터 추가"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 이미 아이템이 있는지 확인
    cursor.execute("SELECT COUNT(*) FROM items")
    count = cursor.fetchone()[0]
    
    if count == 0:
        sample_items = [
            ("한정판 티셔츠", 10, 50000),
            ("콘서트 티켓", 5, 100000),
            ("사인 CD", 20, 30000),
        ]
        cursor.executemany("INSERT INTO items (name, stock, price) VALUES (%s, %s, %s)", sample_items)
        conn.commit()
    
    conn.close()


def get_all_items():
    """모든 아이템 조회"""
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()
    conn.close()
    return items


def get_item_by_id(item_id: int):
    """아이템 ID로 조회"""
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
    item = cursor.fetchone()
    conn.close()
    return item


def purchase_item_unsafe(user_id: int, item_id: int, quantity: int = 1) -> dict:
    """
    아이템 구매 (동시성 문제 있는 버전)
    Race condition 발생 가능!
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. 재고 확인
        cursor.execute("SELECT stock FROM items WHERE id = %s", (item_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return {"success": False, "message": "아이템을 찾을 수 없습니다"}
        
        current_stock = result[0]
        
        # 2. 재고 부족 체크
        if current_stock < quantity:
            conn.close()
            logging.warning(f"❌ [UNSAFE] 구매 실패: user_id={user_id}, item_id={item_id}, 재고={current_stock}")
            return {"success": False, "message": f"재고 부족 (현재: {current_stock}개)"}
        
        # ⚠️ 문제: 여기서 다른 요청이 끼어들 수 있음!
        
        # 3. 재고 감소
        new_stock = current_stock - quantity
        cursor.execute("UPDATE items SET stock = %s WHERE id = %s", (new_stock, item_id))
        
        # 4. 구매 내역 저장
        cursor.execute("INSERT INTO purchases (user_id, item_id, quantity) VALUES (%s, %s, %s)",
                      (user_id, item_id, quantity))
        
        conn.commit()
        conn.close()
        logging.info(f"✅ [UNSAFE] 구매 성공: user_id={user_id}, item_id={item_id}, 남은재고={new_stock}")
        return {"success": True, "message": "구매 완료!", "remaining_stock": new_stock}
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "message": f"오류 발생: {str(e)}"}


def purchase_item_safe(user_id: int, item_id: int, quantity: int = 1) -> dict:
    """
    아이템 구매 (동시성 문제 해결 버전)
    SELECT ... FOR UPDATE 사용
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 트랜잭션 시작
        conn.begin()
        
        # 1. 재고 확인 (비관적 락 사용)
        cursor.execute("SELECT stock FROM items WHERE id = %s FOR UPDATE", (item_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.rollback()
            conn.close()
            return {"success": False, "message": "아이템을 찾을 수 없습니다"}
        
        current_stock = result[0]
        
        # 2. 재고 부족 체크
        if current_stock < quantity:
            conn.rollback()
            conn.close()
            logging.warning(f"❌ [SAFE] 구매 실패: user_id={user_id}, item_id={item_id}, 재고={current_stock}")
            return {"success": False, "message": f"재고 부족 (현재: {current_stock}개)"}
        
        # 3. 재고 감소 (원자적 연산)
        cursor.execute("UPDATE items SET stock = stock - %s WHERE id = %s", (quantity, item_id))
        
        # 4. 구매 내역 저장
        cursor.execute("INSERT INTO purchases (user_id, item_id, quantity) VALUES (%s, %s, %s)",
                      (user_id, item_id, quantity))
        
        conn.commit()
        conn.close()
        
        new_stock = current_stock - quantity
        logging.info(f"✅ [SAFE] 구매 성공: user_id={user_id}, item_id={item_id}, 남은재고={new_stock}")
        return {"success": True, "message": "구매 완료!", "remaining_stock": new_stock}
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "message": f"오류 발생: {str(e)}"}


def get_user_purchases(user_id: int):
    """사용자 구매 내역 조회"""
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute('''
        SELECT p.*, i.name as item_name, i.price
        FROM purchases p
        JOIN items i ON p.item_id = i.id
        WHERE p.user_id = %s
        ORDER BY p.purchased_at DESC
    ''', (user_id,))
    purchases = cursor.fetchall()
    conn.close()
    return purchases
