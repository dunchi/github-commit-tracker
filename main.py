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


class CommitFormatter:
    """Formats commit data for various output formats"""

    @staticmethod
    def clean_commit_message_line(line: str) -> str:
        """Remove pattern from commit message line: ^.*\([^)]+\):\s*"""
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

        for repo_name, repo_commit_list in repo_commits.items():
            lines.append(f"{repo_name}")
            lines.append("")

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
                for idx, body_line in enumerate(body_lines, 1):
                    lines.append(f"{idx}. {body_line}")

                lines.append("")  # Empty line after each commit

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

        github_config = config.get_github_config()
        organizations = config.get_organizations()
        usernames = config.get_usernames()
        branch_strategy = config.get_branch_strategy()
        date_range = config.get_date_range(dry_run=args.dry_run)

        print(f"Target organizations: {organizations}")
        print(f"Target usernames: {usernames}")
        print(f"Branch strategy: {branch_strategy}")
        print(f"Date range: {date_range}")

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

        if not commits:
            print("No commits found matching the criteria.")
            return

        # Sort commits (always ascending by date)
        commits = sort_commits(commits, 'asc')

        # Format output (always text format)
        formatter = CommitFormatter()
        output = formatter.format_text(commits)

        # Always output to stdout
        print(output)

    except ConfigError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()