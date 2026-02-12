# Git Commit 추적 인프라

로컬에서 발생하는 모든 git commit을 `~/.git-commit-logs/YYYY-MM-DD.log`에 자동 기록하는 인프라.

## 문제 상황

일부 프로젝트(예: biseo-client)에서 **Husky**를 사용하면 전역 git hook이 무시된다.
- Husky가 `core.hooksPath`를 `.husky/_`로 덮어씀
- 전역 `~/.git-hooks/post-commit`이 실행되지 않음
- 커밋 로그가 누락됨

## 해결책

Husky 프로젝트에 `.husky/post-commit` 파일을 자동 생성하여 전역 훅을 호출하도록 함.

## 파일 구성

```
infrastructure/
├── git-hooks/
│   ├── post-commit              # 전역 post-commit 훅 (커밋 로그 기록)
│   └── restore-husky-hook.sh    # Husky 프로젝트 자동 복구 스크립트
├── launchd/
│   └── com.hanju.restore-husky-hook.plist  # 5분마다 자동 실행
├── zshrc-snippet.sh             # ~/.zshrc에 추가할 코드
└── README.md
```

## 설치 방법

### 1. 전역 Git Hook 설정

```bash
# 디렉토리 생성
mkdir -p ~/.git-hooks

# 파일 복사
cp git-hooks/post-commit ~/.git-hooks/
cp git-hooks/restore-husky-hook.sh ~/.git-hooks/

# 실행 권한 부여
chmod +x ~/.git-hooks/post-commit
chmod +x ~/.git-hooks/restore-husky-hook.sh

# Git 전역 hook 경로 설정
git config --global core.hooksPath ~/.git-hooks
```

### 2. 로그 디렉토리 생성

```bash
mkdir -p ~/.git-commit-logs
```

### 3. launchd 설정 (5분마다 자동 복구)

```bash
# plist 파일 복사
cp launchd/com.hanju.restore-husky-hook.plist ~/Library/LaunchAgents/

# 경로 수정 (사용자명이 다르면 plist 파일 내 경로 수정 필요)
# vi ~/Library/LaunchAgents/com.hanju.restore-husky-hook.plist

# launchd에 등록
launchctl load ~/Library/LaunchAgents/com.hanju.restore-husky-hook.plist

# 확인
launchctl list | grep husky
```

### 4. zshrc 설정 (pnpm install 후 자동 복구)

```bash
# ~/.zshrc 끝에 추가
cat zshrc-snippet.sh >> ~/.zshrc

# 적용
source ~/.zshrc
```

### 5. 즉시 적용

```bash
~/.git-hooks/restore-husky-hook.sh --scan
```

## 작동 원리

### 전역 post-commit 훅

```
git commit 실행
    ↓
~/.git-hooks/post-commit 실행
    ↓
~/.git-commit-logs/2026-02-12.log 에 기록
    ↓
[14:17:21] biseo-client (feat/1327) 498806e7 - feat: 기능 추가
```

### Husky 프로젝트 자동 복구

```
pnpm install 실행 또는 5분마다
    ↓
restore-husky-hook.sh 실행
    ↓
biseo-client* 프로젝트 스캔
    ↓
.husky/post-commit 없으면 생성
.git/info/exclude에 등록 (git에 안 올라감)
```

## 설정 커스터마이징

### 스캔 대상 경로 변경

`restore-husky-hook.sh` 파일의 `BISEO_DIR` 변수 수정:

```bash
BISEO_DIR="/Users/hanju/01dev/01nicemso/biseo"
```

### 스캔 주기 변경

`com.hanju.restore-husky-hook.plist` 파일의 `StartInterval` 수정:

```xml
<key>StartInterval</key>
<integer>300</integer>  <!-- 300초 = 5분 -->
```

## 트러블슈팅

### launchd가 실행 안 될 때

```bash
# 상태 확인
launchctl list | grep husky

# 로그 확인
cat ~/.git-hooks/restore-husky-hook.log

# 재등록
launchctl unload ~/Library/LaunchAgents/com.hanju.restore-husky-hook.plist
launchctl load ~/Library/LaunchAgents/com.hanju.restore-husky-hook.plist
```

### 수동으로 복구 실행

```bash
~/.git-hooks/restore-husky-hook.sh --scan
```

### 특정 프로젝트에서 로그 안 남을 때

```bash
# 해당 프로젝트의 core.hooksPath 확인
cd /path/to/project
git config --local core.hooksPath

# .husky/post-commit 존재 여부 확인
cat .husky/post-commit
```

## 관련 파일 위치 (설치 후)

| 파일 | 위치 |
|------|------|
| 전역 post-commit | `~/.git-hooks/post-commit` |
| 복구 스크립트 | `~/.git-hooks/restore-husky-hook.sh` |
| launchd 설정 | `~/Library/LaunchAgents/com.hanju.restore-husky-hook.plist` |
| 커밋 로그 | `~/.git-commit-logs/YYYY-MM-DD.log` |
| 복구 로그 | `~/.git-hooks/restore-husky-hook.log` |
