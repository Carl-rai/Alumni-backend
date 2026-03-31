from django.db import models
from addevent.models import Event
from user.models import CustomUser

class EventRegistration(models.Model):
    STATUS_CHOICES = [
        ('Registered', 'Registered'),
        ('Attended', 'Attended'),
        ('Cancelled', 'Cancelled'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'user'}, related_name='event_registrations')
    guest_count = models.IntegerField(default=0)
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Registered')
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('event', 'user')
        ordering = ['-registration_date']

    def __str__(self):
        return f"{self.user.email} - {self.event.title}"
