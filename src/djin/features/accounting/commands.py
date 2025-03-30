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
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError # Import the specific exception

from djin.features.accounting.api import get_accounting_api

# Import from the new playwright client
from djin.features.accounting.playwright_client import _get_moneymonk_credentials

# Create console for rich output
console = Console()
# Loguru logger is imported directly


# --- Command Handlers ---


from rich.prompt import Prompt # Import Prompt for better argument handling if needed

def login_command(args: List[str]) -> bool:
    """
    Test MoneyMonk login, navigate to time entry page, and pre-fill form fields.

    Usage: /accounting login <hours> <description> [--headless] [--date=YYYY-MM-DD]
    """
    logger.info(f"Received accounting login command with args: {args}")

    # --- Argument Parsing ---
    headless = "--headless" in args
    if headless:
        args.remove("--headless") # Remove flag so it doesn't interfere

    date_str = None
    date_arg_index = -1
    for i, arg in enumerate(args):
        if arg.startswith("--date="):
            try:
                date_str = arg.split("=")[1]
                # Basic validation
                from datetime import datetime
                datetime.strptime(date_str, "%Y-%m-%d")
                date_arg_index = i
                break
            except ValueError:
                console.print(f"[red]Error: Invalid date format '{arg.split('=')[1]}'. Use YYYY-MM-DD.[/red]")
                return False

    # Remove date arg if found
    if date_arg_index != -1:
        args.pop(date_arg_index)

    # If no date provided, use today's date
    if not date_str:
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"No date provided, using today's date: {date_str}")

    # Expecting hours and description now
    if len(args) < 2:
        console.print(
            "[red]Error: Missing arguments.[/red]\nUsage: /accounting login <hours> <description> [--headless] [--date=YYYY-MM-DD]"
        )
        return False

    hours_str = args[0]
    description = " ".join(args[1:])

    # Validate hours
    try:
        hours_float = float(hours_str)
        if hours_float <= 0:
            raise ValueError("Hours must be positive.")
    except ValueError:
        console.print(f"[red]Error: Invalid hours value '{hours_str}'. Must be a positive number.[/red]")
        return False

    console.print(
        f"[cyan]Attempting MoneyMonk login & form pre-fill (headless={headless}, date={date_str}, hours={hours_str})...[/cyan]"
    )

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

            # Wait briefly to allow for visual inspection
            console.print("[cyan]Waiting 1 second for visual inspection...[/cyan]")
            page.wait_for_timeout(1000)  # 1 second

            # Take a screenshot of the time entry page
            screenshot_path = Path("~/.Djin/logs/time_entry_page.png").expanduser()
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot_path))

            console.print(f"[green]Successfully navigated to time entry page for date: {date_str}[/green]")
            console.print(f"[green]Screenshot saved to: {screenshot_path}[/green]")

            # --- Form Interaction ---
            time_input = "input#time" # Selector for the time input field
            desc_selector = "input#description" # Selector for description (updated based on HTML)
            project_dropdown_trigger = 'div.react-select__control' # More specific selector for dropdown trigger
            project_option_selector_base = 'div[class*="react-select__option"]' # Base selector for options
            project_name_to_select = "AION Titan Streaming PI" # The specific project name (for verification)
            specific_project_option_selector = f"{project_option_selector_base}:has-text('{project_name_to_select}')" # Fallback selector
            selected_project_value_selector = 'div[class*="react-select__single-value"]' # Selector for chosen project display

            if page.is_visible(time_input):
                console.print("[green]Time entry page loaded successfully (time input field visible).[/green]")
                console.print("[cyan]Attempting to pre-fill form fields...[/cyan]")

                try:
                    # Click "Add time entry" button if present (might open a modal)
                    add_entry_button = "button:has-text('Add time entry')"
                    if page.is_visible(add_entry_button):
                        logger.debug("Clicking 'Add time entry' button...")
                        page.click(add_entry_button)
                        page.wait_for_timeout(1000) # Wait for modal

                    # Fill hours
                    logger.debug(f"Filling hours: {hours_str}")
                    page.fill(time_input, hours_str)

                    # Fill description
                    logger.debug(f"Filling description: {description}")
                    page.fill(desc_selector, description)

                    # Select project by selecting the second option in the dropdown
                    logger.debug("Selecting project by choosing the second option in dropdown")
                    logger.debug(f"Clicking project dropdown trigger: {project_dropdown_trigger}")
                    page.click(project_dropdown_trigger)
                    
                    # Wait for dropdown options to appear
                    logger.debug("Waiting for dropdown options to appear")
                    page.wait_for_selector(project_option_selector_base, state='visible', timeout=5000)
                    
                    # Get all options and select the second one (index 1)
                    logger.debug("Selecting the second option from dropdown")
                    # Wait a moment for all options to be fully loaded
                    page.wait_for_timeout(500)
                    
                    # Select the second option (index 1, since indexing starts at 0)
                    all_options = page.query_selector_all(project_option_selector_base)
                    if len(all_options) >= 2:
                        logger.debug(f"Found {len(all_options)} options, selecting option #2")
                        all_options[1].click()
                    else:
                        logger.warning(f"Not enough options found in dropdown (found {len(all_options)})")
                        # Fallback: try to click the first option that contains our target text
                        logger.debug(f"Falling back to text search for '{project_name_to_select}'")
                        page.click(specific_project_option_selector)

                    # Verify project selection
                    logger.debug(f"Verifying selection using selector: {selected_project_value_selector}")
                    page.wait_for_timeout(500) # Short wait for value to update
                    try:
                        # Wait for the selected value element to contain the project name
                        page.wait_for_selector(f"{selected_project_value_selector}:has-text('{project_name_to_select}')", timeout=3000)
                        selected_value = page.text_content(selected_project_value_selector, timeout=1000)
                        logger.info(f"Selected project verified: {selected_value}")
                        # Optional: More robust check if needed
                        # if project_name_to_select not in selected_value:
                        #     logger.warning(f"Selected project text '{selected_value}' does not exactly match '{project_name_to_select}'")
                    except PlaywrightTimeoutError:
                        selected_value_now = page.text_content(selected_project_value_selector, timeout=500) # Get current value if wait failed
                        logger.warning(f"Verification failed: Could not find '{project_name_to_select}' in selected value element '{selected_project_value_selector}'. Current value: '{selected_value_now}'")
                        # Consider taking a screenshot here for debugging
                        screenshot_path = Path("~/.Djin/logs/project_selection_verification_failed.png").expanduser()
                        page.screenshot(path=str(screenshot_path))
                        logger.warning(f"Screenshot saved to: {screenshot_path}")
                        # Decide if this should be a hard failure or just a warning
                        # return False # Uncomment to make it a hard failure


                    console.print("[green]Form fields pre-filled successfully.[/green]")
                    console.print("[cyan]Waiting 1 second before submitting form...[/cyan]")
                    page.wait_for_timeout(1000) # Wait before submitting
                    
                    # Submit the form by clicking the "Toevoegen" button
                    submit_button_selector = "button[data-testid='button']:has-text('Toevoegen')"
                    logger.debug(f"Clicking submit button: {submit_button_selector}")
                    page.click(submit_button_selector)
                    
                    console.print("[green]Form submitted successfully.[/green]")
                    console.print("[cyan]Waiting 1 second for visual confirmation...[/cyan]")
                    page.wait_for_timeout(1000) # Wait after submission for visual confirmation

                except PlaywrightTimeoutError as pte:
                    logger.error(f"Timeout error during form filling: {pte}")
                    console.print(f"[red]Error: Timeout while trying to fill form field. {pte}[/red]")
                    screenshot_path = Path("~/.Djin/logs/form_fill_timeout.png").expanduser()
                    page.screenshot(path=str(screenshot_path))
                    console.print(f"[red]Screenshot saved to: {screenshot_path}[/red]")
                    return False
                except Exception as fill_error:
                    logger.error(f"Error during form filling: {fill_error}", exc_info=True)
                    console.print(f"[red]Error: Could not pre-fill form fields: {fill_error}[/red]")
                    screenshot_path = Path("~/.Djin/logs/form_fill_error.png").expanduser()
                    page.screenshot(path=str(screenshot_path))
                    console.print(f"[red]Screenshot saved to: {screenshot_path}[/red]")
                    return False

            else:
                console.print(
                    "[yellow]Time entry page may not have loaded correctly (time input field not found). Cannot pre-fill form.[/yellow]"
                )
                screenshot_path = Path("~/.Djin/logs/time_input_not_found.png").expanduser()
                page.screenshot(path=str(screenshot_path))
                console.print(f"[yellow]Screenshot saved to: {screenshot_path}[/yellow]")
                return False

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
            "Register hours on MoneyMonk (Usage: /accounting register-hours YYYY-MM-DD hours description [--headless]). Uses BASE_TIME_ENTRY_URL from .env.",
        ),
        "accounting login": (
            login_command,
            "Test login, navigate to time entry page, and pre-fill form (Usage: /accounting login hours description [--headless] [--date=YYYY-MM-DD]).",
        ),
        # Add other accounting commands here
    }
    for name, (func, help_text) in commands_to_register.items():
        register_command(name, func, help_text)
    logger.info(f"Accounting commands registered: {list(commands_to_register.keys())}")


# No module-level side effects for registration
