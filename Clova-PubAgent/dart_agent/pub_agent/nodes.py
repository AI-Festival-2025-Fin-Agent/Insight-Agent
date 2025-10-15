#!/usr/bin/env python3
"""
DART Agent LangGraph 노드들
각 노드는 특정 기능을 담당하며 상태를 업데이트함
"""

import os
from typing import Dict, Any
from langchain_naver import ChatClovaX
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv

from pub_agent.document_searcher import DocumentSearcher
from dart_revised_search.dart_integrated_system import DartIntegratedSystem

class DartAgentNodes:
    """DART Agent의 모든 노드 정의"""

    def __init__(self):
        # LLM 초기화
        self.query_parser_llm = ChatClovaX(
            model="HCX-007",
            temperature=0.1
        )


        # 문서 검색기 초기화
        self.searcher = DocumentSearcher()

        # DART 통합 시스템 초기화 (수정공시 검색용)
        self.dart_system = DartIntegratedSystem()

    def query_parser_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 질문에서 회사명, 연도, 분기 추출 노드"""
        print("[NODE] 질문 파싱 노드 실행")

        query = state.get("query", "")
        if not query:
            return {
                **state,
                "error": "질문이 제공되지 않았습니다."
            }

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
- "삼전" → "삼성전자"
- "현대차" → "현대자동차"
- "sk하이닉스", "sk 하이닉스" → "SK하이닉스"
- "네이버" → "NAVER"

사용자 질문: {query}
{format_instructions}
"""
        )

        chain = prompt | self.query_parser_llm | parser

        try:
            extracted_info = chain.invoke({
                "query": query,
                "format_instructions": parser.get_format_instructions()
            })

            # 추출된 정보를 search_params에 저장
            search_params = {
                "company_name": extracted_info.get("company_name"),
                "year": extracted_info.get("year"),
                "quarter": extracted_info.get("quarter"),
                "extracted_info": extracted_info
            }

            return {
                **state,
                "search_params": search_params
            }

        except Exception as e:
            print(f"정보 추출 중 오류 발생: {e}")
            return {
                **state,
                "error": f"정보 추출 중 오류 발생: {e}"
            }

    def document_search_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """공시 문서 검색 노드 - 전체 분기보고서 검색 후 요청된 항목 표시"""
        print("[NODE] 문서 검색 노드 실행")

        search_params = state.get("search_params", {})
        company_name = search_params.get("company_name")
        requested_year = search_params.get("year")
        requested_quarter = search_params.get("quarter")

        if not company_name:
            return {
                "regular_results": {
                    "error": "검색에 필요한 회사명이 부족합니다."
                }
            }

        # 전체 분기보고서 검색
        quarterly_reports = self.searcher.get_company_quarterly_reports(company_name)

        if quarterly_reports.get("error"):
            return {
                "regular_results": {
                    "error": quarterly_reports.get("error")
                }
            }

        # 모든 분기보고서 실제 데이터 로드하고 요청된 항목 표시
        available_reports = quarterly_reports.get("available_reports", [])
        loaded_reports = []

        for report in available_reports:
            # 요청된 연도/분기와 일치하는지 표시
            if (requested_year and requested_quarter and
                report["year"] == requested_year and report["quarter"] == requested_quarter):
                report["is_target"] = True
            else:
                report["is_target"] = False

            # 모든 분기의 실제 데이터 로드
            loaded_data = self.searcher.get_company_data(company_name, report["year"], report["quarter"])
            if loaded_data.get("success"):
                report["raw_data"] = loaded_data.get("raw_data")
                report["processed_data"] = loaded_data.get("processed_data")

            loaded_reports.append(report)

        # 검색 결과를 results에 저장
        results = {
            "company_name": quarterly_reports.get("company_name"),
            "search_type": "dart_regular_disclosure_all",
            "available_reports": loaded_reports,
            "total_count": quarterly_reports.get("total_count", 0),
            "requested_year": requested_year,
            "requested_quarter": requested_quarter,
            "success": True
        }

        print(f"[NODE] {company_name}의 분기보고서 {results['total_count']}건 발견")
        if requested_year and requested_quarter:
            print(f"[NODE] 요청된 항목: {requested_year}년 {requested_quarter}분기")

        return {
            "regular_results": results
        }

    def revision_search_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """수정공시 검색 노드 - DART API 활용"""
        print("[NODE] 수정공시 검색 노드 실행")

        search_params = state.get("search_params", {})
        company_name = search_params.get("company_name")

        if not company_name:
            return {
                "revision_results": {
                    "error": "회사명이 제공되지 않았습니다."
                }
            }

        try:
            # DART API를 통해 최근 1년간 공시 검색 (수정공시 포함)
            result = self.dart_system.search_and_fetch_documents(
                company_name=company_name,
                max_documents=100,
                days=365,
                fetch_content=True  # 목록만 먼저 가져오기
            )

            # 수정공시만 필터링
            revision_documents = []
            if result.get("documents"):
                for doc in result["documents"]:
                    revision_documents.append(doc)

            revision_results = {
                "total_found": result.get("documents_found", 0),
                "revision_count": len(revision_documents),
                "revision_documents": revision_documents,
                "search_type": "dart_revision_search",
                "company_name": company_name
            }

            print(f"[NODE] 수정공시 검색 완료: 전체 {result.get('documents_found', 0)}건 중 수정공시 {len(revision_documents)}건 발견")

            return {
                "revision_results": revision_results
            }

        except Exception as e:
            print(f"[NODE] 수정공시 검색 중 오류: {e}")
            return {
                "revision_results": {
                    "error": f"수정공시 검색 중 오류 발생: {e}",
                    "company_name": company_name
                }
            }

    def merge_results_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """정기공시와 수정공시 검색 결과를 병합하는 노드"""
        print("[NODE] 검색 결과 병합 노드 실행")

        regular_results = state.get("regular_results", {})
        revision_results = state.get("revision_results", {})

        # 정기공시 검색 결과 확인
        has_regular_results = regular_results and not regular_results.get("error")

        # 수정공시 검색 결과 확인
        has_revision_results = (revision_results and
                               not revision_results.get("error") and
                               revision_results.get("revision_count", 0) > 0)

        if has_regular_results and has_revision_results:
            revision_count = revision_results.get("revision_count", 0)
            print(f"[NODE] 병합 완료: 정기공시 검색 성공, 수정공시 {revision_count}건 발견")
        elif has_regular_results:
            print("[NODE] 병합 완료: 정기공시 검색만 성공")
        else:
            print("[NODE] 병합 완료: 검색 결과 없음")

        # 병합 노드는 상태를 변경하지 않고 로그만 출력
        return {}

