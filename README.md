# 🍱 Local Restaurant Navigator (Japan)

현지인들의 냉정한 미식 평가(Tabelog)와 대중적인 신뢰도(Google Maps)를 결합하여, 일본의 진짜 로컬 맛집을 발굴하고 Notion 데이터베이스로 큐레이션해주는 자동화 데이터 파이프라인입니다.

## 🚀 Key Features

*   **Dual Platform Cross-Validation**: 타베로그(전문가 평점)와 구글 맵(실시간 대중 평점) 데이터를 대조하여 신뢰도 극대화.
*   **AI-Powered Curation**: Gemini AI를 활용한 리뷰 요약, 영업시간 번역 및 교통 정보 정제.
*   **Automatic Notion Publishing**: 수집된 데이터를 Notion DB로 자동 업로드 및 업데이트(Upsert).
*   **Japanese Text Detection**: 자동 업로드 전 데이터의 무결성(일본어 잔존 여부)을 스스로 체크.
*   **Tag Standardization**: 평점 뱃지, 업종, 지역, 결제 수단별로 일관된 색상 코드 적용.

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

### Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### Running Pipeline
```bash
# 전체 파이프라인 수집 및 자동 업로드
python3 run_pipeline.py --publish
```

## 🛰️ Notion Integration
노션의 '버튼' 기능을 통해 원클릭으로 파이프라인을 트리거할 수 있습니다. 상세 설정은 `WEBHOOK_SETUP.md`를 참고하세요.

## 📝 Documentation
*   [Project Overview](project_overview.md): 시스템 상세 설계 및 철학
*   [Handover Guide](HANDOVER.md): 운영 및 유지보수 가이드
*   [Webhook Setup](WEBHOOK_SETUP.md): 노션 버튼 연동 가이드
