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