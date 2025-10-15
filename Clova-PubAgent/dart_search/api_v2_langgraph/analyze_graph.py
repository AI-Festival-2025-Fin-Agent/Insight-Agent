# -*- coding: utf-8 -*-
import sys
import os
from typing import Optional, Literal
from pydantic import BaseModel

# 상위 디렉토리의 search_engine을 import하기 위해 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from search_engine import DartSearchEngine

# 검색 엔진 인스턴스 생성
search_engine = DartSearchEngine()

class AnalyzeState(BaseModel):
    query: str
    mode: Literal['beginner', 'analyst']
    summary: str
    analysis: Optional[str] = None
    error: Optional[str] = None
    success: bool = False

def analyze_node(state: AnalyzeState) -> AnalyzeState:
    """모드별 분석을 수행하는 노드"""
    print(f"[Analyze Node] 질문: '{state.query}', 모드: '{state.mode}' 처리 중...")

    try:
        analysis = search_engine.analyze_by_mode_with_summary(state.query, state.mode, state.summary)
        print(f"[Analyze Node] 분석 완료")
        return AnalyzeState(
            query=state.query,
            mode=state.mode,
            summary=state.summary,
            analysis=analysis,
            success=True
        )
    except Exception as e:
        error_msg = f"분석 중 오류가 발생했습니다: {str(e)}"
        print(f"[Analyze Node] 예외 발생: {error_msg}")
        return AnalyzeState(
            query=state.query,
            mode=state.mode,
            summary=state.summary,
            error=error_msg,
            success=False
        )

# LangGraph 생성
def create_analyze_graph():
    from langgraph.graph import StateGraph, START, END

    workflow = StateGraph(AnalyzeState)
    workflow.add_node("analyze", analyze_node)
    workflow.add_edge(START, "analyze")
    workflow.add_edge("analyze", END)

    return workflow.compile()

# 그래프 인스턴스 생성
graph = create_analyze_graph()