#!/usr/bin/env python3
"""
GitHub Commit Tracker Setup Script
Interactive setup for initial configuration
"""

import os
import shutil
import sys
from typing import List


def print_banner():
    """Print setup banner"""
    print("=" * 60)
    print("🚀 GitHub Commit Tracker - Setup")
    print("=" * 60)
    print()


def check_dependencies():
    """Check if required dependencies are installed"""
    print("📦 Checking dependencies...")

    try:
        import yaml
        import github
        print("  ✅ PyYAML: OK")
        print("  ✅ PyGithub: OK")
    except ImportError as e:
        print(f"  ❌ Missing dependency: {e}")
        print()
        print("Please install dependencies first:")
        print("  pip install -r requirements.txt")
        return False

    print("  ✅ All dependencies installed")
    print()
    return True


def create_config_file():
    """Create config.yaml from template"""
    print("⚙️  Setting up configuration...")

    if os.path.exists("config.yaml"):
        response = input("  config.yaml already exists. Overwrite? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("  ⏭️  Skipping config file creation")
            return

    if not os.path.exists("config.yaml.example"):
        print("  ❌ config.yaml.example not found")
        return False

    # Copy example to config
    shutil.copy("config.yaml.example", "config.yaml")
    print("  ✅ Created config.yaml from template")

    return True


def get_user_input():
    """Get user configuration input"""
    print("📝 Please provide the following information:")
    print()

    # GitHub Token
    print("1. GitHub Personal Access Token")
    print("   Go to: GitHub → Settings → Developer settings → Personal access tokens")
    print("   Required permissions: 'repo', 'read:org'")
    token = input("   Enter your GitHub token: ").strip()

    # Organization
    print("\n2. GitHub Organization")
    print("   The organization name you want to track commits from")
    org = input("   Enter organization name: ").strip()

    # Usernames
    print("\n3. GitHub Usernames")
    print("   Usernames to filter commits (comma-separated)")
    print("   Example: john,jane,bob")
    usernames_input = input("   Enter usernames: ").strip()
    usernames = [name.strip() for name in usernames_input.split(",") if name.strip()]

    return {
        'token': token,
        'organization': org,
        'usernames': usernames
    }


def update_config_file(config_data):
    """Update config.yaml with user data"""
    print("\n💾 Updating configuration file...")

    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            content = f.read()

        # Replace placeholder values
        content = content.replace("your_github_token_here", config_data['token'])
        content = content.replace("your_organization_name", config_data['organization'])

        # Update usernames
        usernames_yaml = str(config_data['usernames']).replace("'", '"')
        content = content.replace('["your_username", "teammate1", "teammate2"]', usernames_yaml)

        with open("config.yaml", "w", encoding="utf-8") as f:
            f.write(content)

        print("  ✅ Configuration updated successfully")
        return True

    except Exception as e:
        print(f"  ❌ Error updating config: {e}")
        return False


def test_configuration():
    """Test the configuration"""
    print("\n🧪 Testing configuration...")

    try:
        # Import and test
        sys.path.insert(0, ".")
        from config_parser import load_config

        config = load_config()

        print("  ✅ Configuration file is valid")
        print(f"  ✅ Organization: {config.get_organizations()}")
        print(f"  ✅ Usernames: {config.get_usernames()}")
        print("  ✅ Token: [HIDDEN]")

        return True

    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False


def show_next_steps():
    """Show next steps to user"""
    print("\n🎉 Setup completed successfully!")
    print()
    print("Next steps:")
    print("1. Test your configuration:")
    print("   python main.py --dry-run")
    print()
    print("2. Run the commit tracker:")
    print("   python main.py")
    print()
    print("3. Schedule daily runs (optional):")
    print("   crontab -e")
    print("   Add: 0 9 * * * cd $(pwd) && python main.py > daily-commits.txt")
    print()


def main():
    """Main setup function"""
    print_banner()

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Create config file
    if not create_config_file():
        sys.exit(1)

    # Get user input
    config_data = get_user_input()

    # Validate input
    if not config_data['token'] or not config_data['organization']:
        print("\n❌ Token and organization are required")
        sys.exit(1)

    # Update config
    if not update_config_file(config_data):
        sys.exit(1)

    # Test configuration
    if not test_configuration():
        print("\nYou can manually edit config.yaml and try again")
        sys.exit(1)

    # Show next steps
    show_next_steps()


if __name__ == "__main__":
    main()