"""
Configuration parser and validator for GitHub commit tracker
"""
import yaml
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class ConfigError(Exception):
    """Configuration error exception"""
    pass


class ConfigParser:
    """Configuration file parser and validator"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = None

    def load(self) -> Dict[str, Any]:
        """Load and validate configuration file"""
        if not os.path.exists(self.config_path):
            raise ConfigError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Replace environment variables
                content = self._expand_env_vars(content)
                self.config = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML format: {e}")

        self._validate_config()
        return self.config

    def _expand_env_vars(self, content: str) -> str:
        """Expand environment variables in config content"""
        def replace_env_var(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))  # Return original if not found

        # Replace ${VAR_NAME} patterns
        return re.sub(r'\$\{([^}]+)\}', replace_env_var, content)

    def _validate_config(self):
        """Validate configuration structure and required fields"""
        if not self.config:
            raise ConfigError("Empty configuration file")

        # Check which mode is enabled
        github_config = self.config.get('github', {})
        local_git_config = self.config.get('local_git', {})

        github_enabled = github_config.get('enabled', False)
        local_git_enabled = local_git_config.get('enabled', False)

        # At least one mode must be enabled
        if not github_enabled and not local_git_enabled:
            raise ConfigError("Either github.enabled or local_git.enabled must be true")

        # Both modes can be enabled for hybrid mode
        # (removed the check that prevented both from being enabled)

        # Validate based on enabled mode
        if github_enabled:
            self._validate_github_config(github_config)

        if local_git_enabled:
            self._validate_local_git_config(local_git_config)

    def _validate_github_config(self, github_config: Dict[str, Any]):
        """Validate GitHub configuration"""
        token = github_config.get('token')
        if not token:
            raise ConfigError("GitHub token is required when github.enabled is true")

        # Check if token is still a placeholder (environment variable not expanded)
        if token.startswith('${') and token.endswith('}'):
            var_name = token[2:-1]
            raise ConfigError(
                f"Environment variable '{var_name}' is not set.\n"
                f"Please set it before running:\n"
                f"  export {var_name}=\"your_github_token_here\"\n"
                f"Or add it to your shell profile (~/.bashrc, ~/.zshrc, etc.)"
            )

        if not github_config.get('organizations'):
            raise ConfigError("At least one organization must be specified")

        usernames = github_config.get('usernames', [])
        if not usernames or not isinstance(usernames, list):
            raise ConfigError("At least one username must be specified in usernames array")

        # Validate branch strategy for GitHub mode
        self._validate_branch_strategy()

    def _validate_local_git_config(self, local_git_config: Dict[str, Any]):
        """Validate local Git configuration"""
        base_paths = local_git_config.get('base_paths', [])
        repositories = local_git_config.get('repositories', [])

        # At least one of base_paths or repositories must be specified
        if not base_paths and not repositories:
            raise ConfigError("At least one of local_git.base_paths or local_git.repositories must be specified")

        # Validate base_paths
        if base_paths:
            if not isinstance(base_paths, list):
                raise ConfigError("local_git.base_paths must be a list")
            for path in base_paths:
                if not isinstance(path, str):
                    raise ConfigError(f"Invalid base_path: {path}. Must be a string")

        # Validate repositories
        if repositories:
            if not isinstance(repositories, list):
                raise ConfigError("local_git.repositories must be a list")
            for path in repositories:
                if not isinstance(path, str):
                    raise ConfigError(f"Invalid repository path: {path}. Must be a string")

        # Validate usernames
        usernames = local_git_config.get('usernames', [])
        if not usernames or not isinstance(usernames, list):
            raise ConfigError("At least one username must be specified in local_git.usernames array")

    def _validate_branch_strategy(self):
        """Validate branch_strategy section (GitHub mode only)"""
        branch_strategy = self.config.get('branch_strategy', {})
        if not branch_strategy:
            raise ConfigError("branch_strategy section is required")

        mode = branch_strategy.get('mode')
        if mode not in ['all', 'specific', 'priority']:
            raise ConfigError("branch_strategy.mode must be one of: 'all', 'specific', 'priority'")

        if mode in ['specific', 'priority']:
            branches = branch_strategy.get('branches', [])
            if not branches or not isinstance(branches, list):
                raise ConfigError(f"branch_strategy.branches is required for mode '{mode}' and must be a list")

        # Validate branch_strategy.overrides section (optional)
        overrides = branch_strategy.get('overrides', {})
        if overrides:
            if not isinstance(overrides, dict):
                raise ConfigError("branch_strategy.overrides must be a dictionary")

            for repo_name, repo_strategy in overrides.items():
                # Validate repo name format (org/repo)
                if '/' not in repo_name:
                    raise ConfigError(f"Invalid repository name in overrides: '{repo_name}'. Must be in 'organization/repository' format")

                # Validate mode
                repo_mode = repo_strategy.get('mode')
                if repo_mode not in ['all', 'specific', 'priority']:
                    raise ConfigError(f"Invalid mode for repository '{repo_name}': '{repo_mode}'. Must be one of: 'all', 'specific', 'priority'")

                # Validate branches if mode is specific or priority
                if repo_mode in ['specific', 'priority']:
                    repo_branches = repo_strategy.get('branches', [])
                    if not repo_branches or not isinstance(repo_branches, list):
                        raise ConfigError(f"branch_strategy.overrides['{repo_name}'].branches is required for mode '{repo_mode}' and must be a list")

    def _validate_date_format(self, date_str: str, field_name: str):
        """Validate date format (YYYY-MM-DD, YYYY-MM-DD HH:MM, or HH:MM)"""
        # Try HH:MM format first
        try:
            datetime.strptime(date_str, '%H:%M')
            return
        except ValueError:
            pass

        # Try YYYY-MM-DD HH:MM format
        try:
            datetime.strptime(date_str, '%Y-%m-%d %H:%M')
            return
        except ValueError:
            pass

        # Try YYYY-MM-DD format
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return
        except ValueError:
            raise ConfigError(f"Invalid {field_name} date format: {date_str}. Use YYYY-MM-DD, YYYY-MM-DD HH:MM, or HH:MM format")

    def get_mode(self) -> str:
        """Get current mode ('github', 'local_git', or 'hybrid')"""
        github_enabled = self.config.get('github', {}).get('enabled', False)
        local_git_enabled = self.config.get('local_git', {}).get('enabled', False)

        if github_enabled and local_git_enabled:
            return 'hybrid'
        elif github_enabled:
            return 'github'
        elif local_git_enabled:
            return 'local_git'
        else:
            raise ConfigError("Either github.enabled or local_git.enabled must be true")

    def get_github_config(self) -> Dict[str, Any]:
        """Get GitHub configuration"""
        return self.config.get('github', {})

    def get_local_git_config(self) -> Dict[str, Any]:
        """Get local Git configuration"""
        return self.config.get('local_git', {})

    def get_organizations(self) -> List[str]:
        """Get organizations list"""
        github_config = self.get_github_config()
        return github_config.get('organizations', [])

    def get_usernames(self) -> List[str]:
        """Get usernames list for filtering (works for all modes)"""
        mode = self.get_mode()
        if mode == 'github':
            github_config = self.get_github_config()
            return github_config.get('usernames', [])
        elif mode == 'local_git':
            local_git_config = self.get_local_git_config()
            return local_git_config.get('usernames', [])
        elif mode == 'hybrid':
            # For hybrid mode, combine usernames from both configs
            github_config = self.get_github_config()
            local_git_config = self.get_local_git_config()
            github_users = set(github_config.get('usernames', []))
            local_users = set(local_git_config.get('usernames', []))
            return list(github_users | local_users)  # Union of both sets
        else:
            return []

    def get_branch_strategy(self, repo_full_name: Optional[str] = None) -> Dict[str, Any]:
        """Get branch strategy configuration for a specific repository

        Args:
            repo_full_name: Full repository name (organization/repository).
                          If None, returns the default strategy.
                          If specified and exists in overrides, returns the override strategy.
                          If specified but not in overrides, returns the default strategy.

        Returns:
            Branch strategy configuration
        """
        branch_strategy = self.config.get('branch_strategy', {})

        # If no repo specified, return default strategy
        if not repo_full_name:
            return branch_strategy

        # Check for repo-specific override
        overrides = branch_strategy.get('overrides', {})
        if repo_full_name in overrides:
            return overrides[repo_full_name]

        # Return default strategy (without overrides key)
        return {
            'mode': branch_strategy.get('mode'),
            'branches': branch_strategy.get('branches', [])
        }

    def get_date_range(self, dry_run: bool = False) -> Dict[str, Optional[str]]:
        """Get date range configuration with defaults"""

        date_range = self.config.get('date_range', {})
        from_date = date_range.get('from')
        to_date = date_range.get('to')

        # If both are empty, default to yesterday (with weekend check)
        if not from_date and not to_date:
            yesterday = datetime.now() - timedelta(days=1)
            from_date = self._get_start_date_with_weekend_check(yesterday, dry_run)
            return {
                'from': from_date,
                'to': None  # None means until now
            }

        # If only from is empty, default to yesterday (with weekend check)
        if not from_date:
            yesterday = datetime.now() - timedelta(days=1)
            from_date = self._get_start_date_with_weekend_check(yesterday, dry_run)

        # Process HH:MM format for from_date (use yesterday's date with weekend check)
        if from_date and self._is_time_only_format(from_date):
            yesterday = datetime.now() - timedelta(days=1)
            base_date = self._get_start_date_with_weekend_check(yesterday, dry_run)
            from_date = f"{base_date} {from_date}"

        # Process HH:MM format for to_date (use today's date)
        if to_date and self._is_time_only_format(to_date):
            today = datetime.now()
            to_date = f"{today.strftime('%Y-%m-%d')} {to_date}"

        return {
            'from': from_date if from_date else None,
            'to': to_date if to_date else None
        }

    def _is_time_only_format(self, date_str: str) -> bool:
        """Check if the string is in HH:MM format"""
        try:
            datetime.strptime(date_str, '%H:%M')
            return True
        except ValueError:
            return False

    def _get_start_date_with_weekend_check(self, yesterday: datetime, dry_run: bool = False) -> str:
        """Check if yesterday was weekend and ask user for preference"""

        # Check if yesterday was Saturday (5) or Sunday (6)
        if yesterday.weekday() in [5, 6]:  # Saturday or Sunday
            friday = yesterday
            # Find the most recent Friday
            while friday.weekday() != 4:  # Friday is 4
                friday = friday - timedelta(days=1)

            yesterday_str = yesterday.strftime('%Y-%m-%d (%A)')
            friday_str = friday.strftime('%Y-%m-%d (%A)')

            if dry_run:
                print(f"어제는 {yesterday_str}입니다. (Dry-run: 금요일부터 조회 가정)")
                return friday.strftime('%Y-%m-%d')
            else:
                print(f"어제는 {yesterday_str}입니다.")
                response = input(f"금요일({friday_str})부터 조회할까요? (y/n): ").strip().lower()

                if response in ['y', 'yes', 'ㅇ', '예']:
                    return friday.strftime('%Y-%m-%d')
                else:
                    return yesterday.strftime('%Y-%m-%d')
        else:
            return yesterday.strftime('%Y-%m-%d')


def load_config(config_path: str = "config.yaml") -> ConfigParser:
    """Load configuration file"""
    parser = ConfigParser(config_path)
    parser.load()
    return parser


if __name__ == "__main__":
    # Test configuration parser
    try:
        config = load_config()
        print("Configuration loaded successfully!")
        print(f"Organizations: {config.get_organizations()}")
        print(f"Usernames: {config.get_usernames()}")
        print(f"Branch strategy: {config.get_branch_strategy()}")
        print(f"Date range: {config.get_date_range()}")
    except ConfigError as e:
        print(f"Configuration error: {e}")