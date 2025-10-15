from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from search_engine import DartSearchEngine

app = FastAPI(title="DART 공시 AI 요약 API", version="1.0.0")



from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 또는 ["http://localhost:3000"] 같이 특정 도메인만 허용
    allow_methods=["*"],
    allow_headers=["*"],
)




# 검색 엔진 인스턴스 생성
search_engine = DartSearchEngine()

class QueryRequest(BaseModel):
    query: str

class ModeAnalysisRequest(BaseModel):
    query: str
    mode: str  # 'beginner' or 'analyst'
    summary: str  # 이미 생성된 요약

class CompanyRequest(BaseModel):
    company_name: str

class CompanyDataRequest(BaseModel):
    company_name: str
    year: int
    quarter: int

class SummaryResponse(BaseModel):
    summary: str
    extracted_info: dict = None
    company_name: str = None
    success: bool = True
    raw_data: dict = None

class SearchResponse(BaseModel):
    extracted_info: dict = None
    company_name: str = None
    success: bool = True
    raw_data: dict = None

class QuarterlyReportsResponse(BaseModel):
    company_name: str = None
    available_reports: list = None
    total_count: int = 0
    success: bool = True

class CompanyDataResponse(BaseModel):
    company_name: str = None
    year: int = None
    quarter: int = None
    raw_data: dict = None
    success: bool = True

@app.post("/summarize", response_model=SummaryResponse)
async def summarize_disclosure(request: QueryRequest):
    """사용자 질문을 받아 DART 공시 요약을 반환

    Args:
        request: 질문 요청
    """
    print(f"[API] POST /summarize 요청 받음")
    print(f"[API] 질문: '{request.query}'")

    if not request.query.strip():
        print(f"[API] 에러: 빈 질문")
        raise HTTPException(status_code=400, detail="질문을 입력해주세요.")

    try:
        print(f"[API] search_engine.search_and_summarize 호출 시작")
        result = search_engine.search_and_summarize(request.query)

        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])

        response_data = {
            "summary": result["summary"],
            "extracted_info": result.get("extracted_info"),
            "company_name": result.get("company_name"),
            "success": True,
            "raw_data": result.get("raw_data")  # 항상 원본 데이터 포함
        }

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")

@app.post("/search_only", response_model=SearchResponse)
async def search_disclosure(request: QueryRequest):
    """사용자 질문을 받아 DART 공시 검색만 수행 (요약 제외)

    Args:
        request: 질문 요청
    """
    print(f"[API] POST /search_only 요청 받음")
    print(f"[API] 질문: '{request.query}'")

    if not request.query.strip():
        print(f"[API] 에러: 빈 질문")
        raise HTTPException(status_code=400, detail="질문을 입력해주세요.")

    try:
        print(f"[API] search_engine.search_only 호출 시작")
        result = search_engine.search_only(request.query)

        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])

        response_data = {
            "extracted_info": result.get("extracted_info"),
            "company_name": result.get("company_name"),
            "success": True,
            "raw_data": result.get("raw_data")
        }

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")

@app.post("/analyze_mode")
async def analyze_mode(request: ModeAnalysisRequest):
    """모드별 추가 분석 (초보자/애널리스트)"""
    print(f"[API] POST /analyze_mode 요청 받음")
    print(f"[API] 질문: '{request.query}', 모드: {request.mode}")

    if not request.query.strip():
        raise HTTPException(status_code=400, detail="질문을 입력해주세요.")

    if request.mode not in ['beginner', 'analyst']:
        raise HTTPException(status_code=400, detail="모드는 'beginner' 또는 'analyst'여야 합니다.")

    try:
        analysis = search_engine.analyze_by_mode_with_summary(request.query, request.mode, request.summary)
        return {"analysis": analysis, "success": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류가 발생했습니다: {str(e)}")

@app.post("/company_reports", response_model=QuarterlyReportsResponse)
async def get_company_reports(request: CompanyRequest):
    """회사명으로 사용 가능한 분기 보고서 목록 조회

    Args:
        request: 회사명 요청
    """
    print(f"[API] POST /company_reports 요청 받음")
    print(f"[API] 회사명: '{request.company_name}'")

    if not request.company_name.strip():
        print(f"[API] 에러: 빈 회사명")
        raise HTTPException(status_code=400, detail="회사명을 입력해주세요.")

    try:
        print(f"[API] search_engine.get_company_quarterly_reports 호출 시작")
        result = search_engine.get_company_quarterly_reports(request.company_name)

        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])

        response_data = {
            "company_name": result["company_name"],
            "available_reports": result["available_reports"],
            "total_count": result["total_count"],
            "success": True
        }

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")

@app.post("/company_data", response_model=CompanyDataResponse)
async def get_company_data(request: CompanyDataRequest):
    """회사명, 연도, 분기로 원본 데이터 조회

    Args:
        request: 회사명, 연도, 분기 요청
    """
    print(f"[API] POST /company_data 요청 받음")
    print(f"[API] 회사명: '{request.company_name}', 연도: {request.year}, 분기: {request.quarter}")

    if not request.company_name.strip():
        print(f"[API] 에러: 빈 회사명")
        raise HTTPException(status_code=400, detail="회사명을 입력해주세요.")

    if request.quarter not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="분기는 1, 2, 3, 4 중 하나여야 합니다.")

    try:
        print(f"[API] search_engine.get_company_data 호출 시작")
        result = search_engine.get_company_data(request.company_name, request.year, request.quarter)

        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])

        response_data = {
            "company_name": result["company_name"],
            "year": result["year"],
            "quarter": result["quarter"],
            "raw_data": result["raw_data"],
            "success": True
        }

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")

@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {"status": "healthy", "message": "DART 공시 AI 요약 서비스가 정상 작동 중입니다."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6000)
    # nohup uvicorn api:app --host 0.0.0.0 --port 6000 &