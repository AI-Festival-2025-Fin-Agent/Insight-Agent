# 📰 공시(Disclosure) 기능 가이드

## 개요

DART(전자공시시스템)의 최근 7일간 공시 데이터를 자동으로 수집하고, 날짜별로 조회할 수 있는 기능입니다.

---

## 🏗️ 시스템 아키텍처

```
DART 웹사이트 (dart.fss.or.kr)
    ↓ 크롤링
Python FastAPI 서버 (포트 8000)
    ↓ REST API 호출
Spring Boot 서버 (포트 8080)
    ↓ DB 저장 및 제공
MariaDB
    ↓ REST API
프론트엔드 (Vue-like SPA)
```

---

## 📁 프로젝트 구조

### Python 크롤러 (dart_search_current)

```
dart_search_current/
├── api_server.py              # FastAPI 서버
├── dart_crawl.py              # DART 크롤러
├── dart_doc_fetcher.py        # 공시 내용 추출
└── requirements.txt           # Python 의존성
```

**주요 API 엔드포인트:**
- `GET /api/disclosures/recent?mday_cnt=1&fetch_all=true` - 최근 공시 목록
- `GET /api/disclosures/{rceptNo}/content` - 공시 상세 내용

### Spring Boot 백엔드

```
stockkkkk/src/main/java/com/example/stockkkkk/disclosure/
├── config/
│   └── DisclosureInitializer.java    # 앱 시작 시 데이터 초기화
├── controller/
│   └── DisclosureController.java     # REST API 엔드포인트
├── domain/
│   └── Disclosure.java               # Entity (JPA)
├── dto/
│   ├── DisclosureResponse.java       # 응답 DTO
│   ├── DisclosureContentResponse.java
│   └── DartApiDisclosureDto.java     # Python API DTO
├── repository/
│   └── DisclosureRepository.java     # JPA Repository
└── service/
    └── DisclosureService.java        # 비즈니스 로직 + 스케줄링
```

### 프론트엔드

```
stockkkkk/src/main/resources/static/
└── features/
    └── disclosure/
        └── disclosure.js             # 공시 페이지 로직
```

---

## 🚀 실행 방법

### 1. Python API 서버 실행

```bash
cd /home/sese-java/rumor_study/dart_search_current

# 의존성 설치 (최초 1회)
pip install fastapi uvicorn requests beautifulsoup4 chardet pydantic

# 서버 실행
python api_server.py > api_server.log 2>&1 &

# 또는 nohup으로 실행
nohup python api_server.py > api_server.log 2>&1 &

# 상태 확인
curl http://localhost:8000/health
```

**출력 예시:**
```json
{"status":"healthy","timestamp":"2025-10-11T21:46:08.070020"}
```

### 2. Spring Boot 서버 실행

```bash
cd /home/sese-java/rumor_study/stockkkkk

# 빌드
./gradlew build

# 실행
nohup java -jar build/libs/stockkkkk-0.0.1-SNAPSHOT.jar > app.log &
```

### 3. 서버 확인

```bash
# 프로세스 확인
ps aux | grep -E "api_server|stockkkkk"

# 로그 확인
tail -f /home/sese-java/rumor_study/dart_search_current/api_server.log
tail -f /home/sese-java/rumor_study/stockkkkk/app.log

# API 테스트
curl http://localhost:8080/api/disclosures/summary
```

---

## 🔄 자동화 기능

### 1. 초기 데이터 로드 (ApplicationRunner)

애플리케이션 시작 시 자동으로 **최근 7일간 공시 데이터**를 Python API에서 가져와 DB에 저장합니다.

```java
// DisclosureInitializer.java
@Component
public class DisclosureInitializer implements ApplicationRunner {
    @Override
    public void run(ApplicationArguments args) {
        disclosureService.loadInitialData(); // 7일치 데이터 로드
    }
}
```

### 2. 당일 공시 자동 갱신 (2분마다)

```java
// DisclosureService.java
@Scheduled(fixedRate = 120000) // 2분
public void refreshTodayDisclosures() {
    fetchAndSaveDisclosures(1); // 당일 공시만 갱신
}
```

### 3. 오래된 데이터 자동 삭제 (매일 자정)

```java
// DisclosureService.java
@Scheduled(cron = "0 0 0 * * *") // 매일 00:00:00
public void cleanOldData() {
    // 7일 이전 데이터 삭제
}
```

---

## 📊 데이터베이스 스키마

### disclosures 테이블

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | BIGINT | PK (자동 증가) |
| rcept_no | VARCHAR(20) | 접수번호 (unique) |
| company | VARCHAR(200) | 회사명 |
| report | VARCHAR(500) | 보고서명 |
| submitter | VARCHAR(200) | 제출인 |
| disclosure_date | DATE | 공시일자 |
| disclosure_time | VARCHAR(10) | 공시시간 |
| market | VARCHAR(10) | 시장구분 (유/코/공) |
| url | VARCHAR(500) | 공시 URL |
| is_correction | BOOLEAN | 정정공시 여부 |
| content | TEXT | 공시 내용 (nullable) |
| content_fetched | BOOLEAN | 내용 조회 여부 |
| created_at | DATETIME | 생성일시 |
| updated_at | DATETIME | 수정일시 |

**인덱스:**
- `idx_disclosure_date` - 날짜별 조회 최적화
- `idx_rcept_no` - 접수번호 unique 제약
- `idx_company` - 회사명 검색 최적화

---

## 🌐 REST API 명세

### 1. 날짜별 공시 요약

**Request:**
```http
GET /api/disclosures/summary
```

