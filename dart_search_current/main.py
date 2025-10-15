"""
DART 통합 시스템
회사명으로 검색 -> 문서 리스트 -> 문서 내용 -> JSON 출력
"""

import json
import requests
from datetime import datetime, timedelta
from dart_crawl import DartWebCrawler
from dart_doc_fetcher import DartDocumentFetcher


class DartIntegratedSystem:
    """DART 검색과 문서 내용 추출을 통합한 시스템"""

    def __init__(self):
        self.crawler = DartWebCrawler()

    def get_recent_and_fetch_documents(self, max_documents=5, mday_cnt=1, company_filter="", fetch_content=True, fetch_all=False):
        """
        최근 공시 목록을 가져오고 문서 내용까지 추출

        Args:
            max_documents (int): 최대 가져올 문서 수 (0=전체, 기본 5개)
            mday_cnt (int): 검색 기간 (1=당일, 2=2일, 3=3일, 7=7일, 30=30일)
            company_filter (str): 특정 회사명으로 필터링 (선택사항, 비어있으면 전체)
            fetch_content (bool): 문서 내용까지 가져올지 여부 (기본 True)
            fetch_all (bool): 전체 페이지를 다 가져올지 여부 (기본 False)

        Returns:
            dict: JSON 형식의 결과
        """
        print(f"🔍 최근 {mday_cnt}일간 공시 검색 및 문서 내용 추출 시작...")
        if company_filter:
            print(f"🏢 회사명 필터: {company_filter}")
        if fetch_all:
            print(f"📚 전체 공시를 가져옵니다 (모든 페이지)")

        result = {
            "search_type": "recent_disclosures",
            "search_date": datetime.now().isoformat(),
            "search_period_days": mday_cnt,
            "company_filter": company_filter,
            "fetch_all": fetch_all,
            "documents_found": 0,
            "documents_processed": 0,
            "documents": []
        }

        try:
            # 1. 최근 공시 검색
            print(f"📋 1단계: 최근 공시 목록 검색...")
            disclosures = self.crawler.get_recent_disclosures(
                mday_cnt=mday_cnt,
                page=1,
                max_results=100,
                company_name=company_filter,
                fetch_all=fetch_all  # 전체 페이지 가져오기 옵션
            )

            result["documents_found"] = len(disclosures)
            print(f"✅ {len(disclosures)}건의 공시 발견")

            if not disclosures:
                print("❌ 검색된 공시가 없습니다.")
                return result

            # 2. 최대 개수만큼 문서 처리
            if max_documents == 0:
                documents_to_process = disclosures  # 전체 처리
            else:
                documents_to_process = disclosures[:max_documents]

            print(f"📄 2단계: {len(documents_to_process)}개 문서 처리...")

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
            if result.get('search_type') == 'recent_disclosures':
                company_filter = result.get('company_filter', 'all')
                company_filter = company_filter.replace(' ', '_') if company_filter else 'all'
                filename = f"dart_recent_{company_filter}_{timestamp}.json"
            else:
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

        if result.get('search_type') == 'recent_disclosures':
            print(f"🔍 검색 유형: 최근 공시")
            if result.get('company_filter'):
                print(f"🏢 회사 필터: {result['company_filter']}")
            print(f"📅 검색 기간: 최근 {result['search_period_days']}일")
        else:
            print(f"🔍 검색어: {result.get('search_query', 'N/A')}")

        print(f"📅 검색일: {result['search_date'][:19]}")
        print(f"📋 발견된 문서: {result['documents_found']}건")
        print(f"📄 처리된 문서: {result['documents_processed']}건")

        if result.get('documents'):
            print(f"\n📝 문서 목록:")
            for doc in result['documents']:
                print(f"  {doc['index']}. {doc['basic_info']['report_name']}")
                print(f"     🏢 {doc['basic_info']['company']}")
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
        print("1. 최근 공시 목록 가져오기 (신규)")
        print("2. 종료")

        choice = input("\n선택하세요 (1-2): ").strip()

        if choice == '2':
            print("👋 종료합니다.")
            break

        if choice != '1':
            print("❌ 잘못된 선택입니다.")
            continue

        # 검색 파라미터 입력
        print("\n📅 검색 기간 선택:")
        print("1. 당일")
        print("2. 최근 2일")
        print("3. 최근 3일")
        print("7. 최근 7일")
        print("30. 최근 30일")

        mday_input = input("\n기간을 선택하세요 (기본값: 1): ").strip()
        mday_cnt = int(mday_input) if mday_input.isdigit() and int(mday_input) in [1, 2, 3, 7, 30] else 1

        # 회사명 필터링 (선택사항)
        company_filter = input("\n🏢 특정 회사명으로 필터링하시겠습니까? (엔터=전체): ").strip()

        # 전체 공시 가져오기 여부
        fetch_all_choice = input("\n📚 해당 기간의 공시를 전부 가져오시겠습니까? (y/N): ").strip().lower()
        fetch_all = (fetch_all_choice == 'y')

        if fetch_all:
            print("✅ 전체 공시를 가져옵니다 (문서 내용은 가져오지 않습니다)")
            max_docs = 0  # 전체 가져오기
            fetch_content = False  # 전체 가져올 때는 내용은 스킵
        else:
            max_docs_input = input("📄 최대 문서 수 (기본값: 5): ").strip()
            max_docs = int(max_docs_input) if max_docs_input.isdigit() else 5
            fetch_content = True

        # 검색 실행
        try:
            print("\n🚀 검색 시작...")
            result = system.get_recent_and_fetch_documents(
                max_documents=max_docs,
                mday_cnt=mday_cnt,
                company_filter=company_filter,
                fetch_content=fetch_content,
                fetch_all=fetch_all
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