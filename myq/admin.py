from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.urls import NoReverseMatch, reverse
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
    list_display = ("title", "owner", "image_preview", "uploaded_at")
    list_filter = ("owner",)
    search_fields = ("title", "owner__username")
    readonly_fields = ("uuid", "uploaded_at", "image_preview_large")

    @admin.display(description="画像プレビュー")
    def image_preview(self, obj):
        if obj.image:
            try:
                url = obj.get_image_url_256()
                full_url = obj.get_image_url()
                return format_html(
                    '<a href="{}" target="_blank" rel="noopener noreferrer">'
                    '<img src="{}" style="max-height: 50px; max-width: 80px; object-fit: contain; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);" />'
                    "</a>",
                    full_url,
                    url,
                )
            except (NoReverseMatch, AttributeError, ValueError):
                return "-"
        return "-"

    @admin.display(description="画像プレビュー（大）")
    def image_preview_large(self, obj):
        if obj.image:
            try:
                url = obj.get_image_url()
                return format_html(
                    '<a href="{}" target="_blank" rel="noopener noreferrer">'
                    '<img src="{}" style="max-height: 300px; max-width: 100%; border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.15);" />'
                    '<br><span style="font-size: 0.85em; color: #666;">※クリックで原寸大表示</span>'
                    "</a>",
                    url,
                    url,
                )
            except (NoReverseMatch, AttributeError, ValueError):
                return "-"
        return "-"


@admin.register(SegmentedPhoto)
class SegmentedPhotoAdmin(admin.ModelAdmin):
    list_display = (
        "owner",
        "original_photo",
        "image_preview",
        "rendered_image_preview",
        "created_at",
    )
    list_filter = ("owner",)
    search_fields = ("owner__username",)
    readonly_fields = (
        "uuid",
        "created_at",
        "image_preview_large",
        "rendered_image_preview_large",
    )

    @admin.display(description="切り抜きプレビュー")
    def image_preview(self, obj):
        if obj.image:
            try:
                url = obj.get_image_url_256()
                full_url = obj.get_image_url()
                return format_html(
                    '<a href="{}" target="_blank" rel="noopener noreferrer">'
                    '<img src="{}" style="max-height: 50px; max-width: 80px; object-fit: contain; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);" />'
                    "</a>",
                    full_url,
                    url,
                )
            except (NoReverseMatch, AttributeError, ValueError):
                return "-"
        return "-"

    @admin.display(description="質感再現プレビュー")
    def rendered_image_preview(self, obj):
        if obj.has_rendered_image:
            try:
                url = obj.get_rendered_image_url_256()
                full_url = obj.get_rendered_image_url()
                return format_html(
                    '<a href="{}" target="_blank" rel="noopener noreferrer">'
                    '<img src="{}" style="max-height: 50px; max-width: 80px; object-fit: contain; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);" />'
                    "</a>",
                    full_url,
                    url,
                )
            except (NoReverseMatch, AttributeError, ValueError):
                return "-"
        return "-"

    @admin.display(description="切り抜きプレビュー（大）")
    def image_preview_large(self, obj):
        if obj.image:
            try:
                url = obj.get_image_url()
                return format_html(
                    '<a href="{}" target="_blank" rel="noopener noreferrer">'
                    '<img src="{}" style="max-height: 300px; max-width: 100%; border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.15);" />'
                    '<br><span style="font-size: 0.85em; color: #666;">※クリックで原寸大表示</span>'
                    "</a>",
                    url,
                    url,
                )
            except (NoReverseMatch, AttributeError, ValueError):
                return "-"
        return "-"

    @admin.display(description="質感再現プレビュー（大）")
    def rendered_image_preview_large(self, obj):
        if obj.has_rendered_image:
            try:
                url = obj.get_rendered_image_url()
                return format_html(
                    '<a href="{}" target="_blank" rel="noopener noreferrer">'
                    '<img src="{}" style="max-height: 300px; max-width: 100%; border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.15);" />'
                    '<br><span style="font-size: 0.85em; color: #666;">※クリックで原寸大表示</span>'
                    "</a>",
                    url,
                    url,
                )
            except (NoReverseMatch, AttributeError, ValueError):
                return "-"
        return "-"


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
