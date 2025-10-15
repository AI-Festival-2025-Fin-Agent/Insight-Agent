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
        self.recent_url = "https://dart.fss.or.kr/dsac001/search.ax"  # 최근 공시 목록 URL

        # 헤더 설정 (웹브라우저처럼 보이게)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'Accept': 'text/html, */*; q=0.01',
            'Accept-Language': 'ko,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7,zh;q=0.6',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': 'https://dart.fss.or.kr/dsac001/mainAll.do',
        })

    def get_recent_disclosures(self, mday_cnt=1, page=1, max_results=50, company_name="", fetch_all=False):
        """
        최근 공시 전체 목록 가져오기 (https://dart.fss.or.kr/dsac001/mainAll.do)

        Args:
            mday_cnt (int): 검색 기간 (1=당일, 2=2일, 3=3일, 7=7일, 30=30일)
            page (int): 페이지 번호
            max_results (int): 페이지당 최대 결과 수
            company_name (str): 특정 회사명으로 필터링 (선택사항)
            fetch_all (bool): 전체 페이지를 다 가져올지 여부 (기본 False)

        Returns:
            list: 공시 목록
        """
        if fetch_all:
            return self.get_all_recent_disclosures(mday_cnt, company_name, max_results)

        print(f"🔍 최근 {mday_cnt}일간 공시 검색 중... (페이지 {page})")

        # POST 데이터 설정
        form_data = {
            'currentPage': str(page),
            'maxResults': str(max_results),
            'maxLinks': '10',
            'sort': '',
            'series': '',
            'pageGrouping': '',
            'mdayCnt': str(mday_cnt),
            'selectDate': '',
            'textCrpCik': company_name  # 회사명 필터링 (비어있으면 전체)
        }

        try:
            response = self.session.post(self.recent_url, data=form_data)
            response.raise_for_status()
            print(f"✅ 요청 성공: 상태 코드 {response.status_code}")

            return self.parse_recent_results(response.text)

        except Exception as e:
            print(f"❌ 요청 실패: {e}")
            return []

    def get_all_recent_disclosures(self, mday_cnt=1, company_name="", max_results=100):
        """
        최근 공시 전체를 모든 페이지에서 가져오기

        Args:
            mday_cnt (int): 검색 기간 (1=당일, 2=2일, 3=3일, 7=7일, 30=30일)
            company_name (str): 특정 회사명으로 필터링 (선택사항)
            max_results (int): 페이지당 최대 결과 수 (기본 100)

        Returns:
            list: 전체 공시 목록
        """
        print(f"🔍 최근 {mday_cnt}일간 공시 전체 가져오기 시작...")
        if company_name:
            print(f"🏢 회사명 필터: {company_name}")

        all_disclosures = []
        page = 1
        max_pages = 100  # 안전장치: 최대 100페이지까지만

        while page <= max_pages:
            print(f"\n📄 페이지 {page} 요청 중...")

            # POST 데이터 설정
            form_data = {
                'currentPage': str(page),
                'maxResults': str(max_results),
                'maxLinks': '10',
                'sort': '',
                'series': '',
                'pageGrouping': '',
                'mdayCnt': str(mday_cnt),
                'selectDate': '',
                'textCrpCik': company_name
            }

            try:
                response = self.session.post(self.recent_url, data=form_data)
                response.raise_for_status()

                disclosures = self.parse_recent_results(response.text)
                print(f"✅ 페이지 {page} 요청 성공: {len(disclosures)}건 발견")

                if not disclosures or len(disclosures) == 0:
                    print(f"✅ 페이지 {page}에서 공시가 없음. 종료합니다.")
                    break

                all_disclosures.extend(disclosures)
                print(f"✅ 페이지 {page}: {len(disclosures)}건 추가 (누적: {len(all_disclosures)}건)")

                # 결과가 max_results보다 적으면 마지막 페이지
                if len(disclosures) < max_results:
                    print(f"✅ 마지막 페이지 도달 (페이지 {page})")
                    break

                page += 1
                time.sleep(0.5)  # 서버 부하 방지

            except Exception as e:
                print(f"❌ 페이지 {page} 요청 실패: {e}")
                break

        print(f"\n🎉 전체 {len(all_disclosures)}건의 공시를 가져왔습니다!")
        return all_disclosures

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

    def parse_recent_results(self, html_content):
        """최근 공시 HTML 파싱하여 공시 목록 추출"""
        soup = BeautifulSoup(html_content, 'html.parser')
        disclosures = []

        # 테이블 찾기
        table = soup.find('table', class_='tbList')
        if not table:
            print("❌ 공시 목록 테이블을 찾을 수 없습니다.")
            return []

        # 데이터 행들 찾기
        tbody = table.find('tbody')
        if not tbody:
            print("❌ tbody를 찾을 수 없습니다.")
            return []

        rows = tbody.find_all('tr')
        print(f"📊 {len(rows)}개의 공시 발견")

        for row in rows:
            try:
                cols = row.find_all('td')
                if len(cols) < 6:  # 최근 공시는 6개 컬럼
                    print(f"⚠️ 컬럼 수 부족: {len(cols)}개 (최소 6개 필요)")
                    continue

                # 데이터 추출 (실제 순서: 시간, 회사명, 보고서명, 제출인, 접수일자, 시장구분)
                time_str = cols[0].get_text(strip=True)  # 시간
                company_cell = cols[1]  # 회사명
                report_cell = cols[2]  # 보고서명
                submitter = cols[3].get_text(strip=True)  # 제출인
                date = cols[4].get_text(strip=True)  # 접수일자
                market = cols[5].get_text(strip=True)  # 시장구분 (유/코/공)

                # 회사명 추출
                company_link = company_cell.find('a')
                company_name = company_link.get_text(strip=True) if company_link else company_cell.get_text(strip=True)

                # 보고서명과 링크 추출
                report_link = report_cell.find('a')
                rcept_no = ""
                if report_link:
                    report_name = report_link.get_text(strip=True)
                    report_url = report_link.get('href', '')

                    # onclick에서 rcpNo 추출
                    onclick = report_link.get('onclick', '')
                    if onclick:
                        # openDartMainAll('20251010800773') 형태에서 접수번호 추출
                        rcpno_match = re.search(r"'(\d{14})'", onclick)
                        if rcpno_match:
                            rcept_no = rcpno_match.group(1)

                    # href에서도 rcpNo 추출 시도
                    if not rcept_no and 'rcpNo=' in report_url:
                        rcpno_match = re.search(r'rcpNo=(\d+)', report_url)
                        if rcpno_match:
                            rcept_no = rcpno_match.group(1)
                else:
                    report_name = report_cell.get_text(strip=True)
                    report_url = ""

                # URL 생성
                if rcept_no and rcept_no.isdigit() and len(rcept_no) == 14:
                    full_url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"
                elif report_url and report_url.startswith('/'):
                    full_url = f"https://dart.fss.or.kr{report_url}"
                else:
                    full_url = report_url if report_url else ""

                # 정정공시인지 확인
                correction_keywords = ['[기재정정]', '[첨부정정]', '[첨부추가]', '[정정명령부과]', '[정정제출요구]', '정정', '풍문']
                is_correction = any(keyword in report_name for keyword in correction_keywords)

                disclosure = {
                    'number': rcept_no,
                    'company': company_name,
                    'report': report_name,
                    'submitter': submitter,
                    'date': date,
                    'time': time_str,
                    'market': market,
                    'rcept_no': rcept_no,
                    'url': full_url,
                    'is_correction': is_correction
                }

                disclosures.append(disclosure)
                time.sleep(0.1)

            except Exception as e:
                print(f"⚠️ 행 파싱 오류: {e}")
                continue

        return disclosures

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
                # if is_correction == 'false' or is_correction == False or is_correction == 'False':
                #     continue

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