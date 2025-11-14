"""
Local Git repository scanner for commit tracking
"""
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import git
from git.exc import InvalidGitRepositoryError, GitCommandError


class LocalGitScanner:
    """Local Git repository scanner for tracking commits"""

    def __init__(self, usernames: List[str], from_date: Optional[datetime] = None, to_date: Optional[datetime] = None):
        self.usernames = usernames
        self.from_date = from_date
        self.to_date = to_date
        self.seen_shas: Set[str] = set()  # SHA 기반 중복 제거

    def scan_repositories(self, base_paths: Optional[List[str]] = None,
                         repositories: Optional[List[str]] = None) -> tuple[List[Dict[str, Any]], List[str], List[str]]:
        """Scan multiple repositories and collect commits

        Args:
            base_paths: List of base directories to scan for Git repositories
            repositories: List of specific repository paths

        Returns:
            Tuple of (list of commit data dictionaries, list of scanned repository paths, list of paths with commits)
        """
        all_commits = []
        repo_paths = []
        repos_with_commits = []

        # Collect repository paths from base_paths
        if base_paths:
            for base_path in base_paths:
                base_path = os.path.expanduser(base_path)
                if os.path.exists(base_path):
                    repo_paths.extend(self._discover_repositories(base_path))
                else:
                    print(f"Warning: Base path does not exist: {base_path}")

        # Add specific repository paths
        if repositories:
            for repo_path in repositories:
                repo_path = os.path.expanduser(repo_path)
                if os.path.exists(repo_path):
                    repo_paths.append(repo_path)
                else:
                    print(f"Warning: Repository path does not exist: {repo_path}")

        # Remove duplicates
        repo_paths = list(set(repo_paths))

        print(f"Found {len(repo_paths)} repositories to scan")

        # Scan each repository
        for repo_path in repo_paths:
            print(f"Scanning repository: {repo_path}")
            commits = self.scan_single_repository(repo_path)
            if commits:  # Only add to repos_with_commits if commits were found
                repos_with_commits.append(repo_path)
            all_commits.extend(commits)
            print(f"  Found {len(commits)} commits")

        return all_commits, repo_paths, repos_with_commits

    def _discover_repositories(self, base_path: str) -> List[str]:
        """Discover Git repositories in a base directory

        Args:
            base_path: Directory to search for Git repositories

        Returns:
            List of repository paths
        """
        repo_paths = []
        base_path_obj = Path(base_path)

        # Check if base_path itself is a Git repository
        if (base_path_obj / '.git').exists():
            repo_paths.append(str(base_path_obj))
            return repo_paths

        # Search for Git repositories in subdirectories
        try:
            for item in base_path_obj.iterdir():
                if item.is_dir():
                    # Check if it's a Git repository
                    if (item / '.git').exists():
                        repo_paths.append(str(item))
        except PermissionError:
            print(f"Warning: Permission denied accessing {base_path}")

        return repo_paths

    def scan_single_repository(self, repo_path: str) -> List[Dict[str, Any]]:
        """Scan a single Git repository for commits

        Args:
            repo_path: Path to the Git repository

        Returns:
            List of commit data dictionaries
        """
        commits = []

        try:
            repo = git.Repo(repo_path)
        except InvalidGitRepositoryError:
            print(f"  Warning: Not a valid Git repository: {repo_path}")
            return commits
        except Exception as e:
            print(f"  Error accessing repository {repo_path}: {e}")
            return commits

        # Get repository name (last part of path)
        repo_name = os.path.basename(repo_path)

        # Get all branches
        try:
            branches = [ref.name for ref in repo.references if isinstance(ref, git.Head)]
        except Exception as e:
            print(f"  Error getting branches: {e}")
            branches = []

        print(f"  Branches: {', '.join(branches)}")

        # Scan each branch
        for branch_name in branches:
            try:
                branch_commits = self._get_commits_from_branch(repo, branch_name, repo_name)
                commits.extend(branch_commits)
            except Exception as e:
                print(f"  Error scanning branch {branch_name}: {e}")

        return commits

    def _get_commits_from_branch(self, repo: git.Repo, branch_name: str, repo_name: str) -> List[Dict[str, Any]]:
        """Get commits from a specific branch

        Args:
            repo: Git repository object
            branch_name: Branch name
            repo_name: Repository name for metadata

        Returns:
            List of commit data dictionaries
        """
        commits = []

        try:
            # Iterate through commits in the branch
            for commit in repo.iter_commits(branch_name):
                # Check if already processed (SHA-based deduplication)
                if commit.hexsha in self.seen_shas:
                    continue

                # Check if commit is by specified user
                if not self._is_user_commit(commit):
                    continue

                # Check date range
                # Convert to KST timezone for comparison
                kst = timezone(timedelta(hours=9))
                commit_date = datetime.fromtimestamp(commit.authored_date, tz=kst)
                if self.from_date and commit_date < self.from_date:
                    continue
                if self.to_date and commit_date > self.to_date:
                    continue

                # Extract commit data
                commit_data = self._extract_commit_data(commit, repo_name, branch_name)
                commits.append(commit_data)

                # Mark SHA as seen
                self.seen_shas.add(commit.hexsha)

        except GitCommandError as e:
            print(f"    Git command error for branch {branch_name}: {e}")
        except Exception as e:
            print(f"    Error processing branch {branch_name}: {e}")

        return commits

    def _is_user_commit(self, commit: git.Commit) -> bool:
        """Check if the commit was made by any of the specified users

        Args:
            commit: Git commit object

        Returns:
            True if commit is by specified user, False otherwise
        """
        if not commit.author:
            return False

        # Check by author name
        author_name = commit.author.name
        if author_name in self.usernames:
            return True

        return False

    def _extract_commit_data(self, commit: git.Commit, repo_name: str, branch_name: str) -> Dict[str, Any]:
        """Extract relevant data from a commit object

        Args:
            commit: Git commit object
            repo_name: Repository name
            branch_name: Branch name

        Returns:
            Commit data dictionary
        """
        # Convert to KST timezone
        kst = timezone(timedelta(hours=9))
        commit_date = datetime.fromtimestamp(commit.authored_date, tz=kst)

        return {
            'sha': commit.hexsha,
            'source': 'local',
            'repository': repo_name,
            'branch': branch_name,
            'message': commit.message.strip(),
            'author_name': commit.author.name if commit.author else 'Unknown',
            'author_email': commit.author.email if commit.author else 'Unknown',
            'date': commit_date,
            'url': ''  # Local commits don't have URLs
        }


