"""
Upload frame scans that still exist under media/ but were saved before Cloudinary.

Run after enabling CLOUDINARY_URL when older rolls show broken thumbnails.
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from studio.models import FrameNote, frame_display


class Command(BaseCommand):
    help = "Upload local media/ scan files to Cloudinary for frames that still have files on disk."

    def add_arguments(self, parser):
        parser.add_argument(
            "--roll",
            type=int,
            help="Only process frames on this roll id.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List what would be uploaded without uploading.",
        )

    def handle(self, *args, **options):
        if not getattr(settings, "USE_CLOUDINARY_STORAGE", False):
            self.stderr.write(
                self.style.ERROR(
                    "Cloudinary is not configured (.env). Nothing to do."
                )
            )
            return

        media_root = Path(settings.MEDIA_ROOT)
        qs = FrameNote.objects.exclude(image="").exclude(image__isnull=True)
        if options["roll"]:
            qs = qs.filter(roll_id=options["roll"])

        uploaded = 0
        skipped = 0
        for frame in qs.order_by("roll_id", "frame_number"):
            if not frame.image.name:
                skipped += 1
                continue
            local_path = media_root / frame.image.name
            if not local_path.is_file():
                skipped += 1
                continue
            label = frame_display(frame.frame_number)
            ext = local_path.suffix.lower() or ".jpg"
            target_name = f"frame_{label}{ext}"
            if options["dry_run"]:
                self.stdout.write(
                    f"would upload roll {frame.roll_id} frame {label}: {local_path}"
                )
                uploaded += 1
                continue
            with local_path.open("rb") as handle:
                frame.image.save(target_name, File(handle), save=True)
            self.stdout.write(
                f"uploaded roll {frame.roll_id} frame {label} → {frame.image.url}"
            )
            uploaded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. uploaded={uploaded} skipped_no_local_file={skipped}"
            )
        )
