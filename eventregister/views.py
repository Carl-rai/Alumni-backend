from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import EventRegistration
from .serializers import EventRegistrationSerializer
from .emails import send_registration_confirmation_email

class EventRegistrationViewSet(viewsets.ModelViewSet):
    queryset = EventRegistration.objects.all()
    serializer_class = EventRegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == 'event_registrations':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin' or user.role == 'staff':
            return EventRegistration.objects.all()
        return EventRegistration.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id

        # Batch/course restriction check
        from addevent.models import Event
        try:
            event = Event.objects.get(id=data.get('event'))
        except Event.DoesNotExist:
            return Response({'detail': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if event.batch_category and str(user.year_graduate) != str(event.batch_category):
            return Response(
                {'detail': f'This event is only open to batch {event.batch_category} graduates.'},
                status=status.HTTP_403_FORBIDDEN
            )
        if event.course_category and (user.course or '').strip().lower() != event.course_category.strip().lower():
            return Response(
                {'detail': f'This event is only open to {event.course_category} course alumni.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Capacity check — count 1 (registrant) + guest_count
        if event.capacity is not None:
            guest_count = int(data.get('guest_count', 0))
            slots_needed = 1 + guest_count
            if event.capacity < slots_needed:
                return Response(
                    {'detail': f'Not enough slots. Only {event.capacity} slot(s) remaining.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Deduct capacity after successful registration
        registration = serializer.instance
        if event.capacity is not None:
            event.capacity -= (1 + registration.guest_count)
            event.save(update_fields=['capacity'])

        send_registration_confirmation_email(registration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        event = instance.event
        # Restore capacity on deletion
        if event.capacity is not None:
            event.capacity += (1 + instance.guest_count)
            event.save(update_fields=['capacity'])
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def my_registrations(self, request):
        registrations = EventRegistration.objects.filter(user=request.user)
        serializer = self.get_serializer(registrations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def event_registrations(self, request):
        event_id = request.query_params.get('event_id')
        if not event_id:
            return Response({'error': 'event_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        registrations = EventRegistration.objects.filter(event_id=event_id)
        serializer = self.get_serializer(registrations, many=True)
        return Response(serializer.data)
