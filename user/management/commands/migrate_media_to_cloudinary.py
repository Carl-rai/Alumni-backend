from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import storages
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from addevent.models import Event
from career.models import JobPost
from user.models import CustomUser


class Command(BaseCommand):
    help = (
        "Upload existing local event, job, and profile images to Cloudinary "
        "using the same folders stored in each model field."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be uploaded without changing the database.",
        )
        parser.add_argument(
            "--types",
            nargs="+",
            choices=["events", "jobs", "profiles"],
            default=["events", "jobs", "profiles"],
            help="Choose which image groups to migrate.",
        )

    def handle(self, *args, **options):
        default_storage = storages["default"]
        if default_storage.__class__.__module__ != "cloudinary_storage.storage":
            raise CommandError(
                "Default storage is not Cloudinary. Check your Cloudinary environment variables first."
            )

        media_root = Path(settings.MEDIA_ROOT)
        dry_run = options["dry_run"]

        tasks = []
        selected_types = set(options["types"])
        if "events" in selected_types:
            tasks.append(("events", Event, "image"))
        if "jobs" in selected_types:
            tasks.append(("jobs", JobPost, "image"))
        if "profiles" in selected_types:
            tasks.append(("profiles", CustomUser, "profile_image"))

        migrated = 0
        missing = 0
        skipped = 0

        for label, model, field_name in tasks:
            queryset = model.objects.exclude(**{field_name: ""}).exclude(**{f"{field_name}__isnull": True})
            self.stdout.write(self.style.NOTICE(f"Checking {label}: {queryset.count()} record(s)"))

            for obj in queryset.iterator():
                field_file = getattr(obj, field_name)
                stored_name = field_file.name
                source_path = media_root / stored_name

                if not stored_name:
                    skipped += 1
                    continue

                if not source_path.exists():
                    missing += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"Missing local file for {label} #{obj.pk}: {source_path}"
                        )
                    )
                    continue

                if dry_run:
                    migrated += 1
                    self.stdout.write(f"Would upload {label} #{obj.pk}: {stored_name}")
                    continue

                self.stdout.write(f"Uploading {label} #{obj.pk}: {stored_name}")
                with source_path.open("rb") as source_file:
                    django_file = File(source_file, name=stored_name)
                    getattr(obj, field_name).save(stored_name, django_file, save=False)

                with transaction.atomic():
                    obj.save(update_fields=[field_name])

                migrated += 1

        summary = f"Completed. Uploaded: {migrated}, missing local files: {missing}, skipped: {skipped}"
        self.stdout.write(self.style.SUCCESS(summary))
