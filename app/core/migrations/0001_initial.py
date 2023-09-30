import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ImageJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "original_image",
                    models.ImageField(
                        null=True,
                        upload_to="original/",
                        validators=[django.core.validators.FileExtensionValidator(["png", "jpeg", "jpg"])],
                    ),
                ),
                (
                    "link_expires_in",
                    models.SmallIntegerField(
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(300),
                            django.core.validators.MaxValueValidator(30000),
                        ],
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("N", "New"), ("P", "Pending"), ("D", "Done"), ("E", "Error")],
                        default="N",
                        max_length=3,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Plan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=30, unique=True)),
                ("keeping_original_image", models.BooleanField(default=False)),
                ("expiring_link", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="UserPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to="core.plan")),
                (
                    "user",
                    models.OneToOneField(on_delete=django.db.models.deletion.RESTRICT, to=settings.AUTH_USER_MODEL),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ThumbnailSize",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("height", models.PositiveSmallIntegerField()),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to="core.plan")),
            ],
        ),
        migrations.CreateModel(
            name="Thumbnail",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="thumbs/")),
                ("height", models.SmallIntegerField()),
                ("external_id", models.UUIDField(null=True)),
                ("external_id_expires_at", models.DateTimeField(null=True)),
                (
                    "image_job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT, related_name="thumbnails", to="core.imagejob"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="imagejob",
            name="user_plan",
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to="core.userplan"),
        ),
    ]
