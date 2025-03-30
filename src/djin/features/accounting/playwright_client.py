"""
Client for interacting with external websites using Playwright.

This module contains the logic to automate browser interactions
for tasks like registering hours on platforms like MoneyMonk using Playwright.
"""

import contextlib  # Use contextlib for managing Playwright instance
from pathlib import Path  # Import Path for handling file paths

import keyring  # Import keyring
import pyotp
from loguru import logger  # Import Loguru logger
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from djin.common.config import SERVICE_NAME, load_config  # Import SERVICE_NAME and load_config
from djin.common.errors import ConfigurationError, MoneyMonkError  # Import custom errors

# --- Helper Functions ---

# Timeout for Playwright operations (in milliseconds)
DEFAULT_TIMEOUT = 30 * 1000  # 30 seconds


def _get_moneymonk_credentials():
    """Loads MoneyMonk credentials from config and keyring."""
    import os

    # First try to get credentials from environment variables
    env_url = os.environ.get("LOGIN_URL")
    env_username = os.environ.get("EMAIL")
    env_password = os.environ.get("PASSWORD")
    env_totp = os.environ.get("TOTP_SECRET")

    # If all environment variables are present, use them
    if env_url and env_username and env_password and env_totp:
        logger.info("Using credentials from environment variables")
        return {"url": env_url, "username": env_username, "password": env_password, "totp_secret": env_totp}

    # Otherwise, fall back to config and keyring
    logger.info("Some credentials missing from environment, falling back to config and keyring")
    config = load_config()
    mm_config = config.get("moneymonk", {})

    # Use environment variables if available, otherwise use config values
    url = env_url or mm_config.get("url")
    username = env_username or mm_config.get("username")

    if not url or not username:
        raise ConfigurationError("MoneyMonk URL or username not configured. Please run 'djin --setup' or edit config.")

    # --- Secret Handling (Password & TOTP) ---
    # Use keyring to retrieve secrets, consistent with config.py
    logger.debug(f"Attempting to retrieve secrets for user '{username}' from keyring service '{SERVICE_NAME}'")

    # Construct keyring usernames based on the pattern in config.py
    # Assumes password handling is added to config.py setup
    password_key = f"moneymonk_password_{username}"  # Key used in config setup
    totp_key = f"moneymonk_totp_{username}"  # Key used in config setup

    password = keyring.get_password(SERVICE_NAME, password_key)
    totp_secret = keyring.get_password(SERVICE_NAME, totp_key)

    if not password:
        logger.error(
            f"MoneyMonk password not found in keyring for key '{password_key}' under service '{SERVICE_NAME}'."
        )
        raise ConfigurationError("MoneyMonk password not found in keyring. Please run 'djin --setup' to configure it.")
    if not totp_secret:
        logger.error(f"MoneyMonk TOTP secret not found in keyring for key '{totp_key}' under service '{SERVICE_NAME}'.")
        raise ConfigurationError(
            "MoneyMonk TOTP secret not found in keyring. Please run 'djin --setup' to configure it."
        )
    else:
        logger.debug("Successfully retrieved password and TOTP secret from keyring.")
    # --- End Secret Handling ---

    return {"url": url, "username": username, "password": password, "totp_secret": totp_secret}


# --- Context Manager for Playwright ---


@contextlib.contextmanager
def playwright_context(headless=False):
    """Provides a Playwright browser context."""
    pw = None
    browser = None
    context = None
    page = None
    try:
        pw = sync_playwright().start()
        # Launch Chromium by default. Can be configured later.
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT)  # Set default timeout for operations
        logger.info(f"Playwright browser launched (headless={headless}).")
        yield page
    except PlaywrightError as e:
        logger.error(f"Playwright setup failed: {e}")
        raise MoneyMonkError(f"Failed to initialize Playwright browser: {e}")
    finally:
        if page:
            try:
                page.close()
            except PlaywrightError as e:
                logger.warning(f"Error closing Playwright page: {e}")
        if context:
            try:
                context.close()
            except PlaywrightError as e:
                logger.warning(f"Error closing Playwright context: {e}")
        if browser:
            try:
                browser.close()
            except PlaywrightError as e:
                logger.warning(f"Error closing Playwright browser: {e}")
        if pw:
            try:
                pw.stop()
                logger.info("Playwright stopped.")
            except Exception as e:  # Catch broader exceptions on stop
                logger.warning(f"Error stopping Playwright: {e}")


