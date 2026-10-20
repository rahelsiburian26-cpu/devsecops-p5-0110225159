"""
Unit tests for TaskFlow API.
Tests cover database CRUD operations, utility helpers, and API routes.
"""

import json
import unittest
from app import create_app
from app.config import TestingConfig
from app.database import (
    init_db, create_task, get_all_tasks, get_task_by_id,
    update_task, delete_task,
)
from app.utils import (
    validate_email, validate_task_status, validate_priority,
    sanitize_string, paginate, days_since, parse_iso_date,
)


class TestUtilityFunctions(unittest.TestCase):
    """Tests for app/utils.py helper functions."""

    # ── Email Validation ──────────────────────────────────────────────────────

    def test_valid_email(self):
        self.assertTrue(validate_email("user@example.com"))

    def test_valid_email_with_subdomain(self):
        self.assertTrue(validate_email("user@mail.example.org"))

    def test_invalid_email_no_at(self):
        self.assertFalse(validate_email("userexample.com"))

    def test_invalid_email_no_domain(self):
        self.assertFalse(validate_email("user@"))

    def test_invalid_email_empty(self):
        self.assertFalse(validate_email(""))

    # ── Status / Priority Validation ─────────────────────────────────────────

    def test_valid_task_statuses(self):
        for s in ("pending", "in_progress", "done", "cancelled"):
            self.assertTrue(validate_task_status(s))

    def test_invalid_task_status(self):
        self.assertFalse(validate_task_status("unknown"))

    def test_valid_priorities(self):
        for p in ("low", "medium", "high"):
            self.assertTrue(validate_priority(p))

    def test_invalid_priority(self):
        self.assertFalse(validate_priority("critical"))

    # ── Sanitize String ───────────────────────────────────────────────────────

    def test_sanitize_strips_whitespace(self):
        self.assertEqual(sanitize_string("  hello  "), "hello")

    def test_sanitize_truncates(self):
        self.assertEqual(len(sanitize_string("a" * 600, max_length=100)), 100)

    def test_sanitize_non_string(self):
        self.assertEqual(sanitize_string(123), "")

    # ── Paginate ──────────────────────────────────────────────────────────────

    def test_paginate_first_page(self):
        result = paginate(list(range(50)), page=1, per_page=10)
        self.assertEqual(result["items"], list(range(10)))
        self.assertEqual(result["total"], 50)
        self.assertEqual(result["total_pages"], 5)

    def test_paginate_last_page(self):
        result = paginate(list(range(25)), page=3, per_page=10)
        self.assertEqual(result["items"], [20, 21, 22, 23, 24])

    def test_paginate_empty_list(self):
        result = paginate([], page=1, per_page=10)
        self.assertEqual(result["items"], [])
        self.assertEqual(result["total"], 0)

    def test_paginate_invalid_page_defaults_to_one(self):
        result = paginate(list(range(5)), page=-1, per_page=10)
        self.assertEqual(result["page"], 1)

    # ── Date Helpers ─────────────────────────────────────────────────────────

    def test_parse_iso_date_valid(self):
        dt = parse_iso_date("2024-01-15T12:00:00")
        self.assertIsNotNone(dt)

    def test_parse_iso_date_invalid(self):
        self.assertIsNone(parse_iso_date("not-a-date"))

    def test_days_since_returns_int(self):
        result = days_since("2020-01-01T00:00:00")
        self.assertIsInstance(result, int)
        self.assertGreater(result, 0)

    def test_days_since_invalid_returns_minus_one(self):
        self.assertEqual(days_since("bad-date"), -1)


