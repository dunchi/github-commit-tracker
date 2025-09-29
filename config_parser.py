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

        # Validate GitHub section
        github_config = self.config.get('github', {})
        if not github_config.get('token'):
            raise ConfigError("GitHub token is required")

        if not github_config.get('organizations'):
            raise ConfigError("At least one organization must be specified")

        usernames = github_config.get('usernames', [])
        if not usernames or not isinstance(usernames, list):
            raise ConfigError("At least one username must be specified in usernames array")

        # Validate branch_strategy section
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

        # Validate date_range section (optional)
        date_range = self.config.get('date_range', {})
        if date_range:
            from_date = date_range.get('from')
            to_date = date_range.get('to')

            if from_date:
                try:
                    datetime.strptime(from_date, '%Y-%m-%d')
                except ValueError:
                    raise ConfigError(f"Invalid from date format: {from_date}. Use YYYY-MM-DD format")

            if to_date:
                try:
                    datetime.strptime(to_date, '%Y-%m-%d')
                except ValueError:
                    raise ConfigError(f"Invalid to date format: {to_date}. Use YYYY-MM-DD format")

    def get_github_config(self) -> Dict[str, Any]:
        """Get GitHub configuration"""
        return self.config.get('github', {})

    def get_organizations(self) -> List[str]:
        """Get organizations list"""
        github_config = self.get_github_config()
        return github_config.get('organizations', [])

    def get_usernames(self) -> List[str]:
        """Get usernames list for filtering"""
        github_config = self.get_github_config()
        return github_config.get('usernames', [])

    def get_branch_strategy(self) -> Dict[str, Any]:
        """Get branch strategy configuration"""
        return self.config.get('branch_strategy', {})

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

        return {
            'from': from_date if from_date else None,
            'to': to_date if to_date else None
        }

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