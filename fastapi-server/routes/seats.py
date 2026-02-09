"""좌석 예약 관련 라우트"""
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import json
from typing import List

from database import (
    get_all_seats,
    reserve_seat_unsafe,
    reserve_seat_safe,
    cancel_reservation,
    get_user_reservation,
    get_user_id,
    init_sample_seats,
    get_all_items,
    get_user_purchases
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# ===== Pydantic 모델 =====
class ReserveRequest(BaseModel):
    username: str
    seat_id: int
    use_safe: bool = False


class CancelRequest(BaseModel):
    username: str
    seat_id: int


# ===== HTML 페이지 엔드포인트 =====
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """실시간 대시보드 페이지"""
    username = request.cookies.get("username")
    
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    # 초기 좌석 데이터 가져오기
    seats = get_all_seats()
    seats_safe = []
    for seat in seats:
        seat_dict = dict(seat)
        for key, value in seat_dict.items():
            if hasattr(value, 'isoformat'):
                seat_dict[key] = str(value)
        seats_safe.append(seat_dict)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": username,
        "initial_seats": json.dumps(seats_safe)
    })


@router.get("/seats", response_class=HTMLResponse)
async def seats_page(request: Request):
    """좌석 예약 페이지"""
    # 샘플 좌석 초기화 (최초 1회)
    init_sample_seats()
    
    username = request.cookies.get("username")
    
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    seats = get_all_seats()
    user_id = get_user_id(username)
    my_reservation = get_user_reservation(user_id) if user_id else None
    
    # datetime 객체를 문자열로 변환 (JSON 직렬화 가능하도록)
    seats_safe = []
    for seat in seats:
        seat_dict = dict(seat)
        # 모든 datetime 객체를 문자열로 변환
        for key, value in seat_dict.items():
            if hasattr(value, 'isoformat'):  # datetime 객체인 경우
                seat_dict[key] = str(value)
        seats_safe.append(seat_dict)
    
    if my_reservation and my_reservation.get('reserved_at'):
        my_reservation['reserved_at'] = str(my_reservation['reserved_at'])
    
    return templates.TemplateResponse("seats.html", {
        "request": request,
        "username": username,
        "seats_json": json.dumps(seats_safe),
        "my_reservation_json": json.dumps(my_reservation) if my_reservation else "null"
    })


# ===== REST API 엔드포인트 =====
@router.get("/api/seats")
async def get_seats_api():
    """좌석 목록 조회 API"""
    seats = get_all_seats()
    return JSONResponse(content={"seats": seats})


@router.post("/api/seats/reserve")
async def reserve_seat_api(reserve_data: ReserveRequest):
    """좌석 예약 API"""
    user_id = get_user_id(reserve_data.username)
    
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "로그인이 필요합니다"}
        )
    
    # 안전한 버전 vs 불안전한 버전 선택
    if reserve_data.use_safe:
        result = reserve_seat_safe(user_id, reserve_data.seat_id)
    else:
        result = reserve_seat_unsafe(user_id, reserve_data.seat_id)
    
    status_code = 200 if result["success"] else 400
    return JSONResponse(status_code=status_code, content=result)


@router.post("/api/seats/cancel")
async def cancel_seat_api(cancel_data: CancelRequest):
    """좌석 예약 취소 API"""
    user_id = get_user_id(cancel_data.username)
    
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "로그인이 필요합니다"}
        )
    
    result = cancel_reservation(user_id, cancel_data.seat_id)
    status_code = 200 if result["success"] else 400
    return JSONResponse(status_code=status_code, content=result)


# ===== WebSocket 실시간 업데이트 (기존 HTTP 방식과 비교) =====
class ConnectionManager:
    """WebSocket 연결 관리 클래스 - 여러 클라이언트의 실시간 연결을 관리"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """새로운 클라이언트 연결"""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ WebSocket 연결됨. 현재 접속자: {len(self.active_connections)}명")
    
    def disconnect(self, websocket: WebSocket):
        """클라이언트 연결 해제"""
        self.active_connections.remove(websocket)
        print(f"❌ WebSocket 연결 끊김. 현재 접속자: {len(self.active_connections)}명")
    
    async def broadcast(self, message: dict):
        """모든 연결된 클라이언트에게 메시지 브로드캐스트 (실시간 업데이트)"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"⚠️ 메시지 전송 실패: {e}")

