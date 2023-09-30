import os

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone

from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import ImageJob, Thumbnail
from core.serializers import ImageJobSerializer, NewImageJobSerializer
from core.tasks import process_image_job


class ImageJobView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    parser_class = [MultiPartParser, FormParser]

    def get_serializer(self, *args, **kwargs):
        context = kwargs.get("context", {})
        context.update({"request": self.request})
        kwargs["context"] = context
        if self.request.method == "POST":
            return NewImageJobSerializer(self.request.user, *args, **kwargs)
        return ImageJobSerializer(*args, **kwargs)

    def get_queryset(self):
        return (
            ImageJob.objects.select_related("user_plan")
            .filter(user_plan__user=self.request.user)
            .prefetch_related("thumbnails")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        super().perform_create(serializer)
        process_image_job.delay(serializer.instance.id)


class ApiCore(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response(
            {
                "image-jobs": request.build_absolute_uri(reverse("image-jobs")),
            }
        )


@api_view(["GET"])
def ext_image(request: HttpRequest, external_id: str, fmt: str) -> HttpResponse:
    thumbnail = get_object_or_404(Thumbnail, external_id=external_id)
    valid_fmt = os.path.splitext(thumbnail.image.path)[-1] == "." + fmt
    expired = thumbnail.external_id_expires_at and thumbnail.external_id_expires_at < timezone.now()
    if not valid_fmt or expired:
        raise Http404()
    return redirect(thumbnail.image.url)
