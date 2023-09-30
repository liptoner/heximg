import os
from datetime import timedelta
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import F
from django.test import TestCase, override_settings
from django.urls import reverse

from parameterized import parameterized
from PIL import Image

from core.models import Plan, Thumbnail, UserPlan

THUMBS_DIR = os.path.join(settings.BASE_DIR, "mediafiles", "thumbs")


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class TestImageJob(TestCase):
    img_path = os.path.join(settings.BASE_DIR, "testdata", "sample.jpg")

    def setUp(self):
        self.user = User.objects.create_user("user1", "user1@example.com", "user1")
        self.client.login(username="user1", password="user1")

    def _post_image(self, filename, link_expires_in=None):
        with open(filename, "rb") as f:
            data = {"original_image": f}
            if link_expires_in:
                data["link_expires_in"] = link_expires_in
            return self.client.post(reverse("image-jobs"), data)

    def _create_user_plan(self, user, plan_title):
        return UserPlan.objects.create(user=user, plan=Plan.objects.get(title=plan_title))

    def _get_thumb_image_height(self, url):
        basename = os.path.basename(url)
        with open(os.path.join(THUMBS_DIR, basename), "rb") as f:
            img = Image.open(f)
            return img.height

    def test_required_auth(self):
        self.client.logout()
        # get
        response = self.client.get(reverse("image-jobs"))
        self.assertEquals(response.status_code, 403)
        self.assertEquals(response.json(), {"detail": "Authentication credentials were not provided."})
        # post
        response = self._post_image(self.img_path)
        self.assertEquals(response.status_code, 403)
        self.assertEquals(response.json(), {"detail": "Authentication credentials were not provided."})

    def test_required_user_plan(self):
        response = self._post_image(self.img_path)
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.json(), {"non_field_errors": ["User plan required"]})

    def test_authorization(self):
        self._create_user_plan(self.user, "Basic")
        response = self._post_image(self.img_path)
        self.assertEquals(response.status_code, 201)
        self.client.logout()

        # no other user has access to the created graphics
        User.objects.create_user("user2", "user2@example.com", "user2")
        self.client.login(username="user2", password="user2")
        response = self.client.get(reverse("image-jobs"))
        job_results = response.json()
        self.assertEquals(len(job_results), 0)

    @parameterized.expand(
        [
            ["Basic", [200]],
            ["Premium", [200, 400]],
            ["Enterprise", [200, 400]],
        ]
    )
    def test_thumbnails_height(self, plan_name, expected_sizes):
        self._create_user_plan(self.user, plan_name)

        response = self._post_image(self.img_path)
        self.assertEquals(response.status_code, 201)

        response = self.client.get(reverse("image-jobs"))
        job_result = response.json()[0]

        thumbnail_sizes = [self._get_thumb_image_height(t["image_url"]) for t in job_result["thumbnails"]]
        self.assertEquals(sorted(thumbnail_sizes), expected_sizes)

    @parameterized.expand(
        [
            ["Basic", False],
            ["Premium", True],
            ["Enterprise", True],
        ]
    )
    def test_keeping_original_img(self, plan_name, keeping):
        self._create_user_plan(self.user, plan_name)

        response = self._post_image(self.img_path)
        self.assertEquals(response.status_code, 201)

        response = self.client.get(reverse("image-jobs"))
        job_result = response.json()[0]

        self.assertEquals(bool(job_result["original_image"]), keeping)

    @parameterized.expand(
        [
            ["Basic"],
            ["Premium"],
        ]
    )
    def test_without_expiring_links(self, plan_name):
        self._create_user_plan(self.user, plan_name)

        response = self._post_image(self.img_path)
        self.assertEquals(response.status_code, 201)

        response = self.client.get(reverse("image-jobs"))
        job_result = response.json()[0]

        self.assertIsNone(job_result["thumbnails"][0]["external_url"])
        self.assertIsNone(job_result["thumbnails"][0]["external_url_expires_at"])

    def test_expiring_links(self):
        self._create_user_plan(self.user, "Enterprise")

        # link_expires_in is optional, but required to prepare external url
        link_expires_in = 300
        response = self._post_image(self.img_path, link_expires_in=link_expires_in)
        self.assertEquals(response.status_code, 201)

        # fetch job result
        response = self.client.get(reverse("image-jobs"))
        job_result = response.json()[0]
        self.assertIsNotNone(job_result["thumbnails"][0]["external_url"])
        self.assertIsNotNone(job_result["thumbnails"][0]["external_url_expires_at"])

        # verify expected redirect
        parsed_url = urlparse(job_result["thumbnails"][0]["image_url"])
        response = self.client.get(job_result["thumbnails"][0]["external_url"], follow=True)
        self.assertEquals([(parsed_url.path, 302)], response.redirect_chain)

        # fake timeout to force the external url to expire
        Thumbnail.objects.update(
            external_id_expires_at=F("external_id_expires_at") - timedelta(seconds=link_expires_in)
        )
        response = self.client.get(job_result["thumbnails"][0]["external_url"])
        self.assertEquals(response.status_code, 404)

        # after timeout external url is removed
        response = self.client.get(reverse("image-jobs"))
        self.assertIsNone(response.json()[0]["thumbnails"][0]["external_url"])
