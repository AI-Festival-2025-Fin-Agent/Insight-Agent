"""
DART 크롤러 FastAPI 서버
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn

from dart_crawl import DartWebCrawler
from dart_doc_fetcher import DartDocumentFetcher

app = FastAPI(title="DART Crawler API", version="1.0.0")

# CORS 설정 (Spring Boot에서 호출 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 크롤러 인스턴스 (재사용)
crawler = DartWebCrawler()


# === DTO 모델 ===
class DisclosureResponse(BaseModel):
    """공시 응답 DTO"""
    number: str
    company: str
    report: str
    submitter: str
    date: str
    time: str
    market: str
    rcept_no: str
    url: str
    is_correction: bool


class DocumentContentResponse(BaseModel):
    """문서 내용 응답 DTO"""
    title: Optional[str] = None
    company: Optional[str] = None
    submitter: Optional[str] = None
    submit_date: Optional[str] = None
    content: Optional[str] = None


class ErrorResponse(BaseModel):
    """에러 응답 DTO"""
    error: str
    message: str


# === API 엔드포인트 ===

@app.get("/")
def read_root():
    """API 상태 확인"""
    return {
        "service": "DART Crawler API",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/disclosures/recent", response_model=List[DisclosureResponse])
def get_recent_disclosures(
    mday_cnt: int = 1,
    company_name: str = "",
    fetch_all: bool = False
):
    """
    최근 공시 목록 가져오기

    Args:
        mday_cnt: 검색 기간 (1=당일, 2=2일, 3=3일, 7=7일, 30=30일)
        company_name: 회사명 필터 (비어있으면 전체)
        fetch_all: 전체 페이지를 다 가져올지 여부

    Returns:
        공시 목록
    """
    try:
        print(f"🔍 요청 받음: mday_cnt={mday_cnt}, company_name={company_name}, fetch_all={fetch_all}")

        disclosures = crawler.get_recent_disclosures(
            mday_cnt=mday_cnt,
            page=1,
            max_results=100,
            company_name=company_name,
            fetch_all=fetch_all
        )

        print(f"✅ {len(disclosures)}건의 공시 반환")
        return disclosures

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/disclosures/by-date", response_model=List[DisclosureResponse])
def get_disclosures_by_date_range(
    start_date: str,
    end_date: str,
    company_name: str = ""
):
    """
    날짜 범위로 공시 검색

    Args:
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        company_name: 회사명 필터 (비어있으면 전체)

    Returns:
        공시 목록
    """
    try:
        print(f"🔍 날짜 범위 검색: {start_date} ~ {end_date}, company={company_name}")

        # 회사명이 있으면 company 검색, 없으면 최근 공시 검색
        if company_name:
            disclosures = crawler.search_company_disclosures(
                company_name=company_name,
                start_date=start_date,
                end_date=end_date
            )
        else:
            # 최근 공시 API는 날짜 범위를 직접 지원하지 않으므로
            # mday_cnt로 대략적인 기간 설정
            from datetime import datetime, timedelta
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            days_diff = (end - start).days + 1

            # mday_cnt 매핑 (1, 2, 3, 7, 30 중 선택)
            if days_diff <= 1:
                mday_cnt = 1
            elif days_diff <= 2:
                mday_cnt = 2
            elif days_diff <= 3:
                mday_cnt = 3
            elif days_diff <= 7:
                mday_cnt = 7
            else:
                mday_cnt = 30

            disclosures = crawler.get_recent_disclosures(
                mday_cnt=mday_cnt,
                page=1,
                max_results=100,
                company_name="",
                fetch_all=True
            )

        print(f"✅ {len(disclosures)}건의 공시 반환")
        return disclosures

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/disclosures/{rcept_no}/content", response_model=DocumentContentResponse)
def get_disclosure_content(rcept_no: str):
    """
    특정 공시의 내용 가져오기

    Args:
        rcept_no: 접수번호 (14자리)

    Returns:
        공시 내용
    """
    try:
        print(f"🔍 공시 내용 요청: {rcept_no}")

        # URL 생성
        dart_url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"

        # 문서 내용 가져오기
        with DartDocumentFetcher() as fetcher:
            doc_info = fetcher.get_document_content(dart_url)

        if not doc_info:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

        print(f"✅ 문서 내용 반환 ({len(doc_info.get('content', ''))} 문자)")
        return doc_info

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    """헬스체크 엔드포인트"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    print("🚀 DART Crawler API 서버 시작...")
    print("📍 http://localhost:8000")
    print("📖 API 문서: http://localhost:8000/docs")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
