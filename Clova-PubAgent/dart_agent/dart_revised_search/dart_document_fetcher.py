"""
DART 문서 내용 가져오기
링크가 주어졌을 때 실제 공시문서 내용을 추출하는 스크립트
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, parse_qs, urlparse


class DartDocumentFetcher:
    """DART 문서 내용 추출 도구"""

    def __init__(self):
        self.base_url = "https://dart.fss.or.kr"
        self.session = requests.Session()

        # 헤더 설정 (브라우저에서 확인한 헤더 사용)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Whale/4.33.325.17 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6',
            'sec-ch-ua': '"Chromium";v="138", "Whale";v="4", "Not.A/Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'upgrade-insecure-requests': '1'
        })

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: U100
        self.session.close()

    def extract_rcept_no(self, dart_url):
        """DART URL에서 접수번호 추출"""
        try:
            parsed_url = urlparse(dart_url)
            query_params = parse_qs(parsed_url.query)
            rcept_no = query_params.get('rcpNo', [None])[0]
            return rcept_no
        except Exception as e:
            print(f"❌ 접수번호 추출 실패: {e}")
            return None

    def extract_dcm_no(self, soup):
        """HTML에서 dcmNo 추출"""
        try:
            # iframe src에서 dcmNo 찾기
            iframes = soup.find_all('iframe')
            for iframe in iframes:
                src = iframe.get('src', '')
                if 'dcmNo=' in src:
                    try:
                        dcm_no = src.split('dcmNo=')[1].split('&')[0]
                        print(f"🔍 iframe에서 발견된 dcmNo: {dcm_no}")
                        return dcm_no
                    except:
                        print("⚠️ iframe에서 dcmNo 추출 실패")
                        pass

            # 스크립트에서 dcmNo 찾기 - 더 넓은 패턴으로 시도
            scripts = soup.find_all('script')
            for script in scripts:
                script_text = script.get_text()
                if 'dcmNo' in script_text:
                    import re
                    # 다양한 패턴으로 시도
                    patterns = [
                        r'viewDoc\([^,]+,\s*["\']?(\d{7,})["\']?',  # viewDoc 함수 호출에서 dcmNo 추출
                        r'linkDoc\([^,]+,\s*["\']?(\d{7,})["\']?',  # linkDoc 함수 호출에서 dcmNo 추출
                        r'dcmNo["\']?\s*[:=]\s*["\']?(\d+)',
                        r'"dcmNo"\s*:\s*"(\d+)"',
                        r"'dcmNo'\s*:\s*'(\d+)'",
                        r'dcmNo\s*=\s*"(\d+)"',
                        r'dcmNo\s*=\s*\'(\d+)\'',
                        r'dcmNo\s*=\s*(\d+)',
                        r'dcmNo":"(\d+)"',
                        r"dcmNo':'(\d+)'",
                        r"dcmNo\]\s*=\s*[\"'](\d+)[\"']",  # node1['dcmNo'] = "10835040"
                        r"dcmNo['\"]?\]\s*=\s*[\"'](\d+)[\"']"
                    ]

                    for pattern in patterns:
                        match = re.search(pattern, script_text)
                        if match:
                            dcm_no = match.group(1)
                            print(f"🔍 스크립트에서 발견된 dcmNo: {dcm_no} (패턴: {pattern})")
                            return dcm_no

            # URL 패턴에서 dcmNo 찾기
            links = soup.find_all('a')
            for link in links:
                href = link.get('href', '')
                if 'dcmNo=' in href:
                    try:
                        dcm_no = href.split('dcmNo=')[1].split('&')[0]
                        if dcm_no and dcm_no.isdigit():
                            print(f"🔍 링크에서 발견된 dcmNo: {dcm_no}")
                            return dcm_no
                    except:
                        pass

            # 모든 텍스트에서 dcmNo 패턴 찾기
            all_text = soup.get_text()
            if 'dcmNo' in all_text:
                import re
                match = re.search(r'dcmNo["\']?\s*[:=]\s*["\']?(\d+)', all_text)
                if match:
                    dcm_no = match.group(1)
                    print(f"🔍 전체 텍스트에서 발견된 dcmNo: {dcm_no}")
                    return dcm_no

            # 기본값 사용
            dcm_no = ""
            print(f"🔍 dcmNo를 찾을 수 없어 빈 값 사용")
            return dcm_no

        except Exception as e:
            print(f"⚠️ dcmNo 추출 중 오류: {e}")
            return ""

    def get_document_content(self, dart_url):
        """DART 링크에서 문서 내용 가져오기"""
        print(f"🔍 문서 내용 가져오는 중...")
        print(f"🔗 URL: {dart_url}")

        rcept_no = self.extract_rcept_no(dart_url)
        if not rcept_no:
            print("❌ 접수번호를 찾을 수 없습니다.")
            return None

        print(f"📋 접수번호: {rcept_no}")

        try:
            # 1. 메인 페이지 접근하여 기본 정보 추출
            print(f"🔍 메인 페이지 접근: {dart_url}")
            response = self.session.get(dart_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 2. 문서 정보 추출
            document_info = self.extract_document_info(soup)

            # 3. 메인 페이지에서 dcmNo 찾기
            dcm_no = self.extract_dcm_no(soup)

            # 4. HTML 형식 우선 시도 (인코딩 문제 해결을 위해)
            print(f"🎯 HTML 형식으로 우선 시도...")
            viewer_url = f"https://dart.fss.or.kr/report/viewer.do?rcpNo={rcept_no}&dcmNo={dcm_no}&eleId=1&offset=0&length=0&dtd=HTML"
            content = self.fetch_document_text(viewer_url, referer=dart_url)

            # HTML 형식 실패 시 다른 방법들 시도
            if not content or len(content.strip()) == 0:
                print(f"🔄 HTML 형식 실패, XML 형식들 시도...")

                # 1. 기본 XML 형식
                viewer_url_2 = f"https://dart.fss.or.kr/report/viewer.do?rcpNo={rcept_no}&dcmNo={dcm_no}&eleId=1&offset=0&length=0&dtd=dart4.xsd"
                print(f"🎯 XML 형식 시도: {viewer_url_2}")
                content = self.fetch_document_text(viewer_url_2, referer=dart_url)

                # 2. eleId=0으로 시도
                if not content or len(content.strip()) == 0:
                    viewer_url_3 = f"https://dart.fss.or.kr/report/viewer.do?rcpNo={rcept_no}&dcmNo={dcm_no}&eleId=0&offset=0&length=0&dtd=dart4.xsd"
                    print(f"🎯 eleId=0으로 시도: {viewer_url_3}")
                    content = self.fetch_document_text(viewer_url_3, referer=dart_url)

                # 3. dcmNo 없이 시도
                if not content or len(content.strip()) == 0:
                    viewer_url_4 = f"https://dart.fss.or.kr/report/viewer.do?rcpNo={rcept_no}&eleId=1&offset=0&length=0&dtd=HTML"
                    print(f"🎯 dcmNo 없이 HTML 시도: {viewer_url_4}")
                    content = self.fetch_document_text(viewer_url_4, referer=dart_url)

            document_info['content'] = content

            return document_info

        except Exception as e:
            print(f"❌ 문서 가져오기 실패: {e}")
            return None

    def extract_document_info(self, soup):
        """문서 기본 정보 추출"""
        info = {
            'title': '',
            'company': '',
            'submitter': '',
            'submit_date': '',
            'content': ''
        }

        try:
            # 제목 추출
            title_elem = soup.find('title')
            if title_elem:
                info['title'] = title_elem.get_text(strip=True)

            # 테이블에서 정보 추출
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)

                        if '회사명' in key or '공시대상회사' in key:
                            info['company'] = value
                        elif '제출인' in key:
                            info['submitter'] = value
                        elif '접수일자' in key or '제출일자' in key:
                            info['submit_date'] = value

        except Exception as e:
            print(f"⚠️ 문서 정보 추출 중 오류: {e}")

        return info

    def find_content_url(self, soup, rcept_no):
        """본문 링크 찾기 - iframe src에서 추출"""
        try:
            # iframe 찾기
            iframe = soup.find('iframe', {'id': 'ifrm'})
            if iframe:
                src = iframe.get('src', '')
                if src:
                    full_url = urljoin(self.base_url, src)
                    print(f"🎯 iframe에서 발견된 문서 URL: {full_url}")
                    return full_url

            # iframe이 없다면 다른 iframe 찾기
            iframes = soup.find_all('iframe')
            for iframe in iframes:
                src = iframe.get('src', '')
                if 'viewer.do' in src or 'report' in src:
                    full_url = urljoin(self.base_url, src)
                    print(f"🎯 iframe에서 발견된 문서 URL: {full_url}")
                    return full_url

            # 본문 버튼이나 링크 찾기
            links = soup.find_all('a')
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)

                # 본문 관련 링크 패턴
                if any(keyword in text for keyword in ['본문', '전체', '내용보기', '문서보기']):
                    if href:
                        full_url = urljoin(self.base_url, href)
                        print(f"🔍 발견된 본문 링크: {full_url}")
                        return full_url

            # 기본 패턴으로 URL 생성
            content_url = f"{self.base_url}/report/viewer.do?rcpNo={rcept_no}"
            print(f"🔍 기본 URL 사용: {content_url}")
            return content_url

        except Exception as e:
            print(f"⚠️ 본문 링크 찾기 실패: {e}")
            return None

    def fetch_document_text(self, content_url, referer=None):
        """실제 문서 텍스트 가져오기"""
        try:
            print(f"📄 본문 가져오는 중: {content_url}")

            # Referer 헤더 설정
            headers = {}
            if referer:
                headers = {
                    'Referer': referer,
                    'sec-fetch-dest': 'iframe'
                }

            response = self.session.get(content_url, headers=headers)
            response.raise_for_status()

            print(f"🔍 페이지 로드 완료")
            print(f"🔍 응답 길이: {len(response.content)} 문자")

            # XML 경고 방지
            import warnings
            from bs4 import XMLParsedAsHTMLWarning
            warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

            # 인코딩 문제 해결 시도 - DART 특수 처리
            html_content = None

            # DART 응답이 XML인 경우 특별 처리
            content_type = response.headers.get('content-type', '').lower()
            print(f"🔍 Content-Type: {content_type}")

            # 1. 인코딩 자동 감지 시도 (더 정확한 한글 감지)
            try:
                import chardet
                detected = chardet.detect(response.content)
                detected_encoding = detected.get('encoding')
                confidence = detected.get('confidence', 0)

                # 한글 컨텐츠에 대해 EUC-KR 우선 처리
                if detected_encoding and confidence > 0.3:  # 신뢰도 더 낮춤
                    # EUC-KR 계열 인코딩이 감지되면 우선 시도
                    if detected_encoding.lower() in ['euc-kr', 'cp949', 'ks_c_5601-1987']:
                        try:
                            html_content = response.content.decode('euc-kr')
                            print(f"🔍 EUC-KR 우선 디코딩 성공")
                        except:
                            html_content = response.content.decode(detected_encoding)
                            print(f"🔍 자동 감지된 인코딩 {detected_encoding} 사용 (신뢰도: {confidence:.2f})")
                    else:
                        html_content = response.content.decode(detected_encoding)
                        print(f"🔍 자동 감지된 인코딩 {detected_encoding} 사용 (신뢰도: {confidence:.2f})")
                else:
                    print(f"⚠️ 자동 감지 실패 또는 낮은 신뢰도: {detected_encoding} ({confidence:.2f})")
            except ImportError:
                print("⚠️ chardet 라이브러리 없음, 수동 인코딩 시도")
            except Exception as e:
                print(f"⚠️ 인코딩 자동 감지 실패: {e}")

            # 2. 응답 헤더에서 인코딩 확인
            if html_content is None:
                if 'charset=' in content_type:
                    charset = content_type.split('charset=')[1].split(';')[0].strip()
                    try:
                        html_content = response.content.decode(charset)
                        print(f"🔍 헤더에서 감지된 인코딩 {charset} 사용")
                    except:
                        print(f"⚠️ 헤더 인코딩 {charset} 실패")

            # 3. 수동 인코딩 시도 (DART용 우선순위 최적화)
            if html_content is None:
                # DART는 주로 EUC-KR을 사용하므로 우선순위 조정
                encodings = ['euc-kr', 'cp949', 'utf-8', 'iso-8859-1', 'utf-8-sig']

                for encoding in encodings:
                    try:
                        test_content = response.content.decode(encoding)

                        # 한글 유니코드 범위 확인 (가-힣, ㄱ-ㅎ, ㅏ-ㅣ)
                        import re
                        korean_pattern = re.compile(r'[가-힣ㄱ-ㅎㅏ-ㅣ]')

                        if korean_pattern.search(test_content):
                            html_content = test_content
                            print(f"🔍 {encoding} 디코딩 성공 - 한글 확인됨")
                            break
                        else:
                            print(f"⚠️ {encoding}으로 디코딩했지만 한글 없음")

                    except UnicodeDecodeError:
                        print(f"⚠️ {encoding} 디코딩 실패")
                        continue

            # 4. 최후의 수단
            if html_content is None:
                html_content = response.content.decode('utf-8', errors='ignore')
                print(f"🔍 UTF-8 디코딩 (에러 무시)")

            # 5. DART XML 특수 처리 - 이미 변환된 한글 복원 시도
            if '?' in html_content and '엫' in html_content:
                print("⚠️ 한글 인코딩 문제 감지, 복원 시도...")
                try:
                    # 잘못 인코딩된 한글을 올바르게 복원
                    html_content_bytes = html_content.encode('iso-8859-1')
                    html_content = html_content_bytes.decode('euc-kr')
                    print("🔍 한글 인코딩 복원 성공")
                except:
                    try:
                        html_content_bytes = html_content.encode('cp1252')
                        html_content = html_content_bytes.decode('euc-kr')
                        print("🔍 한글 인코딩 복원 성공 (cp1252->euc-kr)")
                    except:
                        print("⚠️ 한글 인코딩 복원 실패")

            soup = BeautifulSoup(html_content, 'html.parser')

            # 응답 내용 일부 출력 (디버깅용)
            print(f"🔍 HTML 첫 500자: {html_content[:500]}...")

            # 스크립트, 스타일 태그 제거
            for tag in soup(['script', 'style', 'meta', 'link']):
                tag.decompose()

            # 텍스트 추출 및 정리
            text = soup.get_text()

            # 공백 정리
            lines = [line.strip() for line in text.splitlines()]
            lines = [line for line in lines if line]

            cleaned_text = '\n'.join(lines)

            print(f"🔍 추출된 텍스트 길이: {len(cleaned_text)} 문자")

            return cleaned_text

        except Exception as e:
            print(f"❌ 본문 가져오기 실패: {e}")
            return "본문을 가져올 수 없습니다."

    def print_document(self, doc_info):
        """문서 내용 출력"""
        if not doc_info:
            print("❌ 문서 정보가 없습니다.")
            return

        print("\n" + "="*80)
        print("📄 DART 문서 내용")
        print("="*80)

        print(f"📋 제목: {doc_info.get('title', 'N/A')}")
        print(f"🏢 회사: {doc_info.get('company', 'N/A')}")
        print(f"👤 제출인: {doc_info.get('submitter', 'N/A')}")
        print(f"📅 제출일: {doc_info.get('submit_date', 'N/A')}")

        print("\n" + "-"*80)
        print("📄 문서 내용:")
        print("-"*80)
        print(doc_info.get('content', '내용 없음'))
        print("="*80)


# 테스트 함수
def test_document_fetcher():
    """문서 가져오기 테스트"""
    # 테스트용 DART 링크들 (실제 존재하는 링크)
    test_urls = [
        "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20251001800663",  # LG화학 정정공시
        "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20250828800490",  # LG화학 정정공시
    ]

    with DartDocumentFetcher() as fetcher:
        for i, url in enumerate(test_urls, 1):
            print(f"\n🧪 테스트 {i}: {url}")
            doc_info = fetcher.get_document_content(url)
            fetcher.print_document(doc_info)
            print("\n" + "="*100)


if __name__ == "__main__":
    print("🎯 DART 문서 내용 가져오기 도구")
    print("=" * 40)

    while True:
        print("\n📋 옵션 선택:")
        print("1. DART 링크로 문서 가져오기")
        print("2. 테스트 실행")
        print("3. 종료")

        choice = input("\n선택하세요 (1-3): ").strip()

        if choice == '1':
            url = input("\n🔗 DART URL을 입력하세요: ").strip()
            if url:
                with DartDocumentFetcher() as fetcher:
                    doc_info = fetcher.get_document_content(url)
                    fetcher.print_document(doc_info)

        elif choice == '2':
            test_document_fetcher()

        elif choice == '3':
            print("👋 종료합니다.")
            break

        else:
            print("❌ 잘못된 선택입니다.")