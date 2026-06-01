from pathlib import Path

from django import forms
from .models import FilmRoll, FrameNote, Project, frame_display

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["title", "description"]

class FilmRollForm(forms.ModelForm):
    class Meta:
        model = FilmRoll
        fields = ["label", "stock", "format", "status", "max_frames"]

class FrameNoteForm(forms.ModelForm):
    class Meta:
        model = FrameNote
        fields = ["frame_number", "note", "image"]
        widgets = {
            "frame_number": forms.NumberInput(attrs={"min": -5, "step": 1}),
            "note": forms.Textarea(
                attrs={"rows": 2, "placeholder": "f/8 1/250…"}
            ),
        }
    def __init__(self, *args, roll=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.roll = roll
        self.fields["note"].required = False
        self.fields["image"].required = False

    def clean_frame_number(self):
        frame_number = self.cleaned_data["frame_number"]
        if not self.roll:
            return frame_number
        qs = self.roll.frames.filter(frame_number=frame_number)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            label = frame_display(frame_number)
            raise forms.ValidationError(
                f"Frame {label} already has a note on this roll."
            )
        return frame_number

    def save(self, commit=True):
        instance = super().save(commit=False)
        upload = self.files.get("image")
        if upload:
            instance.scan_filename = Path(upload.name).name
        if commit:
            instance.save()
        return instance