#!/usr/bin/env python3
"""
DART Agent LangGraph 엣지(분기) 로직
워크플로우의 조건부 분기를 담당
"""

from typing import Dict, Any, List
from langgraph.constants import Send

class DartAgentEdges:
    """DART Agent의 모든 엣지(분기) 로직 정의"""

    @staticmethod
    def route_parallel_searches(state: Dict[str, Any]) -> List[Send]:
        """정보 추출 후 dart_type에 따른 검색 라우팅"""
        search_params = state.get("search_params", {})
        if search_params and not state.get("error"):
            dart_type = state.get("dart_type", "regular")
            searches = []

            if dart_type == "regular":
                # 정기공시만
                searches.append(Send("document_search", state))
            elif dart_type == "revision":
                # 수정공시만
                searches.append(Send("revision_search", state))
            elif dart_type == "both":
                # 둘 다
                searches.extend([
                    Send("document_search", state),
                    Send("revision_search", state)
                ])

            return searches
        else:
            # 오류가 있으면 종료
            return []


