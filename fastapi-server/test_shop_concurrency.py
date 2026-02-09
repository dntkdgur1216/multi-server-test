"""동시성 테스트 스크립트 - 여러 요청을 동시에 보내서 Race Condition 테스트"""
import asyncio
import aiohttp
from datetime import datetime


async def buy_item(session, item_id, username, use_safe=False):
    """아이템 구매 요청"""
    url = f"http://localhost:8000/api/items/{item_id}/purchase"
    json_data = {
        "username": username,
        "use_safe": use_safe
    }
    
    try:
        async with session.post(url, json=json_data) as response:
            result = await response.json()
            return response.status, result.get("success", False)
    except Exception as e:
        return f"Error: {e}", False


async def run_concurrent_purchases(item_id, users, use_safe=False):
    """여러 사용자가 동시에 같은 아이템 구매 시도"""
    mode = "안전한 구매 (FOR UPDATE)" if use_safe else "위험한 구매 (Race Condition)"
    num_requests_per_user = 5
    total_requests = len(users) * num_requests_per_user
    
    print(f"\n{'='*70}")
    print(f"🧪 {mode} 테스트 시작")
    print(f"   아이템 ID: {item_id}")
    print(f"   테스트 계정 수: {len(users)}개")
    print(f"   각 계정당 동시 요청 수: {num_requests_per_user}")
    print(f"   총 요청 수: {total_requests}")
    print(f"   시작 시간: {datetime.now().strftime('%H:%M:%S.%f')}")
    print(f"{'='*70}")
    
    async with aiohttp.ClientSession() as session:
        # 각 사용자마다 5번씩 동시 구매 시도
        tasks = []
        for username in users:
            for _ in range(num_requests_per_user):
                tasks.append(buy_item(session, item_id, username, use_safe))
        
        start = datetime.now()
        results = await asyncio.gather(*tasks)
        end = datetime.now()
        
        # 결과 분석
        success_count = sum(1 for status, success in results if success)
        user_success = {}
        
        idx = 0
        for username in users:
            user_results = results[idx:idx+num_requests_per_user]
            user_success[username] = sum(1 for status, success in user_results if success)
            idx += num_requests_per_user
        
        print(f"\n✅ 완료!")
        print(f"   소요 시간: {(end - start).total_seconds():.2f}초")
        print(f"   총 성공 응답: {success_count}개 / {total_requests}개")
        print(f"\n📊 계정별 성공 횟수:")
        for username, count in user_success.items():
            if count > 0:
                print(f"   - {username}: {count}개")
        
        if not use_safe and success_count > 10:
            print(f"\n⚠️  Race Condition 발생!")
            print(f"   재고보다 많이 구매됨 (데이터 무결성 위반 가능)")
        elif use_safe:
            print(f"\n✅ 락(Lock)이 정상 작동!")
            print(f"   재고만큼만 구매 성공 (데이터 무결성 보장)")
        
        print(f"\n💡 MySQL Workbench에서 재고 확인:")
        print(f"   SELECT * FROM items WHERE id = {item_id};")
        print(f"   SELECT COUNT(*) FROM purchases WHERE item_id = {item_id};")


async def main():
    """메인 함수"""
    print("\n" + "="*70)
    print("🔬 아이템 구매 동시성 테스트 도구")
    print("="*70)
    
    # 테스트할 사용자들 (test1 ~ test10)
    users = [f"test{i}" for i in range(1, 11)]
    
    print(f"\n📌 테스트 계정: {', '.join(users)}")
    print("   (사전에 모든 계정이 회원가입되어 있어야 합니다)")
    
    # 테스트할 아이템 ID (기본: 1번 아이템)
    item_id_input = input("\n아이템 ID 입력 (기본: 1): ").strip()
    item_id = int(item_id_input) if item_id_input else 1
    
    print("\n어떤 테스트를 실행하시겠습니까?")
    print("1. 위험한 구매 (Race Condition 테스트)")
    print("2. 안전한 구매 (FOR UPDATE 락 테스트)")
    print("3. 둘 다 비교")
    
    choice = input("\n선택 (1/2/3): ").strip()
    
    if choice == "1":
        await run_concurrent_purchases(item_id, users, use_safe=False)
    elif choice == "2":
        await run_concurrent_purchases(item_id, users, use_safe=True)
    elif choice == "3":
        print("\n먼저 위험한 구매를 테스트합니다...")
        await asyncio.sleep(1)
        await run_concurrent_purchases(item_id, users, use_safe=False)
        
        input("\n\nDB 아이템 재고를 복구하고 Enter를 누르세요 (UPDATE items SET stock=10 WHERE id=아이템ID;)")
        
        print("\n\n안전한 구매를 테스트합니다...")
        await asyncio.sleep(1)
        await run_concurrent_purchases(item_id, users, use_safe=True)
    else:
        print("잘못된 선택입니다.")
    
    print("\n\n테스트 완료!")


if __name__ == "__main__":
    asyncio.run(main())
