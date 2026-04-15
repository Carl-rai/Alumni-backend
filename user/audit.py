from __future__ import annotations

import json
import re
import ipaddress
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from auditlogs.models import AuditLog


EXCLUDED_PREFIXES = (
    "/admin/",
    "/static/",
    "/media/",
)


def _header_value(request, *names: str) -> str:
    for name in names:
        value = request.headers.get(name)
        if value:
            return value
    return ""


def _normalize_ip_address(request) -> str | None:
    raw_value = _header_value(request, "X-Forwarded-For", "X-Real-IP") or request.META.get("REMOTE_ADDR") or ""
    first_value = raw_value.split(",", 1)[0].strip()
    if not first_value:
        return None

    try:
        return str(ipaddress.ip_address(first_value))
    except ValueError:
        return None


def _user_from_bearer_token(request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token_value = auth_header.split(" ", 1)[1].strip()
    if not token_value:
        return None

    try:
        token = AccessToken(token_value)
    except TokenError:
        return None

    user_id_claim = settings.SIMPLE_JWT.get("USER_ID_CLAIM", "user_id")
    user_id = token.get(user_id_claim)
    if user_id is None:
        return None

    User = get_user_model()
    try:
        return User.objects.filter(pk=user_id).first()
    except Exception:
        return None


def _safe_json_body(request) -> dict[str, Any]:
    content_type = (request.META.get("CONTENT_TYPE") or "").lower()
    if "application/json" not in content_type:
        data: dict[str, Any] = {}
        try:
            if hasattr(request, "POST"):
                data.update({k: v for k, v in request.POST.items() if k})
            if hasattr(request, "FILES") and request.FILES:
                data["files"] = list(request.FILES.keys())
        except Exception:
            return {}
        return data

    raw = request.body
    if not raw:
        return {}

    try:
        decoded = raw.decode("utf-8")
        parsed = json.loads(decoded)
        if isinstance(parsed, dict):
            return parsed
        return {"payload": parsed}
    except Exception:
        return {"raw": raw[:1000].decode("utf-8", errors="ignore")}


def _guess_resource(path: str) -> tuple[str, str | None]:
    clean = path.strip("/")
    if not clean:
        return ("root", None)

    parts = clean.split("/")
    resource = parts[1] if parts and parts[0] == "api" and len(parts) > 1 else parts[0]
    resource_id = None
    match = re.search(r"/(\d+)(?:/|$)", path)
    if match:
        resource_id = match.group(1)
    return (resource, resource_id)


def _guess_action(method: str, path: str) -> str:
    method = method.upper()
    lowered = path.lower()
    if method == "POST" and "login" in lowered:
        return "login"
    if method == "POST" and "register" in lowered:
        return "register"
    if method == "POST" and "approve" in lowered:
        return "approve"
    if method == "POST" and "reject" in lowered:
        return "reject"
    if method == "POST" and "reply" in lowered:
        return "reply"
    if method == "POST" and "upload" in lowered:
        return "upload"
    if method in {"PUT", "PATCH"}:
        return "update"
    if method == "DELETE":
        return "delete"
    if method == "POST":
        return "create"
    return method.lower()


def log_audit_event(request, response=None, *, action: str | None = None, details: dict[str, Any] | None = None, success: bool | None = None):
    if not request.path.startswith("/api/"):
        return None

    if request.path.startswith(EXCLUDED_PREFIXES):
        return None

    actor_email = _header_value(request, "X-Actor-Email", "X-User-Email")
    actor_name = _header_value(request, "X-Actor-Name", "X-User-Name")
    actor_role = _header_value(request, "X-Actor-Role", "X-User-Role") or "anonymous"

    request_user = getattr(request, "user", None)
    if not getattr(request_user, "is_authenticated", False):
        request_user = _user_from_bearer_token(request)
    if getattr(request_user, "is_authenticated", False):
        actor_email = actor_email or getattr(request_user, "email", "")
        actor_name = actor_name or f"{getattr(request_user, 'first_name', '')} {getattr(request_user, 'last_name', '')}".strip()
        actor_role = actor_role if actor_role != "anonymous" else getattr(request_user, "role", "anonymous")

    if actor_role not in {choice[0] for choice in AuditLog.ROLE_CHOICES}:
        actor_role = "anonymous"

    status_code = getattr(response, "status_code", None)
    if success is None:
        success = bool(status_code is None or status_code < 400)

    payload = details or _safe_json_body(request)
    guessed_action = action or _guess_action(request.method, request.path)
    resource, resource_id = _guess_resource(request.path)

    AuditLog.objects.create(
        actor_email=actor_email or None,
        actor_name=actor_name or None,
        actor_role=actor_role,
        action=guessed_action,
        method=request.method.upper(),
        path=request.path,
        resource=resource,
        resource_id=resource_id,
        success=success,
        status_code=status_code,
        ip_address=_normalize_ip_address(request),
        user_agent=request.META.get("HTTP_USER_AGENT"),
        details=payload if isinstance(payload, dict) else {"payload": payload},
    )

    return None


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if getattr(request, "_audit_logged", False):
            return response

        if request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"} and request.path.startswith("/api/"):
            if request.path not in {"/api/audit-logs/"}:
                try:
                    log_audit_event(request, response=response)
                except Exception:
                    pass

        return response
