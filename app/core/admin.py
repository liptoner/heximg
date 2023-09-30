from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth.models import User

from core.models import ImageJob, Plan, Thumbnail, ThumbnailSize, UserPlan

admin.site.unregister(User)


class ThumbnailSizeInline(admin.StackedInline):
    model = ThumbnailSize
    extra = 2


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    inlines = [ThumbnailSizeInline]
    list_display = ("title", "keeping_original_image", "expiring_link")


class PlanInline(admin.StackedInline):
    model = UserPlan
    extra = 1


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    inlines = [PlanInline]


class ThumbnailInline(admin.StackedInline):
    model = Thumbnail
    extra = 0


@admin.register(ImageJob)
class ImageRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "original_image", "user_plan")
    inlines = [ThumbnailInline]
