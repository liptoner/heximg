import logging
import sys
from datetime import timedelta
from io import BytesIO
from os import path
from typing import List, Tuple
from uuid import uuid4

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from django.utils import timezone

from celery import shared_task
from PIL import Image

from core.models import ImageJob, Thumbnail, ThumbnailSize

logger = logging.getLogger(__name__)

SUPPORTED_IMG_FORMATS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG"}

SUPPORTED_IMG_CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


def _img_to_dj_mem_file(img: Image.Image, name: str) -> InMemoryUploadedFile:
    ext = path.splitext(name)[-1]
    output = BytesIO()
    img.save(output, SUPPORTED_IMG_FORMATS[ext])
    return InMemoryUploadedFile(
        file=output,
        field_name="ImageField",
        name=name,
        content_type=SUPPORTED_IMG_CONTENT_TYPES[ext],
        size=sys.getsizeof(output),
        charset=None,
    )


def _resized_width(size: Tuple[int, int], h: int) -> int:
    h_percent = h / size[1]
    return round(size[0] * h_percent)


def _process_thumbnails(img_job: ImageJob) -> List[Thumbnail]:
    plan = img_job.user_plan.plan

    # thumbnails
    img = Image.open(img_job.original_image)
    thumbnails = []
    external_linking_enabled = plan.expiring_link and img_job.link_expires_in
    expires_at = (
        (timezone.now() + timedelta(seconds=img_job.link_expires_in))
        if external_linking_enabled and img_job.link_expires_in
        else None
    )

    for thumbnail_size in ThumbnailSize.objects.filter(plan=plan).order_by("-height"):
        size = (_resized_width(img.size, thumbnail_size.height), thumbnail_size.height)
        img.thumbnail(size, Image.Resampling.LANCZOS)  # in place, that's why qset was sorted
        img_name, ext = path.splitext(path.basename(img_job.original_image.path))
        thumbnails.append(
            Thumbnail(
                height=thumbnail_size.height,
                image=_img_to_dj_mem_file(img, f"{img_name}_thumb_{thumbnail_size.height}{ext}"),
                external_id=uuid4() if external_linking_enabled else None,
                external_id_expires_at=expires_at,
            )
        )

    for thumbnail in thumbnails:
        thumbnail.image_job = img_job

    return thumbnails


@shared_task
def process_image_job(img_job_id: int) -> None:
    img_job = ImageJob.objects.select_related("user_plan__plan").get(id=img_job_id)
    if img_job.status == ImageJob.STATUS_PENDING:
        raise Exception("re-pending job isn't allowed")
    img_job.status = ImageJob.STATUS_PENDING
    img_job.save()
    try:
        thumbnails = _process_thumbnails(img_job)
        with transaction.atomic():
            Thumbnail.objects.bulk_create(thumbnails)
            if not img_job.user_plan.plan.keeping_original_image:
                img_job.original_image.delete(save=True)
                img_job.original_image = None
            img_job.status = ImageJob.STATUS_DONE
            img_job.save()
    except Exception as e:
        logger.error(e)
        img_job.status = ImageJob.STATUS_ERROR
        img_job.save()
