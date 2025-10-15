#!/usr/bin/env python3
"""
DART Agent LangGraph 워크플로우
전체 처리 흐름을 정의하고 관리
"""

from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.constants import Send

from pub_agent.nodes import DartAgentNodes
from pub_agent.edges import DartAgentEdges

class DartSearchState(TypedDict):
    """DART 검색 상태 정의 - 병렬 실행을 위한 구조"""
    # 입력
    query: str
    dart_type: str  # "regular"(정기공시만), "revision"(수정공시만), "both"(둘다)

    # 검색 파라미터
    search_params: Dict[str, Any]

    # 검색 결과 - 명확한 구분
    regular_results: Dict[str, Any]    # 정기공시 검색 결과
    revision_results: Dict[str, Any]   # 수정공시 검색 결과

    # 에러
    error: str

class DartAgentWorkflow:
    """DART Agent 워크플로우 관리 클래스"""

    def __init__(self):
        self.nodes = DartAgentNodes()
        self.edges = DartAgentEdges()
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> CompiledStateGraph:
        """LangGraph 워크플로우 구성 - 정기공시 + 수정공시 병렬 검색"""

        # StateGraph 생성
        workflow = StateGraph(DartSearchState)

        # 노드 추가
        workflow.add_node("query_parser", self.nodes.query_parser_node)
        workflow.add_node("document_search", self.nodes.document_search_node)
        workflow.add_node("revision_search", self.nodes.revision_search_node)
        workflow.add_node("merge_results", self.nodes.merge_results_node)

        # 시작점 설정
        workflow.set_entry_point("query_parser")

        # 1. 파싱 후 두 검색을 병렬로 시작 또는 오류 종료
        workflow.add_conditional_edges(
            "query_parser",
            self.edges.route_parallel_searches,
            ["document_search", "revision_search", END]
        )

        # 2. 두 검색이 모두 완료되면 결과 병합
        workflow.add_edge("document_search", "merge_results")
        workflow.add_edge("revision_search", "merge_results")

        # 3. 결과 병합 후 종료
        workflow.add_edge("merge_results", END)

        return workflow.compile()

    def run(self, query: str, dart_type: str = "regular") -> Dict[str, Any]:
        """워크플로우 실행 - 검색 결과 반환"""
        print(f"[WORKFLOW] Document Search Agent 시작: {query}")

        # 초기 상태 설정
        initial_state = DartSearchState(
            query=query,
            dart_type=dart_type,  # 사용자 지정 또는 기본값: 정기공시
            search_params={},
            regular_results={},
            revision_results={},
            error=""
        )

        try:
            # 워크플로우 실행
            result = self.workflow.invoke(initial_state)

            print("[WORKFLOW] Document Search Agent 완료")

            # 검색 결과 반환
            regular_results = result.get("regular_results", {})
            revision_results = result.get("revision_results", {})

            if regular_results and not regular_results.get("error"):
                response = {
                    "success": True,
                    "dart_type": result.get("dart_type", "regular"),
                    "search_params": result.get("search_params", {}),
                    "regular_results": regular_results,
                    "message": "정기공시 검색이 완료되었습니다."
                }

                # 수정공시 검색 결과가 있으면 포함
                if revision_results and not revision_results.get("error"):
                    response["revision_results"] = revision_results
                    revision_count = revision_results.get("revision_count", 0)
                    if revision_count > 0:
                        response["message"] = f"검색이 완료되었습니다. (정기공시 + 수정공시 {revision_count}건)"

                return response
            else:
                return {
                    "success": False,
                    "error": result.get("error", "검색에 실패했습니다."),
                    "search_params": result.get("search_params", {}),
                    "dart_type": result.get("dart_type", "regular")
                }

        except Exception as e:
            print(f"[WORKFLOW] 워크플로우 실행 중 오류: {e}")
            return {
                "success": False,
                "error": f"워크플로우 실행 중 오류가 발생했습니다: {e}"
            }

