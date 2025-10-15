"""
DART 웹사이트 크롤링으로 정정공시 찾기
https://dart.fss.or.kr/dsab001/searchCorp.ax 를 이용한 데이터 수집
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import time

class DartWebCrawler:
    """DART 웹사이트 크롤링 도구"""

    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://dart.fss.or.kr"
        self.search_url = "https://dart.fss.or.kr/dsab001/searchCorp.ax"

        # 헤더 설정 (웹브라우저처럼 보이게)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Whale/4.33.325.17 Safari/537.36',
            'Accept': 'text/html, */*; q=0.01',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': 'https://dart.fss.or.kr/dsab001/search.ax',
        })

    def search_company_disclosures(self, company_name, start_date=None, end_date=None, days=365):
        """회사명으로 공시 검색"""

        # 날짜 설정
        if end_date is None:
            end_date = datetime.now()
        elif isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        if start_date is None:
            start_date = end_date - timedelta(days=days)
        elif isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')

        print(f"🔍 '{company_name}' 공시 검색 중...")
        print(f"📅 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

        # POST 데이터 설정 (실제 DART 사이트 파라미터)
        form_data = {
            'currentPage': '1',
            'maxResults': '50',
            'maxLinks': '10',
            'sort': 'date',
            'series': 'desc',
            'textCrpNm': company_name,  # 회사명
            'startDate': start_date.strftime('%Y%m%d'),  # YYYYMMDD 형식
            'endDate': end_date.strftime('%Y%m%d'),      # YYYYMMDD 형식
            'pageGubun': 'corp',
            'decadeType': 'finalReport',
            'recent': '',
            'attachDocNm': ''
        }

        try:
            response = self.session.post(self.search_url, data=form_data)
            response.raise_for_status()
            # response 결과
            print(f"✅ 요청 성공: 상태 코드 {response.status_code}")

            return self.parse_search_results(response.text)

        except Exception as e:
            print(f"❌ 요청 실패: {e}")
            return []

    def parse_search_results(self, html_content):
        """HTML 파싱하여 공시 목록 추출"""
        soup = BeautifulSoup(html_content, 'html.parser')

        disclosures = []

        # 테이블 찾기
        table = soup.find('table', class_='tbList')
        if not table:
            print("❌ 공시 목록 테이블을 찾을 수 없습니다.")
            return []

        # 데이터 행들 찾기
        rows = table.find('tbody').find_all('tr')

        for row in rows:            
            try:
                cols = row.find_all('td')
                if len(cols) < 5:
                    continue

                # 데이터 추출
                number = cols[0].get_text(strip=True)
                company_cell = cols[1]
                report_cell = cols[2]
                submitter = cols[3].get_text(strip=True)
                date = cols[4].get_text(strip=True)

                # 회사명 추출
                company_link = company_cell.find('a')
                company_name = company_link.get_text(strip=True) if company_link else ""

                # 보고서명과 링크 추출
                report_link = report_cell.find('a')
                if report_link:
                    report_name = report_link.get_text(strip=True)
                    report_url = report_link.get('href', '')

                    # rcpNo 추출
                    rcept_no_match = re.search(r'rcpNo=(\d+)', report_url)
                    rcept_no = rcept_no_match.group(1) if rcept_no_match else ""
                else:
                    report_name = report_cell.get_text(strip=True)
                    report_url = ""
                    rcept_no = ""

                # 정정공시인지 확인
                correction_keywords = ['[기재정정]', '[첨부정정]', '[첨부추가]', '[정정명령부과]', '[정정제출요구]', '정정', '풍문']
                is_correction = any(keyword in report_name for keyword in correction_keywords)
                
                time.sleep(0.2)
                if is_correction == 'false' or is_correction == False or is_correction == 'False':
                    continue

                disclosure = {
                    'number': number,
                    'company': company_name,
                    'report': report_name,
                    'submitter': submitter,
                    'date': date,
                    'rcept_no': rcept_no,
                    'url': f"https://dart.fss.or.kr{report_url}" if report_url else "",
                    'is_correction': is_correction
                }

                disclosures.append(disclosure)

            except Exception as e:
                print(f"⚠️ 행 파싱 오류: {e}")
                continue

        return disclosures

    def find_corrections(self, company_name, start_date=None, end_date=None, days=365):
        """정정공시만 필터링해서 반환"""
        all_disclosures = self.search_company_disclosures(company_name, start_date, end_date, days)

        corrections = [d for d in all_disclosures if d['is_correction']]

        print(f"📊 전체 공시: {len(all_disclosures)}건")
        print(f"🔧 정정공시: {len(corrections)}건")

        return corrections

    def print_results(self, corrections):
        """결과 출력"""
        print(f"\n✅ {len(corrections)}건의 정정공시 발견!")
        print("=" * 80)

        if not corrections:
            print("정정공시가 없습니다.")
            return

        for i, item in enumerate(corrections, 1):
            print(f"{i}. 📋 {item['company']}")
            print(f"   보고서: {item['report']}")
            print(f"   제출인: {item['submitter']}")
            print(f"   날짜: {item['date']}")
            if item['url']:
                print(f"   🔗 링크: {item['url']}")
            print("-" * 80)


if __name__ == "__main__":
    crawler = DartWebCrawler()

    print("🎯 DART 웹 크롤링 정정공시 찾기")
    print("=" * 35)

    while True:
        company = input("\n🏢 회사명을 입력하세요 (종료: q): ").strip()

        if company.lower() == 'q':
            print("👋 종료합니다.")
            break

        if not company:
            print("❌ 회사명을 입력해주세요.")
            continue

        # 날짜 입력 (선택사항)
        print("\n📅 검색 기간 설정 (선택사항):")
        start_input = input("시작일 (YYYY-MM-DD 또는 엔터로 기본값): ").strip()
        end_input = input("종료일 (YYYY-MM-DD 또는 엔터로 오늘): ").strip()

        start_date = start_input if start_input else None
        end_date = end_input if end_input else None

        if not start_date and not end_date:
            days_input = input("최근 며칠간 검색? (기본값: 365일): ").strip()
            days = int(days_input) if days_input.isdigit() else 365
        else:
            days = 365

        # 검색 실행
        try:
            corrections = crawler.find_corrections(company, start_date, end_date, days)
            crawler.print_results(corrections)
        except ValueError as e:
            print(f"❌ 날짜 형식 오류: {e}")
            print("올바른 형식: YYYY-MM-DD (예: 2025-01-01)")