import os
from datetime import datetime
from typing import Optional

from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.utils.serializer_helpers import ReturnDict

from core.models import ImageJob, Thumbnail, UserPlan


class NewImageJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageJob
        extra_kwargs = {"original_image": {"required": True, "allow_null": False}}
        fields = ["id", "original_image", "link_expires_in"]

    def __init__(self, user: AbstractBaseUser, instance=None, *args, **kwargs) -> None:
        super().__init__(instance, *args, **kwargs)
        self._user = user
        self._user_plan = None
        if self.instance:
            self.fields.pop("link_expires_in")

    @property
    def data(self) -> ReturnDict:
        data = super().data
        data.pop("original_image")
        return data

    def validate(self, data):
        self._user_plan = UserPlan.objects.select_related("plan").filter(user=self._user).first()
        if self._user_plan is None:
            raise serializers.ValidationError(_("User plan required"))
        return data

    def create(self, validated_data) -> ImageJob:
        return ImageJob.objects.create(user_plan=self._user_plan, **validated_data)  # type: ignore


class ThumbnailSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField("get_image_url")
    external_url = serializers.SerializerMethodField("get_external_url")
    external_url_expires_at = serializers.SerializerMethodField("get_external_url_expires_at")

    class Meta:
        model = Thumbnail
        fields = ["image_url", "external_url", "external_url_expires_at"]

    def get_image_url(self, obj: Thumbnail) -> str:
        request: HttpRequest = self.context["request"]
        return request.build_absolute_uri(obj.image.url)

    def get_external_url(self, obj: Thumbnail) -> Optional[str]:
        if obj.external_id and obj.external_id_expires_at and obj.external_id_expires_at > timezone.now():
            ext = os.path.splitext(obj.image.name)[-1][1:]  # without dot
            path = reverse("ext_image", args=[obj.external_id, ext])
            request: HttpRequest = self.context["request"]
            return request.build_absolute_uri(path)
        return None

    def get_external_url_expires_at(self, obj: Thumbnail) -> Optional[datetime]:
        return obj.external_id_expires_at


class ImageJobSerializer(serializers.ModelSerializer):
    thumbnails = ThumbnailSerializer(many=True, read_only=True)

    class Meta:
        fields = ["id", "thumbnails", "status", "original_image"]
        model = ImageJob