def create_local_git_scanner(usernames: List[str], from_date: Optional[str] = None,
                             to_date: Optional[str] = None) -> LocalGitScanner:
    """Create local Git scanner instance

    Args:
        usernames: List of usernames to filter commits
        from_date: Start date (datetime object or None)
        to_date: End date (datetime object or None)

    Returns:
        LocalGitScanner instance
    """
    # KST timezone (UTC+9)
    kst = timezone(timedelta(hours=9))
    
    # Parse dates if provided (assuming they're already datetime objects or None)
    from_datetime = None
    to_datetime = None

    if from_date:
        if isinstance(from_date, str):
            # Parse string to datetime with KST timezone
            try:
                naive_dt = datetime.strptime(from_date, '%Y-%m-%d %H:%M')
                from_datetime = naive_dt.replace(tzinfo=kst)
            except ValueError:
                try:
                    naive_dt = datetime.strptime(from_date, '%Y-%m-%d')
                    from_datetime = naive_dt.replace(tzinfo=kst)
                except ValueError:
                    print(f"Warning: Invalid from_date format: {from_date}")
        elif isinstance(from_date, datetime):
            from_datetime = from_date

    if to_date:
        if isinstance(to_date, str):
            # Parse string to datetime with KST timezone
            try:
                naive_dt = datetime.strptime(to_date, '%Y-%m-%d %H:%M')
                to_datetime = naive_dt.replace(tzinfo=kst)
            except ValueError:
                try:
                    naive_dt = datetime.strptime(to_date, '%Y-%m-%d')
                    to_datetime = naive_dt.replace(tzinfo=kst)
                except ValueError:
                    print(f"Warning: Invalid to_date format: {to_date}")
        elif isinstance(to_date, datetime):
            to_datetime = to_date

    return LocalGitScanner(usernames, from_datetime, to_datetime)
