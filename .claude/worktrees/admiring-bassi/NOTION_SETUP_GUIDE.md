# 📔 노션(Notion) API 연동 가이드

이 가이드는 Antigravity가 자동으로 수집한 리포트를 여러분의 노션에 빈틈없이 업로드할 수 있도록 API를 설정하는 방법을 설명합니다.

---

### Step 1: 노션 API 통합(Integration) 생성하기
1. [노션 내 통합(My Integrations)](https://www.notion.so/my-integrations) 페이지에 접속합니다.
2. **`+ 새 통합`** 버튼을 클릭합니다.
3. 관련 정보를 입력합니다:
   - **이름**: `Antigravity Reporter` (원하는 이름 가능)
   - **워크스페이스**: 리포트를 올릴 워크스페이스 선택
4. 설정을 완료하고 **`제출`**을 누르면 **"내부 통합 토큰(Internal Integration Secret)"**이 생성됩니다.
5. 이 토큰을 복사해서 따로 저장해 두세요. (나중에 `.env` 파일에 기록합니다.)

### Step 2: 리포트를 받을 페이지/데이터베이스 준비 및 권한 부여
1. 리포트가 쌓일 **새 페이지** 또는 **데이터베이스**를 노션에 만드세요.
2. 해당 페이지 우측 상단의 **`점 세 개(...)`** 버튼을 누릅니다.
3. 맨 아래의 **`연결 추가(Add connections)`**를 클릭합니다.
4. 방금 만든 통합(`Antigravity Reporter`)을 검색하여 선택하고 **`확인`**을 누릅니다.
   - *이 단계를 누락하면 Antigravity가 해당 페이지에 접근할 수 없습니다.*

### Step 3: 페이지/데이터베이스 ID 확인하기
1. 해당 노션 페이지의 URL 주소를 확인합니다.
2. `https://www.notion.so/myusername/` 뒤에 오는 **32자리 영문/숫자 조합**이 ID입니다.
   - 예: `https://www.notion.so/workspace/8b72...` 이면 `8b72...` 부분이 ID입니다.
   - 데이터베이스인 경우 `?v=` 앞부분까지가 ID입니다.

---

### Step 4: Antigravity에게 정보 전달하기
위 과정에서 준비된 두 가지 정보를 저에게 알려주세요:
1. **내부 통합 토큰** (secret_...)
2. **일본 맛집 데이터베이스 ID** (기존 NOTION_DATABASE_ID 대신 **NOTION_JAPAN_RESTAURANT_DB_ID**로 사용됩니다.)

알려주시면 바로 리포트 전송 로직을 완성해 드릴게요! 🚀
