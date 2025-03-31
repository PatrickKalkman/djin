"""
Configuration management for Djin.
"""

import json
import os
import pathlib

import keyring
from dotenv import load_dotenv
from rich.console import Console

console = Console()

SERVICE_NAME = "Djin-assistant"

CONFIG_DIR = pathlib.Path("~/.Djin").expanduser()
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_CONFIG = {
    "jira": {
        "url": "",
        "username": "",
        "api_token": "",
    },
    "moneymonk": {
        "url": "https://moneymonk.com",
        "username": "",
        "password": "",
        "totp_secret": "",
    },
}


def ensure_config_dir():
    """Ensure the configuration directory exists."""
    CONFIG_DIR.mkdir(exist_ok=True)


def load_config():
    """Load configuration from file and environment."""
    load_dotenv()

    ensure_config_dir()

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    else:
        config = DEFAULT_CONFIG.copy()
        save_config(config)

    if os.getenv("Djin_JIRA_URL"):
        config["jira"]["url"] = os.getenv("Djin_JIRA_URL")
    if os.getenv("Djin_JIRA_USERNAME"):
        config["jira"]["username"] = os.getenv("Djin_JIRA_USERNAME")
    if os.getenv("Djin_MONEYMONK_USERNAME"):
        config["moneymonk"]["username"] = os.getenv("Djin_MONEYMONK_USERNAME")


    if config["jira"]["username"]:
        api_token = keyring.get_password(SERVICE_NAME, f"jira_api_token_{config['jira']['username']}")
        if api_token:
            config["jira"]["api_token"] = api_token

    if config["moneymonk"]["username"]:
        password_key = f"moneymonk_password_{config['moneymonk']['username']}"
        password = keyring.get_password(SERVICE_NAME, password_key)
        if password:
            config["moneymonk"]["password"] = password

        totp_key = f"moneymonk_totp_{config['moneymonk']['username']}"
        totp_secret = keyring.get_password(SERVICE_NAME, totp_key)
        if totp_secret:
            config["moneymonk"]["totp_secret"] = totp_secret

    return config


def save_config(config):
    """Save configuration to file and keyring."""
    ensure_config_dir()

    if config["jira"]["username"] and config["jira"]["api_token"]:
        keyring.set_password(
            SERVICE_NAME,
            f"jira_api_token_{config['jira']['username']}",
            config["jira"]["api_token"],
        )
        safe_config = config.copy()
        safe_config["jira"]["api_token"] = ""
    else:
        safe_config = config.copy()

    if config["moneymonk"]["username"] and config["moneymonk"].get("password"):
        keyring.set_password(
            SERVICE_NAME,
            f"moneymonk_password_{config['moneymonk']['username']}",
            config["moneymonk"]["password"],
        )
        safe_config["moneymonk"]["password"] = ""

    if config["moneymonk"]["username"] and config["moneymonk"].get("totp_secret"):
        keyring.set_password(
            SERVICE_NAME,
            f"moneymonk_totp_{config['moneymonk']['username']}",
            config["moneymonk"]["totp_secret"],
        )
        safe_config["moneymonk"]["totp_secret"] = ""
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

    jira_configured = (
        config["jira"]["url"]
        and config["jira"]["username"]
        and (
            config["jira"]["api_token"]
            or keyring.get_password(SERVICE_NAME, f"jira_api_token_{config['jira']['username']}")
        )
    )

    moneymonk_user = config["moneymonk"]["username"]
    moneymonk_configured = (
        moneymonk_user
        and (
            config["moneymonk"].get("password")
            or keyring.get_password(SERVICE_NAME, f"moneymonk_password_{moneymonk_user}")
        )
        and (
            config["moneymonk"].get("totp_secret")
            or keyring.get_password(SERVICE_NAME, f"moneymonk_totp_{moneymonk_user}")
        )
    )

    return jira_configured and moneymonk_configured
