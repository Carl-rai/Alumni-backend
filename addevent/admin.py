from django.contrib import admin
from .models import Event

class EventModelAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'location')
    search_fields = ('title', 'description', 'location')
    list_per_page = 10
# Register your models here.
admin.site.register(Event, EventModelAdmin)