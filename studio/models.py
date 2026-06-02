from pathlib import Path
from django.db import models
from django.conf import settings


# function returns photo path string
def frame_image_upload_to(instance, filename):
    ext = Path(filename).suffix.lower() or ".jpg"
    label = frame_display(instance.frame_number)
    return f"frames/roll_{instance.roll_id}/frame_{label}{ext}"


def frame_display(number: int) -> str:
    """Film edge labels: 00 and 0 before frame 1."""
    if number == -1:
        return "00"
    if number == 0:
        return "0"
    if number < -1:
        return f"L{abs(number + 1)}"
    return str(number)

# A project groups rolls for a trip, theme, or body of work.
# Rolls are the main record (one physical roll); projects are optional and many-to-many.

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

class FilmRoll(models.Model):
    class Format(models.TextChoices):
        FORMAT_35 = "35mm", "35mm"
        FORMAT_120 = "120", "120"
        OTHER = "other", "Other"
    class Status(models.TextChoices):
        LOADED = "loaded", "Loaded"
        EXPOSED = "exposed", "Exposed"
        AT_LAB = "at_lab", "At lab"
        SCANNED = "scanned", "Scanned"
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="film_rolls",
        null=True,
        blank=True,
    )
    projects = models.ManyToManyField(
        Project,
        related_name="rolls",
        blank=True,
    )
    label = models.CharField(max_length=100, blank=True)
    stock = models.CharField(max_length=100, blank=True)
    format = models.CharField(
        max_length=10,
        choices=Format.choices,
        blank=True,
    )
    iso = models.PositiveSmallIntegerField(null=True, blank=True)
    camera = models.CharField(max_length=100, blank=True)
    loaded_at = models.DateField(null=True, blank=True)
    max_frames = models.PositiveSmallIntegerField(default=36)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.LOADED,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-created_at"]
    def project_titles(self):
        return list(self.projects.values_list("title", flat=True))

    def __str__(self):
        if self.label:
            if self.label.lower().startswith("roll "):
                return self.label
            return f"Roll {self.label}"
        titles = self.project_titles()
        if self.stock:
            if titles:
                return f"{self.stock} ({titles[0]})"
            return self.stock
        if titles:
            if len(titles) == 1:
                return f"Roll on {titles[0]}"
            return f"Roll on {titles[0]} +{len(titles) - 1}"
        return f"Roll #{self.pk}"

class FrameNote(models.Model):
    roll = models.ForeignKey(
        FilmRoll,
        on_delete=models.CASCADE,
        related_name="frames",
    )
    frame_number = models.SmallIntegerField()
    note = models.TextField(blank=True, default="")
    image = models.ImageField(
        upload_to=frame_image_upload_to,
        blank=True,
        null=True,
    )
    scan_filename = models.CharField(
        max_length=255,
        blank=True,
        help_text="Original lab scan filename, if imported.",
    )
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["frame_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["roll", "frame_number"],
                name="unique_frame_per_roll",
            )
        ]
    @property
    def display_number(self):
        return frame_display(self.frame_number)

    def __str__(self):
        return f"Frame {self.display_number} on roll {self.roll_id}"