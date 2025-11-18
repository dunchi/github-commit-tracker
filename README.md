# GitHub Commit Tracker

GitHub 조직 또는 로컬 Git 레포지토리에서 커밋들을 수집하여 깔끔하게 정리해주는 도구입니다.

## ✨ 주요 기능

- 🔄 **두 가지 모드**: GitHub API 또는 로컬 Git 레포지토리 스캔
- 🏢 **조직 단위 수집**: GitHub 조직의 모든 레포지토리를 자동 스캔
- 💻 **로컬 레포 스캔**: Push 안 한 커밋도 포함하여 로컬 레포지토리 스캔
- 👥 **다중 사용자 지원**: 여러 사용자의 커밋을 한 번에 수집
- 🌿 **유연한 브랜치 선택**: 3가지 브랜치 전략 지원 (all/specific/priority)
- 🔗 **SHA 기반 중복 제거**: 여러 브랜치에 같은 커밋이 있어도 한 번만 출력
- 📅 **스마트 날짜 범위**: 주말 감지 및 자동 조정 기능
- 📝 **깔끔한 출력**: 레포지토리별 그룹화 및 메시지 정리

## 🚀 빠른 시작

### 1. 설치
```bash
# 프로젝트 클론
git clone <repository-url>
cd github-commit-tracker

# 의존성 설치
pip install -r requirements.txt
```

### 2. GitHub 토큰 설정
1. GitHub → Settings → Developer settings → Personal access tokens
2. "Generate new token" 클릭
3. 필요한 권한 선택: `repo`, `read:org`
4. **환경변수로 토큰 설정** (필수):
   ```bash
   export GITHUB_TOKEN="your_github_token_here"
   ```

   **영구적으로 설정하려면** shell profile에 추가:
   ```bash
   # ~/.bashrc 또는 ~/.zshrc에 추가
   echo 'export GITHUB_TOKEN="your_github_token_here"' >> ~/.bashrc
   source ~/.bashrc
   ```

### 3. 설정 파일 편집
```bash
# config.yaml 파일 편집 (저장소에 이미 포함됨)
nano config.yaml
```
- `organizations`: 수집할 GitHub 조직명
- `usernames`: 필터링할 사용자 이름들
- `branch_strategy`: 브랜치 수집 전략
- `local_git`: 로컬 Git 레포지토리 경로 (선택사항)

### 4. 실행
```bash
# 설정 검증
python main.py --dry-run

# 실제 실행
python main.py
```

**⚠️ 주의**: `GITHUB_TOKEN` 환경변수가 설정되지 않으면 다음과 같은 에러가 발생합니다:
```
Environment variable 'GITHUB_TOKEN' is not set.
Please set it before running:
  export GITHUB_TOKEN="your_github_token_here"
Or add it to your shell profile (~/.bashrc, ~/.zshrc, etc.)
```

## ⚙️ 설정 옵션

### 모드 선택

두 가지 모드 중 하나를 선택할 수 있습니다 (`enabled: true`로 설정):

#### GitHub API 모드
```yaml
github:
  enabled: true
  token: "${GITHUB_TOKEN}"  # 환경변수 사용
  organizations: ["your_organization"]
  usernames: ["user1", "user2"]
```
- GitHub 조직의 원격 레포지토리에서 커밋 수집
- GitHub Personal Access Token 필요 (환경변수로 설정)
- Push된 커밋만 수집 가능

