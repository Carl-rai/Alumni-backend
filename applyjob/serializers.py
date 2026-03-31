from rest_framework import serializers
from .models import JobApplication


class JobApplicationSerializer(serializers.ModelSerializer):
    applicant_email = serializers.EmailField(source="applicant.email", read_only=True)
    applicant_name = serializers.SerializerMethodField()
    resume_url = serializers.SerializerMethodField()
    job_title = serializers.CharField(source="job.job_title", read_only=True)
    company_name = serializers.CharField(source="job.company_name", read_only=True)

    class Meta:
        model = JobApplication
        fields = [
            "id", "applicant", "applicant_email", "applicant_name",
            "job", "job_title", "company_name",
            "phone", "address",
            "resume", "resume_url", "cover_letter", "portfolio_link",
            "skills", "work_experience", "remarks",
            "status", "applied_at", "updated_at",
        ]
        extra_kwargs = {
            "applicant": {"write_only": True},
            "resume": {"write_only": True},
        }

    def get_applicant_name(self, obj):
        return f"{obj.applicant.first_name} {obj.applicant.last_name}"

    def get_resume_url(self, obj):
        request = self.context.get("request")
        if obj.resume and request:
            return request.build_absolute_uri(obj.resume.url)
        return None
 