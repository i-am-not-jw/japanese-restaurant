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

## 3.1 최종 승인 및 배포 버튼 설정

검토용 데이터베이스(Staging)에 쌓인 데이터를 실제 맛집 DB로 옮기고 웹 지도에 반영하기 위한 버튼입니다.

1.  **버튼 이름**: `🚀 최종 승인 및 배포`
2.  **작업 추가**: `웹훅 보내기 (Send webhook)` 선택
3.  **URL**: `https://<너의-ngrok-주소>.ngrok-free.app/finalize-sync` 입력
4.  **헤더 추가**:
    - **Key**: `Authorization`
    - **Value**: `Bearer <너의-NOTION_WEBHOOK_SECRET>`
5.  **완료**를 누릅니다.

---

## 5. 유료 구독 없이 무료로 버튼 만들기 (Link Button 대안)

노션 무료 요금제에서는 위 '웹훅 보내기' 기능이 제한될 수 있습니다. 이 경우 아래 **'링크 열기'** 버튼을 사용하세요.

1.  노션 페이지에서 `/button`을 입력해 **버튼 블록**을 만듭니다.
2.  **작업 추가**: **'페이지 열기' 또는 '링크 열기' (Open URL)** 선택
3.  **URL**: `https://<너의-ngrok-주소>.ngrok-free.app/trigger-via-browser?token=<your_random_secret_token>` 입력
    - 예: `https://abcd-123.ngrok-free.app/trigger-via-browser?token=some_very_secret_string_123`
4.  **완료**를 누릅니다.

### 작동 방식
버튼을 클릭하면 브라우저 창이 잠시 열리면서 스크립트를 실행하고, 1.5초 뒤에 자동으로 창이 닫힙니다. (실질적으로 웹훅 버튼과 거의 동일한 효과를 무료로 누릴 수 있습니다!)

---

## 4. 실행 테스트

1.  로컬에서 `webhook_receiver.py`와 `ngrok`이 실행 중인지 확인합니다.
2.  노션에서 버튼을 클릭합니다.
3.  로컬 터미널에 `🚀 [Webhook] Triggering pipeline` 메시지가 뜨면 성공입니다!

---

## 6. 재부팅 시 자동 실행 설정 (Persistence)

iMac이 재부팅되더라도 파이프라인 수집 서버와 ngrok이 자동으로 실행되도록 설정되어 있습니다.

### 설정 상세
- **자동 시작 서비스**: `com.antigravity.webhook.plist`를 통해 5분마다 상태를 체크하고, 꺼져 있으면 자동으로 재실행합니다.
- **상태 관리 스크립트**: `execution/health_check.sh`

### 수동 관리 (필요 시)
만약 서비스를 수동으로 끄거나 켜고 싶다면 아래 명령어를 사용하세요.
- **서비스 끄기**: `launchctl unload ~/Library/LaunchAgents/com.antigravity.webhook.plist`
- **서비스 켜기**: `launchctl load ~/Library/LaunchAgents/com.antigravity.webhook.plist`
- **로그 확인**: `.tmp/webhook_receiver.log` 파일에서 실행 이력을 확인할 수 있습니다.