#### 로컬 Git 모드 (신규!)
```yaml
local_git:
  enabled: true
  base_paths:  # 방법 1: 디렉토리 자동 스캔
    - "/home/user/workspace"
    - "/home/user/projects"
  # repositories:  # 방법 2: 특정 레포 직접 지정
  #   - "/home/user/workspace/project-1"
  #   - "/home/user/workspace/project-2"
  usernames: ["user1", "user2"]  # git config user.name과 일치해야 함
```
- 로컬 Git 레포지토리에서 직접 커밋 수집
- **Push 안 한 커밋도 포함** (로컬에만 있는 커밋)
- **모든 브랜치 자동 스캔** (feat/*, hotfix/* 등)
- **SHA 기반 중복 제거** (merge 후에도 중복 없음)
- GitHub 토큰 불필요

### 브랜치 선택 전략 (GitHub 모드 전용)

#### `all` - 모든 브랜치
```yaml
branch_strategy:
  mode: "all"
```
모든 존재하는 브랜치에서 커밋 수집 (중복 허용)

#### `specific` - 지정 브랜치
```yaml
branch_strategy:
  mode: "specific"
  branches: ["main", "develop", "feature/specific"]
```
지정된 브랜치들에서만 수집

#### `priority` - 우선순위 (추천)
```yaml
branch_strategy:
  mode: "priority"
  branches: ["main", "master", "develop"]
```
우선순위 순서로 첫 번째 존재하는 브랜치만 선택 (중복 제거)

### 날짜 범위 설정 (공통)

```yaml
date_range:
  from: ""          # 빈값: 어제부터 (주말이면 금요일부터 선택 가능)
  to: ""            # 빈값: 지금까지
  # from: "2024-01-01"         # 특정 날짜부터
  # from: "2024-01-01 09:00"   # 날짜 + 시간
  # from: "07:00"              # 시간만 (어제 07:00부터)
  # to: "2024-01-31"           # 특정 날짜까지
  # to: "2024-01-31 18:00"     # 날짜 + 시간까지
  # to: "07:00"                # 시간만 (오늘 07:00까지)
```

**시간 형식 지원**:
- `YYYY-MM-DD`: 날짜만 지정
- `YYYY-MM-DD HH:MM`: 날짜와 시간 지정
- `HH:MM`: 시간만 지정 (from: 어제 HH:MM, to: 오늘 HH:MM)

**예시**: `from: "07:00"`, `to: "07:00"` → 어제 07:00부터 오늘 07:00까지

## 📄 출력 형식

```
repository-name

1.
feat: 새로운 기능 추가 (#123)
사용자 인증 로직 구현
API 연동 기능 추가
테스트 코드 작성

2.
fix: 버그 수정 (#124)
로그인 오류 해결

3.
refactor: 코드 리팩토링 (#125)
```

## 🔧 고급 사용법

### 다른 PC에서 사용하기

1. **저장소 클론**:
   ```bash
   git clone <repository-url>
   cd github-commit-tracker
   pip install -r requirements.txt
   ```

2. **GitHub 토큰 설정** (한 번만):
   ```bash
   export GITHUB_TOKEN="your_github_token_here"

   # 영구 설정
   echo 'export GITHUB_TOKEN="your_github_token_here"' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **바로 실행**:
   ```bash
   python main.py
   ```

`config.yaml` 파일은 이미 저장소에 포함되어 있으며, 토큰은 환경변수로 참조합니다.

### 스케줄링 (cron)
```bash
# 매일 오전 9시에 실행
0 9 * * * cd /path/to/github-commit-tracker && python main.py > daily-commits.txt
```

### 설정 파일 검증
```bash
# 설정만 확인하고 API 호출 안함
python main.py --dry-run
```

## 🛠️ 문제해결

### 일반적인 문제들

**Q: "Configuration error: Either github.enabled or local_git.enabled must be true"**
A: `config.yaml`에서 `github.enabled: true` 또는 `local_git.enabled: true` 중 하나를 설정하세요.

**Q: "Configuration error: GitHub token is required" 또는 "Environment variable 'GITHUB_TOKEN' is not set"**
A: `GITHUB_TOKEN` 환경변수를 설정하세요:
```bash
export GITHUB_TOKEN="your_github_token_here"
```

**Q: "Error accessing organization"**
A: 조직에 접근 권한이 있는지, 조직명이 정확한지 확인하세요.

**Q: "No commits found"**
A: 날짜 범위나 사용자명 설정을 확인하세요. 로컬 Git 모드에서는 `git config user.name`과 일치하는 이름을 사용하세요.

**Q: "Warning: Not a valid Git repository"**
A: 로컬 Git 모드에서 지정한 경로에 `.git` 디렉토리가 있는지 확인하세요.

### 디버깅

```bash
# 자세한 처리 과정 확인
python main.py --dry-run

# 특정 설정 파일로 테스트
python main.py --config test-config.yaml --dry-run
```

## 📋 요구사항

- Python 3.8+
- GitHub Personal Access Token (GitHub 모드 사용 시)
- 인터넷 연결 (GitHub 모드 사용 시)

## 🆕 최근 업데이트

### v2.0 - 로컬 Git 모드 추가
- ✅ 로컬 Git 레포지토리 직접 스캔 기능
- ✅ Push 안 한 커밋도 수집 가능
- ✅ SHA 기반 중복 제거 (merge 후에도 중복 없음)
- ✅ 모든 브랜치 자동 스캔
- ✅ 두 가지 경로 지정 방식 (base_paths/repositories)

## 🤝 기여하기

버그 리포트나 기능 제안은 Issues를 통해 알려주세요.

## 📄 라이선스

MIT License