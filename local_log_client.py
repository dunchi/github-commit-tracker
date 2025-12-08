"""
Local log file reader for commit tracking
Reads commits from ~/.git-commit-logs/ directory
"""
import os
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path


class LocalLogReader:
    """Reads commit data from local log files"""

    def __init__(self, log_dir: str = "~/.git-commit-logs",
                 from_date: Optional[datetime] = None,
                 to_date: Optional[datetime] = None):
        self.log_dir = os.path.expanduser(log_dir)
        self.from_date = from_date
        self.to_date = to_date
        self.kst = timezone(timedelta(hours=9))

    def read_commits(self) -> List[Dict[str, Any]]:
        """Read commits from log files within date range

        Returns:
            List of commit data dictionaries
        """
        commits = []

        if not os.path.exists(self.log_dir):
            print(f"Warning: Log directory does not exist: {self.log_dir}")
            return commits

        # Get log files to read based on date range
        log_files = self._get_log_files_in_range()

        print(f"Found {len(log_files)} log files to read")

        for log_file in log_files:
            file_commits = self._read_log_file(log_file)
            commits.extend(file_commits)
            print(f"  {os.path.basename(log_file)}: {len(file_commits)} commits")

        return commits

    def _get_log_files_in_range(self) -> List[str]:
        """Get log files within the date range

        Returns:
            List of log file paths
        """
        log_files = []

        try:
            for filename in os.listdir(self.log_dir):
                if not filename.endswith('.log'):
                    continue

                # Parse date from filename (YYYY-MM-DD.log)
                date_str = filename.replace('.log', '')
                try:
                    file_date = datetime.strptime(date_str, '%Y-%m-%d')
                    file_date = file_date.replace(tzinfo=self.kst)

                    # Check if file date is within range
                    if self.from_date:
                        from_date_only = self.from_date.replace(hour=0, minute=0, second=0, microsecond=0)
                        if file_date.date() < from_date_only.date():
                            continue

                    if self.to_date:
                        to_date_only = self.to_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                        if file_date.date() > to_date_only.date():
                            continue

                    log_files.append(os.path.join(self.log_dir, filename))

                except ValueError:
                    # Invalid date format in filename, skip
                    continue

        except PermissionError:
            print(f"Warning: Permission denied accessing {self.log_dir}")

        # Sort by date (oldest first for consistent ordering)
        log_files.sort()

        return log_files

    def _read_log_file(self, log_file: str) -> List[Dict[str, Any]]:
        """Read commits from a single log file

        Args:
            log_file: Path to the log file

        Returns:
            List of commit data dictionaries
        """
        commits = []

        # Extract date from filename
        filename = os.path.basename(log_file)
        date_str = filename.replace('.log', '')

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    commit_data = self._parse_log_line(line, date_str)
                    if commit_data:
                        # Check time range
                        if self.from_date and commit_data['date'] < self.from_date:
                            continue
                        if self.to_date and commit_data['date'] > self.to_date:
                            continue

                        commits.append(commit_data)

        except Exception as e:
            print(f"  Error reading {log_file}: {e}")

        return commits

    def _parse_log_line(self, line: str, date_str: str) -> Optional[Dict[str, Any]]:
        """Parse a single log line

        Expected format: [HH:MM:SS] repo_name (branch) sha - message

        Args:
            line: Log line to parse
            date_str: Date string from filename (YYYY-MM-DD)

        Returns:
            Commit data dictionary or None if parsing fails
        """
        # Pattern: [HH:MM:SS] repo_name (branch) sha - message
        pattern = r'\[(\d{2}:\d{2}:\d{2})\]\s+(\S+)\s+\(([^)]+)\)\s+(\w+)\s+-\s+(.+)'

        match = re.match(pattern, line)
        if not match:
            return None

        time_str, repo_name, branch, sha, message = match.groups()

        # Combine date and time
        try:
            datetime_str = f"{date_str} {time_str}"
            commit_date = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
            commit_date = commit_date.replace(tzinfo=self.kst)
        except ValueError:
            return None

        return {
            'sha': sha,
            'source': 'local_log',
            'repository': repo_name,
            'branch': branch,
            'message': message,
            'author_name': '',  # Not available in log
            'author_email': '',  # Not available in log
            'date': commit_date,
            'url': ''
        }


def create_local_log_reader(log_dir: str = "~/.git-commit-logs",
                            from_date: Optional[str] = None,
                            to_date: Optional[str] = None) -> LocalLogReader:
    """Create local log reader instance

    Args:
        log_dir: Directory containing log files
        from_date: Start date (datetime object or string)
        to_date: End date (datetime object or string)

    Returns:
        LocalLogReader instance
    """
    kst = timezone(timedelta(hours=9))

    from_datetime = None
    to_datetime = None

    if from_date:
        if isinstance(from_date, str):
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

    return LocalLogReader(log_dir, from_datetime, to_datetime)
