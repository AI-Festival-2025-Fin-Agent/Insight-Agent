# DART 검색 AI 요약 시스템

DART 공시 데이터를 자연어 질문으로 검색하고 AI가 요약해주는 웹 서비스입니다.

## 🚀 주요 기능

- **자연어 질의**: "삼성전자 2023년 4분기 실적 어때?" 같은 질문으로 검색
- **AI 요약**: Google Gemini로 공시 데이터를 이해하기 쉽게 요약
- **모드별 분석**: 초보자/애널리스트 모드로 맞춤형 분석 제공
- **실시간 웹UI**: 직관적인 웹 인터페이스

## 🏗️ 아키텍처

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   사용자     │────│  Flask Web  │────│  FastAPI    │
│  (브라우저)   │    │ Frontend    │    │   Backend   │
│             │    │ :6001       │    │   :6000     │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
                                      ┌─────────────┐
                                      │ AI 검색엔진  │
                                      │ (Gemini +   │
                                      │  Clova)     │
                                      └─────────────┘
```

## 📁 파일 구조

```
dart_search/
├── api.py              # FastAPI 백엔드 API 서버
├── search_engine.py    # 핵심 AI 검색 및 요약 엔진
├── frontend.py         # Flask 웹 프론트엔드
├── requirements.txt    # Python 의존성 패키지
├── templates/
│   └── index.html     # 메인 웹 인터페이스
├── .env               # 환경 변수 (API 키)
├── README.md          # 이 문서
├── api.md             # API 명세서
└── agent.md           # 검색 엔진 구현 가이드
```

## 🛠️ 기술 스택

- **Backend API**: FastAPI + Uvicorn
- **Frontend Web**: Flask + Jinja2
- **AI 모델**:
  - Google Gemini 2.5 Pro (요약 생성)
  - Naver Clova HCX-007 (질의 파싱)
- **기타**: LangChain, Requests, Markdown

## 🚦 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`.env` 파일에 API 키 설정:
```
GOOGLE_API_KEY=your_google_api_key
CLOVASTUDIO_API_KEY=your_clova_api_key
```

### 3. 서버 실행

**Backend API 서버 (필수)**
```bash
python api.py
# http://localhost:6000에서 실행됨
```

**Frontend 웹 서버 (필수)**
```bash
python frontend.py
# http://localhost:6001에서 실행됨
```

> ⚠️ **주의**: 두 서버 모두 실행되어야 정상 동작합니다.

## 📚 문서

- **[api.md](./api.md)** - FastAPI 백엔드 API 명세서
- **[agent.md](./agent.md)** - DartSearchEngine 구현 가이드

**주요 엔드포인트**:
- `POST /search_only` - 공시문서 검색만 수행
- `POST /summarize` - 검색 + AI 요약 생성
- `POST /analyze_mode` - 모드별 추가 분석
- `POST /company_reports` - 회사명으로 분기 보고서 목록 조회
- `POST /company_data` - 회사명+연도+분기로 원본 데이터 조회
- `GET /health` - 서버 상태 확인

## 💡 사용 예시

### 기본 사용법
1. **웹 브라우저로 접속**: http://localhost:6001
2. **질문 입력**: "카카오 2025년 1분기 실적 어때?"
3. **AI 요약 확인**: 자동으로 회사명, 연도, 분기를 추출하여 공시 데이터 요약
4. **모드별 분석**: 초보자 또는 애널리스트 모드로 추가 분석 요청

### 새로운 API 활용법
1. **회사 분기 보고서 목록 조회**: "카카오" 입력 → 사용 가능한 모든 분기 보고서 목록 확인
2. **특정 분기 데이터 조회**: 회사명 + 연도 + 분기 입력 → 해당 분기 원본 데이터 직접 조회

## 🔍 핵심 동작 원리

1. **질문 파싱**: 자연어 질문에서 회사명, 연도, 분기 정보를 AI로 추출
2. **파일 검색**: 추출된 정보로 공시 데이터 파일을 찾고 로드
3. **AI 요약**: Google Gemini로 공시 데이터를 이해하기 쉽게 요약
4. **모드별 분석**: 초보자/애널리스트 모드로 추가 심화 분석

## 📝 개발 참고사항

- **데이터 경로**: `/home/sese/Clova-PubAgent/dart_api_data`
- **회사명 정규화**: 줄임말을 정식 명칭으로 자동 변환
- **유사도 검색**: 정확한 매칭이 없으면 유사도 기반 검색
- **에러 처리**: 타임아웃, 연결 오류 등 다양한 예외 상황 처리

## 🔧 트러블슈팅

### API 서버 연결 오류
- API 서버(6000번 포트)가 실행 중인지 확인
- 방화벽 설정 확인

### AI 모델 오류
- `.env` 파일의 API 키 확인
- 네트워크 연결 상태 확인

### 데이터 검색 실패
- 공시 데이터 경로 확인
- 회사명 정확성 확인 (유사도 검색 활용)