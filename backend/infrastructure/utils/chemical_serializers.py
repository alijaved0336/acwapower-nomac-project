"""
Serialization utilities for chemical data responses.

This module provides helper functions to convert various data types
(datetime, Decimal, numpy types) to JSON-serializable formats for API responses.
"""

from datetime import date, datetime
from decimal import Decimal
import numpy as np
from infrastructure.utils.datetime_utils import DateTimeParser


def _jsonify_scalar(v):
    """
    Convert a scalar value to a JSON-serializable format.

    Args:
        v: Value to convert (datetime, date, Decimal, numpy generic, or other)

    Returns:
        JSON-serializable representation of the value
    """
    if isinstance(v, datetime):
        # Format datetime without timezone for API responses
        return DateTimeParser.format_datetime_without_timezone(v)
    if isinstance(v, date):
        # Date objects don't have timezone, format as YYYY-MM-DD
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, np.generic):
        return np.asarray(v).item()
    return v


def _jsonify_row(row):
    """
    Convert a row (dict, list, tuple, or scalar) to JSON-serializable format.

    Args:
        row: Row data to convert

    Returns:
        JSON-serializable representation of the row
    """
    if isinstance(row, dict):
        return {k: _jsonify_scalar(v) for k, v in row.items()}
    if isinstance(row, (list, tuple)):
        return [_jsonify_scalar(v) for v in row]
    return _jsonify_scalar(row)


def serialize_column_responses(responses):
    """
    Serialize a list of ColumnResponse objects to JSON-compatible format.

    Handles both object-based ColumnResponse instances and dictionary representations.
    Converts all data types to JSON-serializable formats.

    Args:
        responses: List of ColumnResponse objects or dictionaries

    Returns:
        List of dictionaries with serialized column data
    """
    out = []
    for r in (responses or []):
        # ColumnResponse object -> dict
        if hasattr(r, "__dict__"):
            # Be explicit to avoid private attributes
            col = getattr(r, "columnName", None)
            ctype = getattr(r, "columnType", None)
            tname = getattr(r, "tableName", None)
            sname = getattr(r, "siteName", None)
            ds = getattr(r, "dataSource", None)
            racks = getattr(r, "racks", None)
            result_dict = {
                "columnName": col,
                "columnType": ctype,
                "tableName": tname,
                "siteName": sname,
                "dataSource": [_jsonify_row(x) for x in (ds or [])],
            }
            # Include racks if it's not None
            if racks is not None:
                result_dict["racks"] = racks
            out.append(result_dict)
        elif isinstance(r, dict):
            # Already a dict - still normalize any dataSource
            if "dataSource" in r:
                r = {**r, "dataSource": [_jsonify_row(x) for x in (r["dataSource"] or [])]}
            # Include racks if present
            if "racks" in r:
                r["racks"] = r["racks"]
            out.append(r)
        else:
            # Last-resort fallback
            out.append(_jsonify_scalar(r))
    return out
