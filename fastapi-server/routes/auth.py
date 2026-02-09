"""인증 관련 라우트"""
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from database import create_user, verify_user, get_user_id

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# ===== Pydantic 모델 =====
class SignupRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str


# ===== HTML 페이지 엔드포인트 =====


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """회원가입 페이지"""
    return templates.TemplateResponse("signup.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """로그인 페이지"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/welcome", response_class=HTMLResponse)
async def welcome(request: Request):
    """로그인 성공 페이지"""
    username = request.cookies.get("username")
    
    if not username:
        # 로그인 안 되어 있으면 로그인 페이지로
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse("welcome.html", {
        "request": request,
        "username": username
    })


@router.get("/logout")
async def logout():
    """로그아웃"""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("username")
    return response


# ===== REST API 엔드포인트 =====
@router.post("/api/signup")
async def signup_api(signup_data: SignupRequest):
    """회원가입 API"""
    success = create_user(signup_data.username, signup_data.password)
    
    if success:
        return JSONResponse(
            status_code=201,
            content={"success": True, "message": "회원가입 성공"}
        )
    else:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "이미 존재하는 사용자명입니다"}
        )


@router.post("/api/login")
async def login_api(login_data: LoginRequest):
    """로그인 API"""
    if verify_user(login_data.username, login_data.password):
        user_id = get_user_id(login_data.username)
        response = JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "로그인 성공",
                "username": login_data.username,
                "user_id": user_id
            }
        )
        # 쿠키 설정 (로그인 상태 유지)
        response.set_cookie(
            key="username",
            value=login_data.username,
            max_age=3600*24*7,  # 7일
            httponly=True
        )
        return response
    else:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "아이디 또는 비밀번호가 잘못되었습니다"}
        )


@router.get("/api/verify-session")
async def verify_session(request: Request):
    """세션 검증 API - Spring Boot에서 호출"""
    username = request.cookies.get("username")
    
    if username:
        user_id = get_user_id(username)
        return JSONResponse(
            status_code=200,
            content={
                "valid": True,
                "username": username,
                "user_id": user_id
            }
        )
    else:
        return JSONResponse(
            status_code=401,
            content={"valid": False, "message": "로그인되지 않음"}
        )
