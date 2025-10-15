# DART 검색 엔진 (DartSearchEngine) 구현 가이드

`search_engine.py`의 핵심 AI 검색 및 요약 엔진에 대한 상세 구현 문서입니다.

## 🏗️ 전체 아키텍처

```
사용자 질문
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                 DartSearchEngine                           │
├─────────────────────────────────────────────────────────────┤
│  1️⃣ extract_info_from_query()                              │
│     ├─ Clova HCX-007로 질문 파싱                            │
│     ├─ 회사명, 연도, 분기 추출                               │
│     └─ 회사명 정규화 (삼전→삼성전자)                         │
│                                                             │
│  2️⃣ find_and_load_disclosure()                             │
│     ├─ 파일 경로 생성: /data/{year}/Q{quarter}/companies/   │
│     ├─ 정확 매칭 시도                                       │
│     ├─ 부분 매칭 시도 (카카오 vs 카카오뱅크)                │
│     ├─ 유사도 검색 (SequenceMatcher)                        │
│     └─ JSON 파일 로드                                       │
│                                                             │
│  3️⃣ generate_summary() [요약 모드만]                        │
│     ├─ Google Gemini 2.5 Pro 호출                          │
│     ├─ LangChain으로 프롬프트 템플릿 처리                    │
│     └─ 마크다운 형식 요약 생성                               │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
   결과 반환
```

## 🔍 주요 메서드 상세

### 1️⃣ extract_info_from_query()

자연어 질문에서 구조화된 정보를 추출합니다.

```
사용자 질문: "삼성전자 2023년 4분기 실적 어때?"
     │
     ▼
Clova HCX-007 + LangChain JsonOutputParser
     │
     ▼ JSON 파싱
{
  "company_name": "삼성전자",
  "year": 2023,
  "quarter": 4
}
```

**핵심 기능**:
- 회사명 정규화 (줄임말 → 정식명칭)
- 기본값 설정 (연도: 2025, 분기: 1)
- JSON 형식 강제 출력

**정규화 규칙**:
```
"lg엔솔", "엘지엔솔" → "LG에너지솔루션"
"카카오뱅크" → "카카오뱅크"
"삼전" → "삼성전자"
"현대차" → "현대자동차"
"sk하이닉스" → "SK하이닉스"
"네이버" → "NAVER"
```

### 2️⃣ find_and_load_disclosure()

추출된 정보로 공시 파일을 검색하고 로드합니다.

```
추출된 정보
     │
     ▼
경로 생성: /dart_api_data/{year}/Q{quarter}/companies/
     │
     ▼
파일 검색 우선순위:
├─ 1순위: 정확 매칭 (완전 일치)
├─ 2순위: 부분 매칭 (포함 관계)
└─ 3순위: 유사도 검색 (SequenceMatcher > 0.5)
     │
     ▼
JSON 파일 로드 및 반환
```

**검색 전략**:
1. **정확 매칭**: `company_name == file_company_name`
2. **부분 매칭**: 한쪽이 다른 쪽에 포함되는 경우
   - 예: "카카오" vs "카카오뱅크" → 짧은 이름 우선
3. **유사도 검색**: `SequenceMatcher`로 50% 이상 유사한 경우

### 3️⃣ generate_summary()

공시 데이터를 AI로 요약 생성합니다.

```
공시 JSON 데이터
     │
     ▼
LangChain 프롬프트 템플릿:
├─ 핵심 요약 (3-5줄)
├─ 주요 지표 (매출액, 영업이익 등)
├─ 특이사항
└─ 투자 의견
     │
     ▼ Google Gemini 2.5 Pro
마크다운 형식 요약
```

**요약 형식**:
```markdown
## {회사명} {연도}년 {분기}분기 보고서 요약

**핵심 요약**
[3-5줄 요약]

**주요 지표**
- 📈 **매출액**: [금액] (전년 동기 대비 증감률)
- 💰 **영업이익**: [금액] (전년 동기 대비 증감률)
- 👥 **직원 수**: [인원]
- 💼 **주요 투자**: [투자 내역]

**특이사항**
- [중요한 계약, 투자, 리스크 요인]

**투자 의견**
- 🟢 긍정적 / 🔴 부정적 / ⚫ 중립적
- [근거]

**키워드**: #태그1 #태그2
```

## 🎯 메서드별 사용법

### search_only()
공시문서 검색만 수행하고 요약은 생략합니다.

**처리 과정**:
1. `extract_info_from_query()` - 질문에서 회사명, 연도, 분기 추출
2. `find_and_load_disclosure()` - 공시 파일 검색 및 로드
3. 요약 생성 단계 건너뜀

```python
engine = DartSearchEngine()
result = engine.search_only("삼성전자 2023년 4분기")

# 반환값
{
    "extracted_info": {
        "company_name": "삼성전자",
        "year": 2023,
        "quarter": 4
    },
    "company_name": "삼성전자",
    "success": True,
    "raw_data": {
        "metadata": {...},
        "financial_data": {...}
    }
}
```

