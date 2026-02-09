"""좌석 예약 관련 데이터베이스 함수"""
import logging
import pymysql.cursors
from .base import get_connection


def init_sample_seats():
    """샘플 좌석 데이터 초기화 (최초 1회만)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 이미 좌석이 있으면 스킵
    cursor.execute("SELECT COUNT(*) FROM seats")
    count = cursor.fetchone()[0]
    
    if count > 0:
        conn.close()
        return
    
    # 8행 x 10열 = 80개 좌석 생성
    # 이미지 정밀 분석 결과 좌표
    seats_data = []
    
    # 좌석 레이아웃: 5개 블록 x 8행 x 2열
    block_start_x = [8, 184, 364, 544, 744]  # 각 블록의 시작 X 좌표
    seat_start_y = 250  # 첫 번째 행 Y 좌표
    seat_width = 48   # 좌석 너비
    seat_height = 58  # 좌석 높이
    
    # 행별 Y 좌표 (7-8행 사이 간격이 더 큼)
    row_y_positions = [250, 313, 376, 439, 502, 565, 628, 710]
    
    col_gap = 60      # 열 간격 (블록 내 두 좌석 사이)
    
    seat_id = 1
    for row in range(8):  # 8행
        for block_idx, block_x in enumerate(block_start_x):  # 5개 블록
            for col in range(2):  # 각 블록당 2열
                x = block_x + (col * col_gap)
                y = row_y_positions[row]
                seat_number = f"{chr(65+row)}-{seat_id}"  # A-1, A-2, ...
                
                seats_data.append((
                    seat_number,
                    row + 1,
                    seat_id,
                    x,
                    y,
                    seat_width,
                    seat_height
                ))
                seat_id += 1
    
    # 좌석 데이터 삽입
    cursor.executemany('''
        INSERT INTO seats (seat_number, row_num, col_num, x_pos, y_pos, width, height)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', seats_data)
    
    conn.commit()
    conn.close()
    logging.info(f"✅ {len(seats_data)}개의 샘플 좌석이 생성되었습니다")


def get_all_seats():
    """모든 좌석 조회 (예약자 username 포함)"""
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute('''
        SELECT s.id, s.seat_number, s.row_num, s.col_num, s.x_pos, s.y_pos, 
               s.width, s.height, s.status, s.reserved_by,
               u.username as reserved_by_username
        FROM seats s
        LEFT JOIN users u ON s.reserved_by = u.id
        ORDER BY s.row_num, s.col_num
    ''')
    
    seats = cursor.fetchall()
    conn.close()
    return seats


def reserve_seat_unsafe(user_id, seat_id):
    """좌석 예약 (Race Condition 발생 가능)"""
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 1. 좌석 상태 확인
        cursor.execute("SELECT status, reserved_by FROM seats WHERE id = %s", (seat_id,))
        seat = cursor.fetchone()
        
        if not seat:
            conn.close()
            return {"success": False, "message": "존재하지 않는 좌석입니다"}
        
        # 2. 이미 예약된 좌석인지 확인
        if seat['status'] == 'reserved':
            conn.close()
            logging.warning(f"❌ [UNSAFE] 예약 실패: user_id={user_id}, seat_id={seat_id} (이미 예약됨)")
            return {"success": False, "message": "이미 예약된 좌석입니다"}
        
        # 3. 해당 사용자가 이미 다른 좌석을 예약했는지 확인
        cursor.execute("SELECT COUNT(*) as count FROM seats WHERE reserved_by = %s", (user_id,))
        user_reservation = cursor.fetchone()
        
        if user_reservation['count'] > 0:
            conn.close()
            return {"success": False, "message": "이미 좌석을 예약했습니다"}
        
        # ⚠️ Race Condition 발생 구간: 여기서 다른 요청이 끼어들 수 있음
        
        # 4. 좌석 예약
        cursor.execute('''
            UPDATE seats 
            SET status = 'reserved', reserved_by = %s, reserved_at = NOW()
            WHERE id = %s
        ''', (user_id, seat_id))
        
        conn.commit()
        conn.close()
        
        logging.info(f"✅ [UNSAFE] 예약 성공: user_id={user_id}, seat_id={seat_id}")
        return {"success": True, "message": "좌석 예약 성공"}
        
    except Exception as e:
        conn.rollback()
        conn.close()
        logging.error(f"❌ [UNSAFE] 예약 오류: {str(e)}")
        return {"success": False, "message": "예약 중 오류 발생"}


def reserve_seat_safe(user_id, seat_id):
    """좌석 예약 (FOR UPDATE 락 사용)"""
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 트랜잭션 시작
        conn.start_transaction()
        
        # 1. 좌석 상태 확인 (FOR UPDATE 락)
        cursor.execute('''
            SELECT status, reserved_by FROM seats 
            WHERE id = %s 
            FOR UPDATE
        ''', (seat_id,))
        seat = cursor.fetchone()
        
        if not seat:
            conn.rollback()
            conn.close()
            return {"success": False, "message": "존재하지 않는 좌석입니다"}
        
        # 2. 이미 예약된 좌석인지 확인
        if seat['status'] == 'reserved':
            conn.rollback()
            conn.close()
            logging.warning(f"❌ [SAFE] 예약 실패: user_id={user_id}, seat_id={seat_id} (이미 예약됨)")
            return {"success": False, "message": "이미 예약된 좌석입니다"}
        
        # 3. 해당 사용자가 이미 다른 좌석을 예약했는지 확인 (FOR UPDATE 락)
        cursor.execute('''
            SELECT COUNT(*) as count FROM seats 
            WHERE reserved_by = %s 
            FOR UPDATE
        ''', (user_id,))
        user_reservation = cursor.fetchone()
        
        if user_reservation['count'] > 0:
            conn.rollback()
            conn.close()
            return {"success": False, "message": "이미 좌석을 예약했습니다"}
        
        # 4. 좌석 예약 (락이 걸려있어 다른 요청은 대기)
        cursor.execute('''
            UPDATE seats 
            SET status = 'reserved', reserved_by = %s, reserved_at = NOW()
            WHERE id = %s
        ''', (user_id, seat_id))
        
        conn.commit()
        conn.close()
        
        logging.info(f"✅ [SAFE] 예약 성공: user_id={user_id}, seat_id={seat_id}")
        return {"success": True, "message": "좌석 예약 성공"}
        
    except Exception as e:
        conn.rollback()
        conn.close()
        logging.error(f"❌ [SAFE] 예약 오류: {str(e)}")
        return {"success": False, "message": "예약 중 오류 발생"}


def cancel_reservation(user_id, seat_id):
    """좌석 예약 취소"""
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 해당 좌석이 이 사용자가 예약한 것인지 확인
        cursor.execute('''
            SELECT reserved_by FROM seats 
            WHERE id = %s AND reserved_by = %s
        ''', (seat_id, user_id))
        
        seat = cursor.fetchone()
        
        if not seat:
            conn.close()
            return {"success": False, "message": "예약 취소 권한이 없습니다"}
        
        # 예약 취소
        cursor.execute('''
            UPDATE seats 
            SET status = 'available', reserved_by = NULL, reserved_at = NULL
            WHERE id = %s
        ''', (seat_id,))
        
        conn.commit()
        conn.close()
        
        logging.info(f"✅ 예약 취소: user_id={user_id}, seat_id={seat_id}")
        return {"success": True, "message": "예약이 취소되었습니다"}
        
    except Exception as e:
        conn.rollback()
        conn.close()
        logging.error(f"❌ 예약 취소 오류: {str(e)}")
        return {"success": False, "message": "예약 취소 중 오류 발생"}


def get_user_reservation(user_id):
    """사용자의 예약 좌석 조회"""
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute('''
        SELECT id, seat_number, row_num, col_num, reserved_at
        FROM seats
        WHERE reserved_by = %s
    ''', (user_id,))
    
    seat = cursor.fetchone()
    conn.close()
    return seat
