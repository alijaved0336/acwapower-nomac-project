"""
Custom exception classes for the SWRO infrastructure layer.
These exceptions provide structured error handling with proper context.
"""


class ClickHouseServiceError(Exception):
    """
    Base exception for ClickHouse service-related errors.
    Used for database connection failures, query execution errors, etc.
    """
    def __init__(self, message: str, context: dict = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.message)

    def __str__(self):
        if self.context:
            return f"{self.message} | Context: {self.context}"
        return self.message


class DataValidationError(Exception):
    """
    Exception for data validation failures.
    Used when input data doesn't meet required constraints or schema.
    """
    def __init__(self, message: str, field: str = None, value=None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)

    def __str__(self):
        parts = [self.message]
        if self.field:
            parts.append(f"Field: {self.field}")
        if self.value is not None:
            parts.append(f"Value: {self.value}")
        return " | ".join(parts)


class ColumnNotFoundError(DataValidationError):
    """
    Exception raised when a required column is not found in the table.
    """
    def __init__(self, column_name: str, table_name: str = None):
        message = f"Column '{column_name}' not found"
        if table_name:
            message += f" in table '{table_name}'"
        super().__init__(message, field=column_name, value=table_name)


class InvalidColumnNameError(DataValidationError):
    """
    Exception raised when a column name fails validation.
    Used to prevent SQL injection through dynamic column names.
    """
    def __init__(self, column_name: str):
        message = f"Invalid column name: '{column_name}'. Column names must contain only alphanumeric characters and underscores."
        super().__init__(message, field="column_name", value=column_name)


class PaginationError(Exception):
    """
    Exception for pagination-related errors.
    Used when page/limit parameters are invalid or cause issues.
    """
    def __init__(self, message: str, page: int = None, limit: int = None):
        self.message = message
        self.page = page
        self.limit = limit
        super().__init__(self.message)

    def __str__(self):
        parts = [self.message]
        if self.page is not None:
            parts.append(f"Page: {self.page}")
        if self.limit is not None:
            parts.append(f"Limit: {self.limit}")
        return " | ".join(parts)


class TableNotFoundError(ClickHouseServiceError):
    """
    Exception raised when a required table is not found in the database.
    """
    def __init__(self, table_name: str, site_name: str = None):
        message = f"Table '{table_name}' not found"
        context = {"table_name": table_name}
        if site_name:
            message += f" for site '{site_name}'"
            context["site_name"] = site_name
        super().__init__(message, context=context)
