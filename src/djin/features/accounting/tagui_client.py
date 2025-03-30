"""
Client for interacting with external websites using TagUI (or similar).

This module will contain the logic to automate browser interactions
for tasks like registering hours on platforms like MoneyMonk.
"""

import subprocess
import time
from pathlib import Path

import keyring  # Import keyring
import pyotp
from loguru import logger  # Import Loguru logger

from djin.common.config import SERVICE_NAME, load_config  # Import SERVICE_NAME and load_config
from djin.common.errors import ConfigurationError, MoneyMonkError  # Import custom errors

# --- Helper Functions ---


def _get_moneymonk_credentials():
    """Loads MoneyMonk credentials from config and keyring."""
    config = load_config()
    mm_config = config.get("moneymonk", {})
    url = mm_config.get("url")
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


def _run_tagui_script(script_content: str, script_name: str = "temp_script") -> bool:
    """
    Runs a TagUI script saved to a temporary file.

    Args:
        script_content: The content of the TagUI script.
        script_name: A base name for the temporary script file.

    Returns:
        True if the script executed successfully (exit code 0), False otherwise.

    Raises:
        MoneyMonkError: If TagUI command is not found or execution fails unexpectedly.
    """
    # Use Djin's config dir for temp files
    temp_dir = Path("~/.Djin/temp").expanduser()
    temp_dir.mkdir(parents=True, exist_ok=True)
    script_path = temp_dir / f"{script_name}_{int(time.time())}.tag"

    try:
        # Write script to temp file
        with open(script_path, "w") as f:
            f.write(script_content)
        logger.debug(f"TagUI script written to: {script_path}")

        # Execute TagUI script
        # Assumes 'tagui' command is in the system PATH
        # Use -q for quieter execution, remove if debugging needed
        command = ["tagui", str(script_path), "-q"]
        logger.info(f"Executing TagUI command: {' '.join(command)}")
        result = subprocess.run(
            command, capture_output=True, text=True, check=False
        )  # check=False to handle errors manually

        logger.debug(f"TagUI stdout:\n{result.stdout}")
        logger.debug(f"TagUI stderr:\n{result.stderr}")

        if result.returncode != 0:
            error_message = f"TagUI script execution failed with exit code {result.returncode}."
            logger.error(error_message)
            logger.error(f"TagUI stderr: {result.stderr}")
            # Consider including stderr in the exception for more context
            raise MoneyMonkError(f"{error_message} See logs for details.")
        else:
            # Basic success check: Look for common failure indicators in output
            # This might need refinement based on actual MoneyMonk/TagUI output on failure
            if "error" in result.stdout.lower() or "fail" in result.stdout.lower():
                logger.warning("TagUI script finished but output suggests potential failure.")
                # Decide if this should be treated as an error
                # return False # Or raise MoneyMonkError
            logger.info("TagUI script executed successfully.")
            return True

    except FileNotFoundError:
        logger.error("TagUI command not found. Is TagUI installed and in PATH?")
        raise MoneyMonkError("TagUI command not found. Please ensure TagUI is installed and accessible in your PATH.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during TagUI execution: {e}", exc_info=True)
        raise MoneyMonkError(f"An unexpected error occurred during TagUI execution: {str(e)}")
    finally:
        # Clean up the temporary script file
        if script_path.exists():
            try:
                script_path.unlink()
                logger.debug(f"Temporary TagUI script deleted: {script_path}")
            except OSError as e:
                logger.warning(f"Could not delete temporary TagUI script {script_path}: {e}")


# --- Main Functions ---


def login_to_moneymonk() -> bool:
    """
    Logs into the MoneyMonk website using TagUI.

    Returns:
        True if login is successful, False otherwise.

    Raises:
        ConfigurationError: If credentials are not configured.
        MoneyMonkError: If login fails due to TagUI execution or website issues.
    """
    logger.info("Attempting to log in to MoneyMonk...")
    try:
        creds = _get_moneymonk_credentials()
        totp_code = pyotp.TOTP(creds["totp_secret"]).now()
        logger.info("Generated TOTP code.")

        # Construct TagUI script
        # Using f-string requires escaping curly braces {{ }} for TagUI variables/syntax
        # It's often cleaner to use .format() or build the string step-by-step
        script = f"""
// TagUI script to log in to MoneyMonk
{creds["url"]}
wait 2 seconds // Wait for page load

// Enter credentials
type #email as {creds["username"]}
type #password as {creds["password"]}
click button[data-testid="button"]
wait 2 seconds // Wait for potential redirect or TOTP page load

// Check if TOTP is needed (presence of #code field)
present #code
if result == true {{
    echo 'TOTP code entry required.'
    type #code as {totp_code}
    click button[data-testid="button"]
    wait 2 seconds // Wait for post-TOTP login
}} else {{
    echo 'TOTP code entry not required or element not found.'
}}

// Basic check for successful login (e.g., check URL or presence of a dashboard element)
// Replace '#dashboard-element' with an actual selector from the MoneyMonk dashboard
present #dashboard-element
if result == true {{
    echo 'Login successful (dashboard element found).'
}} else {{
    echo 'Login potentially failed (dashboard element not found).'
    // Consider adding 'fail' step here to make TagUI exit with error code
    // fail
}}
"""
        logger.debug("Constructed TagUI login script.")
        return _run_tagui_script(script, "moneymonk_login")

    except (ConfigurationError, MoneyMonkError) as e:
        # Log already happened in helper or here
        logger.error(f"MoneyMonk login failed: {e}")
        raise  # Re-raise the specific error
    except Exception as e:
        logger.error(f"An unexpected error occurred during MoneyMonk login: {e}", exc_info=True)
        raise MoneyMonkError(f"An unexpected error during login: {str(e)}")


# Placeholder function - Implement actual TagUI interaction here
def register_hours_on_website(date: str, description: str, hours: float) -> bool:
    """
    Uses TagUI (or another automation tool) to register hours on the target website.

    Args:
        date: The date for the hour registration (e.g., "YYYY-MM-DD").
        description: The description of the work performed.
        hours: The number of hours to register.

    Returns:
        True if registration was successful, False otherwise.

    Raises:
        NotImplementedError: This is a placeholder.
    """
    logger.info(f"Attempting to register {hours} hours for {date} with description: '{description}'")
    # TODO: Implement the actual TagUI automation script execution
    # Example steps:
    # 1. Launch browser to the specific website (e.g., MoneyMonk)
    # 2. Log in (handle credentials securely)
    # 3. Navigate to the hour registration page
    # 4. Fill in the date, description, and hours
    # 5. Submit the form
    # 6. Check for success confirmation
    logger.warning("TagUI interaction for register_hours_on_website is not implemented yet.")
    raise NotImplementedError("TagUI interaction for register_hours_on_website needs implementation.")
    # return True # Or False based on actual result
