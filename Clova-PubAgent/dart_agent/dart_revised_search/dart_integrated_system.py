"""
DART 통합 시스템
회사명으로 검색 -> 문서 리스트 -> 문서 내용 -> JSON 출력
"""

import json
import requests
from datetime import datetime, timedelta
from .dart_web_crawler import DartWebCrawler
from .dart_document_fetcher import DartDocumentFetcher


class DartIntegratedSystem:
    """DART 검색과 문서 내용 추출을 통합한 시스템"""

    def __init__(self):
        self.crawler = DartWebCrawler()

    def search_and_fetch_documents(self, company_name, max_documents=5, days=365, start_date=None, end_date=None, fetch_content=True):
        """
        회사명으로 검색하고 문서 내용까지 가져오기

        Args:
            company_name (str): 검색할 회사명
            max_documents (int): 최대 가져올 문서 수 (기본 5개)
            days (int): 검색 기간 (기본 365일)
            start_date (str): 시작일 (YYYY-MM-DD)
            end_date (str): 종료일 (YYYY-MM-DD)
            fetch_content (bool): 문서 내용까지 가져올지 여부 (기본 True)

        Returns:
            dict: JSON 형식의 결과
        """
        print(f"🔍 '{company_name}' 검색 및 문서 내용 추출 시작...")

        result = {
            "search_query": company_name,
            "search_date": datetime.now().isoformat(),
            "search_period_days": days,
            "documents_found": 0,
            "documents_processed": 0,
            "documents": []
        }

        try:
            # 1. 공시 검색
            print(f"📋 1단계: 공시 목록 검색...")
            if start_date and end_date:
                disclosures = self.crawler.search_company_disclosures(
                    company_name,
                    start_date=start_date,
                    end_date=end_date
                )
            else:
                disclosures = self.crawler.search_company_disclosures(
                    company_name,
                    days=days
                )

            result["documents_found"] = len(disclosures)
            print(f"✅ {len(disclosures)}건의 공시 발견")

            if not disclosures:
                print("❌ 검색된 공시가 없습니다.")
                return result

            # 2. 최대 개수만큼 문서 처리
            documents_to_process = disclosures[:max_documents]
            print(f"📄 2단계: 상위 {len(documents_to_process)}개 문서 처리...")

            if fetch_content:
                # requests 사용한 문서 내용 추출
                with DartDocumentFetcher() as fetcher:
                    for i, disclosure in enumerate(documents_to_process, 1):
                        print(f"\n📖 {i}/{len(documents_to_process)}: {disclosure['report']}")

                        document_data = {
                            "index": i,
                            "basic_info": {
                                "company": disclosure['company'],
                                "report_name": disclosure['report'],
                                "submitter": disclosure['submitter'],
                                "date": disclosure['date'],
                                "rcept_no": disclosure['rcept_no'],
                                "url": disclosure['url'],
                                "is_correction": disclosure['is_correction']
                            },
                            "content": None,
                            "content_length": 0,
                            "extraction_status": "pending"
                        }

                        # 문서 내용 추출 시도
                        if disclosure['url']:
                            try:
                                doc_info = fetcher.get_document_content(disclosure['url'])
                                if doc_info and doc_info.get('content'):
                                    document_data["content"] = doc_info['content']
                                    document_data["content_length"] = len(doc_info['content'])
                                    document_data["extraction_status"] = "success"

                                    # 추가 정보가 있다면 포함
                                    if doc_info.get('title'):
                                        document_data["basic_info"]["title"] = doc_info['title']

                                    print(f"✅ 내용 추출 완료 ({document_data['content_length']} 문자)")
                                else:
                                    document_data["extraction_status"] = "failed"
                                    print(f"❌ 내용 추출 실패")
                            except Exception as e:
                                document_data["extraction_status"] = "error"
                                document_data["error"] = str(e)
                                print(f"❌ 오류 발생: {e}")
                        else:
                            document_data["extraction_status"] = "no_url"
                            print(f"❌ URL 없음")

                        result["documents"].append(document_data)
                        result["documents_processed"] += 1

            else:
                # 문서 내용 없이 기본 정보만
                for i, disclosure in enumerate(documents_to_process, 1):
                    document_data = {
                        "index": i,
                        "basic_info": {
                            "company": disclosure['company'],
                            "report_name": disclosure['report'],
                            "submitter": disclosure['submitter'],
                            "date": disclosure['date'],
                            "rcept_no": disclosure['rcept_no'],
                            "url": disclosure['url'],
                            "is_correction": disclosure['is_correction']
                        },
                        "content": None,
                        "content_length": 0,
                        "extraction_status": "skipped"
                    }
                    result["documents"].append(document_data)
                    result["documents_processed"] += 1

            print(f"\n✅ 전체 처리 완료!")
            print(f"📊 검색된 문서: {result['documents_found']}건")
            print(f"📊 처리된 문서: {result['documents_processed']}건")

            return result

        except Exception as e:
            result["error"] = str(e)
            print(f"❌ 시스템 오류: {e}")
            return result


    def save_results_to_json(self, result, filename=None):
        """결과를 JSON 파일로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            company_name = result.get('search_query', 'unknown').replace(' ', '_')
            filename = f"dart_results_{company_name}_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"💾 결과를 {filename}에 저장했습니다.")
            return filename
        except Exception as e:
            print(f"❌ JSON 저장 실패: {e}")
            return None

    def print_summary(self, result):
        """결과 요약 출력"""
        print(f"\n📊 검색 결과 요약")
        print("="*50)
        print(f"🔍 검색어: {result['search_query']}")
        print(f"📅 검색일: {result['search_date'][:19]}")
        print(f"📋 발견된 문서: {result['documents_found']}건")
        print(f"📄 처리된 문서: {result['documents_processed']}건")

        if result.get('documents'):
            print(f"\n📝 문서 목록:")
            for doc in result['documents']:
                print(f"  {doc['index']}. {doc['basic_info']['report_name']}")
                print(f"     📅 {doc['basic_info']['date']} | 상태: {doc['extraction_status']}")
                if doc['content_length'] > 0:
                    print(f"     📄 내용: {doc['content_length']} 문자")


def main():
    """메인 함수"""
    system = DartIntegratedSystem()

    print("🎯 DART 통합 검색 시스템")
    print("="*40)

    while True:
        print("\n📋 옵션 선택:")
        print("1. 회사 검색")
        print("2. 종료")

        choice = input("\n선택하세요 (1-2): ").strip()

        if choice == '2':
            print("👋 종료합니다.")
            break

        if choice != '1':
            print("❌ 잘못된 선택입니다.")
            continue

        # 검색 파라미터 입력
        company = input("\n🏢 회사명을 입력하세요: ").strip()
        if not company:
            print("❌ 회사명을 입력해주세요.")
            continue

        max_docs_input = input("📄 최대 문서 수 (기본값: 5): ").strip()
        max_docs = int(max_docs_input) if max_docs_input.isdigit() else 5

        # 날짜 입력 방식 선택
        print("\n📅 검색 기간 설정:")
        print("1. 최근 N일간 검색")
        print("2. 구체적인 날짜 범위 지정")

        date_choice = input("선택하세요 (1-2, 기본값: 1): ").strip()

        start_date = None
        end_date = None
        days = 365

        if date_choice == '2':
            start_input = input("📅 시작일 (YYYY-MM-DD): ").strip()
            end_input = input("📅 종료일 (YYYY-MM-DD): ").strip()

            if start_input and end_input:
                start_date = start_input
                end_date = end_input
                days = None
            else:
                print("❌ 날짜 형식이 잘못되었습니다. 기본값(최근 365일)을 사용합니다.")
        else:
            days_input = input("📅 최근 며칠간? (기본값: 365): ").strip()
            days = int(days_input) if days_input.isdigit() else 365

        # 검색 실행
        try:
            print("\n🚀 검색 시작...")
            result = system.search_and_fetch_documents(
                company,
                max_documents=max_docs,
                days=days,
                start_date=start_date,
                end_date=end_date
            )

            # 결과 출력
            system.print_summary(result)

            # JSON 저장 여부 확인
            save_choice = input(f"\n💾 결과를 JSON 파일로 저장하시겠습니까? (y/N): ").strip().lower()
            if save_choice == 'y':
                filename = system.save_results_to_json(result)
                if filename:
                    print(f"✅ {filename}에 저장 완료")

            # JSON 출력 여부 확인
            json_choice = input(f"\n📋 JSON 결과를 화면에 출력하시겠습니까? (y/N): ").strip().lower()
            if json_choice == 'y':
                print(f"\n📋 JSON 결과:")
                print("="*50)
                print(json.dumps(result, ensure_ascii=False, indent=2))

        except Exception as e:
            print(f"❌ 오류 발생: {e}")


if __name__ == "__main__":
    main()