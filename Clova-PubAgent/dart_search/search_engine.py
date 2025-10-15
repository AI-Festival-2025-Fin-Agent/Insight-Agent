#!/usr/bin/env python3
"""
DART 공시 검색 엔진 - 핵심 로직
"""

import os
import json
from typing import Dict, Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_naver import ChatClovaX
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from difflib import SequenceMatcher
from dotenv import load_dotenv
from postprocess_regular import DartRegularPostprocessor

# .env 파일 로드
load_dotenv()

# 설정 (하드코딩)
BASE_DATA_PATH = "/home/sese/Insight-Agent/Clova-PubAgent/dart_api_data"


class DartSearchEngine:
    def __init__(self):
        # Clova HCX-007 for query parsing
        self.query_parser_llm = ChatClovaX(
            model="HCX-007",
            temperature=0.1
        )

        # Google Gemini for summary generation
        self.summary_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            temperature=0.1,
            convert_system_message_to_human=True
        )
        
        self.postprocessor = DartRegularPostprocessor()

    def extract_info_from_query(self, query: str) -> Optional[Dict]:
        """사용자 질문에서 회사명, 연도, 분기 추출"""
        parser = JsonOutputParser()

        prompt = ChatPromptTemplate.from_template(
            """당신은 정보 추출 어시스턴트입니다.
            사용자의 질문에서 'company_name', 'year', 'quarter' 정보를 추출하는 것이 당신의 임무입니다.
            - 반드시 JSON 객체 형식으로만 답변해야 합니다.
            - JSON 객체는 반드시 'company_name', 'year', 'quarter' 키를 포함해야 합니다.
            - 연도가 명시되지 않은 경우, 현재 연도인 2025년을 사용하세요.
            - 분기가 명시되지 않은 경우, 가장 최신 분기인 2025년 2분기를 사용하세요.
            - 분기는 반드시 1, 2, 3, 4 중 하나의 숫자여야 합니다.
            - 어떤 설명도 추가하지 말고, JSON 객체만 반환하세요.

            # 회사명 정규화 규칙 (줄임말을 정식명칭으로 변환)
            - "lg엔솔", "엘지엔솔", "lg 엔솔" → "LG에너지솔루션"
            - "카카오뱅크" → "카카오뱅크"
            - "kakao" → "카카오"
            - "삼전" → "삼성전자" (만약 삼성전자를 의미하는 경우)
            - "현대차" → "현대자동차"
            - "sk하이닉스", "sk 하이닉스" → "SK하이닉스"
            - "네이버" → "NAVER"
            - 기타 줄임말이나 영문명이 나올 경우 가장 일반적인 한국 정식 회사명으로 변환

            # 예시
            - 사용자 질문: "삼성전자 작년 1분기 실적 알려줘"
            - JSON: {{"company_name": "삼성전자", "year": 2024, "quarter": 1}}
            - 사용자 질문: "카카오 실적"
            - JSON: {{"company_name": "카카오", "year": 2025, "quarter": 1}}
            - 사용자 질문: "lg엔솔 최근 실적"
            - JSON: {{"company_name": "LG에너지솔루션", "year": 2025, "quarter": 1}}

            사용자 질문: {query}
            {format_instructions}
            """
        )

        chain = prompt | self.query_parser_llm | parser

        try:
            info = chain.invoke({
                "query": query,
                "format_instructions": parser.get_format_instructions()
            })
            return info
        except Exception as e:
            print(f"정보 추출 중 오류 발생: {e}")
            return None

    def find_similar_company_names(self, target_name: str, file_list: List[str]) -> List[str]:
        """파일 리스트에서 유사한 회사명 찾기"""
        candidates = []

        for filename in file_list:
            if filename.endswith('.json'):
                # 파일명에서 회사명 부분 추출 (예: "000010_신한은행.json" -> "신한은행")
                try:
                    if '_' in filename:
                        company_part = filename.split('_', 1)[1].replace('.json', '')
                        similarity = SequenceMatcher(None, target_name, company_part).ratio()
                        if similarity > 0.5:  # 50% 이상 유사도
                            candidates.append((filename, company_part, similarity))
                except:
                    continue

        # 유사도 순으로 정렬
        candidates.sort(key=lambda x: x[2], reverse=True)
        return candidates[:5]  # 상위 5개만 반환

    def find_and_load_disclosure(self, info: Dict) -> Optional[Dict]:
        """추출된 정보로 공시 파일 검색 및 로드"""
        company_name = info.get("company_name")
        year = info.get("year")
        quarter = info.get("quarter")

        if not all([company_name, year, quarter]):
            print("파일 검색에 필요한 정보가 부족합니다.")
            return None

        target_path = os.path.join(BASE_DATA_PATH, str(year), f"Q{quarter}", "companies")

        if not os.path.exists(target_path):
            print(f"경로를 찾을 수 없습니다: {target_path}")
            return None

        try:
            file_list = os.listdir(target_path)

            exact_match = None
            partial_matches = []

            for filename in file_list:
                if filename.endswith('.json') and '_' in filename:
                    if "카카오" in filename:
                        print(filename)
                    try:
                        file_company_name = filename.split('_', 1)[1].replace('.json', '')
                        # 정확히 일치하는 경우
                        if company_name == file_company_name:
                            exact_match = filename
                            break
                        # 부분 매칭 후보 저장 (바로 return하지 않음)
                        elif company_name in file_company_name or file_company_name in company_name:
                            partial_matches.append((filename, file_company_name))
                    except:
                        continue

            # 정확 매칭 우선
            if exact_match:
                file_path = os.path.join(target_path, exact_match)
                print(f"파일을 찾았습니다: {exact_match}")
                result = self.postprocessor.process_file(file_path)
                return result

            # 부분 매칭이 여러 개 있으면 가장 짧은 이름 선택 (예: 카카오 vs 카카오뱅크 → 카카오 선택)
            if partial_matches:
                partial_matches.sort(key=lambda x: len(x[1]))  # 이름 길이 기준 정렬
                best_match = partial_matches[0][0]
                file_path = os.path.join(target_path, best_match)
                print(f"부분 매칭 파일을 사용합니다: {best_match}")
                result = self.postprocessor.process_file(file_path)
                return result

            # 유사도 검색
            similar_companies = self.find_similar_company_names(company_name, file_list)
            if similar_companies:
                print(f"정확한 매칭을 찾지 못했습니다. 유사한 회사들:")
                for filename, company_part, similarity in similar_companies:
                    print(f"  - {company_part} (유사도: {similarity:.2f})")

                best_match = similar_companies[0][0]
                file_path = os.path.join(target_path, best_match)
                print(f"가장 유사한 파일을 사용합니다: {best_match}")
                result = self.postprocessor.process_file(file_path)
                return result

            print(f"'{company_name}'와 유사한 회사를 찾지 못했습니다.")
            return None

        except Exception as e:
            print(f"파일 검색 중 오류 발생: {e}")
            return None


    def generate_summary(self, data: Dict, query: str) -> str:
        """공시 데이터 요약 생성"""
        context = json.dumps(data, indent=2, ensure_ascii=False)
        try:
            new_context = f"""# 메타데이터: {data.get("metadata", {})}\n\n\n# 데이터"""
            for api_data in data.get("api_data", {}).values():
                new_context += f"\n\n{api_data}"

            context = new_context
        except Exception as e:
            print(f"{type(data)} 컨텍스트 변환 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            print(type(data))

        prompt_template = ChatPromptTemplate.from_template(
            """
            당신은 DART 전자공시를 전문적으로 요약하는 AI 애널리스트입니다.
            제공된 JSON 공시 데이터와 사용자의 질문을 바탕으로 보고서를 생성해주세요.

            --- [CONTEXT] ---
            {context}
            --- [END CONTEXT] ---

            --- [QUERY] ---
            {query}
            --- [END QUERY] ---

            --- [출력 형식] ---
            ## {company_name} {year}년 {quarter}분기 보고서 요약

            **핵심 요약**
            [CONTEXT를 분석하여 3-5줄 이내의 핵심 요약을 작성하세요]

            **주요 지표**
            - 📈 **매출액**: [금액] (전년 동기 대비 증감률)
            - 💰 **영업이익**: [금액] (전년 동기 대비 증감률)
            - 👥 **직원 수**: [인원]
            - 💼 **주요 투자**: [주요 투자 내역]

            **특이사항**
            - [중요한 계약, 투자, 리스크 요인 등]

            **투자 의견**
            - 🟢 긍정적 / 🔴 부정적 / ⚫ 중립적
            - [간단한 근거]

            ---
            **키워드**: #매출증가 #신규투자 등 관련 태그
            """
        )

        chain = prompt_template | self.summary_llm | StrOutputParser()

        # 메타데이터에서 정보 추출
        corp_name = data.get("metadata", {}).get("corp_name", "알 수 없음")
        year_quarter = data.get("metadata", {}).get("year_quarter", "알 수 없음").split('_')
        year = year_quarter[0] if len(year_quarter) > 0 else "알 수 없음"
        quarter = year_quarter[1].replace('Q', '') if len(year_quarter) > 1 else "알 수 없음"

        try:
            response = chain.invoke({
                "context": context,
                "query": query,
                "company_name": corp_name,
                "year": year,
                "quarter": quarter
            })
            return response
        except Exception as e:
            return f"요약 생성 중 오류가 발생했습니다: {e}"

    def search_only(self, query: str) -> Dict:
        """공시문서 검색만 수행 (요약 제외)"""
        print("[SEARCH_ENGINE] 검색 시작")

        # 1. 정보 추출
        print("[SEARCH_ENGINE] 1단계: 질문에서 정보 추출 중...")
        info = self.extract_info_from_query(query)
        if not info:
            print("[SEARCH_ENGINE] 에러: 정보 추출 실패")
            return {"error": "질문에서 정보를 추출할 수 없습니다."}

        print(f"[SEARCH_ENGINE] 정보 추출 완료: {info}")

        # 2. 파일 검색 및 로드
        print("[SEARCH_ENGINE] 2단계: 공시 파일 검색 및 로드 중...")
        data = self.find_and_load_disclosure(info)
        
        if not data:
            print(f"[SEARCH_ENGINE] 에러: 파일을 찾을 수 없음 - {info.get('company_name')}")
            return {"error": f"해당 회사({info.get('company_name')})의 공시 데이터를 찾을 수 없습니다."}

        print("[SEARCH_ENGINE] 파일 로드 완료")

        result = {
            "extracted_info": info,
            "company_name": data.get("metadata", {}).get("corp_name"),
            "success": True,
            "raw_data": data
        }

        return result

    def search_and_summarize(self, query: str) -> Dict:
        """전체 검색 및 요약 프로세스"""
        print("[SEARCH_ENGINE] 검색 및 요약 시작")

        # 1. 정보 추출
        print("[SEARCH_ENGINE] 1단계: 질문에서 정보 추출 중...")
        info = self.extract_info_from_query(query)
        if not info:
            print("[SEARCH_ENGINE] 에러: 정보 추출 실패")
            return {"error": "질문에서 정보를 추출할 수 없습니다."}

        print(f"[SEARCH_ENGINE] 정보 추출 완료: {info}")

        # 2. 파일 검색 및 로드
        print("[SEARCH_ENGINE] 2단계: 공시 파일 검색 및 로드 중...")
        data = self.find_and_load_disclosure(info)
        if not data:
            print(f"[SEARCH_ENGINE] 에러: 파일을 찾을 수 없음 - {info.get('company_name')}")
            return {"error": f"해당 회사({info.get('company_name')})의 공시 데이터를 찾을 수 없습니다."}

        print("[SEARCH_ENGINE] 파일 로드 완료")

        # 3. 요약 생성
        print("[SEARCH_ENGINE] 3단계: AI 요약 생성 중...")
        summary = self.generate_summary(data, query)
        print("[SEARCH_ENGINE] 요약 생성 완료")

        result = {
            "summary": summary,
            "extracted_info": info,
            "company_name": data.get("metadata", {}).get("corp_name"),
            "success": True,
            "raw_data": data  # 항상 원본 데이터 포함
        }

        return result

    def get_company_quarterly_reports(self, company_name: str) -> Dict:
        """회사명으로 사용 가능한 분기 보고서 목록 조회"""
        print(f"[SEARCH_ENGINE] {company_name}의 분기 보고서 목록 조회 시작")

        available_reports = []

        # 2024, 2025년의 모든 분기 검색
        for year in [2024, 2025]:
            for quarter in [1, 2, 3, 4]:
                target_path = os.path.join(BASE_DATA_PATH, str(year), f"Q{quarter}", "companies")

                if not os.path.exists(target_path):
                    continue

                try:
                    file_list = os.listdir(target_path)

                    for filename in file_list:
                        if filename.endswith('.json') and '_' in filename:
                            try:
                                file_company_name = filename.split('_', 1)[1].replace('.json', '')

                                # 정확 매칭 또는 부분 매칭
                                if (company_name == file_company_name or
                                    company_name in file_company_name or
                                    file_company_name in company_name):

                                    # 파일이 실제로 존재하는지 확인
                                    file_path = os.path.join(target_path, filename)
                                    if os.path.exists(file_path):
                                        available_reports.append({
                                            "year": year,
                                            "quarter": quarter,
                                            "company_name": file_company_name,
                                            "filename": filename,
                                            "file_path": file_path
                                        })
                                        break  # 같은 분기에서 첫 번째 매칭만 취함
                            except:
                                continue

                except Exception as e:
                    print(f"경로 {target_path} 검색 중 오류: {e}")
                    continue

        if not available_reports:
            return {"error": f"'{company_name}'에 해당하는 분기 보고서를 찾을 수 없습니다."}

        # 연도, 분기 순으로 정렬 (최신순)
        available_reports.sort(key=lambda x: (x["year"], x["quarter"]), reverse=True)

        return {
            "company_name": company_name,
            "available_reports": available_reports,
            "total_count": len(available_reports),
            "success": True
        }

    def get_company_data(self, company_name: str, year: int, quarter: int) -> Dict:
        """회사명, 연도, 분기로 직접 원본 데이터 조회"""
        print(f"[SEARCH_ENGINE] {company_name} {year}년 {quarter}분기 데이터 조회 시작")

        target_path = os.path.join(BASE_DATA_PATH, str(year), f"Q{quarter}", "companies")

        if not os.path.exists(target_path):
            return {"error": f"{year}년 {quarter}분기 데이터 경로를 찾을 수 없습니다."}

        try:
            file_list = os.listdir(target_path)

            exact_match = None
            partial_matches = []

            for filename in file_list:
                if filename.endswith('.json') and '_' in filename:
                    try:
                        file_company_name = filename.split('_', 1)[1].replace('.json', '')

                        # 정확히 일치하는 경우
                        if company_name == file_company_name:
                            exact_match = filename
                            break
                        # 부분 매칭 후보 저장
                        elif company_name in file_company_name or file_company_name in company_name:
                            partial_matches.append((filename, file_company_name))
                    except:
                        continue

            # 정확 매칭 우선
            if exact_match:
                file_path = os.path.join(target_path, exact_match)
                print(f"파일을 찾았습니다: {exact_match}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        "company_name": data.get("metadata", {}).get("corp_name"),
                        "year": year,
                        "quarter": quarter,
                        "raw_data": data,
                        "success": True
                    }

            # 부분 매칭이 있으면 사용
            if partial_matches:
                partial_matches.sort(key=lambda x: len(x[1]))  # 이름 길이 기준 정렬
                best_match = partial_matches[0][0]
                file_path = os.path.join(target_path, best_match)
                print(f"부분 매칭 파일을 사용합니다: {best_match}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        "company_name": data.get("metadata", {}).get("corp_name"),
                        "year": year,
                        "quarter": quarter,
                        "raw_data": data,
                        "success": True
                    }

            return {"error": f"'{company_name}'의 {year}년 {quarter}분기 데이터를 찾을 수 없습니다."}

        except Exception as e:
            return {"error": f"파일 검색 중 오류 발생: {str(e)}"}

    def analyze_by_mode_with_summary(self, query: str, mode: str, existing_summary: str) -> str:
        """모드별 추가 분석 (이미 생성된 요약 사용) HCX-007 사용"""
        print(f"[SEARCH_ENGINE] 모드별 분석 시작 (기존 요약 사용): {mode}")

        # HTML 태그 제거하여 텍스트만 추출
        import re
        summary_text = re.sub(r'<[^>]+>', '', existing_summary)

        # 회사명 추출 (요약에서 "## 회사명" 형태로 찾기)
        company_match = re.search(r'##\s*([^\s]+)\s*\d+년', summary_text)
        company_name = company_match.group(1) if company_match else "해당 회사"

        if mode == 'beginner':
            prompt_template = ChatPromptTemplate.from_template(
                """
                사용자가 초보 모드를 선택했습니다.
                투자 경험이 많지 않은 사용자가 이해할 수 있도록 공시 내용을 쉽게 설명하세요.

                --- [기본 요약] ---
                {summary}
                --- [END 기본 요약] ---

                --- [회사명] ---
                {company_name}
                --- [END 회사명] ---

                다음 지침을 따라 쉬운 설명을 작성하세요:

                1. 공시의 목적과 의미를 일상적인 예시와 비유를 들어 설명합니다.
                2. 어려운 용어(예: 자기자본비율, IFRS, 자사주 매입)는 반드시 **간단한 정의와 사례**를 덧붙입니다.
                3. 투자와 직접적으로 연결되는 '좋은 소식인지, 주의해야 할 소식인지'를 **초보자의 눈높이**에서 짚어주세요.
                4. 숫자(재무지표, 금액, 비율)는 요약하여 '이 정도면 크다/작다, 긍정적/부정적' 정도로 해석을 덧붙이세요.

                출력 형식:
                **🔰 쉬운 의미 설명**

                [일상적인 비유를 포함한 쉬운 설명]

                **💡 핵심 포인트**
                - 좋은 소식: [긍정적 요소들]
                - 주의할 점: [부정적 요소들]

                **📝 용어 설명**
                - [어려운 용어]: [쉬운 설명]

                사용자 질문: {query}
                """
            )
        else:  # analyst mode
            prompt_template = ChatPromptTemplate.from_template(
                """
                사용자가 애널리스트 모드를 선택했습니다.
                공시 내용을 재무·산업 관점에서 깊이 있게 분석해 전문적 해석을 제공하세요.

                --- [기본 요약] ---
                {summary}
                --- [END 기본 요약] ---

                --- [회사명] ---
                {company_name}
                --- [END 회사명] ---

                다음 지침을 따라 전문적 분석을 작성하세요:

                1. 공시의 핵심 내용을 요약하고, 해당 기업 및 업종 전반에 미칠 수 있는 영향까지 설명합니다.
                2. 재무지표(ROE, 부채비율, PER 등)를 활용하여 의미를 수치적으로 해석하세요.
                3. 업종 전반에 미칠 영향, 최근 동종업계 사례, 규제/정책 변화, 경쟁사 동향과 연결 지어 분석합니다.
                4. 단순히 '좋다/나쁘다'가 아니라, **단기적/중장기적 시사점**을 나눠서 정리합니다.
                5. 투자 판단을 직접적으로 제시하지 말고, 전문가적 참고 관점에서만 설명합니다.

                출력 형식:
                **📊 전문적 해석**

                **재무 영향 분석**
                - [재무지표 중심의 분석]

                **업종 맥락**
                - [업계 동향 및 경쟁사 비교]

                **투자 시사점**
                - 단기적 관점: [1년 이내 영향]
                - 중장기적 관점: [2-3년 영향]

                **주의사항**
                - [리스크 요인 및 불확실성]

                사용자 질문: {query}
                """
            )

        chain = prompt_template | self.query_parser_llm | StrOutputParser()

        try:
            analysis = chain.invoke({
                "query": query,
                "summary": summary_text,
                "company_name": company_name
            })
            return analysis
        except Exception as e:
            return f"분석 중 오류가 발생했습니다: {str(e)}"


# 테스트용 함수
def main():
    engine = DartSearchEngine()

    while True:
        query = input("\n질문을 입력하세요 (종료: exit): ")
        if query.lower() == 'exit':
            break

        result = engine.search_and_summarize(query)

        if result.get("error"):
            print(f"❌ 오류: {result['error']}")
        else:
            print("\n" + "="*50)
            print(result["summary"])
            print("="*50)


if __name__ == "__main__":
    main()