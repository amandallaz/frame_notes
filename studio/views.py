from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Count, Prefetch, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .folder_import import clear_roll_images, import_roll_folder, set_frame_one
from .forms import FilmRollForm, FrameNoteForm, ProjectForm, SignUpForm
from .models import FilmRoll, FrameNote, Project, frame_display


class StudioLoginView(LoginView):
    template_name = "studio/login.html"
    redirect_authenticated_user = True


def _user_rolls(user):
    return FilmRoll.objects.filter(owner=user).order_by("-updated_at")


def _user_can_access_roll(user, roll):
    if roll.owner_id == user.id:
        return True
    return roll.projects.filter(owner=user).exists()


def _roll_url(project, roll_pk, frame_number=None, *, panel=False):
    if project is not None:
        url = reverse(
            "roll_detail",
            kwargs={"project_pk": project.pk, "roll_pk": roll_pk},
        )
    else:
        url = reverse("roll_detail_direct", kwargs={"roll_pk": roll_pk})
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


def _suggested_frame_number(roll):
    nums = list(roll.frames.values_list("frame_number", flat=True))
    return max(nums) + 1 if nums else 1


def _handle_set_frame_one(request, roll, project, roll_pk):
    raw_source = request.POST.get("frame_one_source", "").strip()
    try:
        source_frame_number = int(raw_source)
    except ValueError:
        messages.error(request, "Choose which scan should be frame 1.")
        return redirect(_roll_url(project, roll_pk))
    try:
        delta = set_frame_one(roll, source_frame_number)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect(_roll_url(project, roll_pk))
    if delta == 0:
        messages.info(request, "That scan is already frame 1.")
    else:
        messages.success(
            request,
            f"That scan is now frame 1. Other frames were renumbered to match.",
        )
    return redirect(_roll_url(project, roll_pk))

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
            rolls_on_project = list(project.rolls.all())
            roll_count = len(rolls_on_project)
            for roll in rolls_on_project:
                if roll.owner_id is None:
                    roll.owner = request.user
                    roll.save(update_fields=["owner_id"])
            project.delete()
            if roll_count:
                messages.success(
                    request,
                    f"Deleted project “{title}”. "
                    f"{roll_count} roll{'s' if roll_count != 1 else ''} kept — "
                    f"see Rolls.",
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
                roll = roll_form.save(commit=False)
                roll.owner = request.user
                roll.save()
                roll.projects.add(project)
                url = reverse(
                    "roll_detail",
                    kwargs={"project_pk": pk, "roll_pk": roll.pk},
                )
                return redirect(f"{url}?log=1")
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
def roll_list(request):
    user_projects = Project.objects.filter(owner=request.user)
    frames_with_scans = FrameNote.objects.exclude(
        Q(image="") | Q(image__isnull=True)
    ).order_by("frame_number")
    rolls = (
        _user_rolls(request.user)
        .annotate(frame_count=Count("frames"))
        .prefetch_related(
            Prefetch("projects", queryset=user_projects),
            Prefetch(
                "frames",
                queryset=frames_with_scans,
                to_attr="preview_frames",
            ),
        )
    )
    roll_rows = []
    for roll in rolls:
        project = next(iter(roll.projects.all()), None)
        roll_rows.append(
            {
                "roll": roll,
                "project": project,
                "preview_frames": roll.preview_frames[:5],
            }
        )
    return render(request, "studio/roll_list.html", {"roll_rows": roll_rows})


@login_required
def roll_detail(request, project_pk, roll_pk):
    project = get_object_or_404(Project, pk=project_pk, owner=request.user)
    roll = get_object_or_404(FilmRoll, pk=roll_pk)
    if not _user_can_access_roll(request.user, roll):
        raise Http404
    if not roll.projects.filter(pk=project.pk).exists():
        return redirect("roll_detail_direct", roll_pk=roll_pk)
    return _roll_detail(request, project, roll)


@login_required
def roll_detail_direct(request, roll_pk):
    roll = get_object_or_404(FilmRoll, pk=roll_pk, owner=request.user)
    project = roll.projects.filter(owner=request.user).first()
    return _roll_detail(request, project, roll)


def _roll_detail(request, project, roll):
    roll_pk = roll.pk
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
            if project is not None:
                return redirect("project_detail", pk=project.pk)
            return redirect("roll_list")

        elif action == "edit_roll":
            roll_form = FilmRollForm(request.POST, instance=roll)
            if roll_form.is_valid():
                roll_form.save()
                messages.success(request, "Roll updated.")
                return redirect(_roll_url(project, roll_pk))
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
            return redirect(_roll_url(project, roll_pk))

        elif action == "set_frame_one" or request.POST.get("frame_one_source") is not None:
            return _handle_set_frame_one(request, roll, project, roll_pk)

        elif action == "clear_images":
            removed = clear_roll_images(roll)
            if removed:
                messages.success(
                    request,
                    f"Cleared {removed} scan{'s' if removed != 1 else ''}. Text notes kept.",
                )
            else:
                messages.info(request, "No scans to clear on this roll.")
            return redirect(_roll_url(project, roll_pk))

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
            return redirect(_roll_url(project, roll_pk))

        elif action == "delete_frame":
            raw = request.POST.get("frame_number")
            frame = _get_frame(roll, raw)
            if frame is None:
                messages.error(request, "Could not find that frame to delete.")
            else:
                label = frame.display_number
                frame.delete()
                messages.success(request, f"Deleted frame {label}.")
            return redirect(_roll_url(project, roll_pk))

        elif action == "save_frame" and request.POST.get("frame_one_source") is None:
            raw = request.POST.get("frame_number")
            is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
            instance = _get_frame(roll, raw)
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
                if request.FILES.get("image"):
                    return redirect(
                        _roll_url(
                            project, roll_pk, frame.frame_number, panel=True
                        )
                    )
                return redirect(_roll_url(project, roll_pk))
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
            return redirect(_roll_url(project, roll_pk))
        if request.GET.get("panel") == "1" and raw:
            instance = _get_frame(roll, raw)
            show_log_frame = instance is not None
        elif request.GET.get("log") == "1":
            instance = None
            show_log_frame = True
        else:
            instance = None
        form_initial = None
        if instance is None:
            form_initial = {"frame_number": _suggested_frame_number(roll)}
        form = FrameNoteForm(roll=roll, instance=instance, initial=form_initial)
        show_import = request.GET.get("import") == "1"
        show_roll_edit = request.GET.get("edit") == "1"

    frames = roll.frames.all()
    has_scans = any(frame.image.name for frame in frames)
    if request.method != "POST" and not frames.exists():
        show_import = request.GET.get("import") == "1"
        show_log_frame = not show_import

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