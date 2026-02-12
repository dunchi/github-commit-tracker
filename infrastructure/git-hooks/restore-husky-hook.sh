#!/bin/bash
# Husky 프로젝트에서 post-commit 훅 자동 복구 스크립트
# 로컬 커밋 로깅을 위해 .husky/post-commit을 자동 생성

BISEO_DIR="/Users/hanju/01dev/01nicemso/biseo"
GLOBAL_POST_COMMIT="$HOME/.git-hooks/post-commit"

restore_husky_hook() {
    local project_dir="$1"
    local husky_dir="$project_dir/.husky"
    local post_commit="$husky_dir/post-commit"
    local git_exclude="$project_dir/.git/info/exclude"

    # .husky 디렉토리가 없으면 husky 프로젝트 아님
    [[ ! -d "$husky_dir" ]] && return 0

    # .husky/post-commit 덮어쓰기 (항상 최신 상태 보장)
    echo "$GLOBAL_POST_COMMIT" > "$post_commit"
    chmod +x "$post_commit"

    # .git/info/exclude에 추가 (중복 방지)
    if [[ -f "$git_exclude" ]] && ! grep -q "^.husky/post-commit$" "$git_exclude" 2>/dev/null; then
        echo ".husky/post-commit" >> "$git_exclude"
    fi
}

# 현재 디렉토리가 husky 프로젝트면 복구 (pnpm install 후 호출용)
if [[ -d ".husky" ]]; then
    restore_husky_hook "$(pwd)"
fi

# biseo-client* 프로젝트들 스캔 (cron용)
if [[ "$1" == "--scan" ]]; then
    for dir in "$BISEO_DIR"/biseo-client*/; do
        [[ -d "$dir" ]] && restore_husky_hook "$dir"
    done
fi
