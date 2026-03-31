from django.contrib import admin
from .models import EventRegistration

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'event', 'guest_count', 'status', 'registration_date']
    list_filter = ['status', 'registration_date']
    search_fields = ['user__email', 'event__title']
    readonly_fields = ['registration_date']
