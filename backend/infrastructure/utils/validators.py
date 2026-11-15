import re
import uuid


def validate_uuid_format(uuid_string):
    """
    Validates if a string is a valid UUID format.

    Args:
        uuid_string (str): String to validate as UUID

    Returns:
        tuple: (is_valid: bool, error_message: str or None)

    Examples:
        >>> validate_uuid_format("550e8400-e29b-41d4-a716-446655440000")
        (True, None)

        >>> validate_uuid_format("invalid-uuid")
        (False, "Invalid UUID format")

        >>> validate_uuid_format("")
        (False, "UUID cannot be empty")
    """
    if not uuid_string or not uuid_string.strip():
        return False, "UUID cannot be empty"

    uuid_string = uuid_string.strip()

    # Check basic UUID pattern (8-4-4-4-12 hexadecimal digits)
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
    )

    if not uuid_pattern.match(uuid_string):
        return (
            False,
            "Invalid UUID format. Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        )

    # Additional validation using Python's uuid module
    try:
        uuid_obj = uuid.UUID(uuid_string)
        # Ensure the string representation matches (catches edge cases)
        if str(uuid_obj).lower() != uuid_string.lower():
            return False, "Invalid UUID format"
        return True, None
    except ValueError:
        return False, "Invalid UUID format"


def validate_user_id(user_id):
    """
    Validates user_id parameter specifically.

    Args:
        user_id (str): User ID to validate

    Returns:
        tuple: (is_valid: bool, error_message: str or None)

    Examples:
        >>> validate_user_id("550e8400-e29b-41d4-a716-446655440000")
        (True, None)

        >>> validate_user_id("invalid")
        (False, "Invalid user_id format. Must be a valid UUID.")
    """
    if not user_id or not isinstance(user_id, str):
        return False, "user_id parameter is required and must be a string"

    is_valid, error_msg = validate_uuid_format(user_id)

    if not is_valid:
        return False, f"Invalid user_id format. Must be a valid UUID. {error_msg}"

    return True, None
