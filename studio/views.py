from django.shortcuts import get_object_or_404, render

from .models import FilmRoll, Project
def project_list(request):
    projects = Project.objects.filter(is_archived=False)
    return render(request, "studio/project_list.html", {"projects": projects})

def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    rolls = project.rolls.all()
    return render(
        request,
        "studio/project_detail.html",
        {"project": project, "rolls": rolls},
    )

def roll_detail(request, project_pk, roll_pk):
    project = get_object_or_404(Project, pk=project_pk)
    roll = get_object_or_404(FilmRoll, pk=roll_pk, project=project)
    frames = roll.frames.all()
    return render(
        request,
        "studio/roll_detail.html",
        {"project": project, "roll": roll, "frames": frames},
    )