**Response:**
```json
{
  "2025-10-05": 152,
  "2025-10-06": 198,
  "2025-10-07": 234,
  "2025-10-08": 187,
  "2025-10-09": 156,
  "2025-10-10": 262,
  "2025-10-11": 89
}
```

### 2. 특정 날짜의 공시 목록

**Request:**
```http
GET /api/disclosures?date=2025-10-11
```

**Response:**
```json
[
  {
    "id": 1,
    "rceptNo": "20251011000123",
    "company": "삼성전자",
    "report": "주요사항보고서",
    "submitter": "삼성전자",
    "disclosureDate": "2025-10-11",
    "disclosureTime": "09:00",
    "market": "유",
    "url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20251011000123",
    "isCorrection": false,
    "contentFetched": false
  }
]
```

### 3. 공시 상세 내용 조회

**Request:**
```http
GET /api/disclosures/{rceptNo}/content
```

**Response:**
```json
{
  "rceptNo": "20251011000123",
  "company": "삼성전자",
  "report": "주요사항보고서",
  "content": "공시 전체 내용...",
  "contentLength": 15234
}
```

### 4. 수동 데이터 갱신 (테스트용)

**Request:**
```http
POST /api/disclosures/refresh
```

**Response:**
```json
"데이터 갱신 완료"
```

---

## 🎨 프론트엔드 구조

### 화면 구성

1. **날짜 캘린더** (최근 7일)
   - 가로로 7개 날짜 카드 표시
   - 각 날짜별 공시 개수 표시
   - 오늘 날짜는 노란색으로 강조

2. **공시 목록**
   - 선택한 날짜의 공시 목록
   - 회사명, 보고서명, 제출인, 시간
   - 정정공시는 빨간색 태그

3. **상세 모달**
   - 공시 클릭 시 모달로 전체 내용 표시
   - DART 원문 링크 제공

### 주요 함수

```javascript
// disclosure.js

// 페이지 초기화
function initDisclosurePage() { ... }

// 7일간 요약 데이터 로드
async function loadDisclosureSummary() { ... }

// 날짜 캘린더 렌더링
function renderDateCalendar() { ... }

// 특정 날짜의 공시 목록 로드
async function loadDisclosureList(dateStr) { ... }

// 공시 상세 모달 표시
async function showDisclosureDetail(rceptNo) { ... }
```

---

## 🔧 트러블슈팅

### 1. 403 Forbidden 에러

**증상:**
```
Failed to load resource: the server responded with a status of 403
```

**원인:** SecurityConfig에서 `/api/disclosures/**` 경로가 차단됨

**해결:**
```java
// SecurityConfig.java
.requestMatchers("/api/disclosures/**").permitAll()
```

### 2. 공시 데이터가 없음

**증상:** 프론트엔드에 "해당 날짜에 공시가 없습니다" 표시

**원인:**
1. Python API 서버가 실행되지 않음
2. 초기 데이터 로드 실패

**해결:**
```bash
# Python API 서버 확인
curl http://localhost:8000/health

# 수동 데이터 로드
curl -X POST http://localhost:8080/api/disclosures/refresh

# 로그 확인
tail -f app.log
```

### 3. Python API 연결 실패

**증상:**
```
공시 데이터 가져오기 실패: Connection refused
```

**해결:**
```bash
# Python API 서버 재시작
cd /home/sese-java/rumor_study/dart_search_current
pkill -f api_server.py
python api_server.py > api_server.log 2>&1 &
```

### 4. 인코딩 문제 (한글 깨짐)

**원인:** DART 사이트의 EUC-KR 인코딩

**해결:** `dart_doc_fetcher.py`에서 이미 처리됨
```python
# 자동 인코딩 감지 (chardet)
# EUC-KR 우선 디코딩
```

---

## 📝 추가 개발 사항

### 향후 개선 가능 항목

1. **검색 기능**
   - 회사명으로 검색
   - 키워드로 검색

2. **필터링**
   - 정정공시만 보기
   - 특정 시장만 보기 (유가증권/코스닥/공모)

3. **알림 기능**
   - 특정 회사의 공시 알림
   - 중요 공시 푸시 알림

4. **통계 대시보드**
   - 일별 공시 트렌드
   - 회사별 공시 빈도

5. **공시 분석**
   - AI를 통한 공시 요약
   - 중요도 자동 분석

---

## 📚 참고 자료

- [DART 전자공시시스템](https://dart.fss.or.kr)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Spring Boot Scheduling](https://docs.spring.io/spring-framework/reference/integration/scheduling.html)
- [JPA Auditing](https://docs.spring.io/spring-data/jpa/reference/auditing.html)

---

## 💡 FAQ

### Q: 공시 데이터는 얼마나 보관되나요?
**A:** 최근 7일치만 보관됩니다. 매일 자정에 7일 이전 데이터는 자동 삭제됩니다.

### Q: 실시간으로 공시를 가져오나요?
**A:** 당일 공시는 1시간마다 자동으로 갱신됩니다.

### Q: Python 서버가 다운되면 어떻게 되나요?
**A:** Spring Boot는 계속 실행되며, 기존 DB 데이터는 조회 가능합니다. 새로운 공시만 업데이트되지 않습니다.

### Q: 공시 내용은 언제 가져오나요?
**A:** 사용자가 공시를 클릭할 때 처음으로 가져와 DB에 저장합니다 (Lazy Loading).

---

## 👨‍💻 개발자 정보

- **작성일:** 2025-10-11
- **버전:** 1.0.0
- **문의:** 프로젝트 README 참조
