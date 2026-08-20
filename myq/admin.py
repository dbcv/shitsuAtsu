from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.html import format_html

from .models import AccessLog, Photo, Profile, SegmentedPhoto


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "path", "method", "ip_address")
    list_filter = (
        "method",
        "user",
        ("timestamp", admin.DateFieldListFilter),  # 日付範囲フィルタ
    )
    search_fields = ("path", "ip_address", "user_agent", "referer")
    readonly_fields = (
        "timestamp",
        "user",
        "path",
        "method",
        "ip_address",
        "user_agent",
        "referer",
    )
    ordering = ("-timestamp",)

    # 編集を防止（閲覧専用）
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True  # 手動削除は可


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "uploaded_at")
    list_filter = ("owner",)
    search_fields = ("title", "owner__username")


@admin.register(SegmentedPhoto)
class SegmentedPhotoAdmin(admin.ModelAdmin):
    list_display = ("owner", "created_at")
    list_filter = ("owner",)
    search_fields = ("owner__username",)


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "プロフィール情報"
    fk_name = "user"


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)

    @admin.display(description="年齢")
    def get_age(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.age if profile and profile.age is not None else "-"

    @admin.display(description="性別")
    def get_gender(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.get_gender_display() if profile and profile.gender else "-"

    def photos_link(self, obj):
        url = reverse("admin:myq_photo_changelist") + f"?owner__id__exact={obj.id}"

        return format_html('<a href="{}">Photos</a>', url)

    def segmented_link(self, obj):
        url = (
            reverse("admin:myq_segmentedphoto_changelist")
            + f"?owner__id__exact={obj.id}"
        )

        return format_html('<a href="{}">SegmentedPhotos</a>', url)

    list_display = (
        *UserAdmin.list_display,
        "get_age",
        "get_gender",
        "photos_link",
        "segmented_link",
    )


# admin.site.register(Photo)
# admin.site.register(SegmentedPhoto)
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