### search_and_summarize()
검색 + AI 요약을 모두 수행합니다.

```python
engine = DartSearchEngine()
result = engine.search_and_summarize("삼성전자 2023년 4분기 실적 어때?")

# 반환값
{
    "summary": "AI 생성 요약",
    "extracted_info": {...},
    "company_name": "삼성전자",
    "success": True,
    "raw_data": {...}
}
```

### analyze_by_mode_with_summary()
기존 요약을 바탕으로 모드별 추가 분석을 수행합니다.

```python
analysis = engine.analyze_by_mode_with_summary(
    query="삼성전자 분석해줘",
    mode="beginner",  # 또는 "analyst"
    existing_summary="기존 요약 내용"
)
```

### get_company_quarterly_reports()
회사명으로 사용 가능한 분기 보고서 목록을 조회합니다.

```python
engine = DartSearchEngine()
result = engine.get_company_quarterly_reports("카카오")

# 반환값
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
        # ... 더 많은 보고서
    ],
    "total_count": 5,
    "success": True
}
```

### get_company_data()
회사명, 연도, 분기로 직접 원본 데이터를 조회합니다.

```python
engine = DartSearchEngine()
result = engine.get_company_data("카카오", 2024, 4)

# 반환값
{
    "company_name": "카카오",
    "year": 2024,
    "quarter": 4,
    "raw_data": {
        "metadata": {...},
        "financial_data": {...}
    },
    "success": True
}
```

## 🔄 모드별 분석 흐름

```
기존 요약 결과
     │
     ▼
mode 선택:
├─ beginner: 초보자용 쉬운 설명
│   ├─ 일상적 비유 포함
│   ├─ 용어 설명 (자기자본비율, IFRS 등)
│   ├─ 투자 의미 해석
│   └─ 좋은/나쁜 소식 구분
│
└─ analyst: 전문가용 심화 분석
    ├─ 재무지표 분석 (ROE, PER 등)
    ├─ 업종 맥락 및 경쟁사 비교
    ├─ 단기/중장기 투자 시사점
    └─ 리스크 요인 분석
     │
     ▼ Clova HCX-007
추가 분석 결과
```

**Beginner 모드 특징**:
- 일상적 비유와 쉬운 설명
- 어려운 용어의 간단한 정의
- "좋은 소식/주의할 점" 구분
- 투자 초보자 눈높이 맞춤

**Analyst 모드 특징**:
- 재무지표 중심 분석
- 업계 동향 및 경쟁사 비교
- 단기/중장기 관점 분리
- 전문적 투자 시사점

## 🛠️ 설정 및 환경변수

### AI 모델 설정
```python
# Clova HCX-007 (질의 파싱용)
self.query_parser_llm = ChatClovaX(
    model="HCX-007",
    temperature=0.1
)

# Google Gemini 2.5 Pro (요약 생성용)
self.summary_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0.1,
    convert_system_message_to_human=True
)
```

### 데이터 경로 구조
```
/home/sese/Clova-PubAgent/dart_api_data/
├── 2023/
│   ├── Q1/companies/
│   ├── Q2/companies/
│   ├── Q3/companies/
│   └── Q4/companies/
├── 2024/
│   └── Q1/companies/
│       ├── 000660_SK하이닉스.json
│       ├── 035720_카카오.json
│       └── ...
└── 2025/
    └── Q1/companies/
```

## ⚠️ 주요 에러 처리

### 정보 추출 실패
```python
if not info:
    return {"error": "질문에서 정보를 추출할 수 없습니다."}
```

### 파일 검색 실패
```python
if not data:
    return {"error": f"해당 회사({company_name})의 공시 데이터를 찾을 수 없습니다."}
```

### AI 모델 오류
```python
try:
    response = chain.invoke(...)
except Exception as e:
    return f"요약 생성 중 오류가 발생했습니다: {e}"
```

## 🔧 성능 최적화 팁

1. **파일 검색 최적화**: 정확 매칭을 먼저 시도하여 불필요한 유사도 계산 방지
2. **회사명 정규화**: 미리 정의된 규칙으로 빠른 변환
3. **LangChain 활용**: 프롬프트 템플릿과 출력 파서로 안정적인 AI 호출
4. **에러 처리**: 각 단계별 명확한 에러 메시지로 디버깅 용이

## 📝 개발 참고사항

- **온도 설정**: 0.1로 낮춰 일관된 결과 보장
- **JSON 파싱**: 강제 JSON 출력으로 구조화된 데이터 확보
- **파일명 규칙**: `{종목코드}_{회사명}.json` 형식 준수
- **유사도 임계값**: 0.5 (50%) 이상에서 매칭 성공