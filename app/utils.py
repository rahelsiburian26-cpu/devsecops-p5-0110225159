"""
Utility helpers for TaskFlow API.
Provides input validation, response formatting, and date helpers.
"""

import re
from datetime import datetime, timezone


# ── Validation Helpers ────────────────────────────────────────────────────────

def validate_email(email: str) -> bool:
    """Return True if the string looks like a valid e-mail address."""
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_task_status(status: str) -> bool:
    """Return True if the status is one of the allowed task statuses."""
    return status in {"pending", "in_progress", "done", "cancelled"}


def validate_priority(priority: str) -> bool:
    """Return True if the priority level is valid."""
    return priority in {"low", "medium", "high"}


def sanitize_string(value: str, max_length: int = 500) -> str:
    """Strip whitespace and truncate a string to max_length characters."""
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_length]


# ── Response Formatters ───────────────────────────────────────────────────────

def success_response(data, message: str = "Success", status_code: int = 200) -> dict:
    """Build a standard success response envelope."""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": utc_now_iso(),
    }, status_code


def error_response(message: str, status_code: int = 400, details: dict = None) -> tuple:
    """Build a standard error response envelope."""
    body = {
        "success": False,
        "error": message,
        "timestamp": utc_now_iso(),
    }
    if details:
        body["details"] = details
    return body, status_code


# ── Date / Time Helpers ───────────────────────────────────────────────────────

def utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def parse_iso_date(date_str: str):
    """
    Parse an ISO-8601 datetime string.
    Returns a datetime object or None if parsing fails.
    """
    try:
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None


def days_since(date_str: str) -> int:
    """
    Compute the number of whole days between date_str and now (UTC).
    Returns -1 if date_str cannot be parsed.
    """
    parsed = parse_iso_date(date_str)
    if parsed is None:
        return -1
    now = datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (now - parsed).days


# ── Pagination Helper ─────────────────────────────────────────────────────────

def paginate(items: list, page: int = 1, per_page: int = 20) -> dict:
    """
    Slice a list into pages and return pagination metadata.

    Args:
        items:    The full list of items to paginate.
        page:     1-based page number.
        per_page: Number of items per page.

    Returns:
        A dict with keys: items, page, per_page, total, total_pages.
    """
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 20
    total = len(items)
    total_pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "items": items[start:end],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
    }
