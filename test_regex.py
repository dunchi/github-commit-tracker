#!/usr/bin/env python3
"""
정규식 패턴 테스트 스크립트
test-data.txt 파일의 커밋 메시지에서 패턴을 제거하여 결과를 출력합니다.

패턴: 임의의 글자 + (괄호 안 글자) + ': '
예: '* feat(types): 유저정보 타입 추가' → '유저정보 타입 추가'
"""

import re
import os


def clean_commit_message_line(line: str) -> str:
    """
    커밋 메시지 라인에서 패턴을 제거합니다.

    패턴: ^.*\([^)]+\):\s*
    - ^.*        : 줄 시작부터 임의의 문자들
    - \([^)]+\)  : 괄호로 둘러싸인 내용 (괄호 안에 최소 1글자)
    - :\s*       : 콜론 + 0개 이상의 공백
    """
    pattern = r'^.*\([^)]+\):\s*'
    cleaned = re.sub(pattern, '', line.strip())
    return cleaned


def process_test_data():
    """test-data.txt 파일을 읽어서 패턴 치환 결과를 출력"""

    test_file = 'test-data.txt'

    if not os.path.exists(test_file):
        print(f"❌ {test_file} 파일이 존재하지 않습니다.")
        return

    print("🔍 정규식 패턴 테스트")
    print("=" * 80)
    print("패턴: ^.*\\([^)]+\\):\\s*")
    print("설명: 줄 시작 ~ (괄호내용): 까지 제거")
    print("=" * 80)

    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        print(f"📁 {test_file} 파일에서 {len(lines)}개 라인 처리 중...")
        print()

        for i, line in enumerate(lines, 1):
            line = line.rstrip('\n')

            # 빈 줄이나 주석은 스킵
            if not line.strip() or line.strip().startswith('#'):
                continue

            original = line
            cleaned = clean_commit_message_line(line)

            print(f"[{i:2d}] 원본  : {original}")
            print(f"     결과  : {cleaned}")

            # 변경사항이 있었는지 표시
            if original.strip() != cleaned:
                print("     상태  : ✅ 변경됨")
            else:
                print("     상태  : ⚪ 변경없음")
            print()

    except Exception as e:
        print(f"❌ 파일 처리 중 오류: {e}")


def test_sample_patterns():
    """샘플 패턴들로 테스트"""

    print("\n🧪 샘플 패턴 테스트")
    print("=" * 80)

    test_cases = [
        "* feat(types): 유저정보 타입 추가",
        "* feat(mocks): 유저정보 목업 추가",
        "* refactor(components): 코드 정리",
        "* fix(api): 버그 수정",
        "일반 텍스트",
        "* 괄호가 없는 메시지",
        "* feat(): 빈 괄호",
        "* feat(very-long-scope-name): 긴 스코프명",
    ]

    for i, test_case in enumerate(test_cases, 1):
        result = clean_commit_message_line(test_case)
        print(f"[{i}] '{test_case}' → '{result}'")


if __name__ == "__main__":
    print("🚀 커밋 메시지 패턴 제거 테스트")
    print()

    # 먼저 샘플 테스트 실행
    test_sample_patterns()

    # test-data.txt 파일 처리
    process_test_data()

    print("\n✅ 테스트 완료")