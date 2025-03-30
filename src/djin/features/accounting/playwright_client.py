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

    config = load_config()
    mm_config = config.get("moneymonk", {})

    # Use LOGIN_URL from environment if available, otherwise use URL from config
    url = os.environ.get("LOGIN_URL") or mm_config.get("url")
    username = mm_config.get("username")

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


def login_to_moneymonk(headless=True) -> bool:
    """
    Logs into the MoneyMonk website using Playwright.

    Args:
        headless: Run the browser in headless mode (default True).

    Returns:
        True if login is successful, False otherwise (though exceptions are preferred).

    Raises:
        ConfigurationError: If credentials are not configured.
        MoneyMonkError: If login fails due to Playwright execution or website issues.
    """
    logger.info(f"Attempting to log in to MoneyMonk via Playwright (headless={headless})...")
    try:
        creds = _get_moneymonk_credentials()
        totp_code = pyotp.TOTP(creds["totp_secret"]).now()
        logger.info("Generated TOTP code.")

        with playwright_context(headless=headless) as page:
            logger.debug(f"Navigating to {creds['url']}")
            page.goto(creds["url"])

            logger.debug("Waiting for login form elements.")
            page.wait_for_selector("#email", state="visible")
            page.wait_for_selector("#password", state="visible")
            page.wait_for_selector("button[data-testid='button']", state="visible")

            logger.debug("Entering credentials...")
            page.fill("#email", creds["username"])
            page.fill("#password", creds["password"])

            logger.debug("Clicking login button...")
            page.click("button[data-testid='button']")

            # Wait for potential navigation or TOTP page load
            page.wait_for_load_state("networkidle", timeout=10000)  # Wait max 10s for network idle

            # Check if TOTP is needed
            # Use page.is_visible() for a non-blocking check
            if page.is_visible("#code"):
                logger.info("TOTP code entry required.")
                page.fill("#code", totp_code)
                logger.debug("Clicking submit button after TOTP...")
                page.click("button[data-testid='button']")
                page.wait_for_load_state("networkidle", timeout=15000)  # Wait longer after TOTP
            else:
                logger.info("TOTP code entry not required or element not found.")

            # Basic check for successful login
            # Replace '#dashboard-element' with a reliable selector from the MoneyMonk dashboard
            # Example: Check if the URL contains '/dashboard' or a specific element exists
            dashboard_selector = "nav a[href*='/dashboard']"  # Example selector
            try:
                page.wait_for_selector(dashboard_selector, state="visible", timeout=10000)
                logger.info("Login successful (dashboard element found).")
                return True
            except PlaywrightTimeoutError:
                logger.error("Login potentially failed (dashboard element not found after timeout).")
                # Capture screenshot on failure for debugging
                screenshot_path = Path("~/.Djin/logs/login_failure.png").expanduser()
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot_path))
                logger.error(f"Screenshot saved to {screenshot_path}")
                raise MoneyMonkError("Login failed: Could not verify dashboard access.")

    except (ConfigurationError, MoneyMonkError) as e:
        logger.error(f"MoneyMonk login failed: {e}")
        raise
    except PlaywrightTimeoutError as e:
        logger.error(f"Playwright operation timed out during login: {e}")
        raise MoneyMonkError(f"Operation timed out during login: {e}")
    except PlaywrightError as e:
        logger.error(f"A Playwright error occurred during login: {e}")
        raise MoneyMonkError(f"A browser automation error occurred during login: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during MoneyMonk login: {e}", exc_info=True)
        raise MoneyMonkError(f"An unexpected error during login: {str(e)}")


