"""좌석 예약 동시성 테스트 스크립트 - 여러 사용자가 동시에 같은 좌석 예약"""
import asyncio
import aiohttp
from datetime import datetime


async def reserve_seat(session, seat_id, username, use_safe=False):
    """좌석 예약 요청"""
    url = f"http://localhost:8000/api/seats/reserve"
    json_data = {
        "username": username,
        "seat_id": seat_id,
        "use_safe": use_safe
    }
    
    try:
        async with session.post(url, json=json_data) as response:
            result = await response.json()
            return response.status, result.get("success", False), result.get("message", "")
    except Exception as e:
        return f"Error: {e}", False, str(e)


async def run_concurrent_reservations(seat_id, users, use_safe=False):
    """여러 사용자가 동시에 같은 좌석 예약 시도"""
    mode = "안전한 예약 (FOR UPDATE)" if use_safe else "위험한 예약 (Race Condition)"
    print(f"\n{'='*70}")
    print(f"🧪 {mode} 테스트 시작")
    print(f"   좌석 ID: {seat_id}")
    print(f"   테스트 계정 수: {len(users)}개")
    print(f"   각 계정당 동시 요청 수: 5")
    print(f"   총 요청 수: {len(users) * 5}")
    print(f"   시작 시간: {datetime.now().strftime('%H:%M:%S.%f')}")
    print(f"{'='*70}")
    
    async with aiohttp.ClientSession() as session:
        # 각 사용자마다 5번씩 동시 예약 시도
        tasks = []
        for username in users:
            for _ in range(5):
                tasks.append(reserve_seat(session, seat_id, username, use_safe))
        
        start = datetime.now()
        results = await asyncio.gather(*tasks)
        end = datetime.now()
        
        # 결과 분석
        success_count = sum(1 for status, success, msg in results if success)
        user_success = {}
        
        idx = 0
        for username in users:
            user_results = results[idx:idx+5]
            user_success[username] = sum(1 for status, success, msg in user_results if success)
            idx += 5
        
        print(f"\n✅ 완료!")
        print(f"   소요 시간: {(end - start).total_seconds():.2f}초")
        print(f"   총 성공 응답: {success_count}개 / {len(results)}개")
        print(f"\n📊 계정별 성공 횟수:")
        for username, count in user_success.items():
            if count > 0:
                print(f"   - {username}: {count}개")
        
        if not use_safe and success_count > 1:
            print(f"\n⚠️  Race Condition 발생!")
            print(f"   여러 사용자가 동시에 예약 성공 (데이터 무결성 위반)")
            print(f"   예상: 1명만 성공, 실제: {success_count}명 성공")
        elif use_safe and success_count == 1:
            print(f"\n✅ 락(Lock)이 정상 작동!")
            print(f"   한 명만 예약 성공 (데이터 무결성 보장)")
        elif success_count == 0:
            print(f"\n⚠️  모든 요청 실패! 좌석 ID나 계정을 확인하세요.")
        
        print(f"\n💡 MySQL Workbench에서 확인:")
        print(f"   SELECT * FROM seats WHERE id = {seat_id};")
        print(f"   SELECT seat_number, reserved_by FROM seats WHERE reserved_by IS NOT NULL;")


async def cleanup_reservations():
    """테스트 후 예약 초기화"""
    print("\n🧹 예약 데이터 정리 중...")
    async with aiohttp.ClientSession() as session:
        # 모든 예약 취소 (DB 직접 접근 대신 API 사용)
        url = "http://localhost:8000/api/seats"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                seats = data.get("seats", [])
                
                # 예약된 좌석들 찾아서 취소
                # 실제로는 DB에서 직접 DELETE 하는게 나음
                print("   ⚠️  수동으로 DB 초기화 필요: DELETE FROM seats WHERE reserved_by IS NOT NULL;")


async def main():
    """메인 함수"""
    print("\n" + "="*70)
    print("🔬 좌석 예약 동시성 테스트 도구")
    print("="*70)
    
    # 테스트할 사용자들 (test1 ~ test10)
    users = [f"test{i}" for i in range(1, 11)]
    
    print(f"\n📌 테스트 계정: {', '.join(users)}")
    print("   (사전에 모든 계정이 회원가입되어 있어야 합니다)")
    
    # 테스트할 좌석 ID
    seat_id_input = input("\n좌석 ID 입력 (기본: 1): ").strip()
    seat_id = int(seat_id_input) if seat_id_input else 1
    
    print("\n어떤 테스트를 실행하시겠습니까?")
    print("1. 위험한 예약 (Race Condition 테스트)")
    print("2. 안전한 예약 (FOR UPDATE 락 테스트)")
    print("3. 둘 다 비교")
    
    choice = input("\n선택 (1/2/3): ").strip()
    
    if choice == "1":
        await run_concurrent_reservations(seat_id, users, use_safe=False)
    elif choice == "2":
        await run_concurrent_reservations(seat_id, users, use_safe=True)
    elif choice == "3":
        print("\n먼저 위험한 예약을 테스트합니다...")
        await asyncio.sleep(1)
        await run_concurrent_reservations(seat_id, users, use_safe=False)
        
        input("\n\nDB를 초기화하고 Enter를 누르세요 (DELETE FROM seats WHERE reserved_by IS NOT NULL;)")
        
        print("\n\n안전한 예약을 테스트합니다...")
        await asyncio.sleep(1)
        await run_concurrent_reservations(seat_id, users, use_safe=True)
    else:
        print("잘못된 선택입니다.")
    
    print("\n\n테스트 완료!")


if __name__ == "__main__":
    asyncio.run(main())
