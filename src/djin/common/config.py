"""
Configuration management for Djin.
"""

import json
import os
import pathlib

import keyring
from dotenv import load_dotenv
from rich.console import Console

# Create console for rich output
console = Console()

# Service name for keyring
SERVICE_NAME = "Djin-assistant"

# Default configuration directory
CONFIG_DIR = pathlib.Path("~/.Djin").expanduser()
CONFIG_FILE = CONFIG_DIR / "config.json"

# Default configuration template
DEFAULT_CONFIG = {
    "jira": {
        "url": "",
        "username": "",
        "api_token": "",  # Will be stored in keyring
    },
    "moneymonk": {
        "url": "https://moneymonk.com",
        "username": "",
        "password": "",     # Will be stored in keyring
        "totp_secret": "",  # Will be stored in keyring
    },
    # Removed TagUI config section
}


def ensure_config_dir():
    """Ensure the configuration directory exists."""
    CONFIG_DIR.mkdir(exist_ok=True)


def load_config():
    """Load configuration from file and environment."""
    # Load .env file if it exists
    load_dotenv()

    # Ensure config directory exists
    ensure_config_dir()

    # Load config file if it exists, otherwise create default
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    else:
        config = DEFAULT_CONFIG.copy()
        save_config(config)

    # Override with environment variables if they exist
    if os.getenv("Djin_JIRA_URL"):
        config["jira"]["url"] = os.getenv("Djin_JIRA_URL")
    if os.getenv("Djin_JIRA_USERNAME"):
        config["jira"]["username"] = os.getenv("Djin_JIRA_USERNAME")
    if os.getenv("Djin_MONEYMONK_USERNAME"):
        config["moneymonk"]["username"] = os.getenv("Djin_MONEYMONK_USERNAME")
    # Removed TAGUI_PATH environment variable check


    # Load secrets from keyring
    if config["jira"]["username"]:
        api_token = keyring.get_password(SERVICE_NAME, f"jira_api_token_{config['jira']['username']}")
        if api_token:
            config["jira"]["api_token"] = api_token

    if config["moneymonk"]["username"]:
        # Load MoneyMonk password from keyring
        password_key = f"moneymonk_password_{config['moneymonk']['username']}"
        password = keyring.get_password(SERVICE_NAME, password_key)
        if password:
            config["moneymonk"]["password"] = password

        # Load MoneyMonk TOTP secret from keyring
        totp_key = f"moneymonk_totp_{config['moneymonk']['username']}"
        totp_secret = keyring.get_password(SERVICE_NAME, totp_key)
        if totp_secret:
            config["moneymonk"]["totp_secret"] = totp_secret

    return config


def save_config(config):
    """Save configuration to file and keyring."""
    # Ensure config directory exists
    ensure_config_dir()

    # Save API tokens to keyring
    if config["jira"]["username"] and config["jira"]["api_token"]:
        keyring.set_password(
            SERVICE_NAME,
            f"jira_api_token_{config['jira']['username']}",
            config["jira"]["api_token"],
        )
        # Don't store API token in config file
        safe_config = config.copy()
        safe_config["jira"]["api_token"] = ""
    else:
        safe_config = config.copy()

    # Save MoneyMonk password to keyring
    if config["moneymonk"]["username"] and config["moneymonk"].get("password"):
        keyring.set_password(
            SERVICE_NAME,
            f"moneymonk_password_{config['moneymonk']['username']}",
            config["moneymonk"]["password"],
        )
        # Don't store password in config file
        safe_config["moneymonk"]["password"] = ""

    # Save MoneyMonk TOTP secret to keyring
    if config["moneymonk"]["username"] and config["moneymonk"].get("totp_secret"):
        keyring.set_password(
            SERVICE_NAME,
            f"moneymonk_totp_{config['moneymonk']['username']}",
            config["moneymonk"]["totp_secret"],
        )
        # Don't store TOTP secret in config file
        safe_config["moneymonk"]["totp_secret"] = ""

    # Save config to file (without sensitive data)
    with open(CONFIG_FILE, "w") as f:
        json.dump(safe_config, f, indent=2)


def setup_config():
    """Interactive setup for configuration."""
    config = load_config()

    console.print("\n[bold cyan]Djin Configuration Setup[/bold cyan]")
    console.print("Press Enter to keep current values in [brackets].\n")

    # Jira configuration
    console.print("[bold]Jira Configuration[/bold]")
    config["jira"]["url"] = input(f"Jira URL [{config['jira']['url']}]: ") or config["jira"]["url"]
    config["jira"]["username"] = input(f"Jira Username [{config['jira']['username']}]: ") or config["jira"]["username"]

    if config["jira"]["username"]:
        new_token = input("Jira API Token (leave empty to keep existing): ")
        if new_token:
            config["jira"]["api_token"] = new_token

    # MoneyMonk configuration
    console.print("\n[bold]MoneyMonk Configuration[/bold]")
    config["moneymonk"]["username"] = (
        input(f"MoneyMonk Username [{config['moneymonk']['username']}]: ") or config["moneymonk"]["username"]
    )

    if config["moneymonk"]["username"]:
        new_password = input("MoneyMonk Password (leave empty to keep existing): ")
        if new_password:
            config["moneymonk"]["password"] = new_password

        new_totp = input("MoneyMonk TOTP Secret (leave empty to keep existing): ")
        if new_totp:
            config["moneymonk"]["totp_secret"] = new_totp

    # Removed TagUI configuration section

    # Save the updated configuration
    save_config(config)
    console.print("\n[green]Configuration saved![/green]")


def is_configured():
    """Check if the application is configured."""
    config = load_config()

    # Check Jira configuration
    jira_configured = (
        config["jira"]["url"]
        and config["jira"]["username"]
        and (
            config["jira"]["api_token"]
            or keyring.get_password(SERVICE_NAME, f"jira_api_token_{config['jira']['username']}")
        )
    )

    # Check MoneyMonk configuration
    moneymonk_user = config["moneymonk"]["username"]
    moneymonk_configured = (
        moneymonk_user
        and (
            config["moneymonk"].get("password") # Check if loaded into config
            or keyring.get_password(SERVICE_NAME, f"moneymonk_password_{moneymonk_user}") # Check keyring directly
        )
        and (
            config["moneymonk"].get("totp_secret") # Check if loaded into config
            or keyring.get_password(SERVICE_NAME, f"moneymonk_totp_{moneymonk_user}") # Check keyring directly
        )
    )

    return jira_configured and moneymonk_configured
