from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .folder_import import clear_roll_images, import_roll_folder
from .forms import FilmRollForm, FrameNoteForm, ProjectForm, SignUpForm
from .models import FilmRoll, FrameNote, Project


class StudioLoginView(LoginView):
    template_name = "studio/login.html"
    redirect_authenticated_user = True


def _roll_url(project_pk, roll_pk, frame_number=None, *, panel=False):
    url = reverse(
        "roll_detail",
        kwargs={"project_pk": project_pk, "roll_pk": roll_pk},
    )
    params = []
    if frame_number is not None:
        params.append(f"frame={frame_number}")
    if panel:
        params.append("panel=1")
    if params:
        url = f"{url}?{'&'.join(params)}"
    return url


def _get_frame(roll, raw):
    if raw in (None, ""):
        return None
    try:
        return roll.frames.get(frame_number=int(raw))
    except (FrameNote.DoesNotExist, TypeError, ValueError):
        return None


def _user_projects(user):
    return Project.objects.filter(owner=user, is_archived=False)

def home(request):
    if request.user.is_authenticated:
        return redirect("project_list")
    return render(request, "studio/home.html")

@login_required
def project_list(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            return redirect("project_list")
    else:
        form = ProjectForm()
    projects = _user_projects(request.user)
    return render(
        request,
        "studio/project_list.html",
        {
            "projects": projects,
            "form": form,
            "show_create_form": request.method == "POST" and not form.is_valid(),
        },
    )

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    project_form = ProjectForm(instance=project)
    roll_form = FilmRollForm()
    show_edit_project = False
    show_add_roll = False

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "delete_project":
            title = project.title
            roll_count = project.rolls.count()
            project.delete()
            if roll_count:
                messages.success(
                    request,
                    f"Deleted project “{title}”. "
                    f"{roll_count} roll{'s' if roll_count != 1 else ''} kept.",
                )
            else:
                messages.success(request, f"Deleted project “{title}”.")
            return redirect("project_list")

        if action == "edit_project":
            project_form = ProjectForm(request.POST, instance=project)
            if project_form.is_valid():
                project_form.save()
                messages.success(request, "Project updated.")
                return redirect("project_detail", pk=pk)
            show_edit_project = True

        elif action == "create_roll":
            roll_form = FilmRollForm(request.POST)
            if roll_form.is_valid():
                roll = roll_form.save()
                roll.projects.add(project)
                return redirect("project_detail", pk=pk)
            show_add_roll = True

    else:
        show_edit_project = request.GET.get("edit") == "1"
        show_add_roll = (
            request.GET.get("add_roll") == "1" or not project.rolls.exists()
        )

    rolls = project.rolls.all()
    return render(
        request,
        "studio/project_detail.html",
        {
            "project": project,
            "rolls": rolls,
            "project_form": project_form,
            "roll_form": roll_form,
            "show_edit_project": show_edit_project,
            "show_add_roll": show_add_roll,
        },
    )

@login_required
def roll_detail(request, project_pk, roll_pk):
    project = get_object_or_404(Project, pk=project_pk, owner=request.user)
    roll = get_object_or_404(
        FilmRoll.objects.filter(projects=project),
        pk=roll_pk,
    )
    instance = None
    form = FrameNoteForm(roll=roll)
    roll_form = FilmRollForm(instance=roll)
    show_log_frame = False
    show_import = False
    show_roll_edit = False

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "delete_roll":
            label = str(roll)
            roll.delete()
            messages.success(request, f"Deleted roll {label}.")
            return redirect("project_detail", pk=project_pk)

        elif action == "edit_roll":
            roll_form = FilmRollForm(request.POST, instance=roll)
            if roll_form.is_valid():
                roll_form.save()
                messages.success(request, "Roll updated.")
                return redirect(
                    "roll_detail",
                    project_pk=project_pk,
                    roll_pk=roll_pk,
                )
            show_roll_edit = True

        elif action == "import_folder":
            uploads = request.FILES.getlist("lab_folder")
            reverse_order = request.POST.get("reverse_order") == "on"
            raw_index = request.POST.get("first_file_index", "1").strip()
            try:
                first_file_index = max(1, int(raw_index))
            except ValueError:
                first_file_index = 1
            result = import_roll_folder(
                roll,
                uploads,
                reverse=reverse_order,
                first_file_index=first_file_index,
            )
            if result.imported:
                msg = f"Imported {result.imported} scan{'s' if result.imported != 1 else ''}."
                if result.leaders:
                    msg += f" Leaders: {', '.join(result.leaders)}."
                messages.success(request, msg)
            for line in result.skipped[:5]:
                messages.warning(request, line)
            if len(result.skipped) > 5:
                messages.warning(
                    request,
                    f"…and {len(result.skipped) - 5} more skipped.",
                )
            if not result.imported and not result.skipped:
                messages.error(request, "No files to import.")
            return redirect(
                "roll_detail",
                project_pk=project_pk,
                roll_pk=roll_pk,
            )

        elif action == "clear_images":
            removed = clear_roll_images(roll)
            if removed:
                messages.success(
                    request,
                    f"Cleared {removed} scan{'s' if removed != 1 else ''}. Text notes kept.",
                )
            else:
                messages.info(request, "No scans to clear on this roll.")
            return redirect(
                "roll_detail",
                project_pk=project_pk,
                roll_pk=roll_pk,
            )

        elif action == "toggle_favorite":
            raw = request.POST.get("frame_number")
            is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
            frame = _get_frame(roll, raw)
            if frame is None:
                if is_ajax:
                    return JsonResponse(
                        {"error": "Could not find that frame."},
                        status=404,
                    )
                messages.error(request, "Could not find that frame.")
            else:
                frame.is_favorite = not frame.is_favorite
                frame.save(update_fields=["is_favorite"])
                if is_ajax:
                    return JsonResponse(
                        {
                            "frame_number": frame.frame_number,
                            "is_favorite": frame.is_favorite,
                        }
                    )
            return redirect(_roll_url(project_pk, roll_pk))

        elif action == "delete_frame":
            raw = request.POST.get("frame_number")
            frame = _get_frame(roll, raw)
            if frame is None:
                messages.error(request, "Could not find that frame to delete.")
            else:
                label = frame.display_number
                frame.delete()
                messages.success(request, f"Deleted frame {label}.")
            return redirect(_roll_url(project_pk, roll_pk))

        elif action == "save_frame":
            raw = request.POST.get("frame_number")
            is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
            instance = _get_frame(roll, raw)
            if is_ajax and instance is None:
                return JsonResponse(
                    {"error": "Could not find that frame."},
                    status=404,
                )
            form = FrameNoteForm(
                request.POST, request.FILES, roll=roll, instance=instance
            )
            if form.is_valid():
                frame = form.save(commit=False)
                frame.roll = roll
                frame.save()
                if is_ajax:
                    return JsonResponse(
                        {
                            "frame_number": frame.frame_number,
                            "display_number": frame.display_number,
                            "note": frame.note,
                        }
                    )
                return redirect(
                    _roll_url(project_pk, roll_pk, frame.frame_number, panel=True)
                )
            if is_ajax:
                return JsonResponse(
                    {"error": form.errors.get_json_data()},
                    status=400,
                )
            show_log_frame = True

    else:
        raw = request.GET.get("frame")
        if (
            raw
            and request.GET.get("panel") != "1"
            and request.GET.get("log") != "1"
        ):
            return redirect(_roll_url(project_pk, roll_pk))
        if request.GET.get("panel") == "1" and raw:
            instance = _get_frame(roll, raw)
            show_log_frame = instance is not None
        elif request.GET.get("log") == "1":
            instance = None
            show_log_frame = True
        else:
            instance = None
        form = FrameNoteForm(roll=roll, instance=instance)
        show_import = request.GET.get("import") == "1"
        show_roll_edit = request.GET.get("edit") == "1"

    frames = roll.frames.all()
    has_scans = any(frame.image.name for frame in frames)
    if request.method != "POST" and not frames.exists() and not has_scans:
        show_import = True

    return render(
        request,
        "studio/roll_detail.html",
        {
            "project": project,
            "roll": roll,
            "frames": frames,
            "form": form,
            "roll_form": roll_form,
            "editing": instance is not None,
            "has_scans": has_scans,
            "show_log_frame": show_log_frame,
            "show_import": show_import,
            "show_roll_edit": show_roll_edit,
        },
    )

def auth_signup(request):
    if request.user.is_authenticated:
        return redirect("project_list")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome! Your account is ready.")
            return redirect("project_list")
    else:
        form = SignUpForm()
    return render(request, "studio/signup.html", {"form": form})


@login_required
def delete_account(request):
    if request.method == "POST":
        if request.POST.get("confirm") != "yes":
            messages.error(
                request, "Check the box to confirm account deletion."
            )
            return redirect("delete_account")
        user = request.user
        auth_logout(request)
        user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect("home")
    return render(request, "studio/account_delete.html")