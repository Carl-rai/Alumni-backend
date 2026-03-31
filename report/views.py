from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings as django_settings
from .models import Report
from .serializers import ReportSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        email = request.data.get('email', '')
        user = None
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            pass

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='reply')
    def reply(self, request, pk=None):
        report = self.get_object()
        reply_message = request.data.get('reply', '').strip()

        if not reply_message:
            return Response({'error': 'Reply message is required'}, status=status.HTTP_400_BAD_REQUEST)

        report.reply = reply_message
        report.replied_at = timezone.now()
        report.is_read_by_user = False
        report.save()

        # If guest (no registered user), send email
        if not report.user:
            try:
                send_mail(
                    subject='Reply to your report/inquiry - SCSIT Alumni',
                    message=f'Dear {report.name},\n\nThank you for reaching out to us. Here is our reply to your report/inquiry:\n\n"{reply_message}"\n\nIf you have further concerns, feel free to send us another message.\n\nBest regards,\nSCSIT Alumni Management Team',
                    from_email=django_settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[report.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Email sending failed: {e}")

        return Response({'message': 'Reply sent successfully'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        report = self.get_object()
        report.is_read_by_user = True
        report.save()
        return Response({'message': 'Marked as read'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='by-email')
    def by_email(self, request):
        email = request.query_params.get('email', '')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        reports = Report.objects.filter(email=email)
        serializer = self.get_serializer(reports, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='unread-replies')
    def unread_replies(self, request):
        email = request.query_params.get('email', '')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        count = Report.objects.filter(email=email, reply__isnull=False, is_read_by_user=False).count()
        return Response({'unread_count': count})
