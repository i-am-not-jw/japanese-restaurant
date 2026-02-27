# 🏗️ AI 에이전트 팀 부트스트랩 가이드 (Agent Teams Blueprint)

이 문서는 새로운 프로젝트를 시작할 때 **안티그래비티(AI 에이전트)**를 다수의 전문화된 팀으로 전환하여 프로젝트를 수행하게 만드는 설계도입니다.

---

## 1. 프로젝트 초기화 (Directory Setup)

새 프로젝트 폴더를 만들고 아래 명령어를 터미널에서 실행하여 폴더 구조를 생성하세요.

```bash
mkdir -p directives/agents execution .tmp
touch agent.md .env .gitignore
```

---

## 2. 마스터 지침서 세팅 (`agent.md`)

이 내용을 프로젝트 루트의 `agent.md`에 복사하세요. 모든 에이전트 팀 운영의 '헌법'이 됩니다.

```markdown
# Agent Instructions (Master)

당신은 **3-Layer Architecture**와 **Agent Teams** 프레임워크를 기반으로 작동합니다.

## 👥 Agent Teams (Persona Switching)
복잡한 작업을 수행하기 위해 아래 전문 에이전트로 전환하여 작동하세요.
1. **Coordinator (지휘)**: 목표 설정 및 업무 배분 (`directives/agents/coordinator.md`)
2. **Researcher (수집)**: 데이터 수집 및 분석 (`directives/agents/researcher.md`)
3. **Creative (가공)**: 콘텐츠 생성 및 정제 (`directives/agents/creative.md`)
4. **Publisher (배포)**: 최종 플랫폼 발행 (`directives/agents/publisher.md`)

**필수 규칙:** 작업 단계가 바뀔 때마다 "지금부터 [Agent Name] 페르소나로 전환합니다"라고 선언하고 관련 SOP를 로드하세요.

## 🏗️ The 3-Layer Architecture
- **Layer 1 (Directive)**: `directives/` 내의 SOP 준수.
- **Layer 2 (Orchestration)**: 지능적 라우팅 및 에러 처리 (당신의 역할).
- **Layer 3 (Execution)**: `execution/` 내의 파이썬 스크립트 실행.

## 🔄 Self-annealing
에러 발생 시 즉시 스크립트를 수정하고, 다시 시도한 뒤 `Directives`를 업데이트하여 지침을 강화하세요.
```

---

## 3. 에이전트별 전용 지침서 (Persona Templates)

`directives/agents/` 폴더에 아래 형식으로 전문가들을 정의하세요.

### **[Coordinator]** (`directives/agents/coordinator.md`)
- **목표:** 사용자 요청 분석 및 단계별 `task.md` 작성.
- **역할:** 각 단계에 맞는 전문가(Researcher, Creative 등) 소환.

### **[Researcher]** (`directives/agents/researcher_agent.md`)
- **목표:** 외부 소스(웹, API, 파일)에서 데이터 추출.
- **결과물:** `.tmp/raw_data.json` 또는 CSV 생성.

### **[Creative]** (`directives/agents/creative_agent.md`)
- **목표:** 수집된 데이터를 AI로 가공/요약/번역.
- **결과물:** `.tmp/refined_content.csv` 생성.

---

## 4. 인수인계 프로토콜 (Handoff Protocol)

에이전트 팀이 성공적으로 소통하려면 아래의 **'공유 저장소 모델'**을 지켜야 합니다.

1.  **공유 폴더:** 모든 전문 에이전트는 `/tmp/project_name_data/` (또는 프로젝트 내 `.tmp/`)를 공유 메모장으로 사용합니다.
2.  **데이터 바톤:** 
    - `Researcher`가 수집을 완료하면 `raw_data.json`을 남깁니다.
    - `Creative`는 해당 파일을 읽어 작업을 수행하고 `final_report.md`를 남깁니다.
    - `Coordinator`는 최종 파일의 존재 여부를 확인하여 작업 완료를 판단합니다.

---

## 5. 시작 프롬프트 (Kick-off)

파일 세팅이 끝났다면 안티그래비티에게 아래와 같이 명령하여 프로젝트를 가동하세요.

> **"현재 폴더의 `agent.md`와 `directives/`에 정의된 에이전트 팀 시스템을 활성화해 줘. 이번 프로젝트의 목표는 [여기에 목표 입력]이야. 먼저 코디네이터 페르소나로 전환해서 전체 실행 계획(task.md)부터 세워 줘."**

---

### 💡 팁: 왜 이렇게 하나요?
- **확장성:** 새로운 역할이 필요하면 `directives/agents/new_expert.md`만 추가하면 됩니다.
- **신뢰성:** AI가 모든 걸 한 번에 하려다 실수하는 것을 방지하고, 단계별로 검증된 결과물(Layer 3)을 만들어냅니다.
- **복구력:** 에러가 나면 해당 단계의 에이전트 지침만 수정하면 파이프라인 전체가 즉시 복구됩니다.
