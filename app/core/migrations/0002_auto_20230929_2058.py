from django.db import migrations


def create_builtin_plan(apps, schema_editor):
    Plan = apps.get_model("core", "Plan")
    ThumbnailSize = apps.get_model("core", "ThumbnailSize")

    basic_plan = Plan.objects.create(title="Basic")
    ThumbnailSize.objects.bulk_create([ThumbnailSize(plan=basic_plan, height=200)])

    premium_plan = Plan.objects.create(title="Premium", keeping_original_image=True)
    ThumbnailSize.objects.bulk_create([ThumbnailSize(plan=premium_plan, height=200)])
    ThumbnailSize.objects.bulk_create([ThumbnailSize(plan=premium_plan, height=400)])

    enterprise_plan = Plan.objects.create(title="Enterprise", keeping_original_image=True, expiring_link=True)
    ThumbnailSize.objects.bulk_create([ThumbnailSize(plan=enterprise_plan, height=200)])
    ThumbnailSize.objects.bulk_create([ThumbnailSize(plan=enterprise_plan, height=400)])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_builtin_plan),
    ]
