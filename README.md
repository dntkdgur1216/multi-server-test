# EC2 Multi-Server Communication Project

AWS EC2 인스턴스 간 통신을 테스트하기 위한 프로젝트입니다.
(VSCODE 코파일럿 성능 테스트용입니다)
## 아키텍처

```
EC2 Instance #1 (FastAPI)  ←→  EC2 Instance #2 (Spring Boot)
         ↓                             ↓
            RDS MySQL (공유 데이터베이스)
```

## 📁 프로젝트 구조

### fastapi-server/
- **기술 스택**: Python, FastAPI, MySQL
- **포트**: 8000
- **데이터베이스**: login_system
- **기능**:
  - 사용자 인증 (로그인/회원가입)
  - 쿠키 기반 세션 관리
  - 좌석 예약 시스템
  - 쇼핑 시스템 (동시성 테스트)
  - Spring Boot 세션 검증 API

### spring-boot-server/
- **기술 스택**: Java 18, Spring Boot 3.2, JPA/Hibernate, MySQL
- **포트**: 8082
- **데이터베이스**: notice_board
- **기능**:
  - 게시판 (공지사항/게시글/댓글)
  - FastAPI 쿠키 기반 인증 통합
  - MySQL utf8mb4 완벽 지원

## 🔐 인증 통합

두 서버는 쿠키 기반 세션을 공유합니다:
1. 사용자가 FastAPI에서 로그인
2. FastAPI가 세션 쿠키 발급
3. Spring Boot가 게시글 작성 시 쿠키를 FastAPI로 검증
4. FastAPI가 유효성 확인 후 사용자 정보 반환
5. Spring Boot가 해당 사용자로 게시글 저장

## 🚀 로컬 실행

### FastAPI 서버
```bash
cd fastapi-server
python -m venv TESTWEB
TESTWEB\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Spring Boot 서버
```bash
cd spring-boot-server
mvn spring-boot:run
```

### MySQL 데이터베이스 생성
```sql
CREATE DATABASE login_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE notice_board CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## ☁️ AWS 배포 계획

- **EC2 Instance #1**: FastAPI 서버 (Ubuntu 22.04)
- **EC2 Instance #2**: Spring Boot 서버 (Ubuntu 22.04 + JDK 18)
- **RDS MySQL**: 공유 데이터베이스 (Multi-AZ 옵션)

## 📝 주요 학습 내용

- ✅ 서로 다른 EC2 인스턴스 간 HTTP 통신
- ✅ 쿠키 기반 세션 공유 메커니즘
- ✅ MySQL utf8mb4 인코딩 완벽 처리
- ✅ CORS 설정 (Cross-Origin Resource Sharing)
- ✅ RDS 연결 및 보안 그룹 설정
- ✅ FastAPI + Spring Boot 이종 기술 스택 통합