# WebSocket 연결 관리자 인스턴스
manager = ConnectionManager()


@router.websocket("/ws/seats")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 엔드포인트 - 실시간 좌석 상태 업데이트
    
    기존 HTTP 방식과의 차이:
    - HTTP: 클라이언트가 새로고침해야 다른 사람의 예약을 확인
    - WebSocket: 서버가 자동으로 모든 클라이언트에게 변경사항 푸시
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신 (예약/취소 요청)
            data = await websocket.receive_json()
            action = data.get("action")
            username = data.get("username")
            seat_id = data.get("seat_id")
            use_safe = data.get("use_safe", True)
            
            user_id = get_user_id(username)
            
            if not user_id:
                await websocket.send_json({
                    "type": "error",
                    "message": "로그인이 필요합니다"
                })
                continue
            
            # 액션에 따라 처리
            if action == "reserve":
                # 좌석 예약
                print(f"📥 예약 요청: user={username}, seat={seat_id}, safe={use_safe}")
                if use_safe:
                    result = reserve_seat_safe(user_id, seat_id)
                else:
                    result = reserve_seat_unsafe(user_id, seat_id)
                
                print(f"📋 예약 결과: {result}")
                if result["success"]:
                    # 예약 성공 시 모든 클라이언트에게 브로드캐스트
                    print(f"📢 브로드캐스트 전송 중... 접속자 {len(manager.active_connections)}명")
                    
                    # 최신 좌석 정보 가져오기
                    seats = get_all_seats()
                    seats_safe = []
                    for seat in seats:
                        seat_dict = dict(seat)
                        for key, value in seat_dict.items():
                            if hasattr(value, 'isoformat'):
                                seat_dict[key] = str(value)
                        seats_safe.append(seat_dict)
                    
                    # 모든 클라이언트에게 업데이트된 좌석 정보 전송
                    await manager.broadcast({
                        "type": "seat_update",
                        "action": "reserved",
                        "seat_id": seat_id,
                        "username": username,
                        "message": result["message"],
                        "seats": seats_safe  # 최신 좌석 정보 포함
                    })
                    print("✅ 브로드캐스트 완료")
                else:
                    # 실패 시 해당 클라이언트에게만 응답
                    await websocket.send_json({
                        "type": "error",
                        "message": result["message"]
                    })
            
            elif action == "cancel":
                # 예약 취소
                result = cancel_reservation(user_id, seat_id)
                
                if result["success"]:
                    # 최신 좌석 정보 가져오기
                    seats = get_all_seats()
                    seats_safe = []
                    for seat in seats:
                        seat_dict = dict(seat)
                        for key, value in seat_dict.items():
                            if hasattr(value, 'isoformat'):
                                seat_dict[key] = str(value)
                        seats_safe.append(seat_dict)
                    
                    # 취소 성공 시 모든 클라이언트에게 브로드캐스트
                    await manager.broadcast({
                        "type": "seat_update",
                        "action": "cancelled",
                        "seat_id": seat_id,
                        "username": username,
                        "message": result["message"],
                        "seats": seats_safe  # 최신 좌석 정보 포함
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": result["message"]
                    })
            
            elif action == "refresh" or action == "get_all":
                # 전체 좌석 정보 새로고침 또는 초기 데이터 요청
                seats = get_all_seats()
                
                # datetime 객체를 문자열로 변환 (JSON 직렬화 가능하도록)
                seats_safe = []
                for seat in seats:
                    seat_dict = dict(seat)
                    for key, value in seat_dict.items():
                        if hasattr(value, 'isoformat'):  # datetime 객체인 경우
                            seat_dict[key] = str(value)
                    seats_safe.append(seat_dict)
                
                print(f"📤 좌석 정보 전송: {len(seats_safe)}개 (action: {action})")
                await websocket.send_json({
                    "type": "all_seats",
                    "seats": seats_safe
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"❌ WebSocket 에러: {e}")
        manager.disconnect(websocket)
