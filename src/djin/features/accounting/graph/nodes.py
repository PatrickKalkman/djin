"""
Node definitions for accounting workflows.
"""
from datetime import datetime

from datetime import datetime

from loguru import logger # Import Loguru logger
# Import Playwright exceptions and the actual client function
from playwright.sync_api import Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError

# Import the actual Playwright client function
from djin.features.accounting.playwright_client import register_hours_on_website
from djin.common.errors import MoneyMonkError # Import MoneyMonkError for specific handling

# Loguru logger is imported directly


def validate_input_node(state):
    """Validate the input data for hour registration."""
    logger.debug(f"Validating input: Date='{state.date}', Hours='{state.hours}', Desc='{state.description}'")
    errors = []
    hours_float = None

    # Validate date
    try:
        datetime.strptime(state.date, "%Y-%m-%d")
    except ValueError:
        errors.append(f"Invalid date format: '{state.date}'. Please use YYYY-MM-DD.")

    # Validate description
    if not state.description or not state.description.strip():
        errors.append("Description cannot be empty.")

    # Validate hours (assuming hours are passed as string initially if coming from CLI args)
    # If hours are already float, this validation might be simpler
    try:
        # Example: Assuming hours might come as a string that needs conversion
        # If hours are passed directly as float, adjust this logic
        if isinstance(state.hours, str):
             hours_float = float(state.hours)
        elif isinstance(state.hours, (int, float)):
             hours_float = float(state.hours)
        else:
            raise ValueError("Hours must be a number.")

        if hours_float <= 0:
            errors.append("Hours must be a positive number.")
        # Add more specific hour validation if needed (e.g., max hours per entry)
    except (ValueError, TypeError):
        errors.append(f"Invalid hours value: '{state.hours}'. Please provide a positive number.")

    if errors:
        logger.warning(f"Input validation failed: {errors}")
        return {"validation_errors": errors, "errors": state.errors + errors}
    else:
        logger.debug("Input validation successful.")
        # Ensure hours are stored as float after validation
        return {"hours": hours_float, "validation_errors": []}


def register_hours_node(state):
    """Execute the TagUI script to register hours."""
    # Check if validation failed in the previous step
    if state.validation_errors:
        logger.warning("Skipping hour registration due to previous validation errors.")
        # Ensure the error state is propagated
        return {"registration_successful": False,
                "registration_message": "Input validation failed.",
                "errors": state.errors} # Keep existing errors

    logger.info(f"Attempting to register hours for {state.date} via Playwright.")
    # Default to non-headless mode so user can see what's happening
    headless = False
    try:
        # Call the actual Playwright client function
        # Ensure state.hours is float here (validated in previous node)
        success = register_hours_on_website(state.date, state.description, state.hours, headless=headless)

        if success:
            logger.info("Playwright: Hour registration reported successful.")
            return {"registration_successful": True, "registration_message": "Hours registered successfully via Playwright."}
        else:
            # This path might not be reached if register_hours_on_website raises exceptions on failure
            logger.error("Playwright: Hour registration function returned False.")
            error_msg = "Hour registration failed via Playwright (returned False)."
            return {"registration_successful": False, "registration_message": error_msg, "errors": state.errors + [error_msg]}
    except MoneyMonkError as e: # Catch errors raised by our client
         logger.error(f"Hour registration failed: {e}")
         # Use the error message from the exception
         return {"registration_successful": False, "registration_message": str(e), "errors": state.errors + [str(e)]}
    except (PlaywrightTimeoutError, PlaywrightError) as e: # Catch specific Playwright errors
        logger.error(f"Playwright error during hour registration: {e}")
        error_msg = f"Browser automation error during registration: {str(e)}"
        return {"registration_successful": False, "registration_message": error_msg, "errors": state.errors + [error_msg]}
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"Unexpected error during hour registration node: {e}", exc_info=True)
        error_msg = f"An unexpected error occurred during hour registration: {str(e)}"
        return {"registration_successful": False, "registration_message": error_msg, "errors": state.errors + [error_msg]}


def format_output_node(state):
    """Format the final output message."""
    if state.registration_successful:
        output = f"[green]Success:[/green] {state.registration_message}"
    elif state.validation_errors:
         # Prioritize validation errors for output if they exist
         output = "[red]Error:[/red] Input validation failed:\n- " + "\n- ".join(state.validation_errors)
    elif state.errors:
        # Show other errors if validation passed but registration failed
        output = f"[red]Error:[/red] {state.registration_message or '; '.join(state.errors)}"
    else:
        # Fallback for unexpected states
        output = "[yellow]Unknown outcome for hour registration.[/yellow]"

    logger.debug(f"Formatted output: {output}")
    # Return final state including the formatted output and any errors collected
    return {"formatted_output": output, "errors": state.errors}