# --- Main Functions ---


def register_hours_on_website(date: str, description: str, hours: float, headless=True) -> bool:
    """
    Logs into MoneyMonk and registers hours using Playwright.

    Args:
        date: The date for the hour registration (YYYY-MM-DD).
        description: The description of the work performed.
        hours: The number of hours to register.
        headless: Run the browser in headless mode (default True).

    Returns:
        True if registration was successful.

    Raises:
        ConfigurationError: If credentials or necessary URLs are not configured.
        MoneyMonkError: If login or registration fails due to Playwright or website issues.
    """
    logger.info(f"Attempting to register {hours} hours for {date} via Playwright (headless={headless})...")
    import os
    from datetime import datetime

    try:
        # --- Get Configuration ---
        # Try to get credentials and URLs from environment variables first
        email = os.environ.get("EMAIL")
        password = os.environ.get("PASSWORD")
        totp_secret = os.environ.get("TOTP_SECRET")
        login_url = os.environ.get("LOGIN_URL")
        base_time_entry_url = os.environ.get("BASE_TIME_ENTRY_URL")

        # If any login creds are missing, fall back to keyring
        if not all([email, password, totp_secret, login_url]):
            logger.info("Some login credentials missing from environment, falling back to config/keyring")
            creds = _get_moneymonk_credentials()
            email = email or creds["username"]
            password = password or creds["password"]
            totp_secret = totp_secret or creds["totp_secret"]
            login_url = login_url or creds["url"]

        # Check for base time entry URL (required)
        if not base_time_entry_url:
            raise ConfigurationError("BASE_TIME_ENTRY_URL not set in environment. Please add it to your .env file.")

        # --- Start Playwright ---
        with playwright_context(headless=headless) as page:
            # --- 1. Login ---
            logger.info(f"Logging into {login_url}...")
            page.goto(login_url)
            page.wait_for_timeout(2000)

            logger.debug("Entering credentials...")
            page.fill("#email", email)
            page.fill("#password", password)

            logger.debug("Clicking login button...")
            page.click("button[data-testid='button']")
            page.wait_for_timeout(2000)

            # Handle TOTP if needed
            # Updated selector based on previous command's findings
            totp_selector = "#tfaCode"  # Use #tfaCode instead of #code
            if page.is_visible(totp_selector):
                logger.info("TOTP code entry required.")
                totp_code = pyotp.TOTP(totp_secret).now()
                logger.info(f"Generated TOTP code: {totp_code}")
                page.fill(totp_selector, totp_code)
                logger.debug("Clicking submit button after TOTP...")
                page.click("button[data-testid='button']")
                page.wait_for_timeout(2000)
            else:
                logger.info("TOTP code entry not required.")

            # Check if login was successful
            if page.is_visible("#email") or page.is_visible("#password") or page.is_visible(totp_selector):
                error_msg = "Login failed. Still on login or TOTP screen."
                logger.error(error_msg)
                screenshot_path = Path("~/.Djin/logs/login_failure.png").expanduser()
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot_path))
                logger.error(f"Screenshot saved to: {screenshot_path}")
                raise MoneyMonkError(error_msg)

            logger.info("Login successful.")

            # --- 2. Navigate to Time Entry Page ---
            entry_date = date if date else datetime.now().strftime("%Y-%m-%d")
            registration_url = f"{base_time_entry_url}?date={entry_date}"
            logger.debug(f"Navigating to time registration page: {registration_url}")
            page.goto(registration_url)
            page.wait_for_timeout(3000)  # Slightly longer wait for page load

            # --- 3. Fill and Submit Time Entry Form ---
            logger.info("Attempting to fill and submit time entry form...")

            # Selectors based on correct implementation
            add_entry_button = "button:has-text('Add time entry')"
            # Modal selectors
            hours_selector = "input#time"  # Time input field
            desc_selector = "input#description"  # Description input field
            project_dropdown_trigger = 'div.react-select__control'  # Dropdown trigger
            project_option_selector_base = 'div[class*="react-select__option"]'  # Base selector for options
            project_name_to_select = "AION Titan Streaming PI"  # The specific project name (for verification)
            selected_project_value_selector = 'div[class*="react-select__single-value"]'  # Selector for chosen project display
            submit_button_selector = "button[data-testid='button']:has-text('Toevoegen')"  # Submit button

            # Click "Add time entry" button to open the modal
            if page.is_visible(add_entry_button):
                logger.debug("Clicking 'Add time entry' button...")
                page.click(add_entry_button)
                page.wait_for_timeout(1500)  # Wait for modal animation
            else:
                logger.warning("'Add time entry' button not found. Assuming modal is already open or not needed.")
                # Check if form fields are directly visible
                if not page.is_visible(hours_selector):
                    error_msg = "Cannot find 'Add time entry' button or time input field. Cannot proceed."
                    logger.error(error_msg)
                    screenshot_path = Path("~/.Djin/logs/add_entry_button_missing.png").expanduser()
                    page.screenshot(path=str(screenshot_path))
                    logger.error(f"Screenshot saved to: {screenshot_path}")
                    raise MoneyMonkError(error_msg)

            # Wait for modal form elements
            try:
                logger.debug("Waiting for form elements in modal...")
                page.wait_for_selector(hours_selector, state="visible", timeout=5000)
                page.wait_for_selector(desc_selector, state="visible", timeout=5000)
                page.wait_for_selector(project_dropdown_trigger, state="visible", timeout=5000)
                page.wait_for_selector(submit_button_selector, state="visible", timeout=5000)
                logger.debug("Modal form elements found.")
            except PlaywrightTimeoutError as e:
                error_msg = f"Timeout waiting for modal form elements: {e}"
                logger.error(error_msg)
                screenshot_path = Path("~/.Djin/logs/modal_form_timeout.png").expanduser()
                page.screenshot(path=str(screenshot_path))
                logger.error(f"Screenshot saved to: {screenshot_path}")
                raise MoneyMonkError(error_msg)

            # Fill hours
            logger.debug(f"Filling hours: {hours}")
            page.fill(hours_selector, str(hours))

            # Fill description
            logger.debug(f"Filling description: {description}")
            page.fill(desc_selector, description)

            # Select project (selecting the second option as per correct logic)
            logger.debug("Selecting project by choosing the second option in dropdown")
            logger.debug(f"Clicking project dropdown trigger: {project_dropdown_trigger}")
            page.click(project_dropdown_trigger)
            
            # Wait for dropdown options to appear
            logger.debug("Waiting for dropdown options to appear")
            page.wait_for_selector(project_option_selector_base, state="visible", timeout=5000)
            
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
                specific_project_option_selector = f"{project_option_selector_base}:has-text('{project_name_to_select}')"
                logger.debug(f"Falling back to text search for '{project_name_to_select}'")
                try:
                    page.click(specific_project_option_selector)
                except PlaywrightError as e:
                    logger.error(f"Failed to select project by text: {e}")
                    if len(all_options) > 0:
                        logger.warning("Falling back to first available option")
                        all_options[0].click()
                    else:
                        logger.error("No project options found in dropdown!")
                        # No need to raise here, let submission fail if project is mandatory

            # Verify project selection
            logger.debug(f"Verifying selection using selector: {selected_project_value_selector}")
            page.wait_for_timeout(500)  # Short wait for value to update
            try:
                # Wait for the selected value element to contain the project name
                page.wait_for_selector(f"{selected_project_value_selector}:has-text('{project_name_to_select}')", timeout=3000)
                selected_value = page.text_content(selected_project_value_selector, timeout=1000)
                logger.info(f"Selected project verified: {selected_value}")
            except PlaywrightTimeoutError:
                selected_value_now = page.text_content(selected_project_value_selector, timeout=500)  # Get current value if wait failed
                logger.warning(f"Verification failed: Could not find '{project_name_to_select}' in selected value element. Current value: '{selected_value_now}'")
                # Take a screenshot for debugging
                screenshot_path = Path("~/.Djin/logs/project_selection_verification_failed.png").expanduser()
                page.screenshot(path=str(screenshot_path))
                logger.warning(f"Screenshot saved to: {screenshot_path}")
                # Continue anyway - the selection might still be valid

            # Take screenshot before submission
            screenshot_path = Path("~/.Djin/logs/before_submit.png").expanduser()
            page.screenshot(path=str(screenshot_path))
            logger.debug(f"Screenshot before submission saved to {screenshot_path}")

            # Submit the form
            logger.debug(f"Clicking submit button: {submit_button_selector}")
            page.click(submit_button_selector)
            page.wait_for_timeout(3000)  # Wait for submission processing

            # --- 4. Verify Submission ---
            logger.info("Verifying submission...")
            screenshot_path = Path("~/.Djin/logs/after_submit.png").expanduser()
            page.screenshot(path=str(screenshot_path))
            logger.debug(f"Screenshot after submission saved to {screenshot_path}")

            # Check if the modal is closed (primary success indicator)
            # Use the submit button selector as a proxy for the modal being open
            if not page.is_visible(submit_button_selector):
                logger.info("Hour registration successful (modal likely closed).")
                # Optional: Verify entry appears in the list (can be flaky)
                try:
                    entry_selector = f"text={description}"
                    # Increase timeout slightly for list update
                    page.wait_for_selector(entry_selector, state="visible", timeout=5000)
                    logger.info(f"Verified: Found the newly added entry with description: '{description}'")
                except PlaywrightTimeoutError:
                    logger.warning(
                        f"Could not verify entry '{description}' in list after submission (may take time to appear)."
                    )
                except Exception as e:
                    logger.warning(f"Error verifying entry in list: {e}")
                return True
            else:
                # Modal is still open, check for errors within the modal
                logger.error("Hour registration failed (modal form still visible).")
                # Check for known error message patterns within the modal context if possible
                # Example: error_message_selector = f"{submit_button_selector} >> xpath=../.. >> .error-message"
                error_message = "Submission failed, form still visible."
                # You might need specific selectors for error messages within the modal
                # if page.is_visible("selector-for-modal-error"):
                #     error_message = page.text_content("selector-for-modal-error")

                raise MoneyMonkError(f"Hour registration failed: {error_message}")

    except (ConfigurationError, MoneyMonkError) as e:
        logger.error(f"MoneyMonk hour registration failed: {e}")
        raise  # Re-raise specific errors
    except PlaywrightTimeoutError as e:
        logger.error(f"Playwright operation timed out during registration: {e}")
        raise MoneyMonkError(f"Operation timed out during registration: {e}")  # Wrap as MoneyMonkError
    except PlaywrightError as e:
        logger.error(f"A Playwright error occurred during registration: {e}")
        raise MoneyMonkError(f"A browser automation error occurred during registration: {e}")  # Wrap as MoneyMonkError
    except Exception as e:
        logger.error(f"An unexpected error occurred during hour registration: {e}", exc_info=True)
        raise MoneyMonkError(f"An unexpected error during hour registration: {str(e)}")  # Wrap as MoneyMonkError
