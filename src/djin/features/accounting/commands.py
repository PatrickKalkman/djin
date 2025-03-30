"""
Command handlers for accounting features.
"""

from pathlib import Path
from typing import List

from loguru import logger  # Import Loguru logger
from rich.console import Console

from djin.cli.commands import register_command
from djin.common.errors import (  # Added MoneyMonkError, ConfigurationError
    ConfigurationError,
    DjinError,
    MoneyMonkError,
    handle_error,
)

# Import the API to interact with the agent/workflow
from djin.features.accounting.api import get_accounting_api

# Import from the new playwright client
from djin.features.accounting.playwright_client import _get_moneymonk_credentials

# Create console for rich output
console = Console()
# Loguru logger is imported directly


# --- Command Handlers ---


def login_command(args: List[str]) -> bool:
    """Test the MoneyMonk login process and navigate to time registration page."""
    logger.info("Received accounting login command.")

    # Parse arguments
    headless = "--headless" in args

    # Check if a date parameter was provided
    date_str = None
    for arg in args:
        if arg.startswith("--date="):
            date_str = arg.split("=")[1]
            break

    # If no date provided, use today's date
    if not date_str:
        from datetime import datetime

        date_str = datetime.now().strftime("%Y-%m-%d")

    console.print(f"[cyan]Attempting to log in to MoneyMonk via Playwright (headless={headless})...[/cyan]")

    try:
        # Get the base time entry URL first
        import os

        base_time_entry_url = os.environ.get("BASE_TIME_ENTRY_URL")

        if not base_time_entry_url:
            console.print(
                "[yellow]BASE_TIME_ENTRY_URL not set in environment. Cannot navigate to time registration page.[/yellow]"
            )
            return False

        console.print(f"[cyan]Logging in and navigating to time registration page for date: {date_str}[/cyan]")

        # Create a browser context and handle login + navigation in one session
        from djin.features.accounting.playwright_client import playwright_context

        with playwright_context(headless=headless) as page:
            # Get credentials for login
            import os

            email = os.environ.get("EMAIL")
            password = os.environ.get("PASSWORD")
            totp_secret = os.environ.get("TOTP_SECRET")
            login_url = os.environ.get("LOGIN_URL")

            if not all([email, password, totp_secret, login_url]):
                creds = _get_moneymonk_credentials()
                email = email or creds["username"]
                password = password or creds["password"]
                totp_secret = totp_secret or creds["totp_secret"]
                login_url = login_url or creds["url"]

            # Login first
            logger.debug(f"Navigating to {login_url}")
            page.goto(login_url)
            page.wait_for_timeout(2000)

            logger.debug("Entering credentials...")
            page.fill("#email", email)
            page.fill("#password", password)

            logger.debug("Clicking login button...")
            page.click("button[data-testid='button']")
            page.wait_for_timeout(2000)

            # Handle TOTP if needed
            if page.is_visible("#tfaCode"):
                logger.info("TOTP code entry required.")
                import pyotp

                totp_code = pyotp.TOTP(totp_secret).now()
                logger.info(f"Generated TOTP code: {totp_code}")

                page.fill("#tfaCode", totp_code)
                page.click("button[data-testid='button']")
                page.wait_for_timeout(2000)

            # Check if login was successful
            if page.is_visible("#email") or page.is_visible("#password") or page.is_visible("#tfaCode"):
                console.print("[red]Login failed. Still on login or TOTP screen.[/red]")
                screenshot_path = Path("~/.Djin/logs/login_failure.png").expanduser()
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot_path))
                console.print(f"[red]Screenshot saved to: {screenshot_path}[/red]")
                return False

            console.print("[green]MoneyMonk login successful.[/green]")

            # Now navigate to the time entry page with the date parameter
            registration_url = f"{base_time_entry_url}?date={date_str}"
            logger.debug(f"Navigating to time registration page: {registration_url}")
            page.goto(registration_url)

            # Wait longer (10 seconds) to allow for visual inspection
            console.print("[cyan]Waiting 10 seconds for visual inspection...[/cyan]")
            page.wait_for_timeout(10000)  # 10 seconds

            # Take a screenshot of the time entry page
            screenshot_path = Path("~/.Djin/logs/time_entry_page.png").expanduser()
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot_path))

            console.print(f"[green]Successfully navigated to time entry page for date: {date_str}[/green]")
            console.print(f"[green]Screenshot saved to: {screenshot_path}[/green]")

            # Check if we can see the time input field which indicates we're on the registration page
            time_input = "input#time"
            if page.is_visible(time_input):
                console.print("[green]Time entry page loaded successfully (time input field visible).[/green]")
            else:
                console.print(
                    "[yellow]Time entry page may not have loaded correctly (time input field not found).[/yellow]"
                )

            return True
    except (ConfigurationError, MoneyMonkError) as e:
        # Handle specific errors related to config or Playwright execution
        handle_error(e)  # display_error is called within handle_error
        return False
    except (ConfigurationError, MoneyMonkError) as e:
        # Handle specific errors related to config or Playwright execution
        handle_error(e)  # display_error is called within handle_error
        return False
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during MoneyMonk login test: {e}", exc_info=True)
        handle_error(DjinError(f"An unexpected error occurred during login test: {str(e)}"))
        return False


def register_hours_command(args: List[str]) -> bool:
    """Register hours on an external platform (e.g., MoneyMonk)."""
    logger.debug(f"Received register-hours command with args: {args}")

    # Expecting: date (YYYY-MM-DD), hours (e.g., 7.5), description (multi-word)
    if len(args) < 3:
        console.print(
            "[red]Error: Missing arguments.[/red]\nUsage: /accounting register-hours <YYYY-MM-DD> <hours> <description>"
        )
        return False

    date_str = args[0]
    hours_str = args[1]
    description = " ".join(args[2:])

    # Add --headless flag option
    headless = "--headless" in args
    if headless:
        # Remove the flag from the description if it was included there
        description = description.replace("--headless", "").strip()

    console.print(
        f"[cyan]Attempting to register {hours_str} hours for {date_str} with description: '{description}'...[/cyan]"
    )

    try:
        accounting_api = get_accounting_api()
        result = accounting_api.register_hours(date_str, description, hours_str)

        # Print the formatted output from the workflow/agent
        console.print(result.get("formatted_output", "[yellow]No output received from registration process.[/yellow]"))

        # Return True if the workflow reported success, False otherwise
        return result.get("registration_successful", False)

    except DjinError as e:
        # Handle known Djin errors (e.g., configuration, API connection issues if applicable)
        handle_error(e)
        return False
    except Exception as e:
        # Handle unexpected errors during the command execution
        logger.error(f"Unexpected error in register_hours_command: {e}", exc_info=True)
        handle_error(DjinError(f"An unexpected error occurred: {str(e)}"))
        return False


# --- Registration Function ---


def register_accounting_commands():
    """Registers all commands related to the accounting feature."""
    commands_to_register = {
        "accounting register-hours": (
            register_hours_command,
            "Register hours on MoneyMonk (Usage: /accounting register-hours YYYY-MM-DD hours description). Uses BASE_TIME_ENTRY_URL from .env.",
        ),
        "accounting login": (
            login_command,
            "Test the login process for MoneyMonk and navigate to time entry page. Options: --headless, --date=YYYY-MM-DD",
        ),
        # Add other accounting commands here
    }
    for name, (func, help_text) in commands_to_register.items():
        register_command(name, func, help_text)
    logger.info(f"Accounting commands registered: {list(commands_to_register.keys())}")


# No module-level side effects for registration
