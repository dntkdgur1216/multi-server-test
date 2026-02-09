"""쇼핑몰 관련 라우트"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from database import (
    get_all_items, 
    purchase_item_unsafe, 
    purchase_item_safe,
    get_user_purchases,
    get_user_id,
    init_sample_items
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# ===== Pydantic 모델 =====
class PurchaseRequest(BaseModel):
    username: str
    use_safe: bool = False


# ===== HTML 페이지 엔드포인트 =====
@router.get("/shop", response_class=HTMLResponse)
async def shop(request: Request):
    """아이템 목록 페이지"""
    # 샘플 아이템 초기화 (최초 1회)
    init_sample_items()
    
    items = get_all_items()
    username = request.cookies.get("username")
    
    return templates.TemplateResponse("shop.html", {
        "request": request,
        "items": items,
        "username": username
    })


@router.get("/purchases", response_class=HTMLResponse)
async def my_purchases(request: Request):
    """내 구매 내역"""
    username = request.cookies.get("username")
    
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    user_id = get_user_id(username)
    purchases = get_user_purchases(user_id)
    
    return templates.TemplateResponse("purchases.html", {
        "request": request,
        "purchases": purchases,
        "username": username
    })


# ===== REST API 엔드포인트 =====
@router.get("/api/items")
async def get_items_api():
    """아이템 목록 조회 API"""
    items = get_all_items()
    return JSONResponse(content={"items": items})


@router.post("/api/items/{item_id}/purchase")
async def purchase_item_api(item_id: int, purchase_data: PurchaseRequest):
    """아이템 구매 API"""
    user_id = get_user_id(purchase_data.username)
    
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "로그인이 필요합니다"}
        )
    
    # 안전한 버전 vs 불안전한 버전 선택
    if purchase_data.use_safe:
        result = purchase_item_safe(user_id, item_id, quantity=1)
    else:
        result = purchase_item_unsafe(user_id, item_id, quantity=1)
    
    # 성공/실패에 따라 다른 상태 코드 반환
    status_code = 200 if result["success"] else 400
    return JSONResponse(status_code=status_code, content=result)
