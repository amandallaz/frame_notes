from django.db import models

# A project is a named body of photographic work (a trip, a job, or an ongoing theme, 
# that can hold rolls and frame notes over time.

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="rolls",
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
    def __str__(self):
        if self.label:
            return self.label
        if self.stock:
            return f"{self.stock} ({self.project.title})"
        return f"Roll on {self.project.title}"

class FrameNote(models.Model):
    roll = models.ForeignKey(
        FilmRoll,
        on_delete=models.CASCADE,
        related_name="frames",
    )
    frame_number = models.PositiveSmallIntegerField()
    note = models.TextField()  # required — even "test" or "f/8 1/250"
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["frame_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["roll", "frame_number"],
                name="unique_frame_per_roll",
            )
        ]
    def __str__(self):
        return f"Frame {self.frame_number} — {self.roll}"