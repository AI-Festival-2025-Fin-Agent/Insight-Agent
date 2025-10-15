# DART 통합 검색 시스템

DART(전자공시시스템)에서 회사별 공시 정보를 검색하고 문서 내용을 추출하여 JSON으로 저장하는 도구입니다.

## 사용법

### 1. 통합 시스템 실행
```bash
python dart_integrated_system.py
```

### 2. 검색 옵션
- **회사명**: 검색할 회사명 입력 (예: 삼성전자)
- **최대 문서 수**: 가져올 문서 개수 (기본: 5개)
- **검색 기간**:
  - 최근 N일간 검색
  - 구체적인 날짜 범위 (YYYY-MM-DD 형식)

### 3. 결과 저장
- JSON 파일로 자동 저장
- 파일명: `dart_results_회사명_날짜시간.json`

## 출력 결과

```json
{
  "search_query": "삼성전자",
  "search_date": "2025-10-08T00:55:36",
  "documents_found": 15,
  "documents_processed": 2,
  "documents": [
    {
      "index": 1,
      "basic_info": {
        "company": "삼성전자",
        "report_name": "자기주식취득결과보고서",
        "date": "2025.10.02",
        "url": "https://dart.fss.or.kr/..."
      },
      "content": "문서 전체 내용...",
      "content_length": 5021,
      "extraction_status": "success"
    }
  ]
}
```

## 개별 도구 사용

### 공시 검색만
```bash
python dart_web_crawler.py
```

### 문서 내용 추출만
```bash
python dart_document_fetcher.py
```