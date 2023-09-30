from django.contrib.auth.models import User
from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models


class Plan(models.Model):
    title = models.CharField(max_length=30, unique=True)
    keeping_original_image = models.BooleanField(default=False)
    expiring_link = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.title


class ThumbnailSize(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.RESTRICT)
    height = models.PositiveSmallIntegerField()


class UserPlan(models.Model):
    user = models.OneToOneField(User, on_delete=models.RESTRICT)
    plan = models.ForeignKey(Plan, on_delete=models.RESTRICT)


class ImageJob(models.Model):
    STATUS_NEW = "N"
    STATUS_PENDING = "P"
    STATUS_ERROR = "E"
    STATUS_DONE = "D"
    STATUS_CHOICES = (
        (STATUS_NEW, "New"),
        (STATUS_PENDING, "Pending"),
        (STATUS_DONE, "Done"),
        (STATUS_ERROR, "Error"),
    )
    user_plan = models.ForeignKey(UserPlan, on_delete=models.RESTRICT)
    original_image = models.ImageField(
        upload_to="original/",
        validators=[FileExtensionValidator(["png", "jpeg", "jpg"])],
        null=True,
    )
    link_expires_in = models.SmallIntegerField(null=True, validators=[MinValueValidator(300), MaxValueValidator(30000)])
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default=STATUS_NEW)


class Thumbnail(models.Model):
    image_job = models.ForeignKey(ImageJob, on_delete=models.RESTRICT, related_name="thumbnails")
    image = models.ImageField(upload_to="thumbs/")
    height = models.SmallIntegerField()
    external_id = models.UUIDField(null=True)
    external_id_expires_at = models.DateTimeField(null=True)
