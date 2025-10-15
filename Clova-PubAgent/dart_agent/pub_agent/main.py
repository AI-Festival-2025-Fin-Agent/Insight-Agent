#!/usr/bin/env python3
"""
DART Agent 메인 실행 파일
LangGraph 기반 DART 공시 검색 에이전트
"""

from .workflow import DartAgentWorkflow

# langgraph-cli dev용 전역 워크플로우 객체
agent = DartAgentWorkflow()
workflow = agent.workflow  # langgraph-cli가 찾는 변수명

def main():
    """대화형 인터페이스"""
    print("="*60)
    print("🚀 DART Agent (LangGraph 기반) 시작")
    print("공시문서 검색 및 분석을 도와드립니다.")
    print("="*60)
    print("\n사용법:")
    print("- 일반 질문: '삼성전자 2024년 1분기 실적 알려줘'")
    print("- 검색만: '카카오 2025년 1분기 찾기만 해줘'")
    print("- 검색 타입: 기본(정기공시만), 'revision'(수정공시만), 'both'(둘다)")
    print("- 종료: 'exit' 입력")
    print("-"*60)

    # 이미 전역에서 초기화된 agent 사용

    while True:
        try:
            # 사용자 질문 입력
            query = input("\n💬 질문을 입력하세요: ").strip()

            if query.lower() in ['exit', '종료', 'quit']:
                print("\n👋 DART Agent를 종료합니다.")
                break

            if not query:
                print("❌ 질문을 입력해주세요.")
                continue

            print(f"\n🔍 문서 검색 중...")
            print("-"*60)

            # 워크플로우 실행 (기본값: 정기공시만)
            result = agent.run(query)

            # 결과 출력
            print("\n📋 검색 결과:")
            print("="*60)
            if result.get("success"):
                print(f"✅ {result.get('message')}")
                print(f"회사명: {result.get('company_name')}")
                extracted_info = result.get('extracted_info', {})
                if extracted_info:
                    print(f"추출된 정보: {extracted_info}")
                raw_data = result.get('raw_data', {})
                if raw_data:
                    print(f"검색된 문서 수: {len(raw_data.get('documents', []))}")
            else:
                print(f"❌ 검색 실패: {result.get('error')}")
            print("="*60)

        except KeyboardInterrupt:
            print("\n\n👋 사용자 중단으로 DART Agent를 종료합니다.")
            break
        except Exception as e:
            print(f"\n❌ 오류가 발생했습니다: {e}")
            print("다시 시도해주세요.")

def test_basic_functionality():
    """기본 기능 테스트"""
    print("🧪 DART Agent 기본 기능 테스트")
    print("-"*40)

    agent = DartAgentWorkflow()

    test_cases = [
        {
            "query": "삼성전자 2024년 1분기 실적",
            "mode": None,
            "description": "기본 검색 및 요약"
        },
        {
            "query": "카카오 2025년 1분기 찾기만",
            "mode": None,
            "description": "검색만 수행"
        },
        {
            "query": "LG에너지솔루션 최근 실적",
            "mode": "beginner",
            "description": "초보자 모드 분석"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n테스트 {i}: {test['description']}")
        print(f"질문: {test['query']}")
        print(f"모드: {test['mode'] or '기본'}")
        print("-"*30)

        try:
            result = agent.run(test['query'])
            print("✅ 성공")
            print(f"검색 성공: {result.get('success', False)}")
        except Exception as e:
            print(f"❌ 실패: {e}")

        print("-"*30)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_basic_functionality()
    else:
        main()