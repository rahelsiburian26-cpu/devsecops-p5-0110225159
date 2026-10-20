"""
Routes module for TaskFlow API.
Defines REST API endpoints for tasks, authentication, and health check.
"""

from flask import Blueprint, request, jsonify
from .database import (
    create_task, get_all_tasks, get_task_by_id,
    update_task, delete_task,
)

# ── Blueprints ────────────────────────────────────────────────────────────────
tasks_bp = Blueprint("tasks", __name__)
auth_bp = Blueprint("auth", __name__)
health_bp = Blueprint("health", __name__)


# ── Health Check ──────────────────────────────────────────────────────────────

@health_bp.route("/health", methods=["GET"])
def health_check():
    """Return application health status."""
    return jsonify({"status": "healthy", "service": "TaskFlow API", "version": "1.0.0"}), 200


# ── Task Endpoints ────────────────────────────────────────────────────────────

@tasks_bp.route("/", methods=["GET"])
def list_tasks():
    """
    GET /api/tasks/
    Query params: status, priority
    Returns a list of all tasks, optionally filtered.
    """
    status = request.args.get("status")
    priority = request.args.get("priority")

    valid_statuses = {"pending", "in_progress", "done", "cancelled"}
    valid_priorities = {"low", "medium", "high"}

    if status and status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
    if priority and priority not in valid_priorities:
        return jsonify({"error": f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"}), 400

    tasks = get_all_tasks(status=status, priority=priority)
    return jsonify({"tasks": tasks, "count": len(tasks)}), 200


@tasks_bp.route("/<int:task_id>", methods=["GET"])
def get_task(task_id):
    """
    GET /api/tasks/<task_id>
    Returns a single task by ID.
    """
    task = get_task_by_id(task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task), 200


@tasks_bp.route("/", methods=["POST"])
def create_new_task():
    """
    POST /api/tasks/
    Body: { title, description?, priority?, tags? }
    Creates a new task.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "Field 'title' is required and cannot be empty"}), 422

    if len(title) > 200:
        return jsonify({"error": "Title must not exceed 200 characters"}), 422

    priority = data.get("priority", "medium")
    if priority not in {"low", "medium", "high"}:
        return jsonify({"error": "Priority must be 'low', 'medium', or 'high'"}), 422

    task = create_task(
        title=title,
        description=data.get("description", ""),
        priority=priority,
        tags=data.get("tags", []),
    )
    return jsonify(task), 201


@tasks_bp.route("/<int:task_id>", methods=["PATCH"])
def update_existing_task(task_id):
    """
    PATCH /api/tasks/<task_id>
    Body: { title?, description?, status?, priority?, tags? }
    Partially updates a task.
    """
    if get_task_by_id(task_id) is None:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    if "status" in data and data["status"] not in {"pending", "in_progress", "done", "cancelled"}:
        return jsonify({"error": "Invalid status value"}), 422

    if "priority" in data and data["priority"] not in {"low", "medium", "high"}:
        return jsonify({"error": "Invalid priority value"}), 422

    updated = update_task(task_id, **data)
    return jsonify(updated), 200


@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
def delete_existing_task(task_id):
    """
    DELETE /api/tasks/<task_id>
    Deletes a task by ID.
    """
    deleted = delete_task(task_id)
    if not deleted:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"message": f"Task {task_id} deleted successfully"}), 200


# ── Auth Endpoints (Stub) ─────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /api/auth/login
    Stub endpoint — returns a placeholder token for demo purposes.
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    if not username:
        return jsonify({"error": "Username is required"}), 400
    # Stub: in production this would verify credentials and return a real JWT
    return jsonify({
        "token": "demo-token-replace-with-real-jwt",
        "username": username,
        "message": "Login stub — integrate real authentication in production",
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """POST /api/auth/logout — Stub logout endpoint."""
    return jsonify({"message": "Logged out successfully"}), 200
