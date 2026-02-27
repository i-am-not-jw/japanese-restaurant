# 🛰️ Notion Button Webhook Setup Guide

이 가이드는 노션의 버튼 클릭 신호를 JW님의 로컬 컴퓨터로 전달하여 파이프라인을 자동 실행하는 방법을 설명합니다.

---

## 1. 로컬 환경 준비

### 필요 라이브러리 설치
```bash
pip install flask python-dotenv
```

### 보안 토큰 설정 (`.env`)
`.env` 파일에 아래 내용을 추가하세요 (나만 아는 복잡한 문자열 추천).
```env
NOTION_WEBHOOK_SECRET=your_awesome_secret_token_123
```

### 서버 실행
```bash
python3 execution/webhook_receiver.py
```

---

## 2. 외부 노출 (ngrok 사용)

노션(클라우드)이 로컬 컴퓨터에 접근할 수 있도록 터널링을 수행합니다.

1.  [ngrok.com](https://ngrok.com/)에서 가입 후 대시보드에서 `auth token`을 확인합니다.
2.  터미널에 토큰을 설정합니다 (처음 한 번만):
    ```bash
    ngrok config add-authtoken <YOUR_AUTH_TOKEN>
    ```
3.  터널을 엽니다:
    ```bash
    ngrok http 5001
    ```
4.  터미널에 표시된 `Forwarding` 주소(예: `https://abcd-123.ngrok-free.app`)를 복사합니다.

---

## 3. 노션 버튼 설정

노션 페이지에 버튼 블록을 추가하고 다음과 같이 구성합니다.

1.  **버튼 이름**: `🚀 맛집 데이터 업데이트`
2.  **작업 추가**: `웹훅 보내기 (Send webhook)` 선택
3.  **URL**: `https://<너의-ngrok-주소>.ngrok-free.app/trigger-pipeline` 입력
4.  **헤더 추가**:
    - **Key**: `Authorization`
    - **Value**: `Bearer <너의-NOTION_WEBHOOK_SECRET>`
5.  **완료**를 누릅니다.

---

## 5. 유료 구독 없이 무료로 버튼 만들기 (Link Button 대안)

노션 무료 요금제에서는 위 '웹훅 보내기' 기능이 제한될 수 있습니다. 이 경우 아래 **'링크 열기'** 버튼을 사용하세요.

1.  노션 페이지에서 `/button`을 입력해 **버튼 블록**을 만듭니다.
2.  **작업 추가**: **'페이지 열기' 또는 '링크 열기' (Open URL)** 선택
3.  **URL**: `https://<너의-ngrok-주소>.ngrok-free.app/trigger-via-browser?token=<너의-토큰>` 입력
    - 예: `https://abcd-123.ngrok-free.app/trigger-via-browser?token=japanese_restaurant_secret_2026`
4.  **완료**를 누릅니다.

### 작동 방식
버튼을 클릭하면 브라우저 창이 잠시 열리면서 스크립트를 실행하고, 1.5초 뒤에 자동으로 창이 닫힙니다. (실질적으로 웹훅 버튼과 거의 동일한 효과를 무료로 누릴 수 있습니다!)

---

## 4. 실행 테스트

1.  로컬에서 `webhook_receiver.py`와 `ngrok`이 실행 중인지 확인합니다.
2.  노션에서 버튼을 클릭합니다.
3.  로컬 터미널에 `🚀 [Webhook] Triggering pipeline` 메시지가 뜨면 성공입니다!

---

## 💡 꿀팁: 맥이 잠들지 않게 하기 (Sleep Prevention)

현재 파이프라인은 macOS의 `caffeinate` 명령어를 사용하도록 설정되어 있습니다. 
- **작동 방식**: 버튼을 누르면 파이프라인이 실행되는 동안 맥이 '잠자기(Sleep)' 모드로 들어가는 것을 자동으로 차단합니다. 
- **주의 사항**: 
    - 버튼을 누르는 순간에는 맥이 **깨어 있는 상태**(또는 최소한 네트워크 수신이 가능한 상태)여야 합니다. 
    - 맥의 덮개를 닫아도 네트워크가 유지되도록 설정(`시스템 설정 > 디스플레이 > 고급 > 전원 어댑터 연결 시 디스플레이가 꺼져 있을 때 자동으로 잠들지 않게 하기`)해두시면 가장 좋습니다.
