from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def _sole_user(apps):
    User = apps.get_model(settings.AUTH_USER_MODEL)
    if User.objects.count() == 1:
        return User.objects.order_by("pk").first()
    return None


def backfill_project_owners(apps, schema_editor):
    Project = apps.get_model("studio", "Project")
    FilmRoll = apps.get_model("studio", "FilmRoll")

    for project in Project.objects.filter(owner__isnull=True):
        roll = (
            FilmRoll.objects.filter(projects=project, owner__isnull=False)
            .order_by("id")
            .first()
        )
        if roll:
            project.owner_id = roll.owner_id
            project.save(update_fields=["owner_id"])
            continue
        user = _sole_user(apps)
        if user:
            project.owner_id = user.pk
            project.save(update_fields=["owner_id"])


def backfill_roll_owners(apps, schema_editor):
    FilmRoll = apps.get_model("studio", "FilmRoll")
    for roll in FilmRoll.objects.filter(owner__isnull=True):
        project = roll.projects.filter(owner__isnull=False).order_by("id").first()
        if project:
            roll.owner_id = project.owner_id
            roll.save(update_fields=["owner_id"])
            continue
        user = _sole_user(apps)
        if user:
            roll.owner_id = user.pk
            roll.save(update_fields=["owner_id"])


def assert_owners_set(apps, schema_editor):
    Project = apps.get_model("studio", "Project")
    FilmRoll = apps.get_model("studio", "FilmRoll")
    project_count = Project.objects.filter(owner__isnull=True).count()
    roll_count = FilmRoll.objects.filter(owner__isnull=True).count()
    if project_count or roll_count:
        raise RuntimeError(
            "Cannot require owner: "
            f"{project_count} project(s) and {roll_count} roll(s) still have no owner. "
            "Assign owner in Django admin or shell, then run migrate again."
        )


class Migration(migrations.Migration):

    dependencies = [
        ("studio", "0010_filmroll_owner"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(backfill_project_owners, migrations.RunPython.noop),
        migrations.RunPython(backfill_roll_owners, migrations.RunPython.noop),
        migrations.RunPython(assert_owners_set, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="project",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="projects",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="filmroll",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="film_rolls",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
