from django.shortcuts import render

from .models import Project
def project_list(request):
    projects = Project.objects.filter(is_archived=False)
    return render(request, "studio/project_list.html", {"projects": projects})
