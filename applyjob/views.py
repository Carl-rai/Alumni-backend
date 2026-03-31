from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .models import JobApplication
from .serializers import JobApplicationSerializer


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def apply_job_api(request):
    """Alumni submits a job application"""
    serializer = JobApplicationSerializer(data=request.data, context={"request": request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_all_applications_api(request):
    """Admin/Staff: get all job applications"""
    applications = JobApplication.objects.all()
    serializer = JobApplicationSerializer(applications, many=True, context={"request": request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_application_api(request, app_id):
    """Get a single job application by ID"""
    try:
        application = JobApplication.objects.get(id=app_id)
        serializer = JobApplicationSerializer(application, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    except JobApplication.DoesNotExist:
        return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
def get_user_applications_api(request, user_id):
    """Get all applications by a specific user"""
    applications = JobApplication.objects.filter(applicant_id=user_id)
    serializer = JobApplicationSerializer(applications, many=True, context={"request": request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT"])
def update_application_api(request, app_id):
    """Admin/Staff: update remarks and status"""
    try:
        application = JobApplication.objects.get(id=app_id)
        application.remarks = request.data.get("remarks", application.remarks)
        application.status = request.data.get("status", application.status)
        application.save()
        serializer = JobApplicationSerializer(application, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    except JobApplication.DoesNotExist:
        return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["DELETE"])
def delete_application_api(request, app_id):
    """Delete a job application"""
    try:
        application = JobApplication.objects.get(id=app_id)
        application.delete()
        return Response({"message": "Application deleted successfully"}, status=status.HTTP_200_OK)
    except JobApplication.DoesNotExist:
        return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)
