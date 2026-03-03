# 🍱 Local Restaurant Navigator (Japan)

현지인들의 냉정한 미식 평가(Tabelog)와 대중적인 신뢰도(Google Maps)를 결합하여, 일본의 진짜 로컬 맛집을 발굴하고 Notion 데이터베이스로 큐레이션해주는 자동화 데이터 파이프라인입니다.

## 🚀 Key Features

*   **Premium Web Map UI**: 현대적이고 직관적인 드롭다운 기반 필터링 시스템(지역/구/음식 종류)과 Glassmorphism 디자인 적용.
*   **Pure Japanese Naming**: 타베로그 원문 이름을 그대로 유지하여 데이터의 원형을 보존 (`은하수` 등 혼용 방지).
*   **Two-Stage Sync & Review**: 수집 후 검토용 DB(Staging)에서 승인을 거쳐야만 최종 배포되는 안전한 워크플로우.
*   **Notion Notifications**: 수집 완료 시 노션에서 사용자(@태그)에게 즉시 푸시 알림 발송.
*   **Reboot Persistence**: iMac 재부팅 시에도 수집 서버와 터널이 자동으로 자가 복구되어 상시 대기.
*   **Monetization Ready**: 지역별(도쿄, 오사카 등) CSV 파티셔닝 및 Google My Maps 최적화 포맷 지원.
*   **Dual Platform Cross-Validation**: 타베로그(전문가 평점)와 구글 맵(실시간 대중 평점) 데이터를 대조하여 신뢰도 극대화.
*   **AI-Powered Curation**: Gemini AI를 활용한 리뷰 요약, 영업시간 번역 및 교통 정보 정제.

## 🔍 Data Collection & Curation Criteria

단순히 평점이 높은 식당이 아닌, 다각도의 검증을 거친 **'진짜 현지인 맛집'**만을 선별합니다.

### 1. 엄격한 선별 기준 (Curation Logic)
데이터 적재 전, 다음 세 가지 카테고리 중 하나에 부합하는 식당만 데이터베이스에 포함됩니다:
*   **🦄 0.1% 레전드 맛집**: 타베로그 평점 **4.0 이상**. (현지에서도 예약이 힘든 전설적인 명점)
*   **🏆 현지인 인증맛집**: 타베로그 평점 **3.5 ~ 3.9**. (실패 없는 확실한 퀄리티의 로컬 맛집)
*   **💡 숨겨진 맛집**: 타베로그 평점 **3.2 ~ 3.4** 이지만, 구글 맵 평점 **4.2 이상** + 리뷰 **50개 이상** + **최근 2개월 내 리뷰**가 있는 활동적인 곳.

### 2. 신뢰도 필터링 (Integrity Filtering)
*   **Japanese-Only Reviews**: 인위적인 번역 리뷰나 관광객 위주의 평가를 배제하기 위해, 구글 맵에서 **일본어 원문 리뷰**만 필터링하여 수집합니다.
*   **Pure Regional Focus**: 일본 전역의 대도시(도쿄, 오사카, 정령지정도시 등)부터 특색 있는 소도시(이시카와, 가고시마 등)까지 20개 이상의 지역을 커버합니다.
*   **Exclude Foreign-Cuisine**: 현지 미식 경험에 집중하기 위해 정통 일식을 제외한 한국 요리 등은 자동으로 필터링됩니다.

## 🏗️ Architecture

3-Layer Architecture (Directive - Orchestration - Execution) 구조를 채택하여 안정성과 확장성을 확보했습니다.

*   **Layer 1: Directive**: 관외 SOP 및 필터링 규칙 정의 (`directives/`).
*   **Layer 2: Orchestration**: 전국 8대 도시 및 주요 소도시를 순회하며 전체 프로세스 제어 (`execution/daily_orchestrator.py`).
*   **Layer 3: Execution**: 크롤링, AI 분석, 노션 출판 등 개별 기능을 담당하는 모듈형 스크립트.

## 🛠️ Setup & Running

### Prerequisites
*   Python 3.9+
*   Notion API Token & Database ID
*   Google Gemini API Key
*   ngrok Account (for Webhook)

### Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### Running Pipeline
```bash
# 전체 파이프라인 수집 (Staging DB로 업로드)
python3 run_pipeline.py --publish

# 웹 맵 데이터 동기화 및 CSV 수출
python3 execution/map_data_bridge.py
```

## 🛰️ Notion Integration & Persistence
노션의 '버튼' 기능을 통해 원클릭으로 파이프라인을 트리거하고 최종 승인할 수 있습니다. 
상세 설정 및 서버 상시 가동 방법은 `WEBHOOK_SETUP.md`를 참고하세요.

## 📝 Documentation
*   [Webhook Setup](WEBHOOK_SETUP.md): 노션 버튼 연동 및 자동 실행 가이드
*   [Changelog](CHANGELOG.md): 주요 업데이트 내역
