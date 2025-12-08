#!/usr/bin/env python3
"""
GitHub Commit Tracker
Collects commits from specified repositories and branches based on configuration
"""
import argparse
import sys
import json
import csv
import re
from datetime import datetime
from typing import List, Dict, Any

from config_parser import load_config, ConfigError
from github_client import create_github_client
from local_git_client import create_local_git_scanner
from local_log_client import create_local_log_reader


class CommitFormatter:
    """Formats commit data for various output formats"""

    @staticmethod
    def clean_commit_message_line(line: str) -> str:
        r"""Remove pattern from commit message line: ^.*\([^)]+\):\s*"""
        pattern = r'^.*\([^)]+\):\s*'
        return re.sub(pattern, '', line.strip())

    @staticmethod
    def format_text(commits: List[Dict[str, Any]]) -> str:
        """Format commits as readable text grouped by repository"""
        if not commits:
            return "No commits found."

        # Group commits by repository
        repo_commits = {}
        for commit in commits:
            repo_name = commit['repository'].split('/')[-1]  # Get just the repo name
            if repo_name not in repo_commits:
                repo_commits[repo_name] = []
            repo_commits[repo_name].append(commit)

        lines = []

        for idx, (repo_name, repo_commit_list) in enumerate(repo_commits.items()):
            # Add blank line before repository name (except for first repo)
            if idx > 0:
                lines.append("")

            lines.append(f"{repo_name}")

            for i, commit in enumerate(repo_commit_list, 1):
                # Parse commit message: first line = title, rest = body
                message_lines = commit['message'].strip().split('\n')
                title = message_lines[0]
                body_lines = []

                # Process body lines (skip empty lines, clean pattern from items)
                for line in message_lines[1:]:
                    line = line.strip()
                    if line and line.startswith('*'):
                        # Remove pattern and line breaks within the item
                        clean_line = CommitFormatter.clean_commit_message_line(line)
                        if clean_line:  # Only add if there's content after cleaning
                            body_lines.append(clean_line)

                # Format title as plain text (no markdown link)
                lines.append(f"- {title}")

                # Add cleaned body items
                for body_idx, body_line in enumerate(body_lines, 1):
                    lines.append(f"{body_idx}. {body_line}")

        return "\n".join(lines)

    @staticmethod
    def format_json(commits: List[Dict[str, Any]]) -> str:
        """Format commits as JSON"""
        # Convert datetime objects to strings for JSON serialization
        serializable_commits = []
        for commit in commits:
            commit_copy = commit.copy()
            commit_copy['date'] = commit['date'].isoformat()
            serializable_commits.append(commit_copy)

        return json.dumps(serializable_commits, indent=2, ensure_ascii=False)

    @staticmethod
    def format_csv(commits: List[Dict[str, Any]]) -> str:
        """Format commits as CSV"""
        if not commits:
            return ""

        import io
        output = io.StringIO()
        fieldnames = ['date', 'repository', 'branch', 'author_name', 'author_email', 'sha', 'message', 'url']
        writer = csv.DictWriter(output, fieldnames=fieldnames)

        writer.writeheader()
        for commit in commits:
            row = commit.copy()
            row['date'] = commit['date'].isoformat()
            writer.writerow(row)

        return output.getvalue()


def sort_commits(commits: List[Dict[str, Any]], sort_order: str) -> List[Dict[str, Any]]:
    """Sort commits by date"""
    reverse = sort_order.lower() == 'desc'
    return sorted(commits, key=lambda x: x['date'], reverse=reverse)


