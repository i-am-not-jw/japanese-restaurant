# 로컬 맛집 내비게이터 (Japan Local Restaurant Scraper) - 인수인계서 (Handover Guide)

본 문서는 프로젝트를 이어받을 분(또는 AI 에이전트)이 **시스템의 설계 철학을 이해하고 즉시 파이프라인을 운영**할 수 있도록 작성된 종합 가이드입니다.

---

## 1. 프로젝트 개요 및 아키텍처 (Architecture)

본 시스템은 타베로그(Tabelog)와 구글 맵(Google Maps)의 데이터를 교차 검증하여, 광고성 리뷰를 걷어낸 '진짜 일본 현지인 맛집' 데이터를 Notion 데이터베이스에 자동 업로드하는 봇입니다. 

안정성을 위해 **3-Layer Architecture** 원칙에 따라 구축되었습니다.
- **Layer 1: Directive (지시/목적)**: `directives/routine_collection_sop.md` 및 마크다운 파일에 룰셋(평점 기준 3.5 이상, 리뷰 요구치 등) 정의.
- **Layer 2: Orchestration (라우팅/조율)**: `execution/daily_orchestrator.py`가 일본 전역의 주요 도시(Tier 1~3)를 순회하며 실행 로직을 통제. 오류나 API 제한(429 Error) 발생 시 안전하게 멈춤.
- **Layer 3: Execution (스크립트)**: 실제 크롤링, AI 요약, DB 업로드를 담당하는 개별 모듈 로직.

---

## 2. 필수 환경 설정 (Dependencies & Auth)

프로젝트 루트 디렉토리의 `.env` 파일에 아래와 같은 권한 키가 설정되어 있어야 합니다:

```env
NOTION_TOKEN=ntn_...
NOTION_JAPAN_RESTAURANT_DB_ID=307deb...
GEMINI_API_KEY=AIzaSy...
```

- **Notion SDK**: 노션 페이지 쿼리, 생성, 업데이트(Upsert) 시 사용됩니다.
- **Google Gemini API**: 일본어 리뷰 번역 및 자연어 요약, 철도역 이름 번역, 특이한 대중교통(버스 등) 텍스트 정제에 쓰입니다. (Gemini 1.5 Flash 권장)
- **Playwright**: 구글 맵 크롤링 시 안티 봇 우회 목적으로 사용합니다.

---

## 3. 핵심 스크립트 역할 (Execution Layer)

스크립트는 일련의 흐름(Pipeline)대로 작동합니다. 일회성/테스트 스크립트는 모두 제거되었으며, 아래 핵심 스크립트 5개만 유지합니다.

1. **`execution/tabelog_lookup.py` (타베로그 추출)**
   - 역할: 특정 지역의 타베로그 트렌딩 리스트(`?SrtT=trend`)에서 평점, 영업시간, 편의시설, 리뷰 텍스트 등을 크롤링.
   - 특징: 철도역 및 버스 정류장 등 교통 정보를 위키피디아 API & Gemini로 정제.
   - 출력: `/tmp/japanese_restaurant_data/tabelog_report.json`

2. **`execution/google_maps_lookup.py` (구글 맵 교차 검증)**
   - 역할: JSON 데이터를 읽어 각 식당을 구글 맵에서 검색. 
   - 특징: Playwright를 사용하여 동적 렌더링을 뚫고 최신 리뷰(최신순 정렬)와 리뷰 개수, 평점을 스크랩.
   - 출력: 기존 JSON에 구글 맵 데이터를 업데이트 덮어쓰기.

3. **`execution/export_to_csv.py` (Staging 및 AI 요약 적용)**
   - 역할: JSON 데이터를 읽어, Gemini에게 양 플랫폼의 리뷰 요약을 지시하고 최종 데이터를 CSV로 임시 저장.
   - 특징: 이 파일을 통해 자동 포스팅 전 데이터 오염 여부를 사람이 확인할 수 있음.
   - 출력: `/tmp/japanese_restaurant_data/staged_restaurants.csv`

4. **`execution/publish_from_csv.py` (Notion 최종 발행)**
   - 역할: CSV를 읽어 노션 데이터베이스에 업로드.
   - 특징: 고유 키(Tabelog URL)를 검사하여 있으면 속성 업데이트(PATCH), 없으면 신규 발행(POST)하는 Upsert 로직. 지역 공식 깃발까지 지원.

5. **`execution/sns_scanner.py` (보조 기능)**
   - 역할: 구글 검색을 활용해 인스타그램, 쓰레드 등 타 플랫폼 언급량 측정 지원. (원할 경우 파이프라인에 추가 가능)

6. **`execution/daily_orchestrator.py` (자동화 메인 컨트롤러)**
   - 역할: 위 1번부터 3번까지의 스크립트를 일본 전국 도시 목록(Tier 1+Tier 2)대로 순회 실행시킴.

---

## 4. 운영 워크플로우 (How to Run)

평상시 데이터 수집 시, 작업자는 다음 2단계 명령어만 실행하면 됩니다.

**Step 1: 데이터 추출 및 Staging (AI 요약 포함)**
```bash
python3 execution/daily_orchestrator.py
```
- 스크립트가 각 도시별로 크롤링을 진행하고, 최종 검증 데이터 묶음을 `~/.local/share/antigravity/staged_restaurants.csv` 에 떨굽니다.

**Step 2: 리뷰 검수 후 Notion 업로드**
- 에디터 프로그램 등으로 `staged_restaurants.csv`의 요약이나 태그가 잘 들어갔는지 가볍게 훑어봅니다.
- 문제가 없다면 아래 스크립트로 실제 출판합니다:
```bash
python3 execution/publish_from_csv.py
```

---

## 5. 알려진 엣지 케이스 및 유지보수 포인트

1. **Gemini API 초당 요율 제한 (Rate Limit 429 Error)**
   - 영업 시간과 리뷰 요약을 동시다발적으로 요청하므로 Gemini Cloud에서 `429 Too Many Requests` 상태를 뱉을 수 있습니다. 현재 시스템은 429 감지 시 파이프라인을 파괴하지 않고 상태 코드를 보내 우아하게(Gracefully) 중단됩니다. 이후 재개하면 됩니다.
2. **구글 맵 캡챠(Bot Detection)**
   - `.tmp` 하위에 캐시(Cache)를 적재하도록 Playwright를 세팅했습니다. 스크래퍼가 종종 블록당할 수 있으니 `google_maps_lookup.py` 의 딜레이(Time.sleep)를 유지해 주세요.
3. **태그 매핑 수정**
   - 만약 새로운 "소도시 지역명"이나 "요리 종류"가 들어와 노션 업로드 시 에러가 난다면, `execution/notion_publisher.py` 의 `LOCATION_KO` 및 `CUISINE_KO` 딕셔너리에 매핑을 추가하면 됩니다.

---

본 인수인계서를 읽은 당신(Human/AI)은 이제 로컬 맛집 내비게이터 파이프라인의 최고 관리자입니다! 필요한 유지보수나 확장을 자유롭게 진행해 주세요.
