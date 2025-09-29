# GitHub Commit Tracker

GitHub 조직 내 레포지토리에서 커밋들을 수집하여 깔끔하게 정리해주는 도구입니다.

## ✨ 주요 기능

- 🏢 **조직 단위 수집**: GitHub 조직의 모든 레포지토리를 자동 스캔
- 👥 **다중 사용자 지원**: 여러 사용자의 커밋을 한 번에 수집
- 🌿 **유연한 브랜치 선택**: 3가지 브랜치 전략 지원 (all/specific/priority)
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

### 2. 설정
```bash
# 설정 파일 복사
cp config.yaml.example config.yaml

# 설정 파일 편집
nano config.yaml
```

### 3. GitHub 토큰 설정
1. GitHub → Settings → Developer settings → Personal access tokens
2. "Generate new token" 클릭
3. 필요한 권한 선택: `repo`, `read:org`
4. 생성된 토큰을 `config.yaml`의 `token`에 입력

### 4. 실행
```bash
# 설정 검증
python main.py --dry-run

# 실제 실행
python main.py
```

## ⚙️ 설정 옵션

### 브랜치 선택 전략

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

### 날짜 범위 설정

```yaml
date_range:
  from: ""          # 빈값: 어제부터 (주말이면 금요일부터 선택 가능)
  to: ""            # 빈값: 지금까지
  # from: "2024-01-01"  # 특정 날짜부터
  # to: "2024-01-31"    # 특정 날짜까지
```

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

### 환경변수 사용
```bash
# 토큰을 환경변수로 설정
export GITHUB_TOKEN="your_token_here"

# config.yaml에서 환경변수 참조
token: "${GITHUB_TOKEN}"
```

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

**Q: "Configuration error: GitHub token is required"**
A: `config.yaml`에 올바른 GitHub 토큰을 설정했는지 확인하세요.

**Q: "Error accessing organization"**
A: 조직에 접근 권한이 있는지, 조직명이 정확한지 확인하세요.

**Q: "No commits found"**
A: 날짜 범위나 사용자명 설정을 확인하세요.

### 디버깅

```bash
# 자세한 처리 과정 확인
python main.py --dry-run

# 특정 설정 파일로 테스트
python main.py --config test-config.yaml --dry-run
```

## 📋 요구사항

- Python 3.8+
- GitHub Personal Access Token
- 인터넷 연결

## 🤝 기여하기

버그 리포트나 기능 제안은 Issues를 통해 알려주세요.

## 📄 라이선스

MIT License