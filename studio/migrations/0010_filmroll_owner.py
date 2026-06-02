from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def backfill_roll_owners(apps, schema_editor):
    FilmRoll = apps.get_model("studio", "FilmRoll")
    for roll in FilmRoll.objects.all():
        if roll.owner_id:
            continue
        project = roll.projects.order_by("id").first()
        if project and project.owner_id:
            roll.owner_id = project.owner_id
            roll.save(update_fields=["owner_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("studio", "0009_project_owner"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="filmroll",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="film_rolls",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(backfill_roll_owners, migrations.RunPython.noop),
    ]
