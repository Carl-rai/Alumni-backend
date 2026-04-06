from django.db import models

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField(null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=255)
    venue = models.CharField(max_length=255, blank=True, null=True)
    image = models.FileField(upload_to='alumni/events/', blank=True, null=True)
    batch_category = models.CharField(max_length=100, blank=True, null=True)
    course_category = models.CharField(max_length=100, blank=True, null=True)
    capacity = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['start_time']