def register_hours_on_website(date: str, description: str, hours: float, headless=True) -> bool:
    """
    Uses Playwright to register hours on the MoneyMonk website.

    Args:
        date: The date for the hour registration (YYYY-MM-DD).
        description: The description of the work performed.
        hours: The number of hours to register.
        headless: Run the browser in headless mode (default True).

    Returns:
        True if registration was successful.

    Raises:
        ConfigurationError: If credentials are not configured.
        MoneyMonkError: If registration fails.
    """
    logger.info(f"Attempting to register {hours} hours for {date} via Playwright (headless={headless})...")
    # Note: This assumes login happens implicitly or is handled separately.
    # A robust implementation might call login_to_moneymonk first or handle sessions.
    # For simplicity, we'll assume the user is logged in or the login function
    # establishes a persistent session if run in the same script execution.
    # A better approach would be to pass the 'page' object from login if needed.

    # --- THIS IS A PLACEHOLDER IMPLEMENTATION ---
    # The exact selectors and workflow depend heavily on MoneyMonk's actual UI.
    # You will need to inspect the MoneyMonk hour registration page
    # using browser developer tools to find the correct selectors.

    try:
        creds = _get_moneymonk_credentials()  # Needed for URL at least

        with playwright_context(headless=headless) as page:
            # 1. Login (Required before registering hours)
            #    We call the login function here to ensure we are logged in.
            #    This creates a new browser instance per operation, which is less efficient
            #    but simpler than managing shared browser state.
            logger.info("Ensuring login before registering hours...")
            login_success = login_to_moneymonk(headless=headless)  # Reuse the login function
            if not login_success:
                # The login function already raises MoneyMonkError on failure
                # but we add an explicit check here for clarity.
                raise MoneyMonkError("Login failed, cannot register hours.")
            logger.info("Login confirmed.")

            # 2. Navigate to the hour registration page
            #    Use BASE_TIME_ENTRY_URL from environment if available
            import os

            registration_url = os.environ.get("BASE_TIME_ENTRY_URL")
            if not registration_url:
                # Fall back to constructing URL from base URL if environment variable not set
                registration_url = f"{creds['url']}/path/to/hour/registration"  # <-- Replace this URL
            logger.debug(f"Navigating to hour registration page: {registration_url}")
            page.goto(registration_url)
            page.wait_for_load_state("networkidle")

            # 3. Fill in the form
            #    Replace selectors with actual ones from MoneyMonk
            date_selector = "#date-input"  # <-- Replace selector
            desc_selector = "#description-textarea"  # <-- Replace selector
            hours_selector = "#hours-input"  # <-- Replace selector
            project_selector = "#project-dropdown"  # <-- Replace selector (if needed)
            submit_button_selector = "button[type='submit']"  # <-- Replace selector

            logger.debug("Waiting for registration form elements.")
            page.wait_for_selector(date_selector, state="visible")
            page.wait_for_selector(desc_selector, state="visible")
            page.wait_for_selector(hours_selector, state="visible")
            # page.wait_for_selector(project_selector, state="visible") # If needed
            page.wait_for_selector(submit_button_selector, state="visible")

            logger.debug("Filling registration form...")
            page.fill(date_selector, date)  # Assumes YYYY-MM-DD format is accepted directly
            page.fill(desc_selector, description)
            page.fill(hours_selector, str(hours))  # Convert hours to string for input field

            # Handle project selection if necessary (example)
            # project_name = "Your Project Name" # <-- Get this dynamically if needed
            # page.select_option(project_selector, label=project_name)

            # 4. Submit the form
            logger.debug("Submitting hour registration form...")
            page.click(submit_button_selector)

            # 5. Check for success confirmation
            #    Replace with actual success indicator (e.g., a success message, URL change)
            success_indicator_selector = ".alert-success"  # <-- Replace selector
            try:
                page.wait_for_selector(success_indicator_selector, state="visible", timeout=15000)
                success_message = page.text_content(success_indicator_selector)
                logger.info(f"Hour registration successful. Confirmation: '{success_message}'")
                return True
            except PlaywrightTimeoutError:
                logger.error("Hour registration failed (success indicator not found).")
                # Capture screenshot on failure
                screenshot_path = Path("~/.Djin/logs/registration_failure.png").expanduser()
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot_path))
                logger.error(f"Screenshot saved to {screenshot_path}")
                raise MoneyMonkError("Hour registration failed: Confirmation not found.")

    except (ConfigurationError, MoneyMonkError) as e:
        logger.error(f"MoneyMonk hour registration failed: {e}")
        raise
    except PlaywrightTimeoutError as e:
        logger.error(f"Playwright operation timed out during registration: {e}")
        raise MoneyMonkError(f"Operation timed out during registration: {e}")
    except PlaywrightError as e:
        logger.error(f"A Playwright error occurred during registration: {e}")
        raise MoneyMonkError(f"A browser automation error occurred during registration: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during hour registration: {e}", exc_info=True)
        raise MoneyMonkError(f"An unexpected error during hour registration: {str(e)}")
