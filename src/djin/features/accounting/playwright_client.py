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
        # Get credentials from environment variables first, then fall back to keyring
        import os

        # Try to get credentials from environment variables first
        email = os.environ.get("EMAIL")
        password = os.environ.get("PASSWORD")
        totp_secret = os.environ.get("TOTP_SECRET")
        login_url = os.environ.get("LOGIN_URL")

        # If any are missing, fall back to keyring
        if not all([email, password, totp_secret, login_url]):
            logger.info("Some credentials missing from environment, falling back to keyring")
            creds = _get_moneymonk_credentials()
            email = email or creds["username"]
            password = password or creds["password"]
            totp_secret = totp_secret or creds["totp_secret"]
            login_url = login_url or creds["url"]

        logger.info(f"Using login URL: {login_url}")

        with playwright_context(headless=headless) as page:
            # Step 1: Navigate to login page
            logger.debug(f"Navigating to {login_url}")
            page.goto(login_url)

            # Add a small delay to ensure page is fully loaded (similar to Selenium example)
            page.wait_for_timeout(2000)  # 2 seconds

            # Step 2: Enter credentials
            logger.debug("Entering credentials...")
            page.fill("#email", email)
            page.fill("#password", password)

            # Step 3: Click login button
            logger.debug("Clicking login button...")
            page.click("button[data-testid='button']")

            # Add a small delay to allow for redirects (similar to Selenium example)
            page.wait_for_timeout(2000)  # 2 seconds

            # Step 4: Handle TOTP if needed
            # Take a screenshot before TOTP (for debugging)
            screenshot_path = Path("~/.Djin/logs/before_totp.png").expanduser()
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot_path))

            # Check if TOTP field is visible
            if page.is_visible("#code"):
                logger.info("TOTP code entry required.")
                # Generate TOTP code
                totp_code = pyotp.TOTP(totp_secret).now()
                logger.info(f"Generated TOTP code: {totp_code}")

                # Enter TOTP code
                page.fill("#code", totp_code)

                # Click submit button
                logger.debug("Clicking submit button after TOTP...")
                page.click("button[data-testid='button']")

                # Add a delay after TOTP submission (similar to Selenium example)
                page.wait_for_timeout(2000)  # 2 seconds
            else:
                logger.info("TOTP code entry not required (code field not visible).")

            # Take a screenshot after login attempt (for debugging)
            screenshot_path = Path("~/.Djin/logs/after_login.png").expanduser()
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot_path))

            # Log the current URL for debugging
            logger.debug(f"Current URL after login attempt: {page.url}")

            # Check if we're still on the login or TOTP screen
            if page.is_visible("#email") or page.is_visible("#password"):
                raise MoneyMonkError("Login failed: Still on login screen. Credentials may be incorrect.")

            if page.is_visible("#code"):
                raise MoneyMonkError("Login failed: Still on TOTP screen. TOTP code may be incorrect or not accepted.")

            # If we're not on login or TOTP screens, assume success
            logger.info("Login successful (no longer on login/TOTP screens).")
            return True

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

    try:
        # First, we need to log in
        logger.info("Starting with login process...")

        # Create a new browser context
        with playwright_context(headless=headless) as page:
            # 1. Login first
            import os

            # Try to get credentials from environment variables first
            email = os.environ.get("EMAIL")
            password = os.environ.get("PASSWORD")
            totp_secret = os.environ.get("TOTP_SECRET")
            login_url = os.environ.get("LOGIN_URL")

            # If any are missing, fall back to keyring
            if not all([email, password, totp_secret, login_url]):
                logger.info("Some credentials missing from environment, falling back to keyring")
                creds = _get_moneymonk_credentials()
                email = email or creds["username"]
                password = password or creds["password"]
                totp_secret = totp_secret or creds["totp_secret"]
                login_url = login_url or creds["url"]

            # Step 1: Navigate to login page
            logger.debug(f"Navigating to {login_url}")
            page.goto(login_url)

            # Add a small delay to ensure page is fully loaded
            page.wait_for_timeout(2000)  # 2 seconds

            # Step 2: Enter credentials
            logger.debug("Entering credentials...")
            page.fill("#email", email)
            page.fill("#password", password)

            # Step 3: Click login button
            logger.debug("Clicking login button...")
            page.click("button[data-testid='button']")

            # Add a small delay to allow for redirects
            page.wait_for_timeout(2000)  # 2 seconds

            # Step 4: Handle TOTP if needed
            if page.is_visible("#code"):
                logger.info("TOTP code entry required.")
                # Generate TOTP code
                totp_code = pyotp.TOTP(totp_secret).now()
                logger.info(f"Generated TOTP code: {totp_code}")

                # Enter TOTP code
                page.fill("#code", totp_code)

                # Click submit button
                logger.debug("Clicking submit button after TOTP...")
                page.click("button[data-testid='button']")

                # Add a delay after TOTP submission
                page.wait_for_timeout(2000)  # 2 seconds
            else:
                logger.info("TOTP code entry not required (code field not visible).")

            # Check if login was successful
            if page.is_visible("#email") or page.is_visible("#password") or page.is_visible("#code"):
                raise MoneyMonkError("Login failed, cannot register hours.")

            logger.info("Login successful, proceeding to hour registration.")

            # 2. Navigate to the hour registration page
            # Format the URL with the date parameter
            from datetime import datetime

            # Use the provided date or today's date if not specified
            entry_date = date if date else datetime.now().strftime("%Y-%m-%d")

            # Get the base URL from environment
            base_time_entry_url = os.environ.get("BASE_TIME_ENTRY_URL")
            if not base_time_entry_url:
                # If not set in environment, raise an error
                raise ConfigurationError("BASE_TIME_ENTRY_URL not set in environment. Please add it to your .env file.")

            # Add the date parameter
            registration_url = f"{base_time_entry_url}?date={entry_date}"

            logger.debug(f"Navigating to hour registration page: {registration_url}")
            page.goto(registration_url)

            # Add a delay to ensure page is fully loaded
            page.wait_for_timeout(2000)  # 2 seconds

            # Take a screenshot of the registration page for debugging
            screenshot_path = Path("~/.Djin/logs/registration_page.png").expanduser()
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot_path))
            logger.debug(f"Screenshot of registration page saved to {screenshot_path}")

            # 3. Fill in the form with MoneyMonk's actual selectors
            # The date is already set in the URL, so we don't need to fill it in the form

            # Look for the "Add time entry" button and click it
            add_entry_button = "button:has-text('Add time entry')"
            logger.debug("Looking for 'Add time entry' button...")

            if page.is_visible(add_entry_button):
                logger.debug("Clicking 'Add time entry' button...")
                page.click(add_entry_button)
                page.wait_for_timeout(1000)  # Wait for modal to appear

            # Now fill in the form in the modal
            # Note: We don't need a date selector since the date is in the URL
            date_selector = None  # Define it but we won't use it for filling
            desc_selector = "textarea[placeholder='Description']"
            hours_selector = "input[placeholder='Hours']"
            submit_button_selector = "button:has-text('Save')"

            # Log the current page content for debugging
            logger.debug(f"Current page content: {page.content()}")

            # Wait for form elements with explicit timeouts
            try:
                # We don't need to wait for date input since it's in the URL
                # logger.debug("Waiting for date input field...")
                # page.wait_for_selector(date_selector, state="visible", timeout=5000)

                logger.debug("Waiting for description field...")
                page.wait_for_selector(desc_selector, state="visible", timeout=5000)

                logger.debug("Waiting for hours field...")
                page.wait_for_selector(hours_selector, state="visible", timeout=5000)

                logger.debug("Waiting for submit button...")
                page.wait_for_selector(submit_button_selector, state="visible", timeout=5000)
            except PlaywrightTimeoutError as e:
                logger.error(f"Timeout waiting for form elements: {e}")
                screenshot_path = Path("~/.Djin/logs/form_timeout.png").expanduser()
                page.screenshot(path=str(screenshot_path))
                logger.error(f"Screenshot saved to {screenshot_path}")
                raise MoneyMonkError(f"Could not find registration form elements: {e}")

            # Fill in the form
            # We don't need to fill the date field since it's in the URL
            # logger.debug(f"Filling date field with: {date}")
            # page.fill(date_selector, date)

            logger.debug(f"Filling description field with: {description}")
            page.fill(desc_selector, description)

            logger.debug(f"Filling hours field with: {hours}")
            page.fill(hours_selector, str(hours))

            # Take a screenshot before submission
            screenshot_path = Path("~/.Djin/logs/before_submit.png").expanduser()
            page.screenshot(path=str(screenshot_path))
            logger.debug(f"Screenshot before submission saved to {screenshot_path}")

            # Submit the form
            logger.debug("Clicking submit button...")
            page.click(submit_button_selector)

            # Add a delay after submission
            page.wait_for_timeout(3000)  # 3 seconds

            # Take a screenshot after submission
            screenshot_path = Path("~/.Djin/logs/after_submit.png").expanduser()
            page.screenshot(path=str(screenshot_path))
            logger.debug(f"Screenshot after submission saved to {screenshot_path}")

            # Check for success indicators
            # In MoneyMonk, success might be indicated by:
            # 1. The modal closing
            # 2. The new entry appearing in the list
            # 3. A toast notification

            # Wait a moment for any animations to complete
            page.wait_for_timeout(2000)

            # Take a screenshot after submission for verification
            screenshot_path = Path("~/.Djin/logs/after_submit_final.png").expanduser()
            page.screenshot(path=str(screenshot_path))
            logger.debug(f"Final screenshot saved to {screenshot_path}")

            # Check if the modal is closed (success indicator)
            if not page.is_visible(desc_selector) and not page.is_visible(hours_selector):
                logger.info("Hour registration successful (form modal closed).")

                # Look for the entry in the list (optional verification)
                try:
                    # Look for an entry with our description
                    entry_selector = f"text={description}"
                    if page.is_visible(entry_selector):
                        logger.info(f"Found the newly added entry with description: {description}")
                    else:
                        logger.info("Entry added but not immediately visible in the list.")
                except Exception as e:
                    logger.warning(f"Could not verify entry in list: {e}")

                return True

            # If we're still seeing the form, it might indicate failure
            if page.is_visible(desc_selector) or page.is_visible(hours_selector):
                logger.error("Hour registration failed (form still visible).")

                # Check for error messages
                error_selectors = [".error-message", ".alert-error", "text=Error", "text=Failed"]

                error_message = "Unknown error"
                for selector in error_selectors:
                    if page.is_visible(selector):
                        try:
                            error_message = page.text_content(selector)
                            logger.error(f"Error message found: {error_message}")
                            break
                        except Exception:
                            pass

                raise MoneyMonkError(f"Hour registration failed: {error_message}")

            # If we can't determine success or failure, assume success
            logger.info("Hour registration likely successful (no error indicators).")
            return True

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
