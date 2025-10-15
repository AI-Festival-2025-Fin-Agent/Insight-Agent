# DART 검색 API 명세서

DART 공시 데이터 검색 및 요약을 위한 FastAPI 백엔드 API입니다.

## 🚀 서버 정보

- **Base URL**: `http://localhost:6000`
- **API Framework**: FastAPI
- **Documentation**: `http://localhost:6000/docs` (Swagger UI)

## 🔌 API 엔드포인트

### POST /search_only
공시문서 검색만 수행합니다 (요약 제외).

**요청**:
```json
{
    "query": "삼성전자 2023년 4분기 실적"
}
```

**응답**:
```json
{
    "extracted_info": {
        "company_name": "삼성전자",
        "year": 2023,
        "quarter": 4
    },
    "company_name": "삼성전자",
    "success": true,
    "raw_data": {
        "metadata": {...},
        "financial_data": {...}
    }
}
```

### POST /summarize
사용자 질문을 받아 AI 요약을 반환합니다.

**요청**:
```json
{
    "query": "삼성전자 2023년 4분기 실적 어때?"
}
```

**응답**:
```json
{
    "summary": "AI 생성 요약 내용",
    "extracted_info": {
        "company_name": "삼성전자",
        "year": 2023,
        "quarter": 4
    },
    "company_name": "삼성전자",
    "success": true,
    "raw_data": {
        "metadata": {...},
        "financial_data": {...}
    }
}
```

### POST /analyze_mode
모드별 추가 분석을 제공합니다.

**요청**:
```json
{
    "query": "질문 내용",
    "mode": "beginner",  // "beginner" 또는 "analyst"
    "summary": "기존 요약 내용"
}
```

**응답**:
```json
{
    "analysis": "모드별 분석 내용",
    "success": true
}
```

### POST /company_reports
회사명으로 사용 가능한 분기 보고서 목록을 조회합니다.

**요청**:
```json
{
    "company_name": "카카오"
}
```

**응답**:
```json
{
    "company_name": "카카오",
    "available_reports": [
        {
            "year": 2025,
            "quarter": 1,
            "company_name": "카카오",
            "filename": "035720_카카오.json",
            "file_path": "/path/to/file"
        },
        {
            "year": 2024,
            "quarter": 4,
            "company_name": "카카오",
            "filename": "035720_카카오.json",
            "file_path": "/path/to/file"
        }
    ],
    "total_count": 2,
    "success": true
}
```

### POST /company_data
회사명, 연도, 분기로 원본 데이터를 직접 조회합니다.

**요청**:
```json
{
    "company_name": "카카오",
    "year": 2024,
    "quarter": 4
}
```

**응답**:
```json
{
    "company_name": "카카오",
    "year": 2024,
    "quarter": 4,
    "raw_data": {
        "metadata": {...},
        "financial_data": {...}
    },
    "success": true
}
```

### GET /health
서버 상태를 확인합니다.

**응답**:
```json
{
    "status": "healthy",
    "message": "DART 공시 AI 요약 서비스가 정상 작동 중입니다."
}
```

## 📊 데이터 모델

### QueryRequest
```python
{
    "query": str  # 사용자 질문
}
```

### SearchResponse
```python
{
    "extracted_info": dict,    # 추출된 회사/연도/분기 정보
    "company_name": str,       # 회사명
    "success": bool,           # 성공 여부
    "raw_data": dict          # 원본 공시 데이터
}
```

### SummaryResponse
```python
{
    "summary": str,           # AI 생성 요약
    "extracted_info": dict,   # 추출된 회사/연도/분기 정보
    "company_name": str,      # 회사명
    "success": bool,          # 성공 여부
    "raw_data": dict         # 원본 공시 데이터
}
```

### ModeAnalysisRequest
```python
{
    "query": str,    # 사용자 질문
    "mode": str,     # "beginner" 또는 "analyst"
    "summary": str   # 기존 요약 내용
}
```

### CompanyRequest
```python
{
    "company_name": str  # 회사명
}
```

### CompanyDataRequest
```python
{
    "company_name": str,  # 회사명
    "year": int,          # 연도
    "quarter": int        # 분기 (1, 2, 3, 4)
}
```

### QuarterlyReportsResponse
```python
{
    "company_name": str,       # 회사명
    "available_reports": list, # 사용 가능한 보고서 목록
    "total_count": int,        # 총 보고서 수
    "success": bool            # 성공 여부
}
```

### CompanyDataResponse
```python
{
    "company_name": str,  # 회사명
    "year": int,          # 연도
    "quarter": int,       # 분기
    "raw_data": dict,     # 원본 공시 데이터
    "success": bool       # 성공 여부
}
```

## ⚠️ 에러 응답

### 400 Bad Request
```json
{
    "detail": "질문을 입력해주세요."
}
```

### 404 Not Found
```json
{
    "detail": "해당 회사(회사명)의 공시 데이터를 찾을 수 없습니다."
}
```

### 500 Internal Server Error
```json
{
    "detail": "서버 오류가 발생했습니다: 오류 메시지"
}
```

## 🔧 API 사용 예시

### cURL 예시

**검색만 수행**:
```bash
curl -X POST "http://localhost:6000/search_only" \
     -H "Content-Type: application/json" \
     -d '{"query": "카카오 2025년 1분기"}'
```

**요약 포함 검색**:
```bash
curl -X POST "http://localhost:6000/summarize" \
     -H "Content-Type: application/json" \
     -d '{"query": "카카오 2025년 1분기 실적 어때?"}'
```

**모드별 분석**:
```bash
curl -X POST "http://localhost:6000/analyze_mode" \
     -H "Content-Type: application/json" \
     -d '{
         "query": "카카오 실적 분석해줘",
         "mode": "beginner",
         "summary": "기존 요약 내용..."
     }'
```

**회사 분기 보고서 목록 조회**:
```bash
curl -X POST "http://localhost:6000/company_reports" \
     -H "Content-Type: application/json" \
     -d '{"company_name": "카카오"}'
```

**특정 분기 데이터 조회**:
```bash
curl -X POST "http://localhost:6000/company_data" \
     -H "Content-Type: application/json" \
     -d '{
         "company_name": "카카오",
         "year": 2024,
         "quarter": 4
     }'
```

### Python 예시

```python
import requests

# 검색만 수행
response = requests.post(
    "http://localhost:6000/search_only",
    json={"query": "삼성전자 2023년 4분기"}
)
data = response.json()

# 요약 포함 검색
response = requests.post(
    "http://localhost:6000/summarize",
    json={"query": "삼성전자 2023년 4분기 실적 어때?"}
)
summary_data = response.json()

# 회사 분기 보고서 목록 조회
response = requests.post(
    "http://localhost:6000/company_reports",
    json={"company_name": "카카오"}
)
reports_data = response.json()

# 특정 분기 데이터 조회
response = requests.post(
    "http://localhost:6000/company_data",
    json={
        "company_name": "카카오",
        "year": 2024,
        "quarter": 4
    }
)
company_data = response.json()
```

## 🚦 서버 실행

```bash
# 개발 모드
python api.py

# 또는 uvicorn 직접 실행
uvicorn api:app --host 0.0.0.0 --port 6000

# 백그라운드 실행
nohup uvicorn api:app --host 0.0.0.0 --port 6000 &
```