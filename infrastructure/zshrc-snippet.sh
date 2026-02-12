# pnpm wrapper: install 후 husky 프로젝트면 post-commit 훅 자동 복구
pnpm() {
    command pnpm "$@"
    local exit_code=$?
    if [[ "$1" == "install" || "$1" == "i" ]]; then
        ~/.git-hooks/restore-husky-hook.sh 2>/dev/null
    fi
    return $exit_code
}
