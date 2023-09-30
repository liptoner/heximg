from django.urls import path

from core import views

urlpatterns = [
    path("image-jobs/", views.ImageJobView.as_view(), name="image-jobs"),
    path("", views.ApiCore.as_view(), name="core"),
    path("image/<slug:external_id>.<str:fmt>", views.ext_image, name="ext_image"),
]
