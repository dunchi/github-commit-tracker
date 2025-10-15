"""
GitHub API client for commit tracking
"""
import fnmatch
from datetime import datetime
from typing import List, Dict, Any, Optional, Iterator
from github import Github, Repository, PaginatedList
from github.Commit import Commit
from github.GithubException import GithubException, UnknownObjectException


class GitHubCommitTracker:
    """GitHub API client for tracking commits"""

    def __init__(self, token: str, usernames: List[str], from_date: Optional[str] = None, to_date: Optional[str] = None):
        self.github = Github(token)
        self.usernames = usernames
        self.from_date = self._parse_date(from_date) if from_date else None
        self.to_date = self._parse_date(to_date) if to_date else None

    def get_organization_repositories(self, org_name: str) -> List[Repository.Repository]:
        """Get all repositories from an organization"""
        try:
            org = self.github.get_organization(org_name)
            return list(org.get_repos())
        except GithubException as e:
            print(f"Error accessing organization {org_name}: {e}")
            return []

    def get_repository(self, repo_name: str) -> Optional[Repository.Repository]:
        """Get a specific repository by name (org/repo)"""
        try:
            return self.github.get_repo(repo_name)
        except GithubException as e:
            print(f"Error accessing repository {repo_name}: {e}")
            return None

    def get_all_repository_branches(self, repo: Repository.Repository) -> List[str]:
        """Get all branches in the repository"""
        try:
            return [branch.name for branch in repo.get_branches()]
        except GithubException as e:
            print(f"Error getting branches for {repo.full_name}: {e}")
            return []

    def get_commits_from_branch(self, repo: Repository.Repository, branch_name: str) -> List[Dict[str, Any]]:
        """Get commits from a specific branch, filtered by user and date range"""
        commits = []
        try:
            # Get commits with date filtering
            kwargs = {'sha': branch_name}
            if self.from_date:
                kwargs['since'] = self.from_date
            if self.to_date:
                kwargs['until'] = self.to_date

            branch_commits = repo.get_commits(**kwargs)

            for commit in branch_commits:
                if self._is_user_commit(commit):
                    commit_data = self._extract_commit_data(commit, repo.full_name, branch_name)
                    commits.append(commit_data)

        except UnknownObjectException:
            print(f"Branch {branch_name} not found in {repo.full_name}")
        except GithubException as e:
            print(f"Error getting commits from {repo.full_name}:{branch_name}: {e}")

        return commits

    def get_commits_from_organizations(self, organizations: List[str], branch_strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get commits from all repositories in the organizations using branch strategy"""
        all_commits = []

        for org_name in organizations:
            print(f"Processing organization: {org_name}")
            repositories = self.get_organization_repositories(org_name)

            for repo in repositories:
                print(f"  Processing repository: {repo.full_name}")
                # Get repo-specific branch strategy
                repo_strategy = self._get_repo_specific_strategy(repo.full_name, branch_strategy)
                target_branches = self._get_target_branches(repo, repo_strategy)
                print(f"    Target branches: {target_branches}")

                for branch in target_branches:
                    print(f"    Processing branch: {branch}")
                    branch_commits = self.get_commits_from_branch(repo, branch)
                    all_commits.extend(branch_commits)

        return all_commits

    def _get_repo_specific_strategy(self, repo_full_name: str, branch_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Get repository-specific branch strategy

        Args:
            repo_full_name: Full repository name (organization/repository)
            branch_strategy: Default branch strategy with optional overrides

        Returns:
            Branch strategy for the specific repository
        """
        overrides = branch_strategy.get('overrides', {})

        # Check if there's a repo-specific override
        if repo_full_name in overrides:
            return overrides[repo_full_name]

        # Return default strategy (without overrides key)
        return {
            'mode': branch_strategy.get('mode'),
            'branches': branch_strategy.get('branches', [])
        }

    def _get_target_branches(self, repo: Repository.Repository, branch_strategy: Dict[str, Any]) -> List[str]:
        """Get target branches based on strategy"""
        mode = branch_strategy.get('mode', 'all')

        if mode == 'all':
            return self.get_all_repository_branches(repo)

        elif mode == 'specific':
            specified_branches = branch_strategy.get('branches', [])
            all_branches = self.get_all_repository_branches(repo)
            return [branch for branch in specified_branches if branch in all_branches]

        elif mode == 'priority':
            priority_branches = branch_strategy.get('branches', [])
            all_branches = self.get_all_repository_branches(repo)

            # Return first existing branch from priority list
            for branch in priority_branches:
                if branch in all_branches:
                    return [branch]

            # If no priority branch exists, return empty list
            return []

        return []

    def _is_user_commit(self, commit: Commit) -> bool:
        """Check if the commit was made by any of the specified users"""
        if not commit.author:
            return False

        # Check by username
        if commit.author.login in self.usernames:
            return True

        return False

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object"""
        return datetime.strptime(date_str, '%Y-%m-%d')

    def _extract_commit_data(self, commit: Commit, repo_name: str, branch_name: str) -> Dict[str, Any]:
        """Extract relevant data from a commit object"""
        return {
            'sha': commit.sha,
            'repository': repo_name,
            'branch': branch_name,
            'message': commit.commit.message.strip(),
            'author_name': commit.commit.author.name if commit.commit.author else 'Unknown',
            'author_email': commit.commit.author.email if commit.commit.author else 'Unknown',
            'date': commit.commit.author.date if commit.commit.author else datetime.now(),
            'url': commit.html_url
        }


def create_github_client(token: str, usernames: List[str], from_date: Optional[str] = None,
                        to_date: Optional[str] = None) -> GitHubCommitTracker:
    """Create GitHub client instance"""
    return GitHubCommitTracker(token, usernames, from_date, to_date)