def deduplicate_commits_by_sha(commits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """SHA 기반으로 중복 커밋 제거
    
    동일 SHA는 1개만 유지:
    - 로컬과 GitHub에 같은 SHA가 있으면 로컬 우선
      (로컬이 더 상세한 정보를 가질 수 있음)
    - 같은 소스에서 중복되면 첫 번째만 유지
    
    Args:
        commits: GitHub + 로컬에서 수집한 전체 커밋 리스트
    
    Returns:
        SHA 중복이 제거된 커밋 리스트
    """
    seen_shas = {}
    result = []
    
    for commit in commits:
        sha = commit['sha']
        
        if sha not in seen_shas:
            # 처음 보는 SHA
            seen_shas[sha] = commit
            result.append(commit)
        else:
            # 이미 존재하는 SHA
            existing = seen_shas[sha]
            
            # 로컬 > GitHub 우선순위
            current_source = commit.get('source', 'github')
            existing_source = existing.get('source', 'github')
            
            if current_source == 'local' and existing_source == 'github':
                # GitHub 것을 로컬 것으로 교체
                result.remove(existing)
                result.append(commit)
                seen_shas[sha] = commit
            # else: 이미 로컬이거나, 같은 소스면 첫 번째 유지
    
    return result


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='GitHub Commit Tracker')
    parser.add_argument('--config', '-c', default='config.yaml',
                       help='Configuration file path (default: config.yaml)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show configuration without fetching commits')

    args = parser.parse_args()

    try:
        # Load configuration
        print(f"Loading configuration from: {args.config}")
        config = load_config(args.config)

        # Get mode
        mode = config.get_mode()
        print(f"Mode: {mode}")

        usernames = config.get_usernames()
        date_range = config.get_date_range(dry_run=args.dry_run)

        print(f"Target usernames: {usernames}")
        print(f"Date range: {date_range}")

        scanned_repo_paths = []  # Store scanned repository paths
        repos_with_commits = []  # Store paths with actual commits

        if mode == 'local_log':
            # Local log mode (reads from ~/.git-commit-logs/)
            local_log_config = config.get_local_log_config()
            log_dir = local_log_config.get('log_dir', '~/.git-commit-logs')

            print(f"Log directory: {log_dir}")

            if args.dry_run:
                print("Dry run mode - configuration validation complete.")
                return

            # Create local log reader
            print("Reading local commit logs...")
            reader = create_local_log_reader(
                log_dir=log_dir,
                from_date=date_range['from'],
                to_date=date_range['to']
            )

            # Collect commits
            commits = reader.read_commits()
            print(f"Found {len(commits)} commits from local logs")

        elif mode == 'github':
            # GitHub mode
            github_config = config.get_github_config()
            organizations = config.get_organizations()
            branch_strategy = config.get_branch_strategy()

            print(f"Target organizations: {organizations}")
            print(f"Branch strategy: {branch_strategy}")

            if args.dry_run:
                print("Dry run mode - configuration validation complete.")
                return

            # Create GitHub client
            print("Connecting to GitHub API...")
            github_client = create_github_client(
                token=github_config['token'],
                usernames=usernames,
                from_date=date_range['from'],
                to_date=date_range['to']
            )

            # Collect commits
            print("Collecting commits...")
            commits = github_client.get_commits_from_organizations(organizations, branch_strategy)

        elif mode == 'local_git':
            # Local Git mode
            local_git_config = config.get_local_git_config()
            base_paths = local_git_config.get('base_paths', [])
            repositories = local_git_config.get('repositories', [])

            print(f"Base paths: {base_paths}")
            print(f"Repositories: {repositories}")

            if args.dry_run:
                print("Dry run mode - configuration validation complete.")
                return

            # Create local Git scanner
            print("Scanning local repositories...")
            scanner = create_local_git_scanner(
                usernames=usernames,
                from_date=date_range['from'],
                to_date=date_range['to']
            )

            # Collect commits
            print("Collecting commits...")
            commits, scanned_repo_paths, repos_with_commits = scanner.scan_repositories(base_paths=base_paths, repositories=repositories)

        elif mode == 'hybrid':
            # Hybrid mode: GitHub + Local Git
            github_config = config.get_github_config()
            organizations = config.get_organizations()
            branch_strategy = config.get_branch_strategy()

            local_git_config = config.get_local_git_config()
            base_paths = local_git_config.get('base_paths', [])
            repositories = local_git_config.get('repositories', [])

            print(f"Target organizations: {organizations}")
            print(f"Branch strategy: {branch_strategy}")
            print(f"Base paths: {base_paths}")
            print(f"Repositories: {repositories}")

            if args.dry_run:
                print("Dry run mode - configuration validation complete.")
                return

            # Collect from GitHub
            print("Connecting to GitHub API...")
            github_client = create_github_client(
                token=github_config['token'],
                usernames=usernames,
                from_date=date_range['from'],
                to_date=date_range['to']
            )
            print("Collecting commits from GitHub...")
            github_commits = github_client.get_commits_from_organizations(organizations, branch_strategy)

            # Collect from local repositories
            print("Scanning local repositories...")
            scanner = create_local_git_scanner(
                usernames=usernames,
                from_date=date_range['from'],
                to_date=date_range['to']
            )
            print("Collecting commits from local...")
            local_commits, scanned_repo_paths, repos_with_commits = scanner.scan_repositories(base_paths=base_paths, repositories=repositories)

            # Merge and deduplicate
            print("Merging and deduplicating commits...")
            all_commits = github_commits + local_commits
            commits = deduplicate_commits_by_sha(all_commits)

            # Print statistics
            github_count = sum(1 for c in commits if c.get('source') == 'github')
            local_count = sum(1 for c in commits if c.get('source') == 'local')
            print(f"GitHub 커밋: {github_count}개")
            print(f"로컬 커밋: {local_count}개")
            print(f"총 커밋: {len(commits)}개 (중복 제거 완료)")

        else:
            raise ConfigError(f"Unknown mode: {mode}")

        if not commits:
            print("No commits found matching the criteria.")
            return

        # Sort commits (always descending by date - newest first)
        commits = sort_commits(commits, 'desc')

        # Format output (always text format)
        formatter = CommitFormatter()
        output = formatter.format_text(commits)

        # Print separator and output
        print("\n" + "=" * 50)
        print("결과")
        print("=" * 50 + "\n")
        
        # Print scanned repository paths for local_git and hybrid mode with colored O/X markers
        if mode in ['local_git', 'hybrid'] and scanned_repo_paths:
            print("스캔한 로컬 레포지토리:")
            repos_with_commits_set = set(repos_with_commits)
            for repo_path in sorted(scanned_repo_paths):
                marker = "✅" if repo_path in repos_with_commits_set else "❌"
                print(f"  {marker} {repo_path}")
            print()
        
        print(output)

    except ConfigError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()