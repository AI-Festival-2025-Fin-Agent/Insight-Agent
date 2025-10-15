# -*- coding: utf-8 -*-
from dotenv import load_dotenv
load_dotenv('.env')
from langchain_naver import ChatClovaX

llm = ChatClovaX(
    model = "HCX-005",
    temperature=0.1
)

import sys
import os
import requests
from typing import Dict, Any, Optional, Annotated
from pydantic import BaseModel

# 상위 디렉토리의 search_engine을 import하기 위해 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from search_engine import DartSearchEngine

# 검색 엔진 인스턴스 생성
search_engine = DartSearchEngine()

# FinAgent API 설정
FINAGENT_API_URL = "http://localhost:8000/search"  # FinAgent API 주소

class SummarizeState(BaseModel):
    query: str
    summary: Optional[str] = None
    extracted_info: Optional[Dict] = None
    company_name: Optional[str] = None
    error: Optional[str] = None
    success: bool = False
    raw_data: Optional[Dict] = None
    need_finagent: bool = False
    finagent_result: Optional[str] = None
    final_output: Optional[Dict] = None

def summarize_node(state: SummarizeState) -> Dict[str, Any]:
    """요약 작업을 수행하는 노드 (병렬 실행용)"""
    print(f"[Summarize Node] 질문: '{state.query}' 처리 중...")

    try:
        result = search_engine.search_and_summarize(state.query)

        if result.get("error"):
            print(f"[Summarize Node] 에러 발생: {result['error']}")
            # summarize 관련 필드만 업데이트
            return {
                "summary": None,
                "extracted_info": None,
                "company_name": None,
                "error": result["error"],
                "success": False,
                "raw_data": None
            }
        else:
            print(f"[Summarize Node] 요약 완료")
            # summarize 관련 필드만 업데이트
            return {
                "summary": result["summary"],
                "extracted_info": result.get("extracted_info"),
                "company_name": result.get("company_name"),
                "success": True,
                "raw_data": result.get("raw_data")
            }
    except Exception as e:
        error_msg = f"서버 오류가 발생했습니다: {str(e)}"
        print(f"[Summarize Node] 예외 발생: {error_msg}")
        return {
            "summary": None,
            "extracted_info": None,
            "company_name": None,
            "error": error_msg,
            "success": False,
            "raw_data": None
        }

