from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import AuditLog
from .serializers import AuditLogSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def audit_logs_api(request):
    if getattr(request.user, "role", None) != "admin":
        return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)

    limit = request.query_params.get("limit", "200")
    try:
        limit_value = max(1, min(int(limit), 1000))
    except (TypeError, ValueError):
        limit_value = 200

    logs = AuditLog.objects.all()[:limit_value]
    return Response(AuditLogSerializer(logs, many=True).data, status=status.HTTP_200_OK)

