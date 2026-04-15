from django.db import models

from backend.storage import AssetFolderCloudinaryStorage


class AlumniStudentCSVUpload(models.Model):
    title = models.CharField(max_length=150, blank=True, null=True)
    csv_file = models.FileField(
        upload_to="alumni-students/csv/",
        storage=AssetFolderCloudinaryStorage(),
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.title:
            return self.title
        return self.csv_file.name

    class Meta:
        ordering = ["-uploaded_at"]
        db_table = "alumnistudent_alumnistudentcsvupload"