def check_and_call_finagent_node(state: SummarizeState) -> Dict[str, Any]:
    """LLM으로 주가 정보 필요성을 판단하고 필요시 FinAgent를 호출하는 통합 노드"""
    print(f"[FinAgent Node] 질문 분석: '{state.query}'")

    try:
        # 1단계: 판단용 프롬프트 (사용자 제공 설명 그대로 사용)
        prompt = f"""
다음 질문이 주가검색 기능을 필요로 하는지 판단해주세요.
해당질문에서 공시 검색 결과는 제공될 예정입니다.
따라서 사용자가 묻는 내용이 공시 정보만으로 답변 가능한지, 아니면 실제 주가 데이터(가격, 거래량, 지수 등)가 필요한지를 판단해야 합니다.
둘다 필요한 경우도 주가검색 기능이 필요합니다.

주가검색 기능 범위:
시스템에서 실제로 지원되는 종목/시장 데이터 조회만 가능

가능한 내용:
- 특정 종목 시가/고가/저가/종가/거래량/등락률 조회
- 시장 지수 조회 (KOSPI/KOSDAQ)
- 시장 통계 조회
- 가격/거래량/등락률 순위 조회
- 기술적 지표 신호 조회 (RSI, 볼린저밴드, 이동평균선, 골든/데드크로스 등)
- 복합조건 검색

예시: "삼성전자 오늘 종가 얼마야?", "KOSPI 지수 오늘 얼마야?", "RSI 과매수 종목 알려줘"

⚠️ PER, PBR, EPS 조회 및 투자 판단/추천/해석 관련 질문은 포함되지 않음

질문: "{state.query}"

위 질문에 답하기 위해 실제 주가 데이터(가격, 거래량, 지수 등)가 필요한지 판단해주세요.
공시 정보만으로는 알 수 없고 실시간/과거 주가 데이터가 필요하다면 "YES",
공시 정보만으로 충분하다면 "NO"로 답변해주세요. 반드시 YES/NO로만 대답해주세요.
"""

        # LLM을 사용해서 판단
        response = llm.invoke(prompt)
        llm_answer = response.content.strip()

        # 응답에서 YES 또는 NO 찾기
        llm_answer_upper = llm_answer.upper()
        if "YES" in llm_answer_upper:
            need_finagent = True
        elif "NO" in llm_answer_upper:
            need_finagent = False
        else:
            # YES/NO가 명확하지 않으면 기본적으로 호출하지 않음
            need_finagent = False
            print(f"[FinAgent Node] WARNING: LLM 응답에서 YES/NO를 찾을 수 없음")

        print(f"[FinAgent Node] LLM 응답: {llm_answer}")
        print(f"[FinAgent Node] 추출된 판단: {'YES' if need_finagent else 'NO'}")

        # 2단계: 필요시 FinAgent 호출
        finagent_result = None
        if need_finagent:
            print(f"[FinAgent Node] FinAgent 호출 중...")
            try:
                
                new_query = f""""{state.query}"
<IMPORTANT SYSTEM PROMPT>
- 지금 공시 정보 호출 후 주가 관련 데이터를 조회해야 합니다.
- 해당 질문에 공시 관련 질문이 있을 수 있으나 주가 관련 질문에만 답해주세요.
- 공시 정보는 위에서 이미 받았으므로, 공시 관련된 분석은 제공하지 마세요.
- 만약 어떤 사건 혹은 발표 전후 주가가 어떻게 변했는지 묻는다면, **발표일이 명확하지 않은 경우 여러 날짜 구간을 자유롭게 설정하여 조회할 수 있습니다.**
- 예를 들어, **1일 단위로 연속된 날짜를 조회**하거나, **1주 단위(같은 요일 기준)**로 비교하거나, **필요에 따라 임의의 간격(며칠, 몇 주, 몇 달 단위)**으로 조회해도 됩니다.
- 주말이나 공휴일로 시장이 휴장된 경우, **가장 가까운 이전 영업일로 자동 조정**하세요.
- 도구를 여러 번 호출해도 되며, 각 호출마다 서로 다른 날짜 범위를 사용할 수 있습니다.
- 도구 호출 단계가 아닌 최종 응답을 생성할 때, 반드시 공시 관련 내용은 포함하지 마세요.
- 오늘은 2025년 10월 14일입니다. 절대 2024년이 아닙니다. 날짜에 관해 혼동하지 마세요.
- 도구 호출 단계에서 날짜 정보가 필요하다면 오늘 날짜가 아닌 사용자 질문에서 날짜를 유추해서 사용하세요. 주말이나 공휴일인 경우, 가장 가까운 이전 영업일을 사용하세요.
"""
                if '네이버' in state.query:
                    new_query += '\n- 네이버의 종목명은 NAVER로 표기합니다.'

                
                payload = {"question": new_query}
                response = requests.post(FINAGENT_API_URL, json=payload, timeout=30)

                if response.status_code == 200:
                    result = response.json()
                    finagent_result = result.get("answer", "")
                    print(f"[FinAgent Node] FinAgent 응답 받음: {len(finagent_result)}자")
                else:
                    finagent_result = f"주가 정보 조회 중 오류가 발생했습니다: API 호출 실패 {response.status_code}"
                    print(f"[FinAgent Node] API 호출 실패: {response.status_code}")

            except Exception as e:
                finagent_result = f"주가 정보 조회 중 오류가 발생했습니다: {str(e)}"
                print(f"[FinAgent Node] FinAgent 호출 중 예외: {str(e)}")
        else:
            print(f"[FinAgent Node] 주가 정보 불필요, FinAgent 호출 생략")

        # 결과 반환
        result = {"need_finagent": need_finagent}
        if finagent_result is not None:
            result["finagent_result"] = finagent_result

        return result

    except Exception as e:
        print(f"[FinAgent Node] 전체 처리 중 오류: {str(e)}")
        return {
            "need_finagent": False,
            "finagent_result": None
        }


def merge_parallel_results_node(state: SummarizeState) -> Dict[str, Any]:
    """병렬 실행된 summarize와 check_finagent 결과를 합치는 노드"""
    print(f"[Merge Results Node] 병렬 실행 결과 합치는 중...")

    # final_output 생성
    final_output = {
        "query": state.query,
        "summary": state.summary,
        "extracted_info": state.extracted_info,
        "company_name": state.company_name,
        "success": state.success,
        "error": state.error,
        "need_finagent": state.need_finagent
    }

    # finagent 결과가 있으면 추가
    if state.finagent_result:
        final_output["finagent_result"] = state.finagent_result

    print(f"[Merge Results Node] 요약 완료: {state.success}")
    print(f"[Merge Results Node] FinAgent 필요: {state.need_finagent}")

    # final_output만 업데이트
    return {
        "final_output": final_output
    }


# LangGraph 생성
def create_summarize_graph():
    from langgraph.graph import StateGraph, START, END

    workflow = StateGraph(SummarizeState)

    # 노드 추가
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("check_and_call_finagent", check_and_call_finagent_node)
    workflow.add_node("merge_results", merge_parallel_results_node)

    # 병렬 실행: START에서 summarize와 check_and_call_finagent 동시 실행
    workflow.add_edge(START, "summarize")
    workflow.add_edge(START, "check_and_call_finagent")

    # 둘 다 완료 후 merge_results로 (LangGraph가 자동으로 병렬 완료 대기)
    workflow.add_edge("summarize", "merge_results")
    workflow.add_edge("check_and_call_finagent", "merge_results")

    # merge_results에서 종료
    workflow.add_edge("merge_results", END)

    return workflow.compile()

# 그래프 인스턴스 생성
graph = create_summarize_graph()