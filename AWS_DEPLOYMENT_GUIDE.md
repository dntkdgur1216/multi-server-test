# AWS 배포 가이드 (EC2 2개 + RDS 구성)

## 🎯 배포 아키텍처

```
인터넷
  ↓
EC2 Instance #1 (FastAPI)  ←→  EC2 Instance #2 (Spring Boot)
  Port 8000                      Port 8082
  ↓                              ↓
        RDS MySQL (공유 데이터베이스)
        login_system + notice_board
```

---

## 📋 사전 준비

### 필요한 계정/도구
- [ ] AWS 계정 ([aws.amazon.com](https://aws.amazon.com))
- [ ] SSH 클라이언트 (Windows: PuTTY 또는 WSL, macOS/Linux: 기본 제공)
- [ ] GitHub 저장소 (코드 배포용)

### 예상 비용
- EC2 t2.micro x2: **프리티어 대상** (12개월 무료, 이후 월 ~$15)
- RDS db.t3.micro: **프리티어 대상** (12개월 무료, 이후 월 ~$15)
- **총 예상 비용**: 프리티어 기간 중 무료, 이후 월 $30

---

## 1단계: RDS MySQL 데이터베이스 생성

### 1.1 RDS 생성
1. AWS Console → **RDS** 서비스 이동
2. **Create database** 클릭
3. 설정:
   - **Engine**: MySQL
   - **Version**: MySQL 8.0.x
   - **Templates**: **Free tier** 선택 ⭐
   - **DB instance identifier**: `multi-server-db`
   - **Master username**: `admin`
   - **Master password**: 안전한 비밀번호 설정 (예: `Admin123!@#`)
   - **DB instance class**: `db.t3.micro` (프리티어)
   - **Storage**: 20GB (기본값)
   - **VPC**: Default VPC 선택
   - **Public access**: **Yes** ⭐ (개발/테스트용)
   - **VPC security group**: 새로 생성 (`multi-server-rds-sg`)
   - **Database name**: `login_system` (초기 DB 이름)

4. **Create database** 클릭 (생성 시간: 약 5-10분)

### 1.2 보안 그룹 설정
1. RDS → Security Groups → `multi-server-rds-sg` 클릭
2. **Inbound rules** 편집:
   - Type: **MySQL/Aurora**
   - Port: **3306**
   - Source: **Anywhere-IPv4** (0.0.0.0/0) ⚠️ 개발용, 프로덕션에서는 EC2 보안그룹만 허용

### 1.3 데이터베이스 생성
RDS 엔드포인트 확인 후 MySQL 접속:
```bash
mysql -h <RDS_ENDPOINT> -u admin -p
```

```sql
-- 두 개의 데이터베이스 생성
CREATE DATABASE login_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE notice_board CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

SHOW DATABASES;
EXIT;
```

**RDS 엔드포인트 예시**: `multi-server-db.xxxx.ap-northeast-2.rds.amazonaws.com`

---

## 2단계: EC2 Instance #1 (FastAPI) 생성

### 2.1 EC2 인스턴스 생성
1. AWS Console → **EC2** 서비스 이동
2. **Launch Instance** 클릭
3. 설정:
   - **Name**: `fastapi-server`
   - **AMI**: Ubuntu Server 22.04 LTS 
   - **Instance type**: **t2.micro** (프리티어)
   - **Key pair**: 새로 생성 (`multi-server-key.pem`) - **저장 필수!**
   - **Network settings**:
     - VPC: Default
     - Auto-assign public IP: **Enable**
     - Security group: 새로 생성 (`fastapi-sg`)
       ```
       SSH      | 22   | My IP
       Custom   | 8000 | Anywhere (0.0.0.0/0)
       ```
4. **Launch instance** 클릭

### 2.2 FastAPI 서버 설정

#### SSH 접속
```bash
chmod 400 multi-server-key.pem
ssh -i multi-server-key.pem ubuntu@<EC2_PUBLIC_IP>
```

#### 시스템 업데이트 및 Python 설치
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git
```

#### 프로젝트 클론
```bash
cd ~
git clone https://github.com/dntkdgur1216/multi-server-test.git
cd multi-server-test/fastapi-server
```

#### 가상환경 및 패키지 설치
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 환경변수 설정
```bash
cp .env.example .env
nano .env
```

`.env` 파일 내용:
```bash
# 데이터베이스 설정 (RDS)
DB_HOST=multi-server-db.xxxx.ap-northeast-2.rds.amazonaws.com
DB_PORT=3306
DB_USER=admin
DB_PASSWORD=Admin123!@#
DB_NAME=login_system

# 서버 설정
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# Spring Boot 서버 URL (나중에 업데이트)
SPRING_BOOT_URL=http://EC2-2-PUBLIC-IP:8082
```

**저장**: `Ctrl+O` → Enter → `Ctrl+X`

#### 서버 실행 테스트
```bash
python main.py
```

브라우저에서 `http://EC2-1-PUBLIC-IP:8000` 접속 확인

---

## 3단계: EC2 Instance #2 (Spring Boot) 생성

### 3.1 EC2 인스턴스 생성
1. EC2 → **Launch Instance**
2. 설정:
   - **Name**: `spring-boot-server`
   - **AMI**: Ubuntu Server 22.04 LTS
   - **Instance type**: **t2.micro**
   - **Key pair**: 기존 `multi-server-key.pem` 선택
   - **Security group**: 새로 생성 (`spring-boot-sg`)
     ```
     SSH      | 22   | My IP
     Custom   | 8082 | Anywhere (0.0.0.0/0)
     ```

### 3.2 Spring Boot 서버 설정

#### SSH 접속
```bash
ssh -i multi-server-key.pem ubuntu@<EC2_2_PUBLIC_IP>
```

#### Java 및 Maven 설치
```bash
sudo apt update
sudo apt install -y openjdk-18-jdk maven git
java -version  # 확인
mvn -version   # 확인
```

#### 프로젝트 클론
```bash
cd ~
git clone https://github.com/dntkdgur1216/multi-server-test.git
cd multi-server-test/spring-boot-server
```

#### 환경변수 설정
```bash
cp .env.example .env
nano .env
```

`.env` 파일 내용:
```bash
# 데이터베이스 설정 (RDS)
DB_HOST=multi-server-db.xxxx.ap-northeast-2.rds.amazonaws.com
DB_PORT=3306
DB_USER=admin
DB_PASSWORD=Admin123!@#
DB_NAME=notice_board

# FastAPI 서버 URL
FASTAPI_URL=http://EC2-1-PUBLIC-IP:8000

# 서버 포트
SERVER_PORT=8082
```

#### 환경변수 로드 및 빌드
```bash
# .env 파일을 시스템 환경변수로 export
export $(cat .env | xargs)

# Maven 빌드 및 실행
mvn clean package
mvn spring-boot:run
```

브라우저에서 `http://EC2-2-PUBLIC-IP:8082` 접속 확인

---

## 4단계: 서버 간 통신 설정

### 4.1 FastAPI의 SPRING_BOOT_URL 업데이트

EC2 #1 (FastAPI)에 접속:
```bash
ssh -i multi-server-key.pem ubuntu@<EC2_1_PUBLIC_IP>
cd ~/multi-server-test/fastapi-server
nano .env
```

`SPRING_BOOT_URL` 수정:
```bash
SPRING_BOOT_URL=http://EC2-2-PUBLIC-IP:8082
```

서버 재시작:
```bash
source venv/bin/activate
python main.py
```

### 4.2 통신 테스트
1. FastAPI 서버에서 회원가입/로그인: `http://EC2-1-PUBLIC-IP:8000/signup`
2. Spring Boot 게시판 접속: `http://EC2-2-PUBLIC-IP:8082`
3. 게시글 작성 → FastAPI 쿠키 인증 확인 ✅
4. 게시판에서 "🔑 로그인" 클릭 → FastAPI 로그인 페이지로 이동 확인 ✅

---

## 5단계: 백그라운드 실행 (서비스화)

### 5.1 FastAPI Systemd 서비스

EC2 #1에서:
```bash
sudo nano /etc/systemd/system/fastapi.service
```

내용:
```ini
[Unit]
Description=FastAPI Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/multi-server-test/fastapi-server
Environment="PATH=/home/ubuntu/multi-server-test/fastapi-server/venv/bin"
EnvironmentFile=/home/ubuntu/multi-server-test/fastapi-server/.env
ExecStart=/home/ubuntu/multi-server-test/fastapi-server/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

활성화:
```bash
sudo systemctl daemon-reload
sudo systemctl enable fastapi
sudo systemctl start fastapi
sudo systemctl status fastapi
```

### 5.2 Spring Boot Systemd 서비스

EC2 #2에서:
```bash
sudo nano /etc/systemd/system/springboot.service
```

내용:
```ini
[Unit]
Description=Spring Boot Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/multi-server-test/spring-boot-server
EnvironmentFile=/home/ubuntu/multi-server-test/spring-boot-server/.env
ExecStart=/usr/bin/mvn spring-boot:run
Restart=always

[Install]
WantedBy=multi-user.target
```

활성화:
```bash
sudo systemctl daemon-reload
sudo systemctl enable springboot
sudo systemctl start springboot
sudo systemctl status springboot
```

---

## ✅ 배포 완료 체크리스트

- [ ] RDS MySQL 생성 완료 (login_system + notice_board)
- [ ] EC2 #1 (FastAPI) 실행 중
- [ ] EC2 #2 (Spring Boot) 실행 중
- [ ] FastAPI → RDS 연결 성공
- [ ] Spring Boot → RDS 연결 성공
- [ ] FastAPI 로그인 기능 동작
- [ ] Spring Boot 게시글 작성 시 FastAPI 세션 검증 성공
- [ ] 서버 간 네비게이션 링크 동작
- [ ] Systemd 서비스 자동 시작 설정 완료

---

## 🔧 트러블슈팅

### RDS 연결 실패
```bash
# 보안 그룹 확인
# RDS 보안 그룹에 3306 포트가 열려있는지 확인
```

### 환경변수가 적용 안 됨
```bash
# .env 파일 확인
cat .env

# 환경변수 export 확인 (Spring Boot)
export $(cat .env | xargs)
env | grep DB_HOST
```

### 포트가 이미 사용 중
```bash
# 기존 프로세스 종료
sudo lsof -ti:8000 | xargs sudo kill -9
sudo lsof -ti:8082 | xargs sudo kill -9
```

### 로그 확인
```bash
# FastAPI
journalctl -u fastapi -f

# Spring Boot
journalctl -u springboot -f
```

---

## 🧹 정리 (과금 방지)

테스트 완료 후:
1. EC2 인스턴스 **Terminate**
2. RDS 데이터베이스 **Delete** (스냅샷 없이)
3. 보안 그룹 삭제
4. Elastic IP 해제 (사용한 경우)

---

## 📚 다음 단계

- [ ] HTTPS 적용 (Let's Encrypt)
- [ ] Nginx 리버스 프록시 설정
- [ ] 프로덕션용 보안 그룹 강화 (EC2만 RDS 접근 허용)
- [ ] Auto Scaling 구성
- [ ] CloudWatch 모니터링 설정
