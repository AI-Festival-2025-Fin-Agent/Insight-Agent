# Clova-PubAgent

DART(금융감독원 전자공시시스템) API를 활용한 AI 기반 공시 문서 검색 및 요약 시스템

## 🎯 프로젝트 개요

Clova-PubAgent는 한국 상장기업의 공시 정보를 자동으로 수집하고, AI를 활용해 자연어 질의응답 형태로 제공하는 시스템입니다. 복잡한 공시 문서를 쉽게 이해할 수 있도록 요약하고 분석해드립니다.

### ✨ 주요 기능
- 📊 **DART API 연동**: 28개 정기보고서 주요정보 API 완전 지원
- 🤖 **AI 기반 요약**: Naver ClovaX + Google Gemini 하이브리드 모델
- 🔍 **자연어 검색**: "삼성전자 2023년 매출액은?" 같은 자연어 질의
- ⚡ **고속 배치 처리**: 다중 API 키로 대용량 데이터 효율적 수집
- 🌐 **웹 API 제공**: FastAPI 기반 RESTful API

## 🛠 기술 스택

- **언어**: Python 3.x
- **AI/ML**:
  - Naver ClovaX (HCX-007) - 질의 파싱
  - Google Gemini (2.5-pro) - 요약 생성
  - LangChain 프레임워크
- **웹 프레임워크**: FastAPI, Flask
- **데이터 처리**: XML 파싱, JSON 변환
- **기타**: Requests, Pydantic, python-dotenv

## 📁 프로젝트 구조

```
Clova-PubAgent/
├── dart_search/              # 🔍 검색 엔진 모듈
│   ├── search_engine.py     # 핵심 검색 및 요약 로직
│   ├── api.py              # FastAPI 웹 서버
│   ├── frontend.py         # 웹 인터페이스
│   └── requirements.txt    # 의존성 목록
├── dart_api_requests.py     # 📡 DART API 요청 모듈 (28개 엔드포인트)
├── dart_batch_collector_fast.py # ⚡ 고속 배치 수집기
├── dart_batch_collector.py  # 📥 기본 배치 수집기
├── dart_corpcode_data/      # 🏢 기업 코드 데이터 관리
├── dart_api_data/          # 💾 수집된 공시 데이터 저장소
├── docs/                   # 📋 문서 및 다이어그램
└── rag_pipeline_v1.ipynb   # 🧪 RAG 파이프라인 프로토타입
```

## 🚀 설치 및 설정

### 1. 환경 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd Clova-PubAgent

# 의존성 설치
pip install -r dart_search/requirements.txt
```

### 2. API 키 설정

`.env` 파일을 생성하고 다음 API 키들을 설정하세요:

```env
# DART API 키 (https://opendart.fss.or.kr/에서 발급)
DART_API_KEY=your_dart_api_key

# Google AI API 키
GOOGLE_API_KEY=your_google_api_key

# Naver ClovaX API 키
CLOVASTUDIO_API_KEY=your_clova_api_key
```

### 3. 데이터 디렉토리 생성

```bash
mkdir -p dart_api_data
```

## 📖 사용법

### 1. API 서버 실행

```bash
cd dart_search
uvicorn api:app --host 0.0.0.0 --port 8000
```

### 2. 웹 인터페이스 실행

```bash
cd dart_search
python frontend.py
```

### 3. 배치 데이터 수집

```bash
# 고속 수집 (권장)
python dart_batch_collector_fast.py

# 기본 수집
python dart_batch_collector.py
```

### 4. API 사용 예시

```python
import requests

# 질의 요청
response = requests.post("http://localhost:8000/summarize",
    json={"query": "삼성전자 2023년 1분기 매출액은?"})

print(response.json()["summary"])
```

## 🎮 질의 예시

- "삼성전자 2023년 매출액은?"
- "카카오 최근 분기 영업이익 알려줘"
- "LG에너지솔루션 2024년 실적"
- "현대차 작년 투자 현황"

## 🔧 주요 특징

### 다중 API 키 관리
- 6개 DART API 키 로테이션으로 속도 제한 회피
- 자동 키 전환 및 에러 핸들링

### AI 하이브리드 모델
- **ClovaX**: 한국어 질의 파싱 및 정보 추출
- **Gemini**: 정확한 요약 및 분석 생성

### 28개 DART API 완전 지원
```python
# 지원 API 목록 (dart_api_requests.py 참조)
- 기업개황: fnlttSinglAcnt_all_info()
- 재무정보: fnlttSinglAcnt_revenue(), fnlttSinglAcnt_assets() 등
- 주주정보: hyslrSttus(), shareholding_change() 등
- 감사정보: accnutAdtorSttus(), auditor_change() 등
```

## 📊 데이터 구조

수집된 데이터는 다음과 같이 구조화됩니다:

```
dart_api_data/
├── 2023/
│   ├── Q1/
│   │   └── companies/
│   │       ├── 000010_신한은행.json
│   │       └── 005930_삼성전자.json
│   └── Q2/
└── 2024/
```

## 🔍 검색 엔진 동작 원리

1. **질의 분석**: ClovaX로 회사명, 연도, 분기 추출
2. **파일 검색**: 추출된 정보로 로컬 데이터 검색
3. **요약 생성**: Gemini로 공시 데이터 요약
4. **결과 반환**: 구조화된 요약 및 원본 데이터 제공

## 🛡 API 키 보안

- 환경변수 또는 `.env` 파일 사용
- 하드코딩된 키는 개발/테스트 용도만
- 프로덕션에서는 반드시 보안 설정 필요

## 📝 로그 및 모니터링

- `log_key*.txt`: 각 API 키별 요청 로그
- `nohup.out`: 백그라운드 실행 로그
- 실시간 진행 상황 콘솔 출력

## 🤝 기여 방법

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다.

## ⚠️ 주의사항

- DART API 사용량 제한 준수
- API 키 보안 관리 필수
- 대용량 데이터 수집 시 네트워크 안정성 확인
- 수집된 데이터는 개인 연구/분석 목적으로만 사용

## 📞 문의

문제가 있거나 개선 사항이 있다면 이슈를 등록해 주세요.

---

**Made with ❤️ for Korean Financial Data Analysis**