class TestDatabaseOperations(unittest.TestCase):
    """Tests for app/database.py CRUD functions using an in-memory DB."""

    def setUp(self):
        """Reinitialise the in-memory database before each test."""
        from app import database as db_module
        db_module._db_path = ":memory:"
        init_db()

    def test_create_task_returns_dict(self):
        task = create_task("Buy groceries")
        self.assertIsInstance(task, dict)
        self.assertEqual(task["title"], "Buy groceries")

    def test_create_task_default_status(self):
        task = create_task("Read a book")
        self.assertEqual(task["status"], "pending")

    def test_create_task_with_tags(self):
        task = create_task("Deploy app", tags=["devops", "ci"])
        self.assertIn("devops", task["tags"])

    def test_get_task_by_id(self):
        created = create_task("Test task")
        fetched = get_task_by_id(created["id"])
        self.assertEqual(fetched["id"], created["id"])

    def test_get_task_by_id_not_found(self):
        self.assertIsNone(get_task_by_id(999))

    def test_get_all_tasks_returns_list(self):
        create_task("Task A")
        create_task("Task B")
        tasks = get_all_tasks()
        self.assertGreaterEqual(len(tasks), 2)

    def test_get_all_tasks_filter_by_status(self):
        create_task("Pending task")
        t = create_task("Done task")
        update_task(t["id"], status="done")
        done = get_all_tasks(status="done")
        self.assertTrue(all(t["status"] == "done" for t in done))

    def test_update_task_status(self):
        task = create_task("Update me")
        updated = update_task(task["id"], status="in_progress")
        self.assertEqual(updated["status"], "in_progress")

    def test_update_task_title(self):
        task = create_task("Old title")
        updated = update_task(task["id"], title="New title")
        self.assertEqual(updated["title"], "New title")

    def test_delete_task_returns_true(self):
        task = create_task("Delete me")
        result = delete_task(task["id"])
        self.assertTrue(result)

    def test_delete_task_nonexistent_returns_false(self):
        self.assertFalse(delete_task(9999))

    def test_delete_task_removes_from_db(self):
        task = create_task("Gone task")
        delete_task(task["id"])
        self.assertIsNone(get_task_by_id(task["id"]))


class TestAPIRoutes(unittest.TestCase):
    """Integration tests for the Flask REST API endpoints."""

    def setUp(self):
        """Create a test Flask client with an in-memory database."""
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()

    def test_health_check(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "healthy")

    def test_create_task_success(self):
        resp = self.client.post(
            "/api/tasks/",
            data=json.dumps({"title": "New Task", "priority": "high"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data["title"], "New Task")

    def test_create_task_missing_title(self):
        resp = self.client.post(
            "/api/tasks/",
            data=json.dumps({"description": "No title here"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 422)

    def test_create_task_invalid_priority(self):
        resp = self.client.post(
            "/api/tasks/",
            data=json.dumps({"title": "Task", "priority": "urgent"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 422)

    def test_list_tasks(self):
        self.client.post(
            "/api/tasks/",
            data=json.dumps({"title": "Listed Task"}),
            content_type="application/json",
        )
        resp = self.client.get("/api/tasks/")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("tasks", data)

    def test_get_single_task(self):
        create_resp = self.client.post(
            "/api/tasks/",
            data=json.dumps({"title": "Single Task"}),
            content_type="application/json",
        )
        task_id = create_resp.get_json()["id"]
        resp = self.client.get(f"/api/tasks/{task_id}")
        self.assertEqual(resp.status_code, 200)

    def test_get_nonexistent_task(self):
        resp = self.client.get("/api/tasks/99999")
        self.assertEqual(resp.status_code, 404)

    def test_update_task(self):
        create_resp = self.client.post(
            "/api/tasks/",
            data=json.dumps({"title": "Original"}),
            content_type="application/json",
        )
        task_id = create_resp.get_json()["id"]
        resp = self.client.patch(
            f"/api/tasks/{task_id}",
            data=json.dumps({"status": "done"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "done")

    def test_delete_task(self):
        create_resp = self.client.post(
            "/api/tasks/",
            data=json.dumps({"title": "To Delete"}),
            content_type="application/json",
        )
        task_id = create_resp.get_json()["id"]
        resp = self.client.delete(f"/api/tasks/{task_id}")
        self.assertEqual(resp.status_code, 200)

    def test_delete_nonexistent_task(self):
        resp = self.client.delete("/api/tasks/99999")
        self.assertEqual(resp.status_code, 404)

    def test_filter_tasks_by_status(self):
        resp = self.client.get("/api/tasks/?status=pending")
        self.assertEqual(resp.status_code, 200)

    def test_filter_tasks_invalid_status(self):
        resp = self.client.get("/api/tasks/?status=invalid")
        self.assertEqual(resp.status_code, 400)

    def test_auth_login_success(self):
        resp = self.client.post(
            "/api/auth/login",
            data=json.dumps({"username": "testuser"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("token", resp.get_json())

    def test_auth_login_missing_username(self):
        resp = self.client.post(
            "/api/auth/login